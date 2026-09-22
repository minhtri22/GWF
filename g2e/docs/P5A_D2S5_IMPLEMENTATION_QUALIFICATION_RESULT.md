# G2E P5A D2-S5 — Implementation / Zero-Model Qualification Result

## Verdict

**PASS — ONE LOCAL D2-S5 SCIENTIFIC ATTEMPT MAY BE LOCKED**

This result supersedes the earlier candidate `85e5312c032225a317c3116ba9150bf325af4b23`
for execution-lock purposes.

The earlier qualification exposed a coverage gap after lock review: the scientific verifier still bound
an obsolete observable-client blob even though the runner/admission bound the final client. That would
have forced `evidence_integrity_valid=0` during a real D2-S5 execution.

The verifier identity was repaired prospectively and the full zero-model macro-gate was rerun.

## Exact authoritative candidate

- SHA: `2b37ade5dab3f13a55192b674d2531ca4876676b`
- workflow: `35794109437`
- Linux job: `106969254830` — PASS
- Windows job: `106969254628` — PASS
- artifact: `10722927391`
- artifact digest:
  `sha256:a959761219fe55806b3a1cb959e52e9a537cb3aa3e07174b4c39e1011c0c4421`

## Frozen execution identity

- study:
  `p5a-d2s5-observability-qualified-functional-successor`
- attempt:
  `p5a-d2s5-p5-fx-001-attempt-001`
- execution config:
  `27bf768c7189fc630d04bcc98d8c854c1409151ab42e3ea466c10128aca36240`
- observable client:
  `72c77c1fbd1e2c20881723f18ef2f1435ded2b2b`
- OQ1 observability:
  `b6d3c6fcb671dd166893edd46388c8d69dca9105`
- runner:
  `259224a53aac7b79d0607360ba496d07503ef38d`
- verifier:
  `91b30c10c0626a82989c6f8091155b63d784fa41`
- admission:
  `a37e78d28bf9cc59b0e9ee5dc2b41c659e316f92`
- one-click:
  `175ff9e22a912c4c1a20d66ddc41ff41a36d7077`
- test:
  `325c8d2836bc67538bd99725fe0ec6954ee18a83`
- workflow:
  `5a933bd64216b924d9e12e624370fd989bb19ef2`

## Qualification evidence

PASS includes:

- bounded repair diff from exact baseline `7072539b2b63b1316b90c7ab270a6f8c84014473`;
- live `RpcClient._record_stdout` synthetic `error` notification;
- live `RpcClient._record_stdout` synthetic `turn/completed(status=failed)`;
- `TurnError.message`, `codexErrorInfo`, `additionalDetails`, `willRetry` preservation;
- privacy redaction end-to-end;
- unrelated protocol payload minimization;
- queue.Empty → TimeoutError regression protection;
- delayed terminal survival across repeated empty polls;
- verifier exact client identity = final observable-client blob;
- verifier exact OQ1 identity = qualified observability blob;
- verifier observability evidence-admission enforcement;
- marker-before-send / sole `turn/start` path;
- frozen 90-second timeout;
- retry budget 0;
- Windows PowerShell 5.1 parser and infrastructure self-test;
- exact official `rust-v0.153.4` D1 structural discovery;
- deterministic P1.5 admission;
- P1/P1.4/P1.5/P2/P3/P4 regressions.

No P5-FX-001 scientific task or model turn was executed by qualification.

## Supersession

The earlier execution lock/result referencing verifier blob
`094809a2edbb1d1d9a207d53644f9f8f8cb89bb6`
is superseded and MUST NOT authorize execution.

Only the repaired verifier blob
`91b30c10c0626a82989c6f8091155b63d784fa41`
is execution-authoritative.

## Authorization consequence

This PASS permits one exact execution lock authorizing **one** local D2-S5 scientific attempt.

It does not authorize retries.

After the durable attempt marker is created, retry budget remains zero.
