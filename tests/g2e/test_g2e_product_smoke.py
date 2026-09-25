from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "g2e_product_smoke.py"


def load_module():
    spec = spec_from_file_location("g2e_product_smoke", SCRIPT)
    mod = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_config_limits_write_and_disables_network(tmp_path):
    mod = load_module()
    result = tmp_path / "result.json"
    cfg = mod.build_config(result)
    assert 'model = "chatgpt-web/high"' in cfg
    assert 'openai_base_url = "http://127.0.0.1:17841/v1"' in cfg
    assert '":root" = "read"' in cfg
    assert 'enabled = false' in cfg
    assert "result.json" in cfg


def test_route_projection_extracts_broker_and_mcp():
    mod = load_module()
    out = mod.route_projection([
        '[chatgpt-web] broker trace=abcDEF12 registered tokenHash=123456abcdef',
        '[chatgpt-web-mcp] exec_command scope=x',
        '[chatgpt-web] broker trace=abcDEF12 completed call=call_1 pending=0',
    ])
    assert out["broker_registrations"][0]["trace_id"] == "abcDEF12"
    assert out["broker_completions"][0]["call"] == "call_1"
    assert out["mcp_tools"] == ["exec_command"]


def test_health_probe_is_native_python_not_nested_powershell():
    src = SCRIPT.read_text(encoding="utf-8")
    assert 'urllib.request.urlopen' in src
    assert '"powershell"' not in src
    assert 'launcher_log = launcher_data / "logs" / "launcher.jsonl"' in src


def test_powershell_wrapper_autostarts_custom_runtime_when_down():
    ps1 = (ROOT / "scripts" / "g2e" / "g2e_product_smoke.ps1").read_text(encoding="utf-8")
    assert "Start-CustomCgwRuntime" in ps1
    assert "CODEX_WEB_GPT_LAUNCHER_DATA_DIR" in ps1
    assert "CODEX_CHATGPT_WEB_HOME" in ps1
    assert "CUSTOM_CGW_RUNTIME_START_TIMEOUT" in ps1
    assert "Start-Process -FilePath $Launcher -PassThru" in ps1
