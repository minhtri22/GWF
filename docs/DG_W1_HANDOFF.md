# GWF — DG-W1 Wave 1 Exit-Gate Handoff

## 1. Purpose

This package closes the Documentation Validator Foundation wave only after exact-head requalification.

Wave 1 contains:

- DG-P0 — external validator foundation + markdownlint;
- DG-P1 — Vale terminology/prose adapter;
- DG-P2 — Lychee link adapter;
- DG-P3 — Git/blob revision evidence resolver.

## 2. Base and QA evidence

- DG-P3 formal-close base: `6c5fa62f81b7bd4e185074a3c947613fa947a8a1`
- Wave-1 QA head: `bea3cf23dd9b14cde999e9effe13e1cc9e6af1e5`
- Wave-1 QA workflow: `35580447186` PASS
- Wave-1 QA artifact: `10630420383`
- artifact digest: `sha256:dca557bfe7cbc4a2fadc7399cf7e0551eadca7194da8d5a28cf9b66bc69647a1`

Exact version/config fingerprints are recorded in `docs/DOCUMENT_QA_DG_W1_WAVE1.md`.

## 3. Exit-gate checks

- DG-P0 PASS.
- DG-P1 PASS.
- DG-P2 PASS.
- DG-P3 PASS.
- All four were requalified on one exact Wave-1 QA HEAD.
- P0/P1/P2 normalize through the shared validator contract.
- Real P3 GitHub exact-identity resolution PASS.
- Tool versions/config identities are attributable.
- No authoritative document-state runtime has been introduced.
- No document registry/graph/lifecycle/validity runtime is present.
- No GAC runtime is present.
- Finding checklist remains OPEN=0.

## 4. Ownership boundary preserved

Wave 1 provides evidence-producing adapters and exact Git identity only.

It does not own:

- stable governed document identity;
- DocumentRecord/DocumentRevision persistence;
- QA/finding persistence;
- lifecycle or validity mapping;
- document relation graph;
- authority semantics;
- GAC publication/catalog/search.

Those remain later-wave concerns.

## 5. Formal-close condition

This handoff is not sufficient by itself. DG-W1 closes only if the combined Wave-1 requalification workflow passes on the exact committed handoff HEAD.

Until then:

```text
DG-W1 = QA_PASS / EXACT_HEAD_PENDING
Wave 2 = NOT_OPEN
GAC = LOCKED_UNTIL_DG-W4_PASS
```


## 6. Formal-close evidence

The committed DG-W1 handoff HEAD `84383fe2978eff8ab795c7607df6f19360a5ca1f` was requalified with the full Wave-1 combined gate.

- workflow: `35580636537`
- conclusion: **PASS**
- artifact: `10629413613`
- artifact digest: `sha256:54b8e518ef51553b6e5be1f428d346551a1c4f7b9b53fe0936c61e592a1cafe2`

All component real gates, cross-item compatibility checks, fingerprint checks and compile passed again.

**DG-W1 status: FORMALLY CLOSED.**

The next roadmap item is DG-P4 — Document facade / identity mapping. GAC remains locked until DG-W4 PASS.
