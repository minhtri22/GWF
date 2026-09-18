# GitHub SHA-Safe QA Standard

This procedure is mandatory for GWF-managed writes to GitHub source code and documentation.

## Security boundary

GWF never persists GitHub access tokens, refresh tokens, passwords, API keys, private keys, or Authorization headers. A plugin connection stores only an opaque external connection reference plus declared capabilities. The host process resolves that reference to credentials outside the GWF database.

Minimum recommended GitHub permissions:

- repository contents: read for inspection;
- repository contents: write only when commit capability is required;
- workflows: write only when a change set modifies `.github/workflows/*`;
- pull requests: write only when PR creation/review workflows are enabled;
- no administration or secrets permission for ordinary source/document writes.

## Standard write procedure

Every GitHub write must follow this sequence:

1. **Freeze the change set**
   - repository binding;
   - target branch;
   - expected branch HEAD SHA;
   - per-file operation;
   - expected current blob SHA for UPDATE/DELETE;
   - SHA-256 of proposed UTF-8 file content;
   - commit message;
   - deterministic manifest hash.

2. **Branch HEAD preflight**
   - fetch the current remote branch SHA;
   - require exact equality with `expected_head_sha`;
   - mismatch means `STALE`; do not overwrite and do not silently refresh the expected SHA.

3. **Per-file blob preflight**
   - CREATE requires the path to be absent at the frozen head;
   - UPDATE/DELETE requires exact equality with the frozen Git blob SHA;
   - any mismatch means `STALE`.

4. **Immediate pre-write HEAD comparison**
   - fetch branch HEAD again immediately before the provider write;
   - require exact equality with the frozen expected SHA.

5. **Provider-side optimistic concurrency**
   - the GitHub adapter must receive `expected_head_sha`;
   - the adapter must reject the operation when the ref changed before the write is committed.

6. **Post-commit verification**
   - fetch the created commit;
   - verify its first parent equals the frozen expected branch SHA;
   - verify target branch HEAD equals the returned commit SHA;
   - fetch every affected path at the new commit;
   - verify SHA-256 content for CREATE/UPDATE and absence for DELETE.

7. **QA completion**
   - only a change set with status `VERIFIED` is QA-complete;
   - `COMMITTED` alone is not sufficient;
   - failed post-write checks produce `VERIFICATION_FAILED`.

8. **Audit**
   - persist the SHA checks and manifest hash;
   - append project audit events for preparation and successful verification.

## Conflict rule

A stale branch or file SHA is not an automatic retry condition. The agent must fetch the new state and create a new change set whose expected SHAs explicitly match the new remote state. This preserves reviewability and prevents accidental overwrite.

## Branch safety

Repository bindings default to `FEATURE_BRANCH_ONLY`. Direct writes to the default branch require:

- a repository binding explicitly configured with `write_policy=DIRECT`;
- the default branch explicitly present in the allowlist;
- a HUMAN actor for the change-set preparation.

Agents can write to allowed feature/fix/docs branches when project authority and plugin capabilities permit it. Changes to `.github/workflows/*` additionally require the declared `WORKFLOW_WRITE` capability.

## Relationship to agent recovery

GitHub SHA conflicts are concurrency/safety failures, not ordinary low-risk transient retries. Even when the phase recovery mode is `AUTO`, GWF must not silently replace a frozen expected SHA with the latest remote SHA. A new reviewed/frozen change set is required.

## GitHub REST API version

The reference adapter sends the versioned REST header and defaults to `2026-03-10`. The version is configurable at adapter construction so a host can advance it deliberately after compatibility testing.
