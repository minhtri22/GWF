from __future__ import annotations

import json
import subprocess
import sys

import pytest

from tools.build_uat_site import assert_no_static_secrets
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
    assert "containsSensitiveMaterial" in js
    assert "purgeSensitiveLocalUatState" in js
    assert "Never enter API keys, tokens, passwords or other secrets." in html
    assert data["projects"][0]["approvals"]
    assert data["projects"][0]["failures"]
    assert meta["authoritative_backend"] is False
    assert meta["secret_storage_allowed"] is False
    assert meta["credential_transport"] == "NONE"
    assert meta["commit"] == "test-sha"


def test_static_secret_scan_rejects_published_secret_material(tmp_path):
    (tmp_path / "index.html").write_text("<html></html>", encoding="utf-8")
    leaked = "github_pat_" + ("A" * 32)
    (tmp_path / "app.js").write_text(f'const token="{leaked}";', encoding="utf-8")
    with pytest.raises(SystemExit, match="STATIC_UAT_SECRET_SCAN_FAILED"):
        assert_no_static_secrets(tmp_path)


def test_static_secret_scan_allows_security_guidance_without_credentials(tmp_path):
    (tmp_path / "index.html").write_text(
        "Never enter API keys, tokens, passwords or other secrets.",
        encoding="utf-8",
    )
    (tmp_path / "app.js").write_text(
        'const note="GitHub Pages is public static hosting";',
        encoding="utf-8",
    )
    assert_no_static_secrets(tmp_path)


def test_static_secret_scan_rejects_secret_field_even_with_placeholder(tmp_path):
    (tmp_path / "config.js").write_text(
        'const config = "api_key: ENV_PLACEHOLDER";',
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="STATIC_UAT_SECRET_SCAN_FAILED"):
        assert_no_static_secrets(tmp_path)
