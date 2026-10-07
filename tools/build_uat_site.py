from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
REQUIRED = ["index.html", "styles.css", "app.js"]


def validate_shell() -> None:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")

    for marker in (
        "Governed Knowledge Studio",
        "BPS-I00",
        "System",
        "Light",
        "Dark",
        "sidebarToggle",
        "LIVE FOUNDATION",
    ):
        assert marker in html, f"missing BPS-I00 shell marker: {marker}"

    for marker in (
        "/browser/bootstrap",
        "/browser/auth/login",
        "/browser/auth/me",
        "/browser/auth/logout",
        "gwr-ui-theme",
        "gwr-ui-sidebar",
    ):
        assert marker in js, f"missing BPS-I00 client marker: {marker}"

    for forbidden in (
        "demo-data.json",
        "gwr-uat-domains",
        "gwr-uat-projects",
        "simulateProtocolIssue",
        "approveProtocolRecovery",
    ):
        assert forbidden not in js, f"legacy static-UAT behavior remains: {forbidden}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist" / "shell-snapshot"))
    ap.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "local"))
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    validate_shell()
    for name in REQUIRED:
        src = WEB / name
        if not src.exists():
            raise SystemExit(f"missing web asset: {name}")
        shutil.copy2(src, out / name)

    (out / ".nojekyll").write_text("", encoding="utf-8")
    meta = {
        "product": "Governed Workflow Runtime",
        "slice": "BPS-I00",
        "commit": args.commit,
        "mode": "STATIC_SHELL_SNAPSHOT",
        "authoritative_backend": False,
        "runtime_required_for_product_uat": True,
    }
    (out / "build-meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "out": str(out),
        "files": sorted(p.name for p in out.iterdir()),
        "mode": meta["mode"],
    }, indent=2))


if __name__ == "__main__":
    main()
