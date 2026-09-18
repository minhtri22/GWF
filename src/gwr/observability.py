from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any
import json
import time

from .utils import utcnow


class NullObserver:
    def emit(self, event: str, **attrs):
        return None
    def metrics(self):
        return {"events": 0, "by_event": {}}


class JsonlObserver:
    """Minimal structured single-node observability sink used before external telemetry backends."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._counts: dict[str, int] = {}
        self._latencies: dict[str, list[float]] = {}

    def emit(self, event: str, **attrs):
        rec = {"timestamp": utcnow(), "event": event, **attrs}
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
            self._counts[event] = self._counts.get(event, 0) + 1
            if attrs.get("latency_ms") is not None:
                self._latencies.setdefault(event, []).append(float(attrs["latency_ms"]))
        return rec

    def metrics(self):
        with self._lock:
            latency = {}
            for event, vals in self._latencies.items():
                s = sorted(vals)
                latency[event] = {"count": len(s), "p50_ms": s[len(s)//2], "max_ms": s[-1]}
            return {"events": sum(self._counts.values()), "by_event": dict(self._counts), "latency": latency}


class Timer:
    def __init__(self): self.started = time.perf_counter()
    def ms(self): return (time.perf_counter() - self.started) * 1000.0
