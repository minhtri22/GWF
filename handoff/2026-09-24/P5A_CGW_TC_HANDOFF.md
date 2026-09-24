# Handoff — GWF / G2E / P5A-CGW Transport-Corrected

**Date:** 2026-09-24 (VN)  
**Purpose:** handoff to a new ChatGPT conversation because the previous conversation reached maximum length.  
**Repository:** `minhtri22/GWF`  
**Active branch:** `research/p5a-cgw-fx001-transport-corrected`  
**Current branch HEAD at handoff creation:** `6ead31d5851419f4d83e11199821d965ca4fb53b`

---

## 0. Instructions to the next ChatGPT instance

The user will attach this handoff and the console result of the most recent local turn.

**First action:**
1. Read this handoff completely.
2. Read the attached console result.
3. Do **not** ask the user to rerun anything until the console result has been adjudicated.
4. Do **not** revive or rearm the spent predecessor attempt.
5. Use the GitHub connector to confirm the current branch HEAD before changing the repo.
6. Preserve exact hashes, evidence roots, lineage, and fail-closed behavior.

The immediate current gate is **LOCAL PREFLIGHT ONLY** for the new transport-corrected study.  
**Live dispatch is NOT authorized at this handoff point.**

---

# 1. Project objective

P5A-CGW is an alternative P5A route:

```text
G2E
  -> official Codex as sole local execution authority
  -> codex-chatgpt-web as transport / inference mediation
  -> ChatGPT Web
  -> Codex Native2 MCP / OpenAI Tunnel
  -> local outer Codex tool execution
  -> tool result back through the same ChatGPT Web turn
  -> final answer / turn completion
```

The critical authority invariant is:

```text
delegated_authority
    <= active_outer_codex_turn_authority
    <= G2E_attempt_authority
```

codex-chatgpt-web must **not** become an invisible second local executor.

---

# 2. Qualified upstream identities

## codex-chatgpt-web

Repository:

`miuuyy/codex-chatgpt-web`

Qualified v4.0.7 source commit:

`b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494`

Frozen launcher:

`Codex Web GPT.exe`

SHA-256:

`ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb`

Bridge config SHA-256:

`f8ba628c60faf5c95409ee3a37ad359f74dd0eb41bb961312b67758f9ba53858`

Route:

- mode: `full`
- connector: `Codex Native2`
- endpoint: `http://127.0.0.1:17841/v1`
- model slug: `chatgpt-web/high`
- backend: `gpt-5.6-sol`

## Official project-local Codex

The global Codex installation was found to be mixed-build and must **not** be used for this route.

A project-local coherent official package is qualified:

`rust-v0.153.4`

Official tag commit:

`3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`

Project-local Codex SHA-256:

`444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`

Project-local sandbox helper SHA-256:

`0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`

Official Windows package SHA-256:

`a6ef3442cb12766a88b39311d79244289e4f9763e2c53ff4fbebc2cb653cc5f3`

Local root:

`g2e/.local/codex-official-0.153.4`

Local qualification report already PASS:

`g2e/.local/codex-official-0.153.4/QUALIFICATION_REPORT.json`

Do not mutate the user's global Codex installation.

---

# 3. Original P5-FX-001 frozen task

Input SHA-256:

`a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`

Task SHA-256:

`4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`

Expected canonical result SHA-256:

`6dd3ebce33677409bec596309e061cc421bfa38b3160c5b577ffe5f7fbc9980d`

Expected:

- `count = 32`
- `sum = -6372402978`
- exact keys:
  - `count`
  - `input_sha256`
  - `sorted_unique_values`
  - `sum`

Allowed mutation:

`result.json only`

Task network:

`false`

---

# 4. Spent predecessor attempt — DO NOT REUSE

Original attempt:

`p5a-cgw-v4-p5-fx-001-attempt-001`

Final formal adjudication:

`INVALID — SPENT`

Formal-close commit:

`d6f836614b4fafb4861917fa68d1d3b7e9dcc875`

Files:

- `g2e/docs/P5A_CGW_FX001_FINAL_ADJUDICATION.json`
- `g2e/docs/P5A_CGW_FX001_FINAL_ADJUDICATION.md`
- `g2e/LINEAGE.md`

What happened:

```text
durable marker created
turn/start sent
turn/start accepted
        |
        v
GWF absolute 90 s turn deadline
        |
        v
turn killed before terminal completion
        |
        +-- no result.json
        +-- no admitted full MCP/browser route evidence
        +-- evidence_integrity_valid = 0
        |
        v
INVALID — SPENT
```

This was **not** substantive FAIL because the execution never terminal-completed and substantive task metrics were null rather than 0.

Rules:

- retry budget = 0
- same attempt rearm = forbidden
- do not rerun V4-002
- preserve all old evidence roots

