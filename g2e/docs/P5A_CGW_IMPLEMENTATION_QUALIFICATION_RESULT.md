# G2E P5A-CGW — Implementation / Synthetic Zero-Model Qualification

## Formal status

**CI/SYNTHETIC PASS / LOCAL RUNTIME Q0b REQUIRED / NO MODEL EXECUTION AUTHORIZED**

Authoritative qualified implementation candidate:

`7033f3cee0f7c6834efe459f5719363ceeeb263c`

Authoritative workflow:

- run: `35801134380`
- Linux job: `106991493556` — PASS
- Windows job: `106991493305` — PASS
- artifact: `10726071300`
- artifact digest: `sha256:c814159181918b1ad0e29ca5bf5fc7371e5028f895d4ae518e380efaf65de955`

Artifact report status:

`SYNTHETIC_ZERO_MODEL_PASS_LOCAL_RUNTIME_ADMISSION_REQUIRED`

No model turn was executed and no scientific attempt was created or consumed.

## Qualified component identities

- bridge qualifier:
  `aa600a55e29bcaf06e2a8531252976575b178b94`
- Windows local zero-model one-click:
  `8d311c1a301e9b96a1d465c9330103a3e5668b82`
- qualification tests:
  `3a650f033324f97e552f9c473a57f381183fa795`
- workflow:
  `4dd9af4a8f6b9e3526ae282f861c602d13b19828`

Specification identities remain:

- specification lock:
  `dda7d753a47245368c1a59d1b88503db87c2e27e`
- trust/authority/observability spec:
  `a9734274ed01b45530c6aa4383e128741c3b3401`
- zero-model qualification plan:
  `fa3eff8ab7b6471ee751b3344c368114477679ef`

## Q0 provenance split

### Q0a — upstream source provenance — PASS

CI fetched and detached exact:

`miuuyy/codex-chatgpt-web@eaf4f09ae92d4dc4429fa597b0861663138f08f8`

The qualifier verified the frozen source-object identities and contract fragments before synthetic admission.

### Q0b — installed local runtime identity — REQUIRED

GitHub Actions cannot establish the identity of the bridge and Codex binaries already installed on the user's Windows machine.

Q0b therefore remains intentionally unresolved until a local read-only admission package proves:

- the installed CGW config is version 3 / release 5.0.8;
- route host is loopback;
- mode and exact connector identity are explicit;
- automatic tool approval is disabled;
- Full mode has a configured tunnel when Full mode is active;
- the CGW health endpoint identifies the expected service/version/mode/port;
- the bridge is accepting turns and idle at collection time;
- Codex `openai_base_url` points to that exact loopback CGW route;
- exact local CGW and Codex command/binary hashes are captured.

No raw browser/tunnel/token secret is admitted to evidence.

## Q1-Q7 — synthetic qualification — PASS

The exact candidate passed 26 dedicated P5A-CGW tests on Linux and the same suite on Windows.

Qualified properties include:

- route ownership and no silent fallback;
- exact request/thread/turn correlation;
- browser lease + logical ChatGPT turn binding contract;
- bridge-side-effect prohibition;
- delegated authority bounded by the active outer Codex turn;
- Full-mode connector/capability/tool-registry binding;
- recursive secret redaction;
- frozen 18-case fail-closed matrix.

These are infrastructure/contract qualifications. They do not establish live model-task success.

## Q8 — G2E regressions — PASS

The authoritative Linux job passed:

- P1 core schemas;
- P1.4 agent binding;
- P1.5 qualification authority;
- P2 deterministic core;
- P3 standalone runtime;
- P4 GWF adapter.

Windows additionally passed:

- P5A-CGW synthetic tests;
- Windows PowerShell parser qualification;
- static firewall proving the qualifier has no model-bearing network client and the one-click does not call `/v1/models` or `/v1/responses`.

## Prequalification repair lineage

Two earlier workflow runs are non-authoritative and retained as implementation QA evidence:

1. run `35800996788`: bounded-diff shell array was escaped literally; Windows also exposed two over-broad privacy assertions.
2. run `35801088549`: CI array expansion was repaired, but the already-identified test assertions had not yet been repaired on that candidate.

The repairs changed only CI/test qualification logic. No browser/model/scientific runtime was invoked by either failed run.

Authoritative qualification is run `35801134380` on candidate `7033f3cee0f7c6834efe459f5719363ceeeb263c`.

## Current authorization

Authorized now:

- exactly the bounded local **zero-model runtime admission collection** defined by the lock.

Not authorized:

- ChatGPT Web message submission;
- Codex `thread/start` / scientific `turn/start`;
- MCP tool invocation through ChatGPT;
- first P5A-CGW functional attempt;
- P5A official fallback/retry;
- P5A official capability promotion;
- A/B comparison.

## Next gate

Run the qualified Windows one-click on the user's already-connected Codex + codex-chatgpt-web installation.

Only if the resulting local report is admitted as `LOCAL_ZERO_MODEL_ADMISSION_PASS` may P5A-CGW zero-model qualification be formally closed and the **design/preregistration** of a first functional P5A-CGW attempt begin.
