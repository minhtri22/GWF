# G2E P5A — Codex Actual-Harness Discovery / Profile Qualification Preparation

**Status:** FROZEN CANDIDATE FOR ZERO-RUNTIME QA  
**Phase:** P5A — Codex profile only  
**Baseline:** `27ad96d384919101285208fe36bf27c76f36bb52`  
**Codex runtime adapter:** NOT AUTHORIZED  
**ChatGPT profile/runtime:** OUT OF SCOPE

## 1. Origin

P1.4 Agent Profile / Binding Identity is qualified at:

`d3cb0bdb5644a9f1cff382450b5476e166759d72`

with evidence closure:

`233ab9442338e7ed0d4a53f70dc87ab803165711`

and lineage close-through:

`27ad96d384919101285208fe36bf27c76f36bb52`.

P1.4 closed P5-F01/P5-F02 by providing canonical AgentCapabilityManifest, AgentEquivalencePolicy, AgentBinding, exact attempt/result binding refs, and deterministic binding identity validation.

P5A now moves from schema readiness to **Codex-specific discovery preparation**.

No Codex execution adapter is authorized by this phase.

## 2. Scientific question

> Can G2E obtain an exact, reproducible, non-secret discovery bundle from the actual Codex harness that is sufficient to construct a truthful AgentCapabilityManifest without inferring capabilities from product documentation or another app?

This phase is preparation plus probe qualification only.

It does not mark Codex AVAILABLE unless the probe is executed against the exact harness that will later be bound.

## 3. Official external evidence boundary

Official OpenAI sources consulted on 2026-09-21:

1. Codex App Server documentation: https://developers.openai.com/docs/app-server
2. OpenAI engineering article: https://openai.com/index/unlocking-the-codex-harness/
3. Codex CLI documentation: https://developers.openai.com/docs/codex/cli
4. Open-source Codex repository: https://github.com/openai/codex
5. Observed open-source `main` commit during preparation: `ebc05da3bdb76f25861e7cb418bd06d28cadc609`

The open-source `main` SHA is **background source identity only**. It MUST NOT be substituted for the installed harness revision.

Official documentation currently describes a bidirectional JSON-RPC App Server, mandatory `initialize` / `initialized` handshake, thread start/resume/fork and thread/session identity, `turn/start` plus streamed turn/item/tool events, command/file-change approvals, MCP surfaces, Skills, version-specific schema generation, CLI repository/tool execution, and automation-oriented SDK/`codex exec` surfaces.

These are **documented capabilities**, not G2E qualification evidence.

## 4. Evidence classes

### D0 — documented

Supported by official OpenAI documentation/source.

D0 never sets `AgentCapability.available=true` by itself.

### D1 — structural actual-harness discovery

Produced by the exact locally installed Codex executable:

- executable path;
- executable SHA-256 when available;
- `codex --version`;
- `codex app-server --help`;
- version-matched `codex app-server generate-json-schema`;
- canonical schema-file inventory + SHA-256;
- required protocol token presence;
- successful app-server `initialize` handshake.

D1 may qualify protocol-surface capabilities demonstrated by the exact generated schema plus handshake.

D1 does not prove that authenticated task execution, repository mutation, network use, approvals, or tool execution succeeds end-to-end.

### D2 — bounded functional harness qualification

A later exact-harness run of the frozen P5-FX-001 proof through the real Codex harness.

D2 is required before the Codex profile may be used for a proof requiring task execution.

P5A preparation does not execute D2.

## 5. Actual-harness discovery target

The discovery target is the concrete executable selected by the environment:

```text
Get-Command codex
        ↓
exact executable path
        ↓
codex --version
        ↓
executable SHA-256 if readable
        ↓
app-server help
        ↓
version-matched JSON schemas
        ↓
initialize handshake
        ↓
P5A_CODEX_DISCOVERY.json
```

No `latest` alias becomes canonical evidence.

Any later material harness-version change requires fresh discovery.

## 6. Required D1 protocol tokens

The exact generated schema bundle is inspected for these stable-surface tokens:

- `initialize`;
- `thread/start`;
- `thread/resume`;
- `turn/start`;
- `item/started`;
- `item/completed`.

Additional tokens are recorded but are not required for D1 minimum admission.

Optional observed tokens include `thread/fork`, `turn/steer`, approval-related methods/events, MCP-related methods/events, skill-related types/methods, and command execution methods/events.

Absence of an optional token yields `UNQUALIFIED` for that capability, not a failure of the entire minimum D1 bundle.

