# G2E P5A D2-S5 — Implementation / Zero-Model Qualification Result

## Verdict

**PASS — ONE LOCAL D2-S5 SCIENTIFIC ATTEMPT MAY BE LOCKED**

The D2-S5 implementation satisfies the preregistered bounded implementation gate without executing a
model-bearing scientific turn.

## Exact qualified candidate

- SHA: `85e5312c032225a317c3116ba9150bf325af4b23`
- workflow: `35791102414`
- Linux job: `106959520892` — PASS
- Windows job: `106959521159` — PASS
- artifact: `10721103828`
- artifact digest:
  `sha256:4a679a55525a0028ce0d64ccceb946bdd1520bac67b265a4f0e64f81793a6b70`

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
  `094809a2edbb1d1d9a207d53644f9f8f8cb89bb6`
- admission:
  `a37e78d28bf9cc59b0e9ee5dc2b41c659e316f92`
- one-click:
  `175ff9e22a912c4c1a20d66ddc41ff41a36d7077`

## Qualification evidence

PASS includes:

- live `RpcClient._record_stdout` synthetic `error` notification;
- live `RpcClient._record_stdout` synthetic `turn/completed(status=failed)`;
- `TurnError.message`, `codexErrorInfo`, `additionalDetails`, `willRetry` preservation;
- privacy redaction end-to-end;
- unrelated protocol payload minimization;
- queue.Empty → TimeoutError regression protection;
- delayed terminal survival across repeated empty polls;
- verifier observability evidence-admission enforcement;
- marker-before-send / sole `turn/start` path;
- frozen 90-second timeout;
- retry budget 0;
- Windows PowerShell 5.1 parser and infrastructure self-test;
- exact official `rust-v0.153.4` D1 structural discovery;
- deterministic P1.5 admission;
- P1/P1.4/P1.5/P2/P3/P4 regressions.

No P5-FX-001 scientific task or model turn was executed by qualification.

## Windows portability finding

An earlier candidate failed only because OQ1 identity was computed from working-tree bytes. Windows
checkout line-ending normalization changed those bytes while the repository Git object remained exact.

The final implementation binds the OQ1 source by exact repository object
`HEAD:scripts/g2e/p5a_codex_observability.py`, while the scientific wrapper/runner independently
fail closed on a dirty worktree before model dispatch.

The repaired candidate passed both Linux and Windows.

This finding changes no scientific semantics.

## Authorization consequence

The PASS permits creation of an exact execution lock authorizing **one** local D2-S5 scientific
attempt.

It does not authorize retries.

After the durable attempt marker is created, retry budget remains zero.
