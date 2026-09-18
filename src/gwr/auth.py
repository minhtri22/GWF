from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .errors import AuthorityDenied, ValidationError
from .utils import canonical_json, uid, utcnow


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64u_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    actor_id: str
    principal_id: str
    session_id: str
    auth_method: str
    issued_at: str
    expires_at: str


class HumanAuthService:
    """Password authentication + signed, revocable bearer sessions for human actors.

    This is intentionally local/self-contained: it supplies a real authentication
    boundary for the alpha runtime without pretending to be an enterprise IdP.
    Production deployments can replace it with OIDC while keeping GovernanceKernel's
    authenticated approval contract unchanged.
    """

    PASSWORD_ITERATIONS = 260_000
    TOKEN_VERSION = "GWR-HS256-v1"

    def __init__(self, db, secret: str | bytes | None = None, *, session_ttl_seconds: int = 900):
        self.db = db
        if secret is None:
            secret = os.environ.get("GWR_AUTH_SECRET")
        if not secret:
            # Safe for ephemeral tests only; restart invalidates sessions by design.
            secret = secrets.token_urlsafe(48)
            self.ephemeral_secret = True
        else:
            self.ephemeral_secret = False
        self.secret = secret.encode("utf-8") if isinstance(secret, str) else secret
        if len(self.secret) < 32:
            raise ValidationError("GWR auth secret must be at least 32 bytes")
        self.session_ttl_seconds = int(session_ttl_seconds)

    @staticmethod
    def _derive(password: str, salt: bytes, iterations: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)

    def register_human(self, actor_id: str, username: str, password: str) -> str:
        actor = self.db.one("SELECT * FROM actors WHERE actor_id=?", (actor_id,))
        if not actor:
            raise ValidationError("Actor does not exist")
        if actor["actor_type"] != "HUMAN":
            raise AuthorityDenied("Credentials may only be registered for HUMAN actors")
        if len(password) < 12:
            raise ValidationError("Password must contain at least 12 characters")
        salt = secrets.token_bytes(16)
        iterations = self.PASSWORD_ITERATIONS
        digest = self._derive(password, salt, iterations)
        cid = uid("cred")
        try:
            self.db.conn.execute(
                "INSERT INTO human_credentials VALUES(?,?,?,?,?,?,?,?,?)",
                (cid, actor_id, username, _b64u(salt), _b64u(digest), iterations, "ACTIVE", utcnow(), None),
            )
            self.db.conn.commit()
        except Exception as exc:
            raise ValidationError("Human username or actor already registered") from exc
        return cid

    def authenticate(self, username: str, password: str, *, client_metadata: dict[str, Any] | None = None) -> str:
        row = self.db.one("SELECT * FROM human_credentials WHERE username=?", (username,))
        if not row or row["status"] != "ACTIVE":
            raise AuthorityDenied("Invalid human credentials")
        expected = _b64u_decode(row["password_hash"])
        actual = self._derive(password, _b64u_decode(row["password_salt"]), int(row["iterations"]))
        if not hmac.compare_digest(expected, actual):
            raise AuthorityDenied("Invalid human credentials")
        actor = self.db.one("SELECT * FROM actors WHERE actor_id=?", (row["actor_id"],))
        if not actor or actor["status"] != "ACTIVE" or actor["actor_type"] != "HUMAN":
            raise AuthorityDenied("Human actor is not active")

        issued = datetime.now(timezone.utc)
        expires = issued + timedelta(seconds=self.session_ttl_seconds)
        sid = uid("sess")
        payload = {
            "v": 1,
            "sid": sid,
            "sub": actor["actor_id"],
            "principal": actor["principal_id"],
            "iat": issued.isoformat(),
            "exp": expires.isoformat(),
            "amr": ["pwd"],
            "nonce": secrets.token_urlsafe(16),
        }
        header = {"alg": "HS256", "typ": self.TOKEN_VERSION}
        h = _b64u(canonical_json(header).encode("utf-8"))
        p = _b64u(canonical_json(payload).encode("utf-8"))
        sig = _b64u(hmac.new(self.secret, f"{h}.{p}".encode("ascii"), hashlib.sha256).digest())
        token = f"{h}.{p}.{sig}"
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self.db.conn.execute(
            "INSERT INTO auth_sessions VALUES(?,?,?,?,?,?,?,?,?)",
            (sid, actor["actor_id"], token_hash, payload["iat"], payload["exp"], None, "PASSWORD", canonical_json(client_metadata or {}), utcnow()),
        )
        self.db.conn.commit()
        return token

    def verify(self, token: str) -> AuthenticatedPrincipal:
        try:
            h, p, sig = token.split(".")
            expected = _b64u(hmac.new(self.secret, f"{h}.{p}".encode("ascii"), hashlib.sha256).digest())
            if not hmac.compare_digest(expected, sig):
                raise AuthorityDenied("Invalid authentication token signature")
            header = json.loads(_b64u_decode(h))
            payload = json.loads(_b64u_decode(p))
        except AuthorityDenied:
            raise
        except Exception as exc:
            raise AuthorityDenied("Malformed authentication token") from exc
        if header.get("typ") != self.TOKEN_VERSION or payload.get("v") != 1:
            raise AuthorityDenied("Unsupported authentication token")
        if _parse_time(payload["exp"]) <= datetime.now(timezone.utc):
            raise AuthorityDenied("Authentication token expired")
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        session = self.db.one("SELECT * FROM auth_sessions WHERE session_id=?", (payload["sid"],))
        if not session or session["revoked_at"] is not None or session["token_hash"] != token_hash:
            raise AuthorityDenied("Authentication session is invalid or revoked")
        actor = self.db.one("SELECT * FROM actors WHERE actor_id=?", (payload["sub"],))
        if not actor or actor["status"] != "ACTIVE" or actor["actor_type"] != "HUMAN":
            raise AuthorityDenied("Authenticated actor is not an active human")
        return AuthenticatedPrincipal(
            actor_id=actor["actor_id"], principal_id=actor["principal_id"], session_id=payload["sid"],
            auth_method="PASSWORD", issued_at=payload["iat"], expires_at=payload["exp"],
        )

    def revoke(self, token: str) -> None:
        principal = self.verify(token)
        self.db.conn.execute("UPDATE auth_sessions SET revoked_at=? WHERE session_id=?", (utcnow(), principal.session_id))
        self.db.conn.commit()
