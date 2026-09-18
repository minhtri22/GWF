from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
REQUIRED = ["index.html", "styles.css", "app.js", "demo-data.json"]


def validate_demo(data):
    assert data["product"]["version"] == "0.8.1"
    assert data["product"]["mode"] == "STATIC_UAT"
    assert data["projects"], "at least one UAT project is required"
    for p in data["projects"]:
        for key in ("id", "name", "status", "metrics", "phases", "approvals", "failures", "distributed"):
            assert key in p, f"project missing {key}"
    first = data["projects"][0]
    assert first["approvals"], "primary UAT project must exercise approval UX"
    assert first["failures"], "primary UAT project must exercise failure/recovery visualization"
    assert first["distributed"]["jobs"], "primary UAT project must exercise distributed dashboard"
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    for marker in ("New Project", "Domain Registry", "Process Inspector", "Phase Inspector"):
        assert marker in html, f"missing UAT marker: {marker}"
    for marker in ("gwr-uat-domains", "gwr-uat-projects", "openPhase"):
        assert marker in js, f"missing lifecycle simulation marker: {marker}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist" / "uat"))
    ap.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "local"))
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in REQUIRED:
        src = WEB / name
        if not src.exists():
            raise SystemExit(f"missing web asset: {name}")
        shutil.copy2(src, out / name)
    data = json.loads((WEB / "demo-data.json").read_text(encoding="utf-8"))
    validate_demo(data)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    meta = {
        "product": "GWR Research Product Alpha",
        "version": "0.8.1",
        "commit": args.commit,
        "mode": "STATIC_UAT",
        "authoritative_backend": False,
    }
    (out / "build-meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "out": str(out), "files": sorted(p.name for p in out.iterdir()), "projects": len(data["projects"])}, indent=2))


if __name__ == "__main__":
    main()
