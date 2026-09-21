# G2E P5A D2-S1 — Elevated Setup Failure Diagnostic QA

**Verdict:** `DIAGNOSTIC_SPEC_PASS_IMPLEMENTATION_REQUIRED`  
**Finding count:** `0`  
**Diagnostic spec candidate:** `eaabb9337f0c59066fd580fb8640cd9ffe421d5e`  
**Fresh scientific turn:** NONE  
**Scientific attempt consumed:** FALSE

## 1. Evidence audit

The observed local preturn established:

```text
readiness_before = updateRequired
setup_requested = true
setup_started = true
setup_completed = true
setup_success = false
thread_id = null
turn_start_request_sent = false
scientific_attempt_consumed = false
result_exists = false
```

This is sufficient to classify the current state as a preturn infrastructure blocker but insufficient to determine its mechanism because the notification `error` field was not persisted.

## 2. Exact-source audit

Checked against exact Codex `rust-v0.153.4` at commit:

```text
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

Confirmed:

- `windowsSandbox/setupCompleted` exposes nullable `error`;
- setup errors have structured code/message forms;
- failures span UAC launch, helper launch/exit, provisioning, DPAPI, firewall, ACL, SID and setup-marker classes;
- diagnosis therefore requires the setup error identity before any further infrastructure amendment is scientifically justified.

## 3. Scope audit

Permitted change:

```text
observe + redact + hash setupCompleted.error
```

Prohibited changes:

- filesystem authority;
- network authority;
- default permission profile;
- elevated sandbox mode;
- fixture/task bytes;
- model/provider;
- timeout semantics except existing setup wait;
- scientific attempt identity;
- retry budget;
- turn dispatch.

## 4. Sensitive-data audit

The implementation must:

- never persist the original unredacted setup error;
- redact current username and current user-profile path;
- record only safe top-level sandbox-state names;
- never read or emit `auth.json` content;
- never read or emit sandbox-user password/DPAPI secret contents.

## 5. Gate review

```text
DFD-Q0 blocker occurred before thread/turn             PASS
DFD-Q1 exact setup error channel source-confirmed      PASS
DFD-Q2 observability-only amendment                    PASS
DFD-Q3 no authority broadening                         PASS
DFD-Q4 redaction required                              PASS
DFD-Q5 unredacted error persistence forbidden          PASS
DFD-Q6 fresh CODEX_HOME/evidence required              PASS
DFD-Q7 no turn/start permitted                         PASS
DFD-Q8 scientific attempt remains unused               PASS
```

## 6. Authorization

This QA authorizes only:

1. extend the existing no-turn preflight with redacted setup-failure capture;
2. add deterministic static/unit tests for redaction and no-turn guarantees;
3. run P1/P1.4/P1.5/P2/P3/P4 regressions;
4. qualify the exact diagnostic implementation;
5. execute one fresh no-turn diagnostic preflight.

It does not authorize a scientific model turn.
