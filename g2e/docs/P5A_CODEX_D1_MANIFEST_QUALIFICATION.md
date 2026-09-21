# G2E P5A.2 — Codex D1 AgentCapabilityManifest Qualification

**Status:** FROZEN CANDIDATE  
**Baseline:** `30ddf0693621ae81f3c7b7aef9eec9f936751f2e`  
**D1 status:** PASS / structural surface only  
**D2:** NOT AUTHORIZED  
**Codex runtime adapter:** NOT AUTHORIZED

## 1. Purpose

Materialize exactly one canonical `AgentCapabilityManifest` from the immutable D1 evidence chain, without adding any capability not demonstrated by D1.

## 2. Exact evidence inputs

- discovery SHA-256: `ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860`
- repaired adjudication SHA-256: `04035432c5f290dfd7bbcc91feba8865dc86bfae11686a4e44da2f56cb4ac578`
- executable SHA-256: `a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`
- schema inventory digest: `4da66f2fac241c53ec857bf1a5f0f9586a445e39c4b0c4e7b4bdb0b103aa8376`
- D1 evidence document: `g2e/docs/P5A_CODEX_D1_EVIDENCE.json`

## 3. Identity mapping

Frozen manifest identity:

- `agent_app = codex`
- `profile_version = g2e-p5a-d1-v1`
- `harness_ref = sha256:<exact executable sha256>`
- `exact_harness_revision = <exact executable sha256>`
- `provider_ref = null`
- `model_ref = null`
- `transport_ref = app-server-stdio`
- `availability = AVAILABLE` only for the D1 structural profile surface.

The reported CLI version string `codex-cli 0.0.0` is preserved as a limitation/evidence note and is not used as exact harness identity.

## 4. Capabilities admitted as available

Only these structural capabilities are admitted with evidence refs:

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

`available=true` for these means only that the exact D1 schema/protocol surface was observed. It does not mean the operation was executed successfully.

## 5. Capabilities explicitly not admitted

The manifest must include these as `available=false`:

- `repository_read`
- `repository_write`
- `shell_execution`
- `test_execution`
- `network_access`
- `side_effect_approval_execution`
- `active_task_cancellation_interruption`
- `completed_task_artifact_extraction`
- `model_task_correctness`

Each must carry a limitation stating that D2 or a separately preregistered functional probe is required.

## 6. Global manifest flags

Frozen conservative values:

- `max_authority_scope = ()`
- `credential_ref_classes = ()`
- `external_session_attribution = true`
- `interruption_supported = false`
- `artifact_extraction_supported = false`
- `structured_output_supported = false`
- `status_normalization_supported = false`

No authority is granted by D1 structural discovery.

## 7. Deterministic provenance

The manifest is sealed with deterministic provenance:

- `created_by = g2e-p5a-d1-materializer`
- `created_at = 2026-09-21T12:05:44.250506Z` (original D1 observation time)
- source refs include exact discovery/adjudication SHA-256 values and the D1 evidence document identity.

Object identity:

- `object_id = agent-capability-manifest-codex-d1`
- `revision_id = a337b7433ebb351c-d1-v1`

## 8. Qualification requirements

The exact-SHA qualification must prove:

1. the repo D1 evidence says PASS;
2. discovery/adjudication hashes exactly match the frozen values;
3. only the admitted structural capabilities are `available=true`;
4. every available capability has qualification refs;
5. every functional capability remains false;
6. manifest canonical hash verifies under P1.4;
7. no Codex execution, model turn, network call or subprocess is used;
8. no `src/g2e` or `src/gwr` mutation occurs;
9. P1/P1.4/P2/P3/P4 regressions remain PASS;
10. D2/runtime adapter remain unauthorized.

## 9. Exit

On PASS, freeze the exact manifest JSON and its canonical `ExactRef`.

Only then may the next scientific step be **D2 P5-FX-001 pre-registration/specification**, not D2 execution.