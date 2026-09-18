from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import os
import tempfile

from .utils import uid, utcnow


@dataclass(frozen=True)
class StoredObject:
    sha256: str
    size_bytes: int
    object_key: str
    content_type: str


class LocalContentAddressedStore:
    """Single-node content-addressed object store with atomic writes and hash verification."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, sha256: str) -> Path:
        return self.root / sha256[:2] / sha256[2:4] / sha256

    def put_bytes(self, data: bytes, *, content_type: str = "application/octet-stream") -> StoredObject:
        digest = hashlib.sha256(data).hexdigest()
        path = self._path(digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            fd, tmp = tempfile.mkstemp(prefix="gwr-obj-", dir=str(path.parent))
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, path)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        meta = path.with_suffix(".json")
        if not meta.exists():
            meta.write_text(json.dumps({"sha256": digest, "size_bytes": len(data), "content_type": content_type}, sort_keys=True), encoding="utf-8")
        return StoredObject(digest, len(data), str(path.relative_to(self.root)).replace("\\", "/"), content_type)

    def put_json(self, payload: Any) -> StoredObject:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return self.put_bytes(raw, content_type="application/json")

    def get_bytes(self, sha256: str) -> bytes:
        path = self._path(sha256)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != sha256:
            raise RuntimeError("object hash mismatch")
        return data

    def verify(self, sha256: str) -> bool:
        try:
            self.get_bytes(sha256)
            return True
        except (FileNotFoundError, RuntimeError):
            return False


class ObjectRefService:
    def __init__(self, db, store: LocalContentAddressedStore):
        self.db = db
        self.store = store

    def attach_bytes(self, project_id: str, owner_kind: str, owner_id: str, data: bytes, *, content_type: str = "application/octet-stream") -> dict[str, Any]:
        obj = self.store.put_bytes(data, content_type=content_type)
        existing = self.db.one(
            "SELECT * FROM object_refs WHERE project_id=? AND owner_kind=? AND owner_id=? AND sha256=?",
            (project_id, owner_kind, owner_id, obj.sha256),
        )
        if existing:
            return dict(existing)
        ref_id = uid("objref")
        self.db.conn.execute(
            "INSERT INTO object_refs VALUES(?,?,?,?,?,?,?,?,?)",
            (ref_id, project_id, owner_kind, owner_id, obj.sha256, obj.size_bytes, obj.content_type, obj.object_key, utcnow()),
        )
        self.db.conn.commit()
        return dict(self.db.one("SELECT * FROM object_refs WHERE ref_id=?", (ref_id,)))

    def attach_json(self, project_id: str, owner_kind: str, owner_id: str, payload: Any) -> dict[str, Any]:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return self.attach_bytes(project_id, owner_kind, owner_id, raw, content_type="application/json")

    def read(self, ref_id: str) -> bytes:
        row = self.db.one("SELECT * FROM object_refs WHERE ref_id=?", (ref_id,))
        if not row:
            raise KeyError(ref_id)
        return self.store.get_bytes(row["sha256"])
