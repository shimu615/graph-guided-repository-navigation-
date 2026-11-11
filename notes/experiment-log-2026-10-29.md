# October 29, 2026 — Independent Evaluation

## Dataset
- Queries evaluated: 12
- Python files indexed: 37
- Import graph edges: 194

## Results

| Metric | Baseline | Graph-guided |
|---|---:|---:|
| Top-1 accuracy | 0.250 | 0.333 |
| Recall@5 | 0.583 | 0.583 |
| MRR | 0.421 | 0.462 |

## Limitations
Prototype exploratory evaluation. Results depend on the query set, target verification, lexical scoring and graph construction. They do not establish general superiority.

The small dataset does not support broad generalization claims.
The evaluator is a prototype and its graph score requires further
validation. Results must be interpreted alongside individual queries.
