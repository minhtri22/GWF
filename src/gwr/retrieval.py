from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .utils import canonical_json, utcnow


class RetrievalError(RuntimeError):
    pass


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str


class HttpTransport(Protocol):
    def request(self, url: str, headers: dict[str, str], timeout: float) -> HttpResponse: ...


class UrllibTransport:
    def request(self, url: str, headers: dict[str, str], timeout: float) -> HttpResponse:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                return HttpResponse(int(getattr(r, "status", 200)), {k.lower(): v for k, v in r.headers.items()}, body, r.geturl())
        except urllib.error.HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            return HttpResponse(int(exc.code), {k.lower(): v for k, v in (exc.headers.items() if exc.headers else [])}, body, url)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RetrievalError(f"network_error:{type(exc).__name__}:{exc}") from exc


@dataclass(frozen=True)
class RetrievalPolicy:
    timeout_seconds: float = 10.0
    max_attempts: int = 4
    backoff_seconds: float = 0.25
    max_backoff_seconds: float = 4.0
    max_response_bytes: int = 5_000_000
    cache_ttl_seconds: int = 86_400
    allow_private_hosts: bool = False


class DurableRetrievalCache:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(value: Any) -> str:
        return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

    def get(self, key: str, *, ttl_seconds: int) -> dict[str, Any] | None:
        p = self.directory / f"{key}.json"
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            age = time.time() - float(data.get("cached_epoch", 0))
            if ttl_seconds >= 0 and age > ttl_seconds:
                return None
            return data
        except Exception:
            return None

    def put(self, key: str, payload: dict[str, Any]) -> Path:
        p = self.directory / f"{key}.json"
        tmp = p.with_suffix(".tmp")
        data = dict(payload)
        data["cached_epoch"] = time.time()
        data["cached_at"] = utcnow()
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        os.replace(tmp, p)
        return p


