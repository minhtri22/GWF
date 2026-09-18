from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv
import hashlib
import json
import math


@dataclass(frozen=True)
class DatasetRecord:
    dataset_id: str
    kind: str
    csv_path: Path
    manifest_path: Path
    manifest: dict[str, Any]


class DatasetRegistry:
    """Pinned development dataset registry with integrity and quality checks.

    Real datasets are local snapshots with explicit source/license metadata. Synthetic
    fixtures are deterministic and intentionally include both healthy and pathological
    cases so the research runtime can test PASS/FAIL/PIVOT/recovery semantics without
    depending on external services.
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        registry = json.loads((self.root / "registry.json").read_text(encoding="utf-8"))
        self.version = str(registry.get("version", "unknown"))
        self._records: dict[str, DatasetRecord] = {}
        for m in registry.get("datasets", []):
            dataset_id = m["dataset_id"]
            matches = list(self.root.rglob(m["file"]))
            if not matches:
                raise FileNotFoundError(f"dataset file not found for {dataset_id}: {m['file']}")
            csv_path = matches[0]
            manifest_candidates = [csv_path.parent / "manifest.json", csv_path.parent / f"{csv_path.stem}.manifest.json"]
            manifest_path = next((p for p in manifest_candidates if p.exists()), csv_path.parent / "manifest.json")
            self._records[dataset_id] = DatasetRecord(dataset_id, m.get("kind", "unknown"), csv_path, manifest_path, m)

    def ids(self) -> list[str]:
        return sorted(self._records)

    def get(self, dataset_id: str) -> DatasetRecord:
        if dataset_id not in self._records:
            raise KeyError(dataset_id)
        return self._records[dataset_id]

    @staticmethod
    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def load_rows(self, dataset_id: str) -> list[dict[str, str]]:
        rec = self.get(dataset_id)
        with rec.csv_path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def validate_integrity(self, dataset_id: str) -> dict[str, Any]:
        rec = self.get(dataset_id)
        rows = self.load_rows(dataset_id)
        actual_hash = self.sha256(rec.csv_path)
        columns = list(rows[0].keys()) if rows else []
        errors: list[str] = []
        if actual_hash != rec.manifest.get("sha256"):
            errors.append("HASH_MISMATCH")
        if len(rows) != int(rec.manifest.get("rows", len(rows))):
            errors.append("ROW_COUNT_MISMATCH")
        expected_cols = list(rec.manifest.get("columns", columns))
        if columns != expected_cols:
            errors.append("SCHEMA_MISMATCH")
        return {
            "dataset_id": dataset_id,
            "ok": not errors,
            "errors": errors,
            "sha256": actual_hash,
            "rows": len(rows),
            "columns": columns,
            "kind": rec.kind,
            "license": rec.manifest.get("license"),
            "source_url": rec.manifest.get("source_url"),
            "doi": rec.manifest.get("doi"),
        }

    def validate_expected_schema(self, dataset_id: str, expected_columns: list[str]) -> dict[str, Any]:
        rows = self.load_rows(dataset_id)
        columns = list(rows[0].keys()) if rows else []
        missing = [c for c in expected_columns if c not in columns]
        extra = [c for c in columns if c not in expected_columns]
        return {"pass": not missing, "missing": missing, "extra": extra, "actual": columns, "expected": expected_columns}

    def missingness(self, dataset_id: str) -> dict[str, float]:
        rows = self.load_rows(dataset_id)
        if not rows:
            return {}
        cols = list(rows[0])
        return {c: sum((r.get(c) is None or str(r.get(c)).strip() == "") for r in rows) / len(rows) for c in cols}

    def detect_exact_target_leakage(self, dataset_id: str, target_column: str) -> list[str]:
        rows = self.load_rows(dataset_id)
        if not rows or target_column not in rows[0]:
            return []
        target = [r[target_column] for r in rows]
        leaks = []
        for c in rows[0]:
            if c in {target_column, "row_id", "id"}:
                continue
            vals = [r[c] for r in rows]
            if vals == target:
                leaks.append(c)
        return leaks

    def group_counts(self, dataset_id: str, group_column: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self.load_rows(dataset_id):
            g = r.get(group_column, "")
            counts[g] = counts.get(g, 0) + 1
        return counts

    def detect_binary_confound_collapse(self, dataset_id: str, group_column: str, value_column: str, confounder_column: str) -> dict[str, Any]:
        rows = self.load_rows(dataset_id)
        groups = sorted({r[group_column] for r in rows})
        strata = sorted({r[confounder_column] for r in rows})
        if len(groups) != 2 or len(strata) < 2:
            return {"flag": False, "reason": "requires two groups and >=2 strata"}
        def mean_for(rs):
            vals = [float(r[value_column]) for r in rs if str(r[value_column]).strip() != ""]
            return sum(vals) / len(vals) if vals else float("nan")
        g0, g1 = groups
        unadj = mean_for([r for r in rows if r[group_column] == g1]) - mean_for([r for r in rows if r[group_column] == g0])
        weighted = 0.0
        total = 0
        details = []
        for z in strata:
            rz = [r for r in rows if r[confounder_column] == z]
            a = [r for r in rz if r[group_column] == g0]
            b = [r for r in rz if r[group_column] == g1]
            if not a or not b:
                continue
            diff = mean_for(b) - mean_for(a)
            weighted += diff * len(rz)
            total += len(rz)
            details.append({"stratum": z, "n": len(rz), "diff": diff})
        adjusted = weighted / total if total else float("nan")
        collapse = abs(adjusted) / abs(unadj) if unadj and math.isfinite(adjusted) else 1.0
        flag = abs(unadj) >= 0.5 and collapse <= 0.25
        return {"flag": flag, "unadjusted_diff": unadj, "stratified_diff": adjusted, "remaining_fraction": collapse, "strata": details}

    def quality_assessment(self, dataset_id: str, *, target_column: str | None = None, max_target_missing: float = 0.10,
                           expected_columns: list[str] | None = None, confounder: dict[str, str] | None = None) -> dict[str, Any]:
        integrity = self.validate_integrity(dataset_id)
        issues = list(integrity["errors"])
        miss = self.missingness(dataset_id)
        if target_column and miss.get(target_column, 0.0) > max_target_missing:
            issues.append("HIGH_TARGET_MISSINGNESS")
        leaks = self.detect_exact_target_leakage(dataset_id, target_column) if target_column else []
        if leaks:
            issues.append("TARGET_LEAKAGE")
        schema = None
        if expected_columns is not None:
            schema = self.validate_expected_schema(dataset_id, expected_columns)
            if not schema["pass"]:
                issues.append("SCHEMA_DRIFT")
        conf = None
        if confounder:
            conf = self.detect_binary_confound_collapse(dataset_id, confounder["group"], confounder["value"], confounder["column"])
            if conf.get("flag"):
                issues.append("CRITICAL_CONFOUND")
        return {
            "dataset_id": dataset_id,
            "pass": not issues,
            "issues": sorted(set(issues)),
            "integrity": integrity,
            "missingness": miss,
            "leak_columns": leaks,
            "schema": schema,
            "confound_check": conf,
        }
