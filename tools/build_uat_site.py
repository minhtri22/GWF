from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
REQUIRED = ["index.html", "styles.css", "app.js", "demo-data.json"]

SECRET_PATTERNS = [
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("github_classic_pat", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "secret_field_assignment",
        re.compile(
            r"""(?ix)
            \b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|authorization)
            \b\s*[:=]
            """
        ),
    ),
]


def assert_no_static_secrets(directory: Path) -> None:
    findings = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        if path.name == ".nojekyll":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    {
                        "file": str(path.relative_to(directory)),
                        "pattern": label,
                        "offset": match.start(),
                    }
                )
    if findings:
        raise SystemExit(
            "STATIC_UAT_SECRET_SCAN_FAILED: "
            + json.dumps(findings, separators=(",", ":"))
        )


def validate_demo(data):
    assert data["product"]["version"] == "0.8.2"
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
    for marker in ("v0.8.2 UAT", "New Project", "Domain Registry", "Process Inspector", "Phase Inspector", "AI Working", "Recovery mode", "Rename project", "Archive project"):
        assert marker in html, f"missing UAT marker: {marker}"
    for marker in ("gwr-uat-domains", "gwr-uat-projects", "openPhase", "simulateProtocolIssue", "approveProtocolRecovery", "renameCurrentProject", "archiveCurrentProject"):
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
        "version": "0.8.2",
        "commit": args.commit,
        "mode": "STATIC_UAT",
        "authoritative_backend": False,
        "secret_storage_allowed": False,
        "credential_transport": "NONE",
    }
    (out / "build-meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    assert_no_static_secrets(out)
    print(json.dumps({
        "status": "PASS",
        "out": str(out),
        "files": sorted(p.name for p in out.iterdir()),
        "projects": len(data["projects"]),
        "static_secret_scan": "PASS",
    }, indent=2))


if __name__ == "__main__":
    main()
