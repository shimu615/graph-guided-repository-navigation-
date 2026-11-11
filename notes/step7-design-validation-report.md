# Step 7 — Design Validation Report

**Status:** STEP 7 DESIGN VALIDATION PASSED

- Experiment: STEP7-REPOSITORY-NAVIGATION
- Checks passed: 13
- Checks failed: 0
- Repository commit: 611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60
- Dataset SHA-256: 16eed990ed42c011b1d751366f7982357a4a5dbef641cf68a21a7fb954e198f3
- Dataset rows: 12

## Validation Checks

- [PASS] repository_exists: C:\Users\shamm\OneDrive\Desktop\gemma4-paper-research\external\requests
- [PASS] repository_commit_matches: expected=611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60; actual=611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60
- [PASS] dataset_exists: C:\Users\shamm\OneDrive\Desktop\gemma4-paper-research\results\independent-query-set.csv
- [PASS] dataset_sha256_matches: expected=16eed990ed42c011b1d751366f7982357a4a5dbef641cf68a21a7fb954e198f3; actual=16eed990ed42c011b1d751366f7982357a4a5dbef641cf68a21a7fb954e198f3
- [PASS] dataset_row_count_matches: expected=12; actual=12
- [PASS] query_ids_match: column=query_id; actual_ids=['IND-001', 'IND-002', 'IND-003', 'IND-004', 'IND-005', 'IND-006', 'IND-007', 'IND-008', 'IND-009', 'IND-010', 'IND-011', 'IND-012']
- [PASS] query_ids_unique: unique=12; total=12
- [PASS] graph_boost_is_frozen: configured graph_boost=0.1
- [PASS] top_k_is_five: configured top_k=5
- [PASS] both_methods_share_controls: Repository, dataset, preprocessing and ground truth must match.
- [PASS] evaluation_metrics_defined: configured=['Mean Reciprocal Rank', 'Recall@5', 'Top-1 Accuracy']
- [PASS] previous_step_outputs_exist: All required Step 4-6 outputs found.
- [PASS] design_document_exists: notes\step7-experimental-design.md

## Errors

- None

## Interpretation

This validates the experiment design and its inputs. It does not run a new retrieval experiment or establish that graph-guided retrieval is superior.