class ResilientHttpClient:
    RETRYABLE = {408, 425, 429, 500, 502, 503, 504}

    def __init__(self, *, user_agent: str, policy: RetrievalPolicy | None = None, transport: HttpTransport | None = None, sleep=time.sleep):
        self.user_agent = user_agent
        self.policy = policy or RetrievalPolicy()
        self.transport = transport or UrllibTransport()
        self.sleep = sleep

    def _validate_url(self, url: str) -> None:
        u = urllib.parse.urlparse(url)
        if u.scheme != "https":
            raise RetrievalError("only_https_sources_are_allowed")
        if not u.hostname:
            raise RetrievalError("source_hostname_missing")
        if self.policy.allow_private_hosts:
            return
        try:
            infos = socket.getaddrinfo(u.hostname, u.port or 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise RetrievalError(f"dns_unavailable:{u.hostname}:{exc}") from exc
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
                raise RetrievalError(f"unsafe_source_address:{ip}")

    def get(self, url: str, *, accept: str = "application/json,text/html,application/pdf;q=0.9,*/*;q=0.1", extra_headers: dict[str, str] | None = None) -> HttpResponse:
        self._validate_url(url)
        headers = {"User-Agent": self.user_agent, "Accept": accept}
        headers.update(extra_headers or {})
        last: Exception | None = None
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                response = self.transport.request(url, headers, self.policy.timeout_seconds)
            except RetrievalError as exc:
                last = exc
                if attempt == self.policy.max_attempts:
                    raise
                self.sleep(min(self.policy.max_backoff_seconds, self.policy.backoff_seconds * (2 ** (attempt - 1))))
                continue
            if len(response.body) > self.policy.max_response_bytes:
                raise RetrievalError(f"response_too_large:{len(response.body)}")
            if 200 <= response.status < 300:
                return response
            if response.status not in self.RETRYABLE or attempt == self.policy.max_attempts:
                raise RetrievalError(f"http_status:{response.status}")
            retry_after = response.headers.get("retry-after")
            try:
                wait = float(retry_after) if retry_after is not None else self.policy.backoff_seconds * (2 ** (attempt - 1))
            except ValueError:
                wait = self.policy.backoff_seconds * (2 ** (attempt - 1))
            self.sleep(min(self.policy.max_backoff_seconds, max(0.0, wait)))
        raise last or RetrievalError("request_failed")


class CrossrefConnector:
    BASE = "https://api.crossref.org/works"

    def __init__(self, client: ResilientHttpClient, cache: DurableRetrievalCache, *, mailto: str, cache_ttl_seconds: int = 86_400):
        if "@" not in mailto:
            raise ValueError("Crossref polite-pool mailto must be an email address")
        self.client = client
        self.cache = cache
        self.mailto = mailto
        self.cache_ttl_seconds = cache_ttl_seconds

    @staticmethod
    def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
        title = (item.get("title") or [""])[0]
        authors = []
        for a in item.get("author") or []:
            name = " ".join(x for x in [a.get("given"), a.get("family")] if x)
            if name:
                authors.append(name)
        issued = item.get("issued", {}).get("date-parts", [[None]])
        year = issued[0][0] if issued and issued[0] else None
        return {
            "title": title,
            "authors": authors,
            "year": year,
            "doi": item.get("DOI"),
            "url": item.get("URL"),
            "type": item.get("type"),
            "publisher": item.get("publisher"),
            "abstract": item.get("abstract"),
            "source": "crossref",
        }

    def search(self, query: str, *, rows: int = 10, allow_cache: bool = True) -> dict[str, Any]:
        rows = max(1, min(int(rows), 50))
        request = {"provider": "crossref", "query": query, "rows": rows, "mailto": self.mailto}
        key = self.cache.key(request)
        if allow_cache:
            cached = self.cache.get(key, ttl_seconds=self.cache_ttl_seconds)
            if cached:
                return {**cached["payload"], "retrieval": {**cached["payload"]["retrieval"], "cache_hit": True}}
        params = urllib.parse.urlencode({"query.bibliographic": query, "rows": rows, "mailto": self.mailto, "select": "DOI,title,author,issued,URL,type,publisher,abstract"})
        url = f"{self.BASE}?{params}"
        response = self.client.get(url, accept="application/json")
        try:
            decoded = json.loads(response.body.decode("utf-8"))
            items = decoded["message"]["items"]
        except Exception as exc:
            raise RetrievalError("crossref_invalid_json") from exc
        normalized = [self._normalize_item(x) for x in items]
        result = {
            "records": normalized,
            "retrieval": {
                "provider": "crossref",
                "request_url": url,
                "status": response.status,
                "response_sha256": hashlib.sha256(response.body).hexdigest(),
                "retrieved_at": utcnow(),
                "cache_hit": False,
                "rate_limit": response.headers.get("x-rate-limit-limit"),
                "rate_interval": response.headers.get("x-rate-limit-interval"),
                "concurrency_limit": response.headers.get("x-concurrency-limit"),
            },
        }
        self.cache.put(key, {"request": request, "payload": result})
        return result


class WebDocumentConnector:
    def __init__(self, client: ResilientHttpClient, cache: DurableRetrievalCache, *, cache_ttl_seconds: int = 86_400):
        self.client = client
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds

    def fetch(self, url: str, *, allow_cache: bool = True) -> dict[str, Any]:
        request = {"provider": "web", "url": url}
        key = self.cache.key(request)
        if allow_cache:
            cached = self.cache.get(key, ttl_seconds=self.cache_ttl_seconds)
            if cached:
                return {**cached["payload"], "retrieval": {**cached["payload"]["retrieval"], "cache_hit": True}}
        response = self.client.get(url)
        ctype = response.headers.get("content-type", "application/octet-stream").split(";", 1)[0].strip().lower()
        if not (ctype.startswith("text/") or ctype in {"application/json", "application/pdf", "application/xml", "application/xhtml+xml", "application/octet-stream"}):
            raise RetrievalError(f"unsupported_content_type:{ctype}")
        payload = {
            "url": response.url,
            "status": response.status,
            "content_type": ctype,
            "bytes": len(response.body),
            "sha256": hashlib.sha256(response.body).hexdigest(),
            "retrieval": {"provider": "web", "retrieved_at": utcnow(), "cache_hit": False},
        }
        self.cache.put(key, {"request": request, "payload": payload})
        return payload


class ProductionPaperRetriever:
    """Production-oriented paper/web retrieval facade.

    Live provider errors are explicit. An offline seed snapshot is only used when
    configured by the caller, and every returned record is provenance-labelled.
    """

    def __init__(self, crossref: CrossrefConnector, web: WebDocumentConnector | None = None, *, offline_records: list[dict[str, Any]] | None = None):
        self.crossref = crossref
        self.web = web
        self.offline_records = list(offline_records or [])

    def search_papers(self, query: str, *, rows: int = 10, offline_fallback: bool = False) -> dict[str, Any]:
        try:
            return self.crossref.search(query, rows=rows)
        except Exception as exc:
            if not offline_fallback:
                raise
            if not self.offline_records:
                raise RetrievalError(f"live_retrieval_failed_and_no_offline_snapshot:{exc}") from exc
            terms = query.lower().split()
            scored = []
            for rec in self.offline_records:
                text = canonical_json(rec).lower()
                score = sum(t in text for t in terms)
                if score:
                    scored.append((score, rec))
            records = [dict(x[1]) for x in sorted(scored, key=lambda x: -x[0])[:rows]] or [dict(x) for x in self.offline_records[:rows]]
            for r in records:
                r["source"] = r.get("source") or "offline-provenance-snapshot"
            return {
                "records": records,
                "retrieval": {
                    "provider": "offline-provenance-snapshot",
                    "cache_hit": True,
                    "live_error": f"{type(exc).__name__}:{exc}",
                    "retrieved_at": utcnow(),
                    "degraded": True,
                },
            }
