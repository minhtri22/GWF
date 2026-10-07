# GWF UI/UX Approved Visual Baseline Manifest

## 1. Identity

```text
BASELINE_ID       = GWF-UI-BASELINE-v1.1
APPROVAL_STATE    = USER_APPROVED
APPROVAL_DATE     = 2026-09-23
REPOSITORY_ASSET  = docs/uiux/approved/GWF_UI_BASELINE_v1_1_APPROVED.jpg
GIT_BLOB_SHA      = ce1db70baf3452b3b295d28b14669e3c7dac9f24
SHA256            = ea26bef13a985df0dc869ef6d04fce8dec2b060ff26bf1888a2799964903af3f
SOURCE_CONTEXT     = user-approved ChatGPT UI/UX visual, repository-compressed reference copy
```

The repository JPG is a compressed visual reference copy of the approved design. It is intentionally accompanied by this textual manifest so small-text compression can never erase normative requirements.

## 2. Approved visual direction

The baseline establishes:

- **Governed Knowledge Studio** visual identity;
- project-centered product navigation rather than implementation-subsystem navigation;
- professional/compact research workspace;
- semantic icon navigation;
- expanded and collapsed sidebar modes;
- complete Light/Dark shell parity;
- project/document workspace capable of hosting Library, Documents and Relations;
- document list + relation graph + contextual Preview/Inspector composition;
- visible exact provenance/governance without turning every screen into a metadata console.

The baseline must not regress to the visual language of the legacy v0.8.5 static dashboard.

## 3. Approved document experience

The approved Documents design uses:

```text
Document list | Relations graph/canvas | Contextual inspector
                                      -> Preview
                                      -> Details
                                      -> Relations
                                      -> History
```

Preview is content-first: users must be able to read useful research content, not only metadata/tags.

## 4. Approved v1.1 textual amendment — Full-screen Reader

After approving the visual composition, the user additionally approved a mandatory full-screen/near-full-screen document reader because research documents and papers are long and information-dense.

Therefore v1.1 additionally requires:

```text
Quick Preview
    ↓ Expand / Full screen
Full-screen Reader
    ↓ Close / Back to graph
same prior project/document/root/selection context
```

The Reader requirement is normative even though the compressed reference image primarily depicts Quick Preview.

## 5. Revision/binding behavior

When the later Documents/Relations slices are authorized:

- `LOGICAL_CURRENT` Preview/Reader resolves and labels the exact current revision at read time;
- `PINNED_REVISION` Preview/Reader stays on the exact pinned revision and visibly distinguishes pinned vs current;
- historical preview never silently floats.

## 6. BPS-I00 boundary

For BPS-I00, this baseline authorizes **visual foundation conformance only**.

The current recovery implements shell/layout/design-system behavior. It does not authorize future Documents/Relations/Reader functionality.

## 7. Future source-code/sandbox direction

Source-code preview, isolated PowerShell/Python execution, function/comment manifests and explainable replay are recorded in `TD-UX-03`.

They are not part of the current visual-shell recovery.

## 8. Precedence

When sources appear to conflict:

1. qualified backend/governance semantics control product truth;
2. `UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` and explicit approved textual amendments control UI behavior;
3. this visual baseline controls composition, hierarchy and visual language;
4. implementation code must conform to the above and never becomes the source of truth merely because it already exists.

A material deviation requires a recorded finding or explicit user-approved baseline amendment.
