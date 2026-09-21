# G2E P5A.1 — Codex D1 Adjudication Lock Result

## Verdict

**PASS — ZERO-FRESH ADJUDICATION LOCK QUALIFIED**

The D1 PASS/FAIL/INVALID adjudication rule is frozen before any target-harness discovery evidence is consumed.

This result does not qualify Codex D1, does not mark the Codex profile AVAILABLE, does not authorize D2, and does not authorize a Codex runtime adapter.

## Qualified candidate

- exact SHA: `685739bf607ed456ace1bf723a352ab72a5237d3`
- baseline: `dea34428cb644a221d34a143a738c35b196d3f05`
- lock blob: `a48236824e66b2618e4a08bf00928c94e9b5a815`
- adjudicator blob: `85cc857593a154109cdf5ed749c73f0a2b1e4adb`
- test blob: `0f35f211f48b09cb6f1b8dcaa99451a1203dfc6e`
- workflow blob: `46f0431d600341d45405f57b6840baf2f3caf88d`

## Exact workflow

- workflow: `G2E P5A.1 Codex D1 Adjudication Lock`
- run: `35593990611`
- job: `106314510193`
- conclusion: **PASS**
- artifact: `10636246771`
- artifact digest: `sha256:d844fcd43f3327c24f5ce7eede11df255895215cbeb84f64a485a216c9a9b184`

All gate steps passed:

1. zero-fresh bounded diff;
2. explicit proof that no tracked `P5A_CODEX_DISCOVERY.json` exists;
3. no `src/g2e` or `src/gwr` mutation;
4. compile of G2E/GWF and adjudicator;
5. P1 regression;
6. P1.4 regression;
7. P2 regression;
8. P3 regression;
9. P4 regression;
10. P5A preparation regression;
11. frozen adjudicator qualification;
12. no process execution path in adjudicator;
13. machine-readable lock report.

## Frozen scientific rule

D1 PASS now requires exact consistency of:

- discovery schema identity;
- discovery status;
- no secret persistence;
- no functional task execution;
- exact version/executable identity;
- app-server help success;
- version-matched schema generation success;
- sorted unique schema inventory;
- exact recomputed schema-inventory digest;
- all frozen required protocol tokens;
- successful initialize handshake;
- sanitized initialize metadata;
- empty discovery errors.

Recognized structural non-pass outcomes produce D1 FAIL.

Malformed, contradictory, digest-invalid, unsanitized, or otherwise scientifically unsafe evidence produces INVALID.

## No-rescue boundary

After first actual target-harness discovery evidence exists, this lineage prohibits:

- changing required protocol tokens;
- changing PASS/FAIL/INVALID rules;
- promoting D0 documentation into D1 evidence;
- changing Codex version merely to obtain PASS;
- rerunning until PASS without a separately justified invalidity mechanism;
- using ChatGPT capability as substitute evidence;
- opening D2 or runtime adapter after FAIL/INVALID.

## Qualified adjudicator

The frozen adjudicator is:

`scripts/g2e/p5a_adjudicate_d1.py`

It reads one discovery JSON and writes a separate adjudication JSON. It does not:

- execute Codex;
- launch App Server;
- use subprocess/process execution;
- create a ProofObligation;
- create an ExecutionAttemptEnvelope;
- create an AgentBinding;
- mutate G2E/GWF runtime state;
- access network resources.

## Current state

```text
P1.4                         PASS
P5A discovery preparation    PASS
P5A.1 D1 adjudication lock   PASS
actual Codex D1 evidence     NOT YET COLLECTED
Codex profile AVAILABLE      NO
D2 authorized                NO
Codex runtime adapter        NOT AUTHORIZED
ChatGPT P5B                  UNTOUCHED
```

## Next admissible step

Exactly one target-harness discovery collection is now admissible:

```text
run qualified P5A discovery probe
on the exact target Codex harness
        ↓
freeze P5A_CODEX_DISCOVERY.json
        ↓
run frozen P5A.1 adjudicator once
        ↓
PASS / FAIL / INVALID
```

No profile-manifest construction or D2 work is admissible before that adjudication.
