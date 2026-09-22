# G2E P5A D2-S4 — Verification Hash Identity Correction

## Status

CLOSED / GOVERNANCE TRANSCRIPTION DEFECT / NO SCIENTIFIC EFFECT

## Frozen scientific value

The D2-S4 top-level scientific report records verification SHA256:

`bf0e848c1eba9e8c0bf8a74da5fcf96dbe29898ec26d1ef91d21aca13a7be01b`

This is a valid 64-hex SHA256 and matches the uploaded verification file byte-for-byte.

## Defective post-closure value

A later governance collector/lock manually transcribed:

`bf0e848c1eba9e8c0bf8a74da5fcf96dbe29898ec26d1ef91d21aca13a7be01`

which is 63 hex characters and is exactly the 64-hex frozen value with the final `b` omitted.

## Adjudication

`VERIFICATION_HASH_EXPECTED_VALUE_TRUNCATED_BY_ONE_HEX_CHAR`

This is not:

- verification-file mutation;
- semantic drift;
- scientific evidence loss;
- a reason to change the D2-S4 verdict.

All future D2-S4 post-closure artifacts must use the full 64-hex value ending in `...be01b`.
