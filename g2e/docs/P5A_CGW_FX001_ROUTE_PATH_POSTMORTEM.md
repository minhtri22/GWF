# P5A_CGW_FX001_ROUTE_PATH_POSTMORTEM

Status: **SOURCE-LEVEL POSTMORTEM COMPLETE; HISTORICAL ROUTE NOT UNIQUELY IDENTIFIABLE**

Scope: bounded, zero-science, no model execution, no browser submission, no MCP invocation, no mutation or reuse of TC-001/002/003 evidence roots.

## Question

Why could Codex app-server produce:

```
turn/start
  -> agentMessage...
  -> turn/completed
```

while the frozen TC-003 route evidence showed:

```
launcher_delta = 0
browser_diagnostics_new_dirs = []
request_id = null
browser_surface = null
MCP correlation = null
result.json = absent
```

## Frozen observation

The consumed TC-003 attempt is already formally closed as `INVALID_SPENT`. It proved:

- the consumption marker was durable and correctly bound;
- Codex accepted the turn and reached exact terminal `completed`;
- no timeout, protocol failure, scope violation, or authority violation was observed;
- no `result.json` was produced;
- launcher delta was zero;
- no new browser diagnostic directory appeared;
- the synthesized four-event route ledger carried null request/browser/MCP correlation fields;
- the verifier therefore set `evidence_integrity_valid=0` and `live_mcp_roundtrip_admitted=false`.

These observations are evidence about the spent attempt. This postmortem does not reinterpret them as a scientific FAIL.

## Exact source ledger

### codex-chatgpt-web 4.0.7

Repository commit: `b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494`

| Path | Git blob | Relevant invariant |
| --- | --- | --- |
| `src/server.ts` | `af4cd5c3886f119f35efa4fc0e28bd2ecfc48530` | `POST /v1/responses` is the local Responses ingress; `chatgpt-web/*` selects the ChatGPT Web adapter. |
| `src/config.ts` | `1444c64ab66282e72411585392e3d242773a971a` | `mode=full` maps to `localToolsEnabled=true`; production config home defaults to `~/.codex-chatgpt-web`. |
| `src/adapters/chatgpt-web/index.ts` | `c7e7f291ae6ea6d23818aba8803ad83e39171dbd` | Tool-capable runtime calls `broker.register(...)` before prompt send. |
| `src/adapters/chatgpt-web/browser-worker.ts` | `4e82981a28158e65705f31213bfbd123a6be5e2e` | Browser diagnostics create a per-trace directory; first normal capture includes `browser-page-acquired`, before send. |
| `src/adapters/chatgpt-web/turn-broker.ts` | `6017bbaafd87c58078a72dbac42e843d5bcf3209` | Broker registration is a runtime event with trace/token evidence. |
| `src/adapters/chatgpt-web/mcp-server.ts` | `51d9c787f93c391fba70f68ce759c673d789275d` | Codex Native2 is the reverse tool bridge into the registered turn, not an arbitrary Codex app-server MCP registration. |
| `launcher/electron/runtime-supervisor.cjs` | `19b19e24b4ab02ae02f762006f750ca9054d7bc6` | Launcher-owned daemon stdout/stderr is piped into `launcher.jsonl`; ownership state records ownerPid/daemonPid. |
| `launcher/electron/main.cjs` | `c3f83aacac26baaa28119ff1b147fbb355c4cac9` | Production launcher sets `CODEX_CHATGPT_WEB_HOME=CORE_HOME`, writes launcher logs under launcher userData, and uses `CORE_HOME/runtime/launcher-browser.json`. |
| `launcher/electron/profile.cjs` | `b1a20dc7fcfffc0ab45bfe916d173a59d4b93e5a` | Production CORE_HOME defaults to `~/.codex-chatgpt-web`; launcher userData defaults to AppData/Codex Web GPT. |
| `launcher/electron/logging.cjs` | `c4149c3c8a27a9b8105d23f58655d9bdc5df9d70` | Structured launcher records contain at/level/event/detail and rotate at 4 MiB. |

### Codex 0.153.4

Repository commit: `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`

| Path | Git blob | Relevant invariant |
| --- | --- | --- |
| `codex-rs/model-provider-info/src/lib.rs` | `3fb3e87a2aa9b034713687b20b7f11c38b182389` | Built-in `openai` provider accepts `openai_base_url` and uses Responses wire API. |
| `codex-rs/core/src/config/mod.rs` | `dca329ab98ea218f7b96f1bd2d4cf25612a5fc1f` | The configured OpenAI base URL feeds effective provider configuration. |

