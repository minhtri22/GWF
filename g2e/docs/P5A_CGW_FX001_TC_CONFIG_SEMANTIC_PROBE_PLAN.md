# P5A-CGW TC — Config Semantic Binding Probe

## Origin

The first TC live-wrapper invocation stopped before the durable marker with
`PREDISPATCH_ADMISSION_BLOCKED`. The sole admission error was
`CGW_CONFIG_HASH_DRIFT`.

Observed runtime evidence still matched the qualified route on the fields
already projected by admission: CGW 4.0.7, full mode, Codex Native2,
127.0.0.1:17841, tunnel present, auto-approve false, healthy/idle bridge,
and exact qualified CGW/Codex binary hashes.

The TC attempt remains RESERVED_UNCONSUMED. The old TC-001 local root is
preserved and must not be deleted or reused.

## Why no immediate repair

The current admission script froze the SHA-256 of the entire CGW
`config.json`. Upstream v4.0.7 configuration contains operational fields
such as control token, runtime command, runtime paths, browser-host paths,
tunnel metadata and other launcher-managed state. Upstream also serializes
configuration through `saveConfig()`.

Therefore whole-file identity is not automatically equivalent to the
scientific transport/authority contract. But removing the hash guard
without observing the remaining semantic fields would be too permissive.

## Authorized next action

Exactly one local read-only semantic probe is authorized.

The probe may:
- read `~/.codex-chatgpt-web/config.json`;
- GET loopback `http://127.0.0.1:17841/healthz`;
- hash raw config bytes for provenance;
- print only a redacted semantic projection.

The probe must never print:
- control token;
- tunnel id;
- runtime key path;
- full runtime command;
- full local private paths;
- browser/session state.

The probe performs no model endpoint request, browser submission, MCP call,
attempt marker write or scientific dispatch.

## Gate

Only after the local semantic projection is observed may a prospective
pre-consumption repair be specified.

No rerun of the TC scientific wrapper is authorized by this probe alone.
