# G2E P5A — Codex Discovery Preparation Result

## Verdict

**PREPARATION_PASS_ACTUAL_HARNESS_PENDING**

P5A discovery preparation is qualified.

This result does **not** mark the Codex profile AVAILABLE and does **not** authorize a Codex runtime adapter.

## Qualified candidate

- exact SHA: `d53ef2d246b099a1f0c654906b1ca35ab61ad9a3`
- specification blob: `14d83df31a788699990aa7cbeed250b85584ad98`
- discovery probe blob: `5861298808bd4cc91845f1c10ae114709a955e88`
- Windows PowerShell entrypoint blob: `20a623830be89ac84bd287b8b49c7db3b7cd748d`
- qualification test blob: `4cc57db26c27eb783438b2bb23716dc387b47dc9`
- workflow blob: `6a5799cd6a5f6a498ca49391de63a21c345958a9`

## Exact qualification workflow

- workflow: `G2E P5A Codex Discovery Preparation`
- run: `35591574804`
- job: `106306922854`
- conclusion: **PASS**
- artifact: `10634153745`
- artifact digest: `sha256:ba379edcd7e60ba50641bdc8cd6a4405dcdb326758482cf9164dce485c5518f7`

The workflow passed:

1. bounded preparation-only diff;
2. no `src/g2e` / `src/gwr` mutation;
3. compile of existing G2E/GWF plus probe;
4. P1 regression;
5. P1.4 regression;
6. P2 regression;
7. P3 regression;
8. P4 regression;
9. P5A fake-harness discovery qualification;
10. no model-turn/proof dispatch path;
11. no Codex/ChatGPT runtime implementation;
12. machine-readable preparation report.

## External evidence classification

Official OpenAI documentation and source were used only to freeze the expected discovery surface.

They are classified as D0 — documented evidence.

D0 does not set `AgentCapability.available=true`.

The preparation explicitly separates:

```text
D0 documented
    ↓
D1 structural actual-harness discovery
    ↓
D2 bounded functional harness qualification
```

This prevents official product documentation from being silently promoted into actual local-harness evidence.

## Qualified discovery instrument

The read-only probe:

`scripts/g2e/p5a_codex_discovery.py`

and Windows entrypoint:

`scripts/g2e/p5a_codex_discovery.ps1`

are qualified to collect D1 evidence from one exact Codex executable.

The probe records:

- exact executable path;
- executable SHA-256 when readable;
- `codex --version`;
- app-server help hash;
- exact generated JSON-schema inventory and per-file SHA-256;
- deterministic schema-inventory digest;
- required/optional protocol-token observations;
- app-server `initialize` handshake;
- sanitized initialize metadata;
- explicit limitations/errors.

The probe persists:

```text
secrets_persisted = false
functional_task_executed = false
```

## Prohibited behavior verified

The preparation probe does not:

- call `thread/start`;
- start a model turn;
- create a G2E ProofObligation;
- create an ExecutionAttemptEnvelope;
- create an AgentBinding;
- invoke Codex task execution;
- mutate a repository;
- invoke a tool/command;
- approve a side effect;
- log in/out;
- collect raw credentials;
- access ChatGPT profile semantics.

It therefore remains a discovery instrument, not an execution adapter.

## D1 minimum contract

A target Codex harness qualifies D1 minimum only when:

1. concrete executable resolves;
2. version resolves;
3. app-server help succeeds;
4. version-matched JSON schema generation succeeds;
5. required tokens are present:
   - `initialize`
   - `thread/start`
   - `thread/resume`
   - `turn/start`
   - `item/started`
   - `item/completed`
6. app-server `initialize` handshake succeeds.

Even after D1 PASS, task-execution capabilities such as repository read/write, shell/test execution, active-turn interruption, approvals, network use and artifact extraction remain UNQUALIFIED until D2 or a dedicated functional probe.

## Current scientific state

```text
P1.4 binding identity      PASS
P5A discovery preparation PASS
Codex D1 actual harness   PENDING
Codex AgentCapabilityManifest not yet admitted
Codex D2 functional proof not authorized yet
Codex runtime adapter     NOT AUTHORIZED
ChatGPT P5B               untouched
```

## Next admissible step

The next step is not runtime-adapter implementation.

It is:

```text
run the qualified discovery probe
on the exact target Codex harness
        ↓
freeze P5A_CODEX_DISCOVERY.json
        ↓
verify executable/version/schema fingerprints
        ↓
adjudicate D1
        ↓
D1 PASS / FAIL / INVALID
```

Only D1 PASS may open construction of the exact Codex AgentCapabilityManifest and a separate bounded D2 P5-FX-001 qualification authorization.