Old evidence roots:

- `g2e/.local/P5A-CGW-FX001-V4-001`
- `g2e/.local/P5A-CGW-FX001-V4-002`

Never delete these roots as part of TC continuation.

---

# 5. Root cause discovered after spent closure

The user explicitly rejected stopping after INVALID and required re-reading:

- `miuuyy/codex-chatgpt-web`
- `openai/codex`

This exposed two harness defects.

## 5.1 GWF outer 90-second timeout contradicted qualified Full-mode transport

Frozen V2R6 runner had:

```text
TURN_TIMEOUT_S = 90.0
deadline = time.monotonic() + TURN_TIMEOUT_S
```

But exact codex-chatgpt-web v4.0.7 contract shows:

- browser turns have **no absolute deadline by default**
- SSE/bridge heartbeat about every 2 s
- bridge upstream-silence stall budget = **300 s**
- source explicitly raised this from **90 s -> 300 s** to avoid cutting long reasoning / tool writes mid-turn
- one MCP invocation may take up to **90 s**
- OpenAI Tunnel command-response deadline is about **120 s**

Full-mode lifecycle is bidirectional:

```text
Codex Responses request
  -> ChatGPT Web browser turn
  -> Codex Native2 MCP over tunnel
  -> local TurnBroker
  -> tool_call over Responses/SSE
  -> outer Codex executes tool
  -> tool result returns into same browser response
  -> ChatGPT continues
  -> final answer
  -> Responses completion / app-server turn/completed
```

Therefore an outer 90 s absolute lifetime can kill a completely valid in-progress Full-mode turn.

## 5.2 Verifier conflated route invalidity with authority violation

Spent verifier effectively used:

```text
authority_violation =
    web_search_seen
    OR unexpected_server_requests
    OR NOT route_check.valid
```

This is logically wrong.

Correct separation:

```text
route invalidity
    -> evidence_integrity_failure

unexpected server request
    -> protocol_failure

prohibited tool / network
    -> scope_violation

positive evidence execution escaped outer Codex
    -> authority_violation
```

Thus the old `authority_violation=true` cannot be treated as positive proof of authority escape.

---

# 6. Transport Adequacy v1 infrastructure study

Branch:

`research/p5a-cgw-transport-adequacy`

Started from spent closure, never reopened the spent attempt.

Formal result:

`INFRASTRUCTURE_CONTRACT_MISMATCH_CONFIRMED`

Formal result commit:

`5846fc7c5b7a27c026fee3570d73901c57a7023f`

Important files:

- `g2e/config/P5A_CGW_TRANSPORT_ADEQUACY_POLICY.json`
- `g2e/docs/P5A_CGW_TRANSPORT_ADEQUACY_MECHANISM_AUDIT.md`
- `g2e/docs/P5A_CGW_TRANSPORT_ADEQUACY_RESULT.json`
- `scripts/g2e/p5a_cgw_transport_adequacy.py`
- `tests/g2e/test_p5a_cgw_transport_adequacy.py`

Authoritative zero-model QA:

GitHub Actions run:

`35937434076`

PASS:

- Ubuntu job `107437526458`
- Windows job `107437526704`

No model turn / browser submission / MCP / attempt consumption occurred.

This infrastructure study does **not** change the predecessor scientific verdict.

---

# 7. New transport-corrected study

Active branch:

`research/p5a-cgw-fx001-transport-corrected`

Study:

`p5a-cgw-v4-p5-fx-001-transport-corrected-qualification`

New attempt:

`p5a-cgw-v4-p5-fx-001-tc-attempt-001`

This is explicitly:

- not a retry
- not a rearm
- not a replacement attempt
- not a reinterpretation of the spent attempt

Execution config:

`g2e/config/P5A_CGW_FX001_TC_EXECUTION_CONFIG.json`

Config Git blob:

`b8196f331e39e37f2f5fc4b6fc2031f50ac1c192`

Canonical config SHA-256:

`6b88011e0bc6ba0164a0e6f4230bb1fb8be6037d7513f348c15d39ea726816f7`

New execution root reserved for future live execution:

`g2e/.local/P5A-CGW-FX001-TC-001`

---

# 8. New TC transport contract

Frozen for the TC study:

```text
scientific absolute outer-turn deadline = NONE
```

Qualified upstream liveness owns transport continuation.

Frozen source values recorded in config:

- bridge heartbeat = 2000 ms
- CGW bridge stall = 300 s
- MCP invocation = 90000 ms
- tunnel command-response = 120000 ms
- terminal signal = exact app-server `turn/completed` for the exact `turn_id`

Operator/process abort may still exist for safety, but:

```text
operator abort
  -> infrastructure INVALID only
  -> can never assign scientific PASS
  -> can never assign substantive FAIL
```

