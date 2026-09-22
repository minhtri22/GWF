# G2E P5A D2-S2 A1 — Config Serialization Preturn Blocker Adjudication

## Status

**Verdict:** PRETURN_INFRASTRUCTURE_BLOCKED / SCIENTIFIC ATTEMPT UNUSED  
**Scientific result:** NONE  
**Model turn executed:** FALSE  
**Scientific attempt consumed:** FALSE

## Bound evidence

Returned A1 report:

- file: `P5A_D2S2_A1_ONECLICK_REPORT(1).json`
- SHA256: `eb7773a0f813a93a0c251e1f7807a540e7c2487101b6f711b2fe3d666034ce2b`
- source HEAD: `58dc2b0a7fa9054afbe945fbef6beb02662b87b9`
- qualified candidate: `858bc509d7aad95423af3eee064329670fcef6f7`
- one-click blob: `23b97c6e41e633782ac0fb69ae67d7596c05ac7d`
- preflight blob: `df3dcf3194d1f6198e75be8d2d46f1f22b8591b5`
- selected drive: `S:`
- fixture hashes: exact frozen values
- task payload names: `input.json`, `TASK.md`
- filesystem-support metadata: `System Volume Information`
- unexpected root names: none
- config SHA256: null
- preflight evidence: none
- `turn_start_request_sent=false`
- `scientific_attempt_consumed=false`

Observed diagnostic:

`Cannot convert argument "oldChar", with value: "\r\n", for "Replace" to type "System.Char"`

## Classification

A1 successfully passed the amended NTFS root-closure policy. The blocker occurred during deterministic
`config.toml` materialization, before App Server preflight and before any thread or scientific turn.

The A1 expression:

`$config.Replace([Environment]::NewLine, [char]10)`

is overload-sensitive under Windows PowerShell 5.1. Because the second argument is explicitly a
`System.Char`, overload resolution selects `String.Replace(Char, Char)`; the CRLF string cannot be
converted to one character.

This is a preturn harness/runtime defect, not scientific evidence.

## No-rescue boundary

The A1 local root, VHDX, report, and all evidence remain historical and immutable. A1 is not rerun.

A successor amendment may change only deterministic config newline serialization and successor-local
artifact identities. It must preserve:

- study/attempt/profile identity;
- frozen fixture/task hashes;
- Codex executable identity;
- NTFS closed-set policy;
- root-read authority confined to the dedicated volume;
- exact result write;
- network disabled;
- no-turn preflight sequence;
- zero scientific attempt consumption.

A later PASS authorizes only another no-turn preturn execution.
