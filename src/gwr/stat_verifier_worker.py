from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def exact_two_sided_sign_test(positive: int, negative: int) -> float:
    n = positive + negative
    if n == 0:
        return 1.0
    k = min(positive, negative)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def verify_payload(request: dict[str, Any]) -> dict[str, Any]:
    rows = request.get("rows") or []
    if not rows:
        raise ValueError("verification request contains no raw rows")
    threshold = float(request["min_relative_reduction"])
    expected_count = int(request.get("expected_row_count", len(rows)))
    if len(rows) != expected_count:
        raise ValueError(f"row_count_mismatch:{len(rows)}!={expected_count}")

    by_n: dict[str, dict[str, Any]] = {}
    positive = negative = ties = 0
    w_abs = []
    a_abs = []
    for row in rows:
        n = str(int(row["n"]))
        w = float(row["wilson_coverage"])
        a = float(row["wald_coverage"])
        if not (0.0 <= w <= 1.0 and 0.0 <= a <= 1.0):
            raise ValueError("coverage_out_of_range")
        we = abs(w - 0.95)
        ae = abs(a - 0.95)
        w_abs.append(we)
        a_abs.append(ae)
        delta = ae - we
        if delta > 1e-15:
            positive += 1
        elif delta < -1e-15:
            negative += 1
        else:
            ties += 1
        bucket = by_n.setdefault(n, {"w": [], "a": []})
        bucket["w"].append(we)
        bucket["a"].append(ae)

    wilson_mae = sum(w_abs) / len(w_abs)
    wald_mae = sum(a_abs) / len(a_abs)
    relative = (wald_mae - wilson_mae) / wald_mae if wald_mae else 0.0
    per_n = {
        n: {
            "wilson_mae": sum(v["w"]) / len(v["w"]),
            "wald_mae": sum(v["a"]) / len(v["a"]),
        }
        for n, v in by_n.items()
    }
    all_n_improve = all(v["wilson_mae"] < v["wald_mae"] for v in per_n.values())
    p_value = exact_two_sided_sign_test(positive, negative)
    passed = bool(relative >= threshold and all_n_improve and p_value < float(request.get("sign_test_alpha", 0.05)))
    result = {
        "pass": passed,
        "relative_mae_reduction": relative,
        "all_n_improve": all_n_improve,
        "positive_points": positive,
        "negative_points": negative,
        "ties": ties,
        "sign_test_p_value": p_value,
        "threshold": threshold,
        "recomputed": {"wilson_mae": wilson_mae, "wald_mae": wald_mae, "by_n": per_n},
        "worker_pid": os.getpid(),
        "verifier_version": "independent-stat-verifier-v0.4",
        "input_sha256": sha256_json(request),
    }
    result["result_sha256"] = sha256_json(result)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    request = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = verify_payload(request)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
