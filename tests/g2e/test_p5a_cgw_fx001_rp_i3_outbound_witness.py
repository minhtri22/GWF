from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "g2e" / "p5a_cgw_fx001_rp_i3_outbound_witness.py"
DESIGN = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_RP_I3_DESIGN.json"


def load_module():
    spec = spec_from_file_location("rp_i3", SCRIPT)
    mod = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_projection_is_bounded_and_does_not_copy_prompt_or_auth():
    mod = load_module()
    body = {
        "model": "chatgpt-web/high",
        "input": [{"role": "user", "content": "SECRET_PROMPT"}],
        "instructions": "SECRET_INSTRUCTIONS",
        "metadata": {"thread_id": "t1", "turn_trigger": "user"},
        "tools": [
            {"type": "function", "name": "apply_patch", "description": "SECRET_SCHEMA"},
            {"type": "function", "function": {"name": "shell", "parameters": {"secret": True}}},
        ],
    }
    raw = __import__("json").dumps(body).encode()
    headers = __import__("email.message").message.Message()
    headers["Authorization"] = "Bearer SECRET_TOKEN"
    out = mod.bounded_projection("POST", "/v1/responses", headers, raw)
    encoded = __import__("json").dumps(out)
    assert out["model"] == "chatgpt-web/high"
    assert out["tool_count"] == 2
    assert out["tools"] == [
        {"type": "function", "name": "apply_patch"},
        {"type": "function", "name": "shell"},
    ]
    assert out["authorization_header_present"] is True
    assert out["thread_metadata_present"] is True
    assert out["turn_metadata_present"] is True
    assert "SECRET_PROMPT" not in encoded
    assert "SECRET_INSTRUCTIONS" not in encoded
    assert "SECRET_SCHEMA" not in encoded
    assert "SECRET_TOKEN" not in encoded


def test_script_has_no_forwarding_and_exact_codex_binding():
    s = SCRIPT.read_text(encoding="utf-8")
    assert "444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b" in s
    assert 'openai_base_url = "http://127.0.0.1:' in s
    assert "forwarded_requests = 0" in s
    assert "requests." not in s
    assert "urllib.request" not in s
    assert "http.client.HTTPConnection" not in s
    assert "https://" not in s


def test_script_is_zero_science_and_rejects_locally():
    s = SCRIPT.read_text(encoding="utf-8")
    assert "g2e_rp_i3_witness_stop" in s
    assert "scientific_attempt_created" in s
    assert "replacement_attempt_authorized" in s
    assert "cgw_request" in s
    assert "browser_submission" in s
    assert "mcp_invocation" in s
    assert "upstream_model_forwarding" in s


def test_design_keeps_tool_surface_observational():
    import json
    d = json.loads(DESIGN.read_text(encoding="utf-8"))
    assert d["pass"] == "PASS_CODEX_OUTBOUND_CONTRACT_WITNESSED"
    assert d["witness_contract"]["forwarding"] is False
    assert d["interpretation_rule"].startswith("Tool-surface presence or absence is an observation")
    assert "replacement attempt activation" in d["prohibited"]
