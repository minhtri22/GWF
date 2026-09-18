from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import math
import random
import subprocess
import sys
import os


class TabularStatistics:
    @staticmethod
    def mean(xs: list[float]) -> float:
        return sum(xs) / len(xs)

    @staticmethod
    def effect(rows: list[dict[str, Any]], group_col: str, value_col: str, a: str, b: str) -> dict[str, Any]:
        va = [float(r[value_col]) for r in rows if str(r[group_col]) == str(a) and str(r[value_col]).strip() != ""]
        vb = [float(r[value_col]) for r in rows if str(r[group_col]) == str(b) and str(r[value_col]).strip() != ""]
        if not va or not vb:
            raise ValueError("empty comparison group")
        return {"n_a": len(va), "n_b": len(vb), "mean_a": TabularStatistics.mean(va), "mean_b": TabularStatistics.mean(vb), "difference_b_minus_a": TabularStatistics.mean(vb) - TabularStatistics.mean(va)}

    @staticmethod
    def permutation_pvalue(rows: list[dict[str, Any]], group_col: str, value_col: str, a: str, b: str, *, permutations: int = 4000, seed: int = 170917) -> float:
        va = [float(r[value_col]) for r in rows if str(r[group_col]) == str(a) and str(r[value_col]).strip() != ""]
        vb = [float(r[value_col]) for r in rows if str(r[group_col]) == str(b) and str(r[value_col]).strip() != ""]
        obs = abs(TabularStatistics.mean(vb) - TabularStatistics.mean(va))
        vals = va + vb
        na = len(va)
        rng = random.Random(seed)
        extreme = 0
        work = vals[:]
        for _ in range(permutations):
            rng.shuffle(work)
            diff = abs(TabularStatistics.mean(work[na:]) - TabularStatistics.mean(work[:na]))
            if diff >= obs - 1e-15:
                extreme += 1
        return (extreme + 1) / (permutations + 1)

    @classmethod
    def verify(cls, payload: dict[str, Any]) -> dict[str, Any]:
        rows = payload["rows"]
        spec = payload["spec"]
        effect = cls.effect(rows, spec["group_column"], spec["value_column"], str(spec["group_a"]), str(spec["group_b"]))
        p = cls.permutation_pvalue(rows, spec["group_column"], spec["value_column"], str(spec["group_a"]), str(spec["group_b"]), permutations=int(spec.get("permutations", 4000)), seed=int(spec.get("seed", 170917)))
        min_effect = float(spec.get("min_effect", 0.0))
        alpha = float(spec.get("alpha", 0.05))
        min_per_group = int(spec.get("min_per_group", 20))
        sufficient = effect["n_a"] >= min_per_group and effect["n_b"] >= min_per_group
        passed = bool(sufficient and effect["difference_b_minus_a"] >= min_effect and p < alpha)
        return {"pass": passed, "sufficient_sample": sufficient, "effect": effect, "permutation_p_value": p, "min_effect": min_effect, "alpha": alpha, "min_per_group": min_per_group}


@dataclass
class SubprocessTabularVerifier:
    timeout_seconds: float = 30.0

    def verify(self, rows: list[dict[str, Any]], spec: dict[str, Any]) -> dict[str, Any]:
        payload = {"rows": rows, "spec": spec}
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        input_hash = hashlib.sha256(raw).hexdigest()
        env = os.environ.copy()
        src_root = str(Path(__file__).resolve().parents[1])
        env["PYTHONPATH"] = src_root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        proc = subprocess.run([sys.executable, "-m", "gwr.tabular_verifier_worker"], input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=self.timeout_seconds, check=False, env=env)
        if proc.returncode != 0:
            raise RuntimeError(f"tabular verifier failed rc={proc.returncode}: {proc.stderr.decode(errors='replace')}")
        out = json.loads(proc.stdout.decode())
        if out.get("input_sha256") != input_hash:
            raise RuntimeError("tabular verifier input hash mismatch")
        out["independent_process"] = True
        out["process_returncode"] = proc.returncode
        return out
