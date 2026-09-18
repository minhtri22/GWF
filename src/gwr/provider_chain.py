from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import time

from .utils import uid, utcnow, canonical_json


@dataclass(frozen=True)
class ProviderAttempt:
    provider: str
    outcome: str
    latency_ms: int
    error: str | None = None


class ProviderFailoverChain:
    """Ordered provider failover with explicit attempt provenance; it never hides degradation."""
    def __init__(self, providers: list[tuple[str, Any]], *, db=None, observer=None):
        if not providers:
            raise ValueError("at least one provider required")
        self.providers = providers
        self.db = db
        self.observer = observer

    def call(self, operation: str, *args, project_id: str | None = None, accept=None, **kwargs) -> dict[str, Any]:
        attempts: list[ProviderAttempt] = []
        last: Exception | None = None
        accept = accept or (lambda x: x is not None)
        for name, provider in self.providers:
            started = time.perf_counter()
            try:
                fn = getattr(provider, operation)
                value = fn(*args, **kwargs)
                latency = int((time.perf_counter() - started) * 1000)
                if not accept(value):
                    raise RuntimeError("provider returned unacceptable result")
                attempt = ProviderAttempt(name, "SUCCESS", latency)
                attempts.append(attempt)
                self._record(project_id, operation, attempt)
                return {"value": value, "provider": name, "degraded": len(attempts) > 1, "attempts": [a.__dict__ for a in attempts]}
            except Exception as exc:
                last = exc
                latency = int((time.perf_counter() - started) * 1000)
                attempt = ProviderAttempt(name, "FAILED", latency, f"{type(exc).__name__}:{exc}")
                attempts.append(attempt)
                self._record(project_id, operation, attempt)
        raise RuntimeError(f"all providers failed for {operation}: {last}; attempts={[a.__dict__ for a in attempts]}")

    def _record(self, project_id, operation, attempt: ProviderAttempt):
        if self.observer:
            self.observer.emit("provider_attempt", project_id=project_id, provider=attempt.provider, operation=operation, outcome=attempt.outcome, latency_ms=attempt.latency_ms, error=attempt.error)
        if self.db:
            self.db.conn.execute(
                "INSERT INTO provider_events VALUES(?,?,?,?,?,?,?,?,?)",
                (uid("provev"), project_id, attempt.provider, operation, attempt.outcome, attempt.latency_ms, attempt.error, canonical_json({}), utcnow()),
            )
            self.db.conn.commit()


class ScholarlyProviderChain:
    def __init__(self, chain: ProviderFailoverChain): self.chain = chain
    def search_papers(self, query: str, rows: int = 10, offline_fallback: bool = False, *, project_id: str | None = None):
        result = self.chain.call("search_papers", query, rows=rows, offline_fallback=offline_fallback, project_id=project_id, accept=lambda x: isinstance(x, dict) and bool(x.get("records")))
        value = dict(result["value"])
        value.setdefault("retrieval", {})
        value["retrieval"] = {**value["retrieval"], "selected_provider": result["provider"], "degraded": bool(value["retrieval"].get("degraded")) or result["degraded"], "provider_attempts": result["attempts"]}
        return value