## 7. D1 handshake rule

The probe starts `codex app-server` over stdio and sends exactly one initialization request with a G2E discovery client identity.

The probe may then emit `initialized`.

It MUST NOT call `thread/start`, start a model turn, mutate a repository, invoke a command/tool, request network access, approve a side effect, log in/out, emit or collect raw credentials, or request hidden reasoning.

A successful `initialize` response establishes only app-server process/protocol readiness.

## 8. Discovery bundle schema

The probe writes `P5A_CODEX_DISCOVERY.json` with at least:

- schema;
- status;
- observed_at;
- platform;
- codex_command;
- executable_path;
- executable_sha256 or explicit unavailable reason;
- codex_version_stdout;
- app_server_help_sha256;
- generated_schema_files sorted by relative path;
- per-file SHA-256;
- whole-bundle digest derived deterministically from the sorted inventory;
- required protocol token results;
- optional protocol token results;
- initialize handshake success/failure;
- sanitized initialize-response metadata;
- errors/limitations;
- `secrets_persisted=false`;
- `functional_task_executed=false`.

The discovery bundle MUST NOT include authentication tokens, environment-variable values, raw reusable credentials, account email, full user profile/account payload, hidden reasoning, or repository contents.

## 9. Codex capability mapping rules

Only D1-observed evidence may populate the future Codex AgentCapabilityManifest.

| G2E capability | D1 admission rule |
| --- | --- |
| `app_server_launch` | executable exists + app-server help succeeds |
| `version_matched_schema_generation` | JSON Schema generation succeeds |
| `jsonrpc_initialize` | initialize handshake succeeds |
| `thread_lifecycle_surface` | required thread tokens present in generated schema |
| `turn_stream_surface` | required turn/item tokens present |
| `external_session_attribution_surface` | thread/session identity fields/tokens observed |
| `approval_surface` | approval tokens observed; still not functionally exercised |
| `mcp_surface` | MCP tokens observed; still not functionally exercised |
| `skills_surface` | Skills tokens observed; still not functionally exercised |

The following remain UNQUALIFIED at D1 unless separately exercised: repository read, repository write, shell execution, test execution, network access, side-effect approvals, cancellation/interruption semantics under an active task, and artifact/evidence extraction from a completed task.

These require D2 or a dedicated bounded functional probe.

## 10. Fail-closed rules

- Codex executable missing → discovery status `HARNESS_NOT_FOUND`.
- `codex --version` fails → `VERSION_UNRESOLVED`.
- schema generation fails → `SCHEMA_DISCOVERY_FAILED`.
- required protocol token missing → `D1_MINIMUM_NOT_QUALIFIED`.
- initialize handshake fails/timeouts → `D1_MINIMUM_NOT_QUALIFIED`.
- executable changes after discovery → prior bundle cannot qualify the new executable.
- schema inventory changes → prior manifest cannot silently migrate.
- documentation/source evidence never upgrades a missing D1 observation.
- ChatGPT capability is never inferred from Codex.

## 11. Probe implementation scope

P5A preparation may add only this specification, a read-only Codex discovery probe, a Windows PowerShell entrypoint, deterministic probe tests using a fake harness, a zero-runtime qualification workflow, result/evidence docs, and append-only lineage after adjudication.

The probe is not a Codex runtime adapter.

It performs no ProofObligation dispatch and creates no ExecutionAttempt.

## 12. Zero-runtime preparation gate

```text
P5A-Q0 P1.4 exact evidence bound
P5A-Q1 official documented-vs-qualified boundary explicit
P5A-Q2 D0/D1/D2 evidence levels frozen
P5A-Q3 exact-version discovery procedure frozen
P5A-Q4 no latest identity substitution
P5A-Q5 secret/redaction boundary frozen
P5A-Q6 fake-harness tests prove deterministic bundle behavior
P5A-Q7 no model turn / repo mutation / runtime adapter
P5A-Q8 existing P1–P4 + P1.4 regressions PASS
```

If this gate passes:

```text
P5A discovery preparation PASS
        ↓
execute discovery probe on target Codex harness
        ↓
freeze exact P5A_CODEX_DISCOVERY.json
        ↓
adjudicate D1
        ↓
D1 PASS ?
        ↓
construct exact Codex AgentCapabilityManifest
        ↓
authorize bounded D2 P5-FX-001 harness qualification
```

Runtime adapter implementation remains prohibited until a separate authorization after exact Codex profile evidence.
