# Step 11 — Robustness Analysis

## 1. Objective

This step evaluates the sensitivity of graph-guided file retrieval to graph edge removal, graph boost values, and repeated execution.

## 2. Lexical baseline

- Top-1: 0.2500
- Recall@5: 0.5833
- MRR: 0.4213

## 3. Boost sensitivity

| Boost | Top-1 | Recall@5 | MRR |
|---:|---:|---:|---:|
| 0.00 | 0.2500 | 0.5833 | 0.4213 |
| 0.05 | 0.2500 | 0.5833 | 0.4213 |
| 0.10 | 0.2500 | 0.5833 | 0.4213 |
| 0.20 | 0.2500 | 0.5833 | 0.4213 |

## 4. Edge dropout

| Dropout | Runs | Mean Top-1 | Mean Recall@5 | Mean MRR |
|---:|---:|---:|---:|---:|
| 10% | 5 | 0.2500 | 0.5833 | 0.4213 |
| 25% | 5 | 0.2500 | 0.5833 | 0.4213 |
| 50% | 5 | 0.2500 | 0.5833 | 0.4213 |

## 5. Ranking stability

- Repetitions per query: 5
- Stable queries: 12/12
- Stability rate: 1.0000

## 6. Threats to validity

### Dataset validity

The evaluation contains 12 manually reviewed queries. This small sample may not represent all repository-navigation tasks.

### Repository validity

Only one pinned Python repository, psf/requests, is evaluated. The findings cannot automatically generalize to other repositories or programming languages.

### Construct validity

File retrieval metrics do not measure code generation correctness, patch quality, task completion, or developer productivity.

### Internal validity

Results depend on the lexical scoring method and import graph construction. Synthetic edge dropout is only one model of graph noise.

### Parameter sensitivity

Only the listed boost values and dropout rates were tested. These experiments do not identify a universally optimal parameter.

### Statistical validity

The sample is small. The reported metrics are descriptive and should not be interpreted as statistically significant evidence.

## 7. Interpretation

The results describe this repository and query set only. They do not establish general superiority of graph-guided retrieval. The lexical baseline remains the comparison reference.

## 8. Reproducibility settings

- Boost values: [0.0, 0.05, 0.1, 0.2]
- Dropout rates: [0.1, 0.25, 0.5]
- Seeds: [11, 22, 33, 44, 55]
- Top-K: 5
