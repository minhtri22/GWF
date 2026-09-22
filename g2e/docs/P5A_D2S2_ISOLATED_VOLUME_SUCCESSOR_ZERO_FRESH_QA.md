# G2E P5A D2-S2 — Isolated-Volume Successor Zero-Fresh QA

**Verdict:** `SPEC_PASS_IMPLEMENTATION_REQUIRED`  
**Finding count:** `0`  
**Scientific model turn:** NONE  
**Scientific attempt consumed:** FALSE

## 1. Predecessor separation

D2-S1 is closed preturn because its exact-file authority cannot satisfy the observed elevated Windows requirement for effective `:root` read without broadening host-drive visibility.

D2-S2 is a new successor with:

```text
study_id  = p5a-d2s2-isolated-volume-root-read-successor
attempt_id = p5a-d2s2-p5-fx-001-attempt-001
profile_id = g2e_p5a_d2s2
```

No predecessor attempt is reused.

## 2. Scientific invariants

Frozen and unchanged:

- P5-FX-001 input bytes/hash;
- TASK.md bytes/hash;
- task/output semantics;
- target capability;
- exact Codex executable;
- model/provider;
- network disabled;
- zero scientific dispatch during preturn;
- no repository scientific claim before final admission.

## 3. Authority analysis

The only broadened filesystem semantic is `:root = read`.

The spec bounds this by requiring the command cwd/root to be a dedicated VHDX-backed NTFS volume containing exactly the task-visible fixture files before App Server startup.

The host repository, normal project tree and user profile remain outside that volume.

The successor fails closed if root confinement cannot be established.

## 4. Local mutation boundary

All persistent study artifacts other than the mounted volume itself remain below:

```text
g2e/.local/P5A-D2S2/
```

The VHDX backing file also resides there.

The one-click wrapper is required to verify path containment and exact source state before creating/mounting the volume.

## 5. One-click governance

The proposed wrapper improves execution integrity because it converts the local procedure from manually copied independent commands into one fail-closed executable unit.

Required properties:

```text
exact-SHA checkout
clean worktree
deterministic drive selection
admin gate
bounded local paths
frozen fixture hashes
fresh CODEX_HOME
no turn/start
JSON + Markdown report
nonzero exit on blocker
```

## 6. Risk review

Checked risks:

- accidental host-drive `:root` exposure;
- VHDX path escape;
- overwriting an existing VHDX;
- drive-letter collision;
- stale mounted study volume;
- dirty Git state;
- scientific turn leakage;
- auth/token report leakage;
- reusing D2-S1 attempt identity;
- silent continuation after failed PowerShell gate.

All are explicitly fail-closed in the spec.

## 7. Gate review

```text
S2-Q0 predecessor closed preturn                     PASS
S2-Q1 new study/attempt/profile identities            PASS
S2-Q2 fixture hashes unchanged                        PASS
S2-Q3 dedicated VHDX root required                    PASS
S2-Q4 host repository outside task volume             PASS
S2-Q5 network disabled                                PASS
S2-Q6 exact result write path                         PASS
S2-Q7 no turn/start preflight                         PASS
S2-Q8 one-click fail-closed wrapper                   PASS
S2-Q9 report contract excludes secrets                PASS
S2-Q10 no scientific authorization                    PASS
```

## 8. Authorization

This QA authorizes implementation and static qualification of:

- a D2-S2 dynamic no-turn preflight driver;
- a D2-S2 one-click PowerShell wrapper;
- tests and exact-SHA CI for those two artifacts.

It does not authorize a model turn or scientific attempt.
