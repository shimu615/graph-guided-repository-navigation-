# Step 9: Query-Level Error Analysis

Generated at (UTC): 2026-11-11T11:37:13.459895+00:00

## 1. Purpose

This analysis investigates query-level ranking changes between the lexical baseline and graph-guided retrieval using the recorded Step 8 experiment results.

No retrieval experiment is rerun and no parameter is tuned.

## 2. Dataset and evaluation scope

- Source: `results/step8-query-results.csv`
- Query count: 12
- Evaluation cutoff: Top-5

## 3. Aggregate metric comparison

| Metric | Baseline | Graph-guided | Difference |
|---|---:|---:|---:|
| Top-1 Accuracy | 0.250000 | 0.250000 | +0.000000 |
| Recall@5 | 0.583333 | 0.583333 | +0.000000 |
| Mean Reciprocal Rank | 0.421261 | 0.420406 | -0.000855 |

## 4. Query-level ranking changes

| Query | Baseline rank | Graph rank | Rank change | Classification |
|---|---:|---:|---:|---|
| IND-001 | 7 | 7 | +0 | UNCHANGED |
| IND-002 | 1 | 1 | +0 | UNCHANGED |
| IND-003 | 3 | 3 | +0 | UNCHANGED |
| IND-004 | 1 | 1 | +0 | UNCHANGED |
| IND-005 | 4 | 4 | +0 | UNCHANGED |
| IND-006 | 9 | 9 | +0 | UNCHANGED |
| IND-007 | 2 | 2 | +0 | UNCHANGED |
| IND-008 | 13 | 15 | -2 | REGRESSED |
| IND-009 | 2 | 2 | +0 | UNCHANGED |
| IND-010 | 1 | 1 | +0 | UNCHANGED |
| IND-011 | 20 | 20 | +0 | UNCHANGED |
| IND-012 | 11 | 11 | +0 | UNCHANGED |

## 5. Change classification

- IMPROVED: 0
- REGRESSED: 1
- UNCHANGED: 11
- GRAPH_RECOVERED: 0
- GRAPH_LOST: 0
- MISSING_BOTH: 0

## 6. Query-level score diagnostics

| Query | Baseline target score | Direct target score | Graph target score |
|---|---:|---:|---:|
| IND-001 | 0.642857 | 0.642857 | 0.728571 |
| IND-002 | 0.833333 | 0.833333 | 0.908333 |
| IND-003 | 0.700000 | 0.700000 | 0.790000 |
| IND-004 | 0.785714 | 0.785714 | 0.850000 |
| IND-005 | 0.750000 | 0.750000 | 0.833333 |
| IND-006 | 0.400000 | 0.400000 | 0.460000 |
| IND-007 | 0.727273 | 0.727273 | 0.800000 |
| IND-008 | 0.285714 | 0.285714 | 0.357143 |
| IND-009 | 0.833333 | 0.833333 | 0.916667 |
| IND-010 | 0.818182 | 0.818182 | 0.881818 |
| IND-011 | 0.230769 | 0.230769 | 0.300000 |
| IND-012 | 0.272727 | 0.272727 | 0.336364 |

## 7. Interpretation

A higher target score does not necessarily mean a better rank. Ranking also depends on the scores of competing files. Therefore, the verified target rank and aggregate retrieval metrics are used to assess retrieval outcomes.

The graph-guided method can change target scores without changing the target's position. Query-level rank changes are therefore reported separately from score changes.

## 8. Limitations

- Only one Python repository was evaluated.
- The dataset contains twelve manually reviewed queries.
- This analysis reuses Step 8 outputs rather than rerunning retrieval.
- No statistical significance claim is made.
- Recorded scores do not independently prove semantic correctness of every query-target pair.

## 9. Conclusion

The results should be interpreted as an exploratory analysis of this repository and query set. They do not establish that either method is generally superior.