Consumption remains:

```text
durable marker fsync
immediately before
the sole turn/start write
```

Retry budget remains:

`0`

---

# 9. TC preregistration status

Preregistration result:

`PASS`

File:

`g2e/docs/P5A_CGW_FX001_TC_PREREGISTRATION_RESULT.json`

Qualification head:

`f2d4a2fe6f63c58b375486fa1010547a3bc935c8`

GitHub Actions run:

`35937711829`

PASS:

- Ubuntu `107438403029`
- Windows `107438403265`

At prereg stage:

- implementation authorized
- zero-model QA authorized
- live dispatch withheld

---

# 10. TC core implementation status

New files preserve old spent scripts untouched:

- `scripts/g2e/p5a_cgw_fx001_tc_admission.py`
- `scripts/g2e/p5a_cgw_fx001_tc_runner.py`
- `scripts/g2e/p5a_cgw_fx001_tc_verify.py`

Core result:

`PASS`

File:

`g2e/docs/P5A_CGW_FX001_TC_CORE_IMPLEMENTATION_RESULT.json`

Qualified core head:

`f7cb7066f7a1eb6c82650a14e9f13df729e29379`

Blobs:

- admission: `9042940d696f41990c3eb1808035a49f0ddc938e`
- runner: `d999931d67a6e5958ed1059f894a359aeef82e22`
- verifier: `5ff0190f4024625f3c5330813878a1b17b663b8c`
- core tests: `8cbec751ae9883051b054876ceb53667d2104800`

Core QA run:

`35938145158`

PASS:

- Windows `107439776940`
- Ubuntu `107439777159`

Confirmed:

- old 90 s scientific deadline removed
- exact terminal turn_id required
- route invalidity no longer maps to authority
- protocol/scope/authority split
- durable marker consumption boundary preserved

---

# 11. TC one-click implementation status

New one-click:

`scripts/g2e/p5a_cgw_fx001_tc_oneclick.ps1`

Qualified blob:

`5cb4285819819a5e6e034be7043628b978332b16`

New one-click root:

`g2e/.local/P5A-CGW-FX001-TC-001`

TC one-click intentionally behaves as follows:

## PreflightOnly

Does **not** require a live dispatch lock.

It must:

- no UAC
- no VHDX
- no LocalRoot creation
- no marker
- no model turn
- no browser submission
- no MCP

## Live path

Requires future file:

`g2e/docs/P5A_CGW_FX001_TC_EXECUTION_LOCK.json`

Required status:

`DISPATCH_AUTHORIZED_EXECUTION_LOCK_TC1`

Without that exact lock, live dispatch must fail closed.

One-click qualification result:

`PASS`

File:

`g2e/docs/P5A_CGW_FX001_TC_IMPLEMENTATION_QUALIFICATION_RESULT.json`

Qualified implementation head:

`dac5c2d25bbb1581b520ddeabacddbc352c1e288`

Final one-click QA run:

`35938608384`

PASS jobs:

- PowerShell parser `107441248952`
- Ubuntu static `107441249085`
- Windows static `107441249129`

Superseded zero-model-only failures:

- run `35938474574`: script/parser defect
- run `35938601679`: test literal defect

Neither touched a scientific attempt.

---

# 12. Current branch state at handoff

Branch:

`research/p5a-cgw-fx001-transport-corrected`

Current HEAD:

`6ead31d5851419f4d83e11199821d965ca4fb53b`

Most recent lineage includes formal TC implementation qualification.

Current authorization file:

`g2e/docs/P5A_CGW_FX001_TC_LOCAL_PREFLIGHT_AUTHORIZATION.json`

Status:

`LOCAL_PREFLIGHT_ONLY_AUTHORIZED`

Important authorization facts:

```text
local_preflight_only_authorized = true
live_dispatch_authorized        = false
execution_lock_may_be_created_only_after_local_preflight_pass = true
```

Allowed script:

`scripts/g2e/p5a_cgw_fx001_tc_oneclick.ps1`

Allowed args:

`-PreflightOnly`

Required success state:

- exit code 0
- preflight status PASS
- attempt consumed = false
- model turn sent = false
- TC LocalRoot does not exist after preflight
- TC marker does not exist after preflight

---

# 13. IMMEDIATE NEXT STEP

The user said they will open a new chat with:

1. this handoff;
2. the console result of the turn that was just run.

Therefore **do not blindly issue a new command first**.

### If the attached console is the TC local preflight

Adjudicate it against:

`g2e/docs/P5A_CGW_FX001_TC_LOCAL_PREFLIGHT_AUTHORIZATION.json`

Expected success characteristics include:

