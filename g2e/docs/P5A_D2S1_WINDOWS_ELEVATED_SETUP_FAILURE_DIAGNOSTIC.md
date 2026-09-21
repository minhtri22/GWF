# G2E P5A D2-S1 — Elevated Setup Failure Diagnostic

**Status:** FROZEN CANDIDATE FOR ZERO-FRESH QA  
**Parent program:** P5A D2-S1 permission-profile successor  
**Observed preturn:** elevated setup started and completed with `success=false`  
**Scientific turn:** NOT SENT  
**Scientific attempt consumed:** FALSE  
**Scope:** infrastructure diagnosis only; no scientific semantics change

## 1. Trigger

The qualified elevated Windows preturn reached:

```text
windowsSandbox/readiness = updateRequired
windowsSandbox/setupStart(mode=elevated) -> started=true
windowsSandbox/setupCompleted -> success=false
```

and stopped before any thread or scientific turn.

The frozen evidence also shows:

```text
thread_id = null
turn_start_request_sent = false
scientific_attempt_consumed = false
result_exists = false
input_unchanged = true
task_unchanged = true
```

The existing preflight recorded only the boolean setup failure and discarded the notification's structured `error` string. Therefore the next valid step is diagnostic observability, not another scientific attempt and not a permission relaxation.

## 2. Exact-source basis

Frozen harness source:

```text
openai/codex
tag: rust-v0.153.4
commit: 3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

Exact App Server protocol defines:

```text
windowsSandbox/setupCompleted:
  mode: elevated | unelevated
  success: boolean
  error: string | null
```

Exact Windows sandbox setup source returns specific setup failures including orchestrator and helper error codes such as:

```text
orchestrator_sandbox_dir_create_failed
orchestrator_elevation_check_failed
orchestrator_helper_launch_failed
orchestrator_helper_launch_canceled
orchestrator_helper_exit_nonzero
orchestrator_helper_report_read_failed
orchestrator_helper_incomplete
helper_request_args_failed
helper_user_provision_failed
helper_users_group_create_failed
helper_user_create_or_update_failed
helper_dpapi_protect_failed
helper_users_file_write_failed
helper_setup_marker_write_failed
helper_sid_resolve_failed
helper_capability_sid_failed
helper_firewall_com_init_failed
helper_firewall_policy_access_failed
helper_firewall_policy_ineffective
helper_firewall_rule_create_or_add_failed
helper_firewall_rule_verify_failed
helper_read_acl_helper_spawn_failed
helper_sandbox_lock_failed
helper_unknown_error
```

The setup error string is therefore required to distinguish platform/UAC/helper/ACL/firewall failures without changing scientific configuration.

## 3. Diagnostic amendment

The local no-turn preflight may be amended only to record safe setup-failure diagnostics.

On `windowsSandbox/setupCompleted` it MUST record:

```text
windows_sandbox_setup_mode
windows_sandbox_setup_success
windows_sandbox_setup_error_code
windows_sandbox_setup_error_redacted
windows_sandbox_setup_error_sha256
```

where:

- `error_code` is the prefix before the first colon when present;
- `error_sha256` hashes the original error string;
- `error_redacted` replaces the current username and user-profile path with placeholders before persistence/output;
- the original unredacted error string MUST NOT be written to evidence or stdout.

No auth/token/password/sandbox-user secret may be read or exposed.

## 4. Fresh diagnostic invocation

Because the previous App Server instance has exited and the setup notification text was not preserved, the diagnostic must use:

- same exact task fixture;
- same exact custom permission profile;
- same elevated sandbox config;
- same exact Codex executable;
- a **fresh isolated CODEX_HOME**;
- a **fresh evidence directory**;
- no `turn/start`;
- no result generation.

The diagnostic may execute `windowsSandbox/setupStart(mode=elevated)` once on that fresh home.

If setup succeeds, the preflight may continue through the already-qualified no-turn profile/thread checks.

If setup fails, it MUST stop after persisting the redacted diagnostic evidence.

## 5. Scientific firewall

The diagnostic MUST NOT change:

- input.json;
- TASK.md;
- expected output semantics;
- profile read/write authority;
- network disabled;
- approval policy;
- model/provider;
- capability target;
- scientific attempt ID;
- retry budget;
- verifier/adjudication rule.

It MUST contain no `turn/start`.

D2-S1 attempt remains:

```text
p5a-d2s1-p5-fx-001-attempt-001
```

and remains unused until a later explicit final admission authorizes scientific dispatch.

## 6. Verdicts

### `DIAGNOSTIC_SPEC_PASS_IMPLEMENTATION_REQUIRED`

Use iff the diagnostic changes observability only and retains the no-turn firewall.

### `DIAGNOSTIC_SPEC_BLOCKED`

Use if the exact setup failure cannot be observed without broadening task authority or exposing sensitive sandbox/auth state.

No scientific PASS/FAIL may be issued from this diagnostic.
