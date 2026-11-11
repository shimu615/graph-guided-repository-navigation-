# Step 10: Ablation Study and Component Analysis

Generated at (UTC): 2026-11-11T11:41:47.321278+00:00

## 1. Objective

This study examines the contribution of one-hop import-neighbor scoring by comparing fixed graph boost values while keeping the repository, queries, ranking implementation, and Top-K cutoff constant.

## 2. Experimental configurations

| Configuration | Graph boost |
|---|---:|
| Lexical-only | 0.00 |
| Graph-low | 0.05 |
| Graph-original | 0.10 |
| Graph-high | 0.20 |

## 3. Aggregate results

| Configuration | Top-1 | Recall@5 | MRR | Δ MRR vs lexical |
|---|---:|---:|---:|---:|
| Lexical-only | 0.2500 | 0.5833 | 0.421261 | +0.000000 |
| Graph-low | 0.2500 | 0.5833 | 0.420406 | -0.000855 |
| Graph-original | 0.2500 | 0.5833 | 0.420406 | -0.000855 |
| Graph-high | 0.2500 | 0.5833 | 0.420803 | -0.000458 |

## 4. Query-level results

| Query | Boost | Target rank | Reciprocal rank | Top-5 |
|---|---:|---:|---:|---|
| IND-001 | 0.00 | 7 | 0.142857 | False |
| IND-002 | 0.00 | 1 | 1.000000 | True |
| IND-003 | 0.00 | 3 | 0.333333 | True |
| IND-004 | 0.00 | 1 | 1.000000 | True |
| IND-005 | 0.00 | 4 | 0.250000 | True |
| IND-006 | 0.00 | 9 | 0.111111 | False |
| IND-007 | 0.00 | 2 | 0.500000 | True |
| IND-008 | 0.00 | 13 | 0.076923 | False |
| IND-009 | 0.00 | 2 | 0.500000 | True |
| IND-010 | 0.00 | 1 | 1.000000 | True |
| IND-011 | 0.00 | 20 | 0.050000 | False |
| IND-012 | 0.00 | 11 | 0.090909 | False |
| IND-001 | 0.05 | 7 | 0.142857 | False |
| IND-002 | 0.05 | 1 | 1.000000 | True |
| IND-003 | 0.05 | 3 | 0.333333 | True |
| IND-004 | 0.05 | 1 | 1.000000 | True |
| IND-005 | 0.05 | 4 | 0.250000 | True |
| IND-006 | 0.05 | 9 | 0.111111 | False |
| IND-007 | 0.05 | 2 | 0.500000 | True |
| IND-008 | 0.05 | 15 | 0.066667 | False |
| IND-009 | 0.05 | 2 | 0.500000 | True |
| IND-010 | 0.05 | 1 | 1.000000 | True |
| IND-011 | 0.05 | 20 | 0.050000 | False |
| IND-012 | 0.05 | 11 | 0.090909 | False |
| IND-001 | 0.10 | 7 | 0.142857 | False |
| IND-002 | 0.10 | 1 | 1.000000 | True |
| IND-003 | 0.10 | 3 | 0.333333 | True |
| IND-004 | 0.10 | 1 | 1.000000 | True |
| IND-005 | 0.10 | 4 | 0.250000 | True |
| IND-006 | 0.10 | 9 | 0.111111 | False |
| IND-007 | 0.10 | 2 | 0.500000 | True |
| IND-008 | 0.10 | 15 | 0.066667 | False |
| IND-009 | 0.10 | 2 | 0.500000 | True |
| IND-010 | 0.10 | 1 | 1.000000 | True |
| IND-011 | 0.10 | 20 | 0.050000 | False |
| IND-012 | 0.10 | 11 | 0.090909 | False |
| IND-001 | 0.20 | 7 | 0.142857 | False |
| IND-002 | 0.20 | 1 | 1.000000 | True |
| IND-003 | 0.20 | 3 | 0.333333 | True |
| IND-004 | 0.20 | 1 | 1.000000 | True |
| IND-005 | 0.20 | 4 | 0.250000 | True |
| IND-006 | 0.20 | 9 | 0.111111 | False |
| IND-007 | 0.20 | 2 | 0.500000 | True |
| IND-008 | 0.20 | 14 | 0.071429 | False |
| IND-009 | 0.20 | 2 | 0.500000 | True |
| IND-010 | 0.20 | 1 | 1.000000 | True |
| IND-011 | 0.20 | 20 | 0.050000 | False |
| IND-012 | 0.20 | 11 | 0.090909 | False |

## 5. Interpretation

The lexical-only configuration represents the absence of the graph-neighbor contribution. The other configurations add a scaled one-hop neighbor score to the direct lexical score.

A change in target score does not necessarily produce a change in target rank because competing files may also receive high scores. Aggregate metrics and per-query ranks are therefore reported separately.

The boost values are fixed sensitivity settings, not a statistically validated hyperparameter search. The results must not be used to claim that one setting is universally optimal.

## 6. Limitations

- Only one Python repository was evaluated.
- The dataset contains twelve manually reviewed queries.
- The analysis uses fixed graph boost values.
- No statistical significance claim is made.
- The experiment does not establish a universally optimal boost.

## 7. Conclusion

This is an exploratory ablation and sensitivity analysis on one Python repository and twelve manually reviewed queries. It does not establish general superiority or statistical significance.
