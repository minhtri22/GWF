from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "tools" / "check_public_site_secrets.py"
SPEC = importlib.util.spec_from_file_location("check_public_site_secrets", MODULE_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_current_web_tree_has_no_public_credentials():
    assert MOD.scan_public_tree(ROOT / "web") == []


@pytest.mark.parametrize(
    ("filename", "body", "kind"),
    [
        ("app.js", 'const headers={"Authorization":"Bearer abcdefghijklmnopqrstuvwxyz"};', "bearer_credential"),
        ("app.js", 'localStorage.setItem("my-api-key", value);', "credential_local_storage"),
        ("app.js", 'const cfg={apiKey:"not-public"};', "credential_object_property"),
        ("index.html", '<input type="password" id="token">', "password_input"),
        ("index.html", '<input id="api_key" value="">', "credential_form_field"),
        ("config.json", '{"token":"ghp_abcdefghijklmnopqrstuvwxyz123456"}', "github_classic_token"),
        ("config.json", '{"token":"github_pat_abcdefghijklmnopqrstuvwxyz123456"}', "github_fine_grained_token"),
        ("config.json", '{"token":"sk-abcdefghijklmnopqrstuvwxyz123456"}', "openai_style_secret"),
        ("key.txt", "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----", "private_key"),
    ],
)
def test_public_secret_scanner_rejects_credentials(tmp_path, filename, body, kind):
    path = tmp_path / filename
    path.write_text(body, encoding="utf-8")
    findings = MOD.scan_public_tree(tmp_path)
    assert any(x["kind"] == kind for x in findings), findings
    with pytest.raises(RuntimeError):
        MOD.assert_public_tree_safe(tmp_path)


def test_security_notice_text_is_allowed(tmp_path):
    (tmp_path / "index.html").write_text(
        "<p>Never enter API keys, tokens, passwords, or secrets on this public site.</p>",
        encoding="utf-8",
    )
    assert MOD.scan_public_tree(tmp_path) == []
