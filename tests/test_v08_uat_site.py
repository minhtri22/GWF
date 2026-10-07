from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_static_shell_snapshot_contains_only_bps_i00_foundation(tmp_path):
    out = tmp_path / "site"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "build_uat_site.py"),
            "--out",
            str(out),
            "--commit",
            "test-sha",
        ],
        check=True,
    )

    html = (out / "index.html").read_text(encoding="utf-8")
    js = (out / "app.js").read_text(encoding="utf-8")
    meta = json.loads((out / "build-meta.json").read_text(encoding="utf-8"))

    assert "Governed Knowledge Studio" in html
    assert "BPS-I00" in html
    assert "LIVE FOUNDATION" in html
    assert "Pending approvals" not in html
    assert "Failure & recovery" not in html
    assert "Distributed runtime" not in html

    assert "/browser/bootstrap" in js
    assert "/browser/auth/login" in js
    assert "gwr-ui-theme" in js
    assert "gwr-ui-sidebar" in js
    assert "demo-data.json" not in js
    assert "gwr-uat-domains" not in js

    assert not (out / "demo-data.json").exists()
    assert meta["mode"] == "STATIC_SHELL_SNAPSHOT"
    assert meta["authoritative_backend"] is False
    assert meta["runtime_required_for_product_uat"] is True
    assert meta["commit"] == "test-sha"