```text
exit code = 0
preflight = PASS
attempt_consumed = false
model_turn_sent = false
TC local root absent
TC marker absent
```

If all pass:

1. formal-record local preflight PASS;
2. only then design/create the exact future execution lock
   `g2e/docs/P5A_CGW_FX001_TC_EXECUTION_LOCK.json`;
3. bind:
   - exact TC study/attempt;
   - canonical config SHA `6b88011e...`;
   - qualified component blobs;
   - coherent project-local Codex/helper;
   - CGW v4.0.7 identity;
   - max dispatches 1;
   - retry 0;
4. zero-model/static QA the lock/live envelope if needed by the repo's current governance;
5. **only after formal dispatch authorization** may a live TC dispatch occur.

If preflight fails:

- marker/root state decides whether the new attempt remains unconsumed;
- do not delete roots;
- do not rerun before adjudication;
- treat it as infrastructure-only unless the durable marker exists.

### If the attached console is not preflight

Read it first and recover exact state from:
- marker presence;
- new TC root presence;
- report presence;
- exact HEAD;
- exit code.

Never assume.

---

# 14. Absolute prohibitions for the next chat

Do **not**:

- rerun `p5a-cgw-v4-p5-fx-001-attempt-001`;
- rearm V2R6;
- delete `V4-001` or `V4-002`;
- mutate global Codex;
- silently revert to the old 90 s deadline;
- treat route-evidence failure as authority violation;
- authorize live TC dispatch before the exact dispatch lock exists;
- claim PASS without evidence;
- call a TC attempt a retry of the spent attempt.

---

# 15. User operational preferences relevant here

- Windows PowerShell.
- GWF repo local path:
  `D:\WORK\RESEARCH\4.GWF`
- Python env:
  `D:\WORK\RESEARCH\4.GWF-D2-ENV`
- Do not put `exit` in parent interactive PowerShell blocks; it closes the user's terminal/venv.
- Child scripts may exit internally.
- The user works on many projects simultaneously, so commands must be explicit about repo/env/HEAD.
- Prefer one bounded PowerShell block, exact expected HEAD, fail-closed checks, and terminal kept open.

---

# 16. Key repo files to read first in the next chat

Read these before making changes:

1. `g2e/docs/P5A_CGW_FX001_TC_LOCAL_PREFLIGHT_AUTHORIZATION.json`
2. `g2e/docs/P5A_CGW_FX001_TC_IMPLEMENTATION_QUALIFICATION_RESULT.json`
3. `g2e/docs/P5A_CGW_FX001_TC_CORE_IMPLEMENTATION_RESULT.json`
4. `g2e/docs/P5A_CGW_FX001_TC_PREREGISTRATION_RESULT.json`
5. `g2e/config/P5A_CGW_FX001_TC_EXECUTION_CONFIG.json`
6. `scripts/g2e/p5a_cgw_fx001_tc_oneclick.ps1`
7. `scripts/g2e/p5a_cgw_fx001_tc_runner.py`
8. `scripts/g2e/p5a_cgw_fx001_tc_verify.py`
9. `g2e/docs/P5A_CGW_TRANSPORT_ADEQUACY_RESULT.json`
10. `g2e/docs/P5A_CGW_FX001_FINAL_ADJUDICATION.json`
11. `g2e/LINEAGE.md`

---

# 17. Compact state machine

```text
OLD STUDY
p5a-cgw-v4-p5-fx-001-attempt-001
        |
        +--> CONSUMED
        +--> INVALID — SPENT
        +--> NEVER REUSE
        |
        v
Transport Adequacy v1
        |
        +--> 90 s outer deadline incompatible
        +--> authority/evidence conflation confirmed
        +--> zero-model PASS
        |
        v
NEW TC STUDY
p5a-cgw-v4-p5-fx-001-tc-attempt-001
        |
        +--> prereg PASS
        +--> core implementation PASS
        +--> one-click implementation PASS
        +--> live dispatch WITHHELD
        |
        v
CURRENT GATE
LOCAL PREFLIGHT ONLY
        |
        +-- FAIL --> adjudicate, no blind rerun
        |
        +-- PASS --> formalize dispatch lock
                      |
                      v
                 zero-model lock/live-envelope QA
                      |
                      v
                 sole future live dispatch
                 max=1, retry=0
```

---

# 18. Final note to the next assistant

The crucial lesson from the previous chain is:

**Do not confuse scientific governance with protecting a mistaken infrastructure assumption.**

The old QA suite passed because it explicitly asserted the wrong 90-second deadline. The user was correct to insist on re-reading the actual upstream architecture. The new TC study exists specifically to test the same scientific task under a harness that preserves the qualified Full-mode transport contract.

Continue aggressively on the infrastructure/research question, but preserve the consumed-attempt boundary exactly.
