# G2E P5A D2-S1 — Root-Read Authority Incompatibility Adjudication

**Status:** `PRETURN_PLATFORM_AUTHORITY_INCOMPATIBLE / D2-S1 CLOSED`  
**Scientific result:** NONE  
**Scientific attempt consumed:** FALSE  
**Model turn executed:** FALSE

## 1. Evidence

The exact qualified D2-S1 elevated setup diagnostic returned:

```text
windows_sandbox_readiness_before = updateRequired
windows_sandbox_setup_requested = true
windows_sandbox_setup_started = true
windows_sandbox_setup_completed = true
windows_sandbox_setup_mode = elevated
windows_sandbox_setup_success = false

windows_sandbox_setup_error_redacted =
  elevated Windows sandbox requires effective `:root` read access

thread_id_present = false
turn_start_request_sent = false
scientific_attempt_consumed = false
result_exists = false
input_unchanged = true
task_unchanged = true
```

## 2. Adjudication

D2-S1 froze an exact-file task authority:

```text
READ:
  exact input.json
  exact TASK.md

WRITE:
  exact result.json

NETWORK:
  disabled
```

The observed Windows elevated sandbox backend requires effective filesystem-root read authority before setup can proceed.

Granting `:root = read` on the current host drive would materially broaden task-data authority beyond the frozen D2-S1 contract.

Therefore it is forbidden to repair D2-S1 by adding host-drive root read.

This is not a scientific FAIL of Codex repository capability. It is a platform/authority incompatibility between:

- the exact-file D2-S1 authority contract; and
- the Windows elevated sandbox enforcement prerequisite in the frozen local harness.

## 3. Closure

D2-S1 is closed at the preturn infrastructure boundary.

```text
scientific attempt identity:
p5a-d2s1-p5-fx-001-attempt-001

attempt consumed:
false

repository_read scientific claim:
not established

repository_write scientific claim:
not established

runtime adapter:
not authorized
```

No LINEAGE scientific milestone is warranted.

## 4. Successor direction

A successor may preserve effective task authority by placing only the frozen task fixture on a dedicated isolated filesystem volume and granting root-read authority only to that isolated volume.

Such a successor must be preregistered independently and must prove before any model turn that:

1. the isolated volume contains exactly the frozen task-visible files;
2. the host repository and normal user data are outside the volume;
3. `:root = read` resolves only to the isolated volume root;
4. network remains disabled;
5. write authority remains limited to the designated result path;
6. setup/thread qualification occurs with no `turn/start`.

That successor is a new study, not a retry of D2-S1.
