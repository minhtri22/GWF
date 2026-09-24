# P5A-CGW FX001 TC-002 — Prospective Pre-consumption Semantic Admission Repair

## Scientific state

The TC scientific attempt `p5a-cgw-v4-p5-fx-001-tc-attempt-001` remains
`RESERVED_UNCONSUMED`.

TC-001 stopped before the durable marker and is preserved immutable under:

`g2e/.local/P5A-CGW-FX001-TC-001`

TC-002 is not a retry of a consumed attempt. It is a prospective
pre-consumption infrastructure repair using a new evidence root:

`g2e/.local/P5A-CGW-FX001-TC-002`

## Proven defect

TC-001 admission rejected the raw CGW config SHA-256 although:

- the same raw bytes were observed with bridge health OK and idle;
- offline semantic probe v2 passed every source-backed config check;
- no scientific dispatch occurred.

Therefore whole-file config SHA is not a valid standalone transport
invariant for this launcher-managed config.

## Repair

TC-002 removes only the whole-file SHA equality requirement.

It retains raw SHA-256 as provenance output and replaces the rejected
guard with explicit semantic checks. In addition to source-validity
checks, TC-002 freezes the exact locally validated values:

- release 4.0.7;
- mode full;
- subagent protocol compatibility-v1;
- loopback 127.0.0.1:17841;
- context window 256000;
- connector Codex Native2;
- browser host launcher;
- Sol=true, Pro=false;
- experimental bigger context=true;
- stall timeout absent or 300 seconds;
- auto-approve=false;
- Windows runtime executable basename bun.exe;
- runtime command length=2.

The guard also retains upstream v4.0.7 structural requirements for control
token, broker endpoint, durable runtime command and full-mode tunnel
metadata without disclosing secret values.

## Unchanged scientific contract

Unchanged:

- study id;
- attempt id;
- task/input/result hashes;
- project-local official Codex identity;
- CGW launcher binary/source identity;
- outer-Codex authority invariant;
- network-disabled task scope;
- result.json-only mutation scope;
- durable-marker consumption boundary;
- retry budget 0;
- max scientific dispatch 1;
- no scientific absolute outer-turn timeout.

## Activation rule

The old TC-001 live lock remains evidence only and is not reused.

TC-002 may not live-dispatch until:
1. successor admission + one-click implementation passes zero-model QA;
2. a TC-002 lock candidate binds exact successor blobs;
3. lock-candidate QA passes;
4. an exact TC-002 live lock is promoted byte-identically.

No live/model/browser/MCP execution is authorized by this plan alone.
