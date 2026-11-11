# Step 12 — Statistical Analysis

## 1. Objective

This analysis compares lexical baseline retrieval with graph-guided retrieval using a paired query-level design.

The primary comparison uses graph boost = 0.10, with no edge dropout, on the same 12 manually reviewed queries.

## 2. Primary MRR comparison

- Baseline mean MRR: 0.4213
- Graph mean MRR: 0.4213
- Mean paired difference (graph - baseline): 0.0000
- Median paired difference: 0.0000
- Wins / ties / losses: 0 / 12 / 0
- Exact paired sign-flip permutation p-value: 1.0000
- Paired bootstrap 95% CI: [0.0000, 0.0000]

## 3. Binary retrieval metrics

| Metric | Baseline | Graph | Difference | Exact McNemar p |
|---|---:|---:|---:|---:|
| Top-1 | 0.2500 | 0.2500 | 0.0000 | 1.0000 |
| Recall@5 | 0.5833 | 0.5833 | 0.0000 | 1.0000 |

## 4. Graph boost sensitivity

| Boost | Top-1 | Recall@5 | MRR |
|---:|---:|---:|---:|
| 0.00 | 0.2500 | 0.5833 | 0.4213 |
| 0.05 | 0.2500 | 0.5833 | 0.4213 |
| 0.10 | 0.2500 | 0.5833 | 0.4213 |
| 0.20 | 0.2500 | 0.5833 | 0.4213 |

## 5. Edge dropout sensitivity

| Dropout | Seeds | Mean seed MRR | SD across seeds |
|---:|---:|---:|---:|
| 0.10 | 5 | 0.4213 | 0.0000 |
| 0.25 | 5 | 0.4213 | 0.0000 |
| 0.50 | 5 | 0.4213 | 0.0000 |

## 6. Interpretation

The primary comparison is paired by query. Positive MRR differences favor graph-guided retrieval; negative differences favor the lexical baseline.

The exact sign-flip permutation test is reported for MRR. Exact McNemar tests are reported for Top-1 and Recall@5.

The bootstrap interval is a descriptive uncertainty estimate for this small query sample and should not be interpreted as proof of performance on other repositories.

Boost and edge-dropout analyses are descriptive sensitivity analyses. They are not treated as independent confirmatory tests.

## 7. Limitations

- Only one repository (psf/requests) was evaluated.
- The paired evaluation contains 12 manually reviewed queries.
- Query-level outcomes are not evidence of broad repository-level generalization.
- Repeated dropout seeds are sensitivity runs, not additional independent queries.
- Statistical results do not establish causal superiority.

## 8. Reproducibility

- Source file: `results/step11-robustness-query-results.csv`
- Query count: 12
- Graph boost for primary comparison: 0.10
- Bootstrap repetitions: 10000
- Random seed: 20261111
