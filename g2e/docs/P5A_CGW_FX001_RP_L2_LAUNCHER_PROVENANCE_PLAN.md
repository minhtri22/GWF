# P5A-CGW FX001 RP-L2 — Launcher Provenance Census

Status: ZERO-SCIENCE READ-ONLY DIAGNOSTIC

## Question

Given that the current portable launcher is same-version but different-SHA and unsigned, determine whether the local machine already contains a stronger provenance source for Codex Web GPT v4.0.7:

1. exact local source tree at release commit `b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494`;
2. local copy of the official Windows installer with official release SHA256
   `90f47feaa5c6c17612ac9bee6a49b11b65e0241b046b7380e2c5219792a55354`;
3. registered installed launcher and its file identity;
4. the existing portable launcher identity for comparison.

## Safety

Read-only filesystem, Git metadata, and registry reads only.
No process launch.
No HTTP.
No download.
No install/extract.
No model/browser/MCP.
No scientific attempt.

## Interpretation

Presence of exact release source or installer provenance is diagnostic only. RP-L2 does not itself authorize any launcher execution.
