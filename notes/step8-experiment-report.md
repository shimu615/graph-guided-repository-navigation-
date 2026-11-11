# Step 8 — Reproducible Experiment Report

- Run date (UTC): 2026-11-09T06:43:59.604559+00:00
- Repository: psf/requests
- Repository commit: `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60`
- Query count: 12
- Python files indexed: 37
- Directed import-graph adjacency entries: 304
- Graph boost: 0.1
- Top-K: 5

## Results

| Metric | Lexical baseline | Graph-augmented |
|---|---:|---:|
| Top-1 Accuracy | 0.2500 | 0.2500 |
| Recall@5 | 0.5833 | 0.5833 |
| MRR | 0.4213 | 0.4204 |

## Interpretation and limitations

This is an exploratory evaluation on one Python repository and twelve manually reviewed queries. It does not establish general superiority. No parameter tuning was performed on the evaluation query set.

The graph method uses the existing one-hop import-neighbor ranking implementation with the pre-fixed boost. The lexical baseline and graph method use the same repository snapshot, query set, target labels, and indexed source files.

## Output files

- `results/step8-query-results.csv`
- `results/step8-experiment-summary.json`
- `results/step8-reproducibility-manifest.json`
- `notes/step8-experiment-report.md`
