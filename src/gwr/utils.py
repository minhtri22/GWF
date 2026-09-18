from __future__ import annotations
import hashlib, json, uuid
from datetime import datetime, timezone
from typing import Any

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

def parse_json(value: str | None, default=None):
    if value is None: return default
    return json.loads(value)