Therefore the hypothesis “Codex 0.153.4 silently ignores `openai_base_url`” is not supported by the exact source.

## Source-derived causal invariants

For a non-compaction `chatgpt-web/high` request that actually reaches the intended CGW 4.0.7 daemon configured `mode=full`:

```
Codex Responses POST
      |
      v
CGW /v1/responses
      |
      v
chatgpt-web adapter
      |
      +-- localToolsEnabled = true
      |
      +-- trusted environment resolution
      |
      +-- broker.register(...)       [before browser send]
      |
      v
browser worker
      |
      +-- browser-page-acquired      [diagnostic directory exists]
      |
      +-- prompt attachment
      +-- send
      +-- send-accepted
      +-- response-visible
      |
      v
optional Codex Native2 MCP calls
      |
      v
terminal response stream
```

Two consequences are important:

1. `configured_mcp_count=0` in Codex app-server is expected under the GWF isolation overrides and does **not** disable the CGW-internal Codex Native2 reverse bridge.
2. “The model chose not to call a tool” can explain no MCP invocation and no `result.json`, but it cannot explain the joint absence of mandatory pre-send broker registration evidence and the first browser diagnostic capture.

## What is ruled out

- **Old 90 s deadline**: ruled out; TC-003 had no scientific absolute turn deadline.
- **Whole-file CGW config hash drift**: ruled out by semantic admission.
- **CGW service unavailable before dispatch**: ruled out for TC-003; readiness and admission health were healthy/idle.
- **Codex app-server never started a turn**: ruled out by exact app-server protocol.
- **Codex `openai_base_url` key unsupported**: ruled out by exact Codex 0.153.4 source.
- **Arbitrary Codex MCP list being empty caused the missing CGW broker registration**: ruled out as a category error; the internal Codex Native2 bridge is separate.

## What the spent evidence cannot distinguish

The historical attempt did not record an ingress witness or bind the service PID to the evidence sinks. Therefore it cannot distinguish these two remaining classes:

### H-R1 — observed-instance / evidence-root mismatch

Codex reached a compatible listener at `127.0.0.1:17841`, but the runner observed launcher state/logs/diagnostics belonging to a different runtime ownership instance or effective home.

This class explains all of:

- valid Responses stream back to Codex;
- app-server agent messages and terminal completion;
- zero delta in the watched launcher log;
- zero new directories in the watched diagnostics root;
- no recoverable CGW request/browser/MCP correlation.

### H-R2 — dual observation-sink failure on the correct instance

The intended daemon handled the request, but both:
- launcher stdout/stderr capture did not expose the runtime trace to the watched log, and
- browser diagnostics failed or resolved to an unobserved path.

The source permits individual diagnostic-capture failure because browser capture errors are swallowed and only warned. However simultaneous loss of both independent sinks is a stronger condition and is not proven by TC-003.

## Postmortem conclusion

The exact historical physical route is **not recoverable from TC-003**. The proven root defect is narrower and more important:

```
ROUTE OBSERVABILITY WAS NOT INSTANCE-BOUND
```

The runner inferred internal route identity after the fact from two side-effect sinks (launcher log delta + browser diagnostic directory), but never proved that:

```
Codex outbound destination
  == TCP listener PID
  == /healthz PID
  == launcher supervisor daemonPid
  == daemon whose stdout/stderr feed the watched launcher.jsonl
  == daemon whose CORE_HOME determines the watched diagnostics root
```

Because that equality chain was absent, null route fields cannot tell us whether the transport bypassed the observed runtime or the observation sinks failed.

This is an **evidence architecture failure**, not evidence that the model failed P5-FX-001.

## Why result.json was absent

The spent protocol contains agent messages and terminal completion but no observed native execution item that wrote `result.json`. That establishes “no observed write occurred.”

It does **not** establish why. The spent evidence did not capture the exact outbound Responses request body/tool catalog at the Codex->CGW boundary, so it cannot distinguish:

- native write/shell tools were not advertised in the outbound request;
- they were advertised but the model chose not to invoke them;
- a different execution route transformed or omitted the expected tool surface.

Therefore `result.json=absent` is downstream evidence, not the root-cause discriminator.

## Governance outcome

Postmortem result:

```
HISTORICAL_ROUTE_UNIDENTIFIABLE
+
OBSERVABILITY_INSTANCE_BINDING_GAP_PROVEN
```

This does **not** authorize a replacement scientific attempt.

The next allowed work is zero-science instrumentation qualification. A replacement attempt can only be considered after the instrumentation can prove the complete pre-model identity chain and the Codex outbound request contract.
