from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GITIGNORE = ROOT / ".gitignore"
SPEC = ROOT / "g2e" / "docs" / "P5A_D2S2_EGGINFO_SOURCE_HYGIENE_REPAIR_SPEC.md"


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_root_gitignore_contains_exact_egg_info_pattern():
    lines = GITIGNORE.read_text(encoding="utf-8").splitlines()
    assert "*.egg-info/" in lines


def test_setuptools_src_egg_info_is_ignored_by_git(tmp_path: Path):
    target = ROOT / "src" / "governed_workflow_runtime.egg-info" / "PKG-INFO"
    target.parent.mkdir(parents=True, exist_ok=True)
    created = not target.exists()
    if created:
        target.write_text("synthetic qualification metadata\n", encoding="utf-8")
    try:
        result = _git("check-ignore", "-q", "--", str(target.relative_to(ROOT)))
        assert result.returncode == 0, result.stderr
    finally:
        if created:
            target.unlink(missing_ok=True)
            try:
                target.parent.rmdir()
            except OSError:
                pass


def test_existing_d2s2_execution_files_remain_frozen():
    expected = {
        "scripts/g2e/p5a_d2s2_isolated_volume_oneclick.ps1": "1507b716645971ee60b0c2131973a953f98e7036",
        "scripts/g2e/p5a_d2s2_isolated_volume_preflight.py": "005bd3ff5f34ea60a05d15baa25a0d4f6e9341c3",
    }
    for path, blob in expected.items():
        result = _git("rev-parse", f"HEAD:{path}")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == blob


def test_spec_keeps_repair_zero_science():
    spec = SPEC.read_text(encoding="utf-8")
    assert "NOT AUTHORIZED and NOT CONSUMED" in spec
    assert "No D2-S2 script, preflight, fixture, model, verifier, retry policy" in spec
    assert "does not authorize the D2-S2 scientific attempt or a model turn" in spec
