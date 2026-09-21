# GWF — LINEAGE

## Policy

This file is **append-only**.

It records completed project milestones and validated work outcomes only. It is not a session log, troubleshooting log, finding ledger, or technical-debt tracker.

Rules:

1. existing lineage entries must not be edited, deleted, reordered, or rewritten;
2. corrections are appended as new correction entries;
3. open issues, failed attempts, implementation troubleshooting and finding-level remediation belong in the applicable finding/handoff documents, not here;
4. an entry is added only after the recorded work result has completed with attributable evidence;
5. exact commit/run/artifact identities should be included when available.

---

## 2026-09-21 — DG-P0 External Validator Foundation completed

- Result: DG-P0 PASS.
- Implementation/handoff head: `ef322ff0618b83fbfaef40b096cb43f5193d8db0`.
- Exact-head workflow: `35560831581` PASS.
- Outcome: normalized external-validator foundation and markdownlint integration qualified.

## 2026-09-21 — DG-P1 Vale adapter completed

- Result: DG-P1 PASS.
- Implementation head: `385016bf6d0c3df512bae6fa8776cca32eac83ee`.
- Workflow: `35563206375` PASS.
- Evidence artifact: `10622049755`.
- Outcome: Vale terminology/prose adapter qualified on the shared validator contract.

## 2026-09-21 — DG-P2 Lychee adapter completed

- Result: DG-P2 formally closed.
- Formal-close head: `462b55b1b493c28791d237708eda7eae91b742c6`.
- Exact-head workflow: `35564699490` PASS.
- Evidence artifact: `10623990886`.
- Outcome: Lychee referential-validation adapter qualified with content-vs-tool failure separation and non-mutating behavior.

## 2026-09-21 — DG-P3 pre-implementation qualification completed

- Result: pre-implementation dependency/reuse qualification PASS.
- Qualification head: `20bb90aa791f20a57de861e2458368e7b0ce9a82`.
- Frozen specification blob: `e005776db28d57ce1276b07475b9a7f7a5b6be97`.
- Outcome: bounded Git/blob resolver contract, reuse decision and F1–F13 fixture matrix frozen.

## 2026-09-21 — DG-P3 implementation qualification completed

- Result: implementation qualification PASS.
- Qualified implementation head: `9b4426f4c0d3dd6f39b2e2b2750473fd309b779b`.
- Workflow: `35577009823` PASS.
- Evidence artifact: `10627989044`.
- Evidence artifact digest: `sha256:ca9f74f9e6b7db30b2f11b81e80604b3dc2aff1c95d0d46f590beb3cabbd82c9`.
- Outcome: exact GitHub repository/commit/blob revision evidence resolver qualified; read-only repository resolution and write capability are separated; existing SHA-safe write behavior remains qualified.


## 2026-09-21 — DG-P3 formally closed

- Result: DG-P3 PASS / formally closed.
- Handoff head: `0331eedf20910b8d3b23018a6f7c86d114258baf`.
- Exact-head workflow: `35577202015` PASS.
- Exact-head evidence artifact: `10628478735`.
- Evidence artifact digest: `sha256:ff7465f287f6b368da995a1defafc67c40cc6d6c2057132a2c0e076f8f4145b8`.
- Outcome: Wave 1's Git/blob revision evidence resolver item is complete; DG-W1 remains a separate open governance gate.


## 2026-09-21 — DG-W1 Wave 1 formally closed

- Result: DG-W1 PASS / formally closed.
- Handoff head: `84383fe2978eff8ab795c7607df6f19360a5ca1f`.
- Exact-head workflow: `35580636537` PASS.
- Evidence artifact: `10629413613`.
- Evidence artifact digest: `sha256:54b8e518ef51553b6e5be1f428d346551a1c4f7b9b53fe0936c61e592a1cafe2`.
- Outcome: Documentation Validator Foundation is complete; DG-P4 is the next roadmap item.
