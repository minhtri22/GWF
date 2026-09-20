# GWF v0.8.5 — Domain Skill Audit

## Baseline and method

Audit baseline for GWF: `f511a6483c86b5b4dff3e6d0860c6d6f022e7a50` (verified v0.8.4 main).

The audit compared the existing domain/skill contracts against two real working patterns:

- **Research:** CQG, observed at main `98da24b82bd327793a179d4c400f3406803dd88f`.
- **Software delivery:** the GWF v0.8.3/v0.8.4 implementation and release process itself.

The purpose is not to make an agent "smart enough" to remember good process. The domain package must encode the important invariants so different agents can produce comparable, auditable outcomes.

## Finding 1 — Research domain was directionally correct but under-specified for confirmatory work

The v0.4 research package already covered the correct macro-cycle:

goal → prior art → hypothesis → formalization → protocol → data/benchmark → implementation → preflight → pilot → main experiment → analysis → adversarial review → PASS/FAIL/PIVOT → replication → report → handoff.

This matches the broad structure used in CQG.

However, CQG uses stronger prospective controls that were previously only implicit in GWF skills:

- preregistration is frozen before fresh outcomes are inspected;
- exact source commit / Git blob / SHA-256 / artifact digest / functional fingerprint is recorded;
- fresh seeds/cohorts are declared prospectively;
- no retraining, recalibration, threshold scaling or post-hoc target changes are permitted unless a new scientific lineage is opened;
- execution-only amendments are distinguished from scientific amendments;
- failed infrastructure attempts are recorded even when no scientific output exists;
- negative results remain part of the lineage;
- branch stop/no-rescue rules and repair budget constrain repeated "fix until PASS" behavior;
- formal adjudication uses the frozen gates rather than the agent's narrative.

### v0.8.5 action

Research domain is upgraded to v0.5 with a normative `study_lock` artifact and v2 skills.

The lock contains at least:

- preregistration SHA-256;
- source commit;
- frozen artifacts;
- fresh data and seed/cohort policy;
- metrics/gates;
- forbidden adaptations;
- amendment policy;
- resource limits;
- branch stop rules;
- repair budget;
- no-rescue policy.

The lock is produced with the protocol and carried through data preparation, implementation, preflight, experiment, analysis, review, adjudication, replay and final reporting.

## Finding 2 — Existing research skills were too generic

The previous seven roles were useful role labels but did not sufficiently constrain behavior across agents.

v2 skill changes:

- **Research Lead:** FAIL is a valid outcome; preserve negative evidence; no silent rescue.
- **Literature Reviewer:** bound novelty; distinguish parent evidence from fresh-study evidence.
- **Protocol Designer:** prospective study lock; execution-only vs scientific amendment boundary.
- **Experimenter:** exact source/artifact/environment verification before fresh execution; AUTO retry only for the same semantic experiment.
- **Reproducibility Reviewer:** independent verification of commit/hash/fingerprint/environment/seed coverage.
- **Analyst:** only frozen metrics decide the formal verdict; post-hoc analysis is exploratory.
- **Adversarial Reviewer:** explicitly tests hidden tuning, privileged information, population drift and amendment dependence.

## Finding 3 — There was no real software domain

At the audit baseline, `domains/example.workflow.yaml` was a scaffold/example, not a software-delivery package.

Using it as the second production domain would have hidden the actual software governance requirements.

### v0.8.5 action

A separate `domains/software.workflow.yaml` is introduced.

Its governed lifecycle is:

remote repository audit → scope lock → change plan → implementation → local verification → integration/full regression → independent QA → candidate verification → merge → exact-main verification → release handoff.

The critical invariants are:

- remote repository is source of truth;
- exact base/branch/blob SHAs are frozen;
- scope and non-goals are explicit before implementation;
- COMMITTED is not QA-complete;
- candidate SHA and workflow evidence are exact;
- expected main SHA is compared before merge;
- all required gates are rerun on the exact merged main SHA;
- no agent may declare release complete before exact-main verification.

## Finding 4 — ResearchOrchestrator could not honestly run software delivery

The existing orchestrator is intentionally research-specific: it requires a research domain, exactly 17 phases, and embeds PASS/FAIL/PIVOT semantics.

### v0.8.5 action

A `LinearDomainOrchestrator` is added for non-research sequential domains. It reuses the same governed execution primitives:

skill pinning → preflight → frozen plan → execute → evidence → gate → verify → handoff → complete,

plus recovery/checkpoints/authority, but without importing research-specific PASS/FAIL/PIVOT semantics.

## Finding 5 — Pilot adoption should not rewrite existing project history

For CQG, importing every historical study into a new runtime would create false authority and expensive reconciliation.

The first pilot therefore uses **NEXT_STUDY** mode:

- existing CQG lineage remains authoritative in CQG;
- exact CQG main SHA is frozen at pilot start as parent evidence;
- GWF governs the next prospectively opened study only.

For GWF, the first self-upgrade uses **BOUNDED_SELF_UPGRADE**:

- feature branch only;
- small change with explicit non-goals;
- full candidate and exact-main verification.

## Verdict

After the v0.8.5 changes, the two domain packages represent the user's actual working patterns substantially better:

- research outcome quality is protected by prospective study locking and falsification/convergence boundaries;
- software outcome quality is protected by repository/SHA/scope/test/QA/release invariants;
- the guarantees live in domain/runtime contracts rather than depending on a particular agent remembering instructions.

The remaining boundary is intentional: GWF governs decisions, evidence and release quality; external integrations remain plugin/tool responsibilities rather than becoming an n8n-style automation platform.
