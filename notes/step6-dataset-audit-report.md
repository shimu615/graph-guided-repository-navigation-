# Step 6 — Dataset Audit Report

Audit date: 2026-11-05T06:46:55.974722+00:00

## 1. Dataset

- Dataset: `C:\Users\shamm\OneDrive\Desktop\gemma4-paper-research\results\independent-query-set.csv`
- Query count: 12
- SHA-256: `16eed990ed42c011b1d751366f7982357a4a5dbef641cf68a21a7fb954e198f3`
- Matches recorded SHA-256: True

## 2. Repository snapshot

- Repository: `psf/requests`
- Actual commit: `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60`
- Expected commit: `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60`
- Snapshot matches: True

## 3. Validation

- Required columns present: True
- Expected query count: True
- All query IDs present: True
- All labels VERIFIED: True
- All target files exist: True
- No duplicate query IDs: True
- No duplicate query texts: True
- No blank required fields: True

## 4. Query-level results

| Query ID | Target | Status | Target exists | Valid |
|---|---|---|---|---|
| IND-001 | `src/requests/api.py` | VERIFIED | True | True |
| IND-002 | `src/requests/sessions.py` | VERIFIED | True | True |
| IND-003 | `src/requests/auth.py` | VERIFIED | True | True |
| IND-004 | `src/requests/adapters.py` | VERIFIED | True | True |
| IND-005 | `src/requests/models.py` | VERIFIED | True | True |
| IND-006 | `src/requests/exceptions.py` | VERIFIED | True | True |
| IND-007 | `src/requests/cookies.py` | VERIFIED | True | True |
| IND-008 | `src/requests/status_codes.py` | VERIFIED | True | True |
| IND-009 | `src/requests/structures.py` | VERIFIED | True | True |
| IND-010 | `src/requests/utils.py` | VERIFIED | True | True |
| IND-011 | `src/requests/hooks.py` | VERIFIED | True | True |
| IND-012 | `src/requests/__init__.py` | VERIFIED | True | True |

## 5. Errors

- No structural validation errors.

## 6. Warnings

- No warnings.

## 7. Manual semantic review limitation

The VERIFIED labels are treated as existing human-review records. This script checks file existence and dataset structure; it does not independently prove that each query semantically matches its proposed target. A human reviewer must inspect query intent and target-file contents before claiming semantic correctness.

## 8. Final status

**Audit passed: True**
