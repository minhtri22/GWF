# P5A-CGW TC — Offline Config Semantic Probe v2

## Origin

The first semantic probe was qualified as read-only but its implementation
required the loopback health endpoint before emitting the config projection.
The local probe encountered WinError 10061 because the CGW service was not
listening. No model/browser/MCP/attempt state was touched.

This does not contradict the prior TC predispatch evidence: during the
pre-dispatch wrapper, the bridge was healthy and idle while the observed
raw config SHA-256 was:

`6f4347acdcb722d52b2ea4bb166a53c28a809fdf13bb9f358e794bad12c16053`.

## Purpose

Probe v2 isolates the missing question:

> Do the exact config bytes that were previously observed together with a
> healthy bridge satisfy the full source-backed v4.0.7 semantic contract?

The raw hash is used only as a provenance join between the earlier health
snapshot and the current offline config projection. It is not promoted to a
new normative transport invariant.

## Authorized action

Exactly one local offline read-only probe is authorized.

The probe may read `~/.codex-chatgpt-web/config.json` and local filesystem
existence/absolute-path properties required by upstream v4.0.7 config
validation.

It performs no network request of any kind.

It must never print:
- control token value;
- tunnel id value;
- runtime key path;
- complete runtime command;
- complete private paths.

## Semantic checks

The probe binds:
- config version 3;
- production config, not dev harness;
- release 4.0.7;
- full mode;
- valid upstream subagent protocol;
- loopback host/port;
- positive context window;
- connector Codex Native2;
- launcher browser host;
- absolute required paths / valid Windows broker endpoint;
- boolean headed/capability fields;
- Sol availability and Pro=>Sol;
- experimental context boolean;
- stall timeout absent or 300 s;
- auto-approve false;
- valid control-token shape without disclosure;
- durable runtime command: nonempty, absolute executable, executable exists,
  and no absolute command component under an ephemeral temp root;
- complete/shape-valid full-mode tunnel metadata, without disclosure.

## Gate

PASS requires both:
1. every semantic check PASS; and
2. raw config SHA-256 equals the exact config hash observed during the
   previously healthy/idle TC predispatch admission.

Only then may the raw whole-file hash guard be prospectively replaced by a
source-backed semantic guard.

No scientific wrapper rerun is authorized by v2 alone.
