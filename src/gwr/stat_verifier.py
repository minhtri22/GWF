from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .utils import canonical_json


class IndependentVerifierError(RuntimeError):
    pass


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class SubprocessStatisticalVerifier:
    """Runs the statistical verification in a separate Python process.

    Only raw experiment rows + precommitted thresholds cross the boundary. Aggregate
    metrics produced by the experiment process are intentionally ignored and recomputed.
    """

    def __init__(self, *, timeout_seconds: int = 30):
        self.timeout_seconds = int(timeout_seconds)

    def verify(self, metrics: dict[str, Any], *, min_relative_reduction: float = 0.20, sign_test_alpha: float = 0.05) -> dict[str, Any]:
        rows = metrics.get("rows")
        if not isinstance(rows, list) or not rows:
            raise IndependentVerifierError("raw experiment rows are required")
        request = {
            "rows": rows,
            "expected_row_count": len(rows),
            "min_relative_reduction": float(min_relative_reduction),
            "sign_test_alpha": float(sign_test_alpha),
        }
        expected_hash = _sha256_json(request)
        with tempfile.TemporaryDirectory(prefix="gwr-stat-verify-") as td:
            inp = Path(td) / "request.json"
            out = Path(td) / "result.json"
            inp.write_text(json.dumps(request, sort_keys=True), encoding="utf-8")
            env = dict(os.environ)
            src = str(Path(__file__).resolve().parents[1])
            env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
            proc = subprocess.run(
                [sys.executable, "-m", "gwr.stat_verifier_worker", "--input", str(inp), "--output", str(out)],
                capture_output=True, text=True, timeout=self.timeout_seconds, env=env,
            )
            if proc.returncode != 0:
                raise IndependentVerifierError(f"verifier_process_failed:{proc.returncode}:{proc.stderr.strip()}")
            try:
                result = json.loads(out.read_text(encoding="utf-8"))
            except Exception as exc:
                raise IndependentVerifierError("verifier_output_invalid") from exc
        if result.get("worker_pid") == os.getpid():
            raise IndependentVerifierError("verifier_not_process_isolated")
        if result.get("input_sha256") != expected_hash:
            raise IndependentVerifierError("verifier_input_hash_mismatch")
        claimed = result.get("result_sha256")
        unsigned = dict(result)
        unsigned.pop("result_sha256", None)
        if claimed != _sha256_json(unsigned):
            raise IndependentVerifierError("verifier_result_hash_mismatch")
        result["independent_process"] = True
        result["parent_pid"] = os.getpid()
        return result
