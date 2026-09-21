# PRD-07 — Execution Protocol

## Purpose

Define the provider-neutral contract between a frozen Proof Obligation and any execution backend.

G2E plans proof; execution backends perform work. The protocol must preserve exact semantic identity across GWF, standalone mode, GitHub Actions, local shell, or external frameworks.

## Execution envelope

Each execution attempt MUST freeze:

- proof-obligation ID/hash;
- implementation/source revision;
- config/artifact/data identities;
- executor/agent binding identity;
- transport/harness identity;
- resource/environment identity;
- fresh-resource authorization;
- expected outputs/evidence;
- retry policy;
- authority scope;
- attempt ID.

Recommended lifecycle:

`CREATED → PREFLIGHT → LOCKED → RUNNING → SUCCEEDED | FAILED | INVALIDATED`.

Executor `SUCCEEDED` means “the executor completed,” **not** G2E PASS.

## Harness versus agent

The protocol must preserve the GWF distinction:

- **Harness** — deterministic or semi-deterministic execution shell/tool environment.
- **Agent/App** — decision-capable actor using the harness/tools.
- **Transport** — communication path such as ARC/MCP/API.
- **Provider** — agent/model/service provider.

These are separate identities.

## Retry rules

Infrastructure retry is allowed only inside the frozen retry policy.

A retry must not mutate:

- proof semantics;
- evidence rule;
- protected data;
- comparator/baseline;
- threshold;
- resource equivalence class, unless prospectively allowed.

Reassignment to a materially different agent/provider/resource produces a new attempt identity and must satisfy any independence/equivalence policy.

## Output

Execution returns a normalized `ExecutionResult` containing:

- status;
- start/end;
- commands/actions summary;
- raw artifact references;
- logs/evidence references;
- resource identity;
- agent/harness/transport identities;
- errors classified technical vs semantic;
- no-secret redacted metadata.

## Acceptance criteria

1. GWF and standalone executors can consume the same frozen proof envelope.
2. Execution completion cannot itself update claim verdict.
3. Every evidence artifact resolves to an execution attempt.
4. Material executor reassignment is visible.
5. Retry budget and semantics are enforceable.
6. Provider credentials never persist in envelopes/evidence.

## Dependencies

- [PRD-03 Proof Planner](PRD_03_PROOF_PLANNER.md)
- [PRD-05 Adjudicator](PRD_05_ADJUDICATOR.md)
- [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)

## References

- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF Agent Execution Protocol behavior](../../README.md)
- [GWF software delivery exact-SHA model](../../domains/software.workflow.yaml)
