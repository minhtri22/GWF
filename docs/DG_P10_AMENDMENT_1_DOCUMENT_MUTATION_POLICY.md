# DG-P10 Amendment 1 — Project document layout, workflow mutation authority and archive lineage

## Status

**Authorization:** explicitly requested by the user after DG-P10 pre-implementation qualification.  
**Scope:** amend Documentation Integrity §14 and DG-P10 pre-implementation semantics only before implementation.  
**Implementation at amendment time:** NOT_STARTED.

## Why the amendment is required

The initial DG-P10 qualification used a conservative NORMATIVE+ human-approval floor because no authoritative document mutation policy was yet frozen.

The user clarified the intended project-document model:

- documentation lives inside each project under `/docs`;
- governance documents live under `/docs/gov`;
- phase documents live under `/docs/<phase>`;
- each scope has its own `archive/`;
- revision archives the exact old active version and creates a versioned new active document linking to the previous archived version;
- document mutation follows the workflow's existing AUTO/HUMAN_APPROVE configuration;
- AUTO grants the working agent authority over documents generated/owned by its workflow scope;
- frozen governance documents are never mutable merely because AUTO is active and require explicit user authorization.

## Critical compatibility finding

Existing v0.8.2 `AUTO` semantics govern **recovery**, where auto-application is limited to LOW-risk, non-normative recovery within budget.

The amendment therefore reuses the same persisted effective mode value/hierarchy, but **does not redefine recovery AUTO**.

Document-mutation authority is a separate decision matrix.

This prevents a documentation policy change from silently broadening runtime recovery authority.

## Pre-commit identity correction

The initial P10 spec assumed an exact candidate commit/blob could always be frozen before revision commit.

That is impossible when GWF/agent itself generates the next document version because the Git commit/blob does not yet exist.

The amended contract freezes:

- exact base revision/source;
- proposed active path;
- proposed content SHA-256;
- next version;
- expected archive path.

After DG-P11 executes the SHA-safe repository change set, the resulting exact commit/blob is resolved and bound into the new Revision.

## Scope boundary

DG-P10 owns:

- change classification;
- policy-context validation;
- workflow-mode mutation-authority decision;
- deterministic archive/version lineage plan;
- immutable classification Evidence.

DG-P11 owns:

- frozen multi-path repository change set;
- CREATE archive exact old bytes;
- CREATE new versioned active file;
- DELETE old active file;
- SHA-safe execution and post-write exact verification.

DG-P15/P16 retain specialized append-only/supersession and generated-document provenance enforcement.

## Amendment gate

The amendment is acceptable only if QA confirms:

- no broadening of recovery AUTO;
- no bypass of GOV/FROZEN;
- AUTO is limited to owned workflow scope;
- HUMAN_APPROVE remains human-gated;
- archive is immutable;
- pre-commit candidate identity is reproducible;
- P10/P11 ownership remains distinct;
- legacy docs are not silently migrated;
- no new table/migration is required;
- Finding OPEN returns to zero.
