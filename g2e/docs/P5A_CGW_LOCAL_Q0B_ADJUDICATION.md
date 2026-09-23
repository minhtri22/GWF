# G2E P5A-CGW — Local Q0b Adjudication

## Verdict

**LOCAL ADMISSION BLOCKED / NOT A SCIENTIFIC FAIL / NO MODEL ATTEMPT / NO RETRY UNDER THE SAME LOCK**

The one authorized local Q0b collection completed without model execution. The route itself is healthy and structurally coherent, but the installed bridge identity does not match the frozen source/runtime requirement.

## Admitted evidence

- uploaded report file SHA-256: `b91f425a1b92ea0c4cf2d5f1179ecd413cc04b5ac6285034dfd975b446efc2ff`
- internal evidence SHA-256: `551d6c90c48c0761880d937257189b626d586772030558e34a516d4d80d6a68e`
- report status: `LOCAL_ZERO_MODEL_ADMISSION_BLOCKED`
- blocker: `CGW_RELEASE_VERSION`

Observed local identities:

- CGW `Codex Web GPT.exe`: `ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb`
- Codex `codex.exe`: `a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`

## What passed locally

The local evidence confirms:

- bridge service healthy and accepting turns;
- no active HTTP/browser turn during collection;
- loopback route `127.0.0.1:17841`;
- `full` mode;
- active connector `Codex Native2`;
- auto approval disabled;
- tunnel configuration present;
- Codex `openai_base_url = http://127.0.0.1:17841/v1`;
- selected Codex model resolves to CGW;
- no model turn, `/v1/models`, `/v1/responses`, browser submission or scientific attempt occurred.

## Blocking mismatch

Installed local CGW:

`4.0.7`

Frozen P5A-CGW source/runtime reference:

`5.0.8`

Therefore Q0b cannot pass. A working Codex↔CGW route is insufficient for this lock because exact runtime identity is part of the admission contract.

## Governance consequence

This is an outcome-independent infrastructure mismatch discovered before model execution. Therefore:

- do not reinterpret it as scientific FAIL;
- do not credit it as functional PASS;
- do not retarget the frozen 5.0.8 specification to 4.0.7 after observing the local result;
- do not run another collection under the consumed one-collection lock;
- do not create the first functional P5A-CGW attempt;
- do not A/B against P5A official.

The admissible successor is a **new bounded zero-model runtime-alignment lock** whose only purpose is to align the installed CGW runtime to the already-frozen 5.0.8 identity and then authorize one fresh Q0b collection.
