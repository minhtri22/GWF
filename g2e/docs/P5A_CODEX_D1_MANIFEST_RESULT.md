# G2E P5A.2 — Codex D1 AgentCapabilityManifest Result

## Verdict

**PASS**

One exact canonical Codex `AgentCapabilityManifest` has been materialized and qualified from D1 structural evidence only.

This result does not authorize D2 execution and does not authorize a Codex runtime adapter.

## Qualified candidate

- exact SHA: `2385a853ac37e6b8937a830e0441fbec6e6f7501`
- manifest qualification spec blob: `9243ed8ea21b5afae62bc1be62e2de0a539f16c4`
- materializer blob: `3fb03310561793faf2451437694e02b1cfe98b46`
- qualification test blob: `1f95e2647a018503f97a6c79a68a1db8f1036d4d`
- workflow blob: `ee36ed396eedadbaf5375b810770047e88481236`

## Exact workflow

- workflow: `G2E P5A.2 Codex D1 Manifest Qualification`
- run: `35599808982`
- job: `106332973410`
- conclusion: **PASS**
- artifact: `10637903885`
- artifact digest: `sha256:4502122d331de20a472284f6a96710acab3caf3501d4b0391d623a98e65643a7`

The artifact contains:

- `P5A_CODEX_AGENT_CAPABILITY_MANIFEST.json`
- `p5a_codex_d1_manifest_report.json`

## Exact canonical manifest identity

```text
object_id    agent-capability-manifest-codex-d1
revision_id  a337b7433ebb351c-d1-v1
content_hash 585d59b32457484e8d4706c3e79a94398569ab4bc3e39ff8fca5502541ece5c5
```

Manifest file SHA-256:

`0b5ad6c71ee5fa74a1ca917a943a38bd96687d7b5571901daa8a6acb8e927eac`

Harness reference:

`sha256:a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`

## D1-qualified structural capabilities

The canonical manifest marks these structural surfaces available:

- `app_server_launch`
- `version_matched_schema_generation`
- `jsonrpc_initialize`
- `thread_lifecycle_surface`
- `turn_stream_surface`
- `external_session_attribution_surface`
- `approval_surface`
- `mcp_surface`
- `skills_surface`
- `thread_fork_surface`
- `turn_steer_surface`
- `command_exec_surface`

`available=true` means only that the exact D1 structural surface was observed and qualified.

## Explicitly unqualified functional capabilities

The canonical manifest keeps all of these `available=false`:

- `repository_read`
- `repository_write`
- `shell_execution`
- `test_execution`
- `network_access`
- `side_effect_approval_execution`
- `active_task_cancellation_interruption`
- `completed_task_artifact_extraction`
- `model_task_correctness`

No authority scope or credential class is granted by the D1 manifest.

## Exact-SHA regressions

On the same exact candidate `2385a853ac37e6b8937a830e0441fbec6e6f7501`:

- P1 run `35599809068` — PASS;
- P2 run `35599809106` — PASS;
- P3 run `35599809084` — PASS;
- P4 run `35599809011` — PASS;
- P5A.2 run `35599808982` — PASS.

The P5A.2 workflow itself also reran P1, P1.4, P2, P3 and P4 before manifest materialization.

## Authorization state

```text
Codex D1 structural evidence       PASS
Canonical AgentCapabilityManifest  PASS
D2 P5-FX-001 preregistration       NEXT
D2 execution                       NOT AUTHORIZED
Codex runtime adapter              NOT AUTHORIZED
ChatGPT P5B                        UNTOUCHED
```

## Next admissible step

The next scientific step is a **D2 P5-FX-001 pre-registration / functional qualification specification**.

That step must freeze the exact ProofObligation/fixture, AgentBinding, workspace mutation boundary, approval behavior, evidence extraction rules, success/failure/invalid criteria, timeout/cancellation policy and no-rescue rule before any Codex model turn is executed.