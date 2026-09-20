from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_uat_site_build_contains_product_surfaces(tmp_path):
    out = tmp_path / "site"
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_uat_site.py"), "--out", str(out), "--commit", "test-sha"], check=True)
    html = (out / "index.html").read_text(encoding="utf-8")
    js = (out / "app.js").read_text(encoding="utf-8")
    data = json.loads((out / "demo-data.json").read_text(encoding="utf-8"))
    meta = json.loads((out / "build-meta.json").read_text(encoding="utf-8"))
    assert "Pending approvals" in html
    assert "Failure & recovery" in html
    assert "Distributed runtime" in html
    assert "Domain SDK" in html
    assert "localStorage" in js
    assert data["projects"][0]["approvals"]
    assert data["projects"][0]["failures"]
    assert meta["authoritative_backend"] is False
    assert meta["commit"] == "test-sha"
    assert meta["credential_policy"] == "PUBLIC_STATIC_NO_CREDENTIALS"
    assert meta["accepts_api_keys"] is False
    assert meta["credential_storage"] == "NONE"
    assert "No credentials:" in html
    assert "connect-src 'self'" in html
