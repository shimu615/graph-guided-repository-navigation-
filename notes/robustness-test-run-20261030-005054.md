# Robustness Test Run — 2026-10-30

- Project root: `C:\Users\shamm\OneDrive\Desktop\gemma4-paper-research`
- Run ID: `20261030-005054`

## Test status

- **Preflight: PASS** — Evaluator, dataset and external repository exist
- **Dataset and index: PASS** — queries=12, indexed_files=37, graph_nodes=20, graph_edges=194
- **A — Existing query wording results: PASS** — rows=36, variant_counts={'original': 12, 'wording_1': 12, 'wording_2': 12}, file=oct30-query-wording-robustness.csv
- **B — Missing graph connections: PASS** — evaluated=12, output=robustness_B_no_graph_edges_20261030-005054.csv, remaining_edges=0
- **C — Missing import edges: PASS** — evaluated=12, original_edges=194, remaining_edges=99, output=robustness_C_half_graph_edges_20261030-005054.csv
- **D — Fair comparison checks: PASS** — same_queries=True, valid_ranks=True, same_query_text_and_targets=True, metrics={'query_count': 12, 'baseline_top1_accuracy': 0.0, 'graph_top1_accuracy': 0.0, 'baseline_mrr': 0.02702702702702703, 'graph_mrr': 0.02702702702702703}
- **E — Invalid target rejection: FAIL** — ValueError: No target column found. Columns: ['query_id', 'query', 'proposed_target', 'review_status', 'reviewer_notes']
- **Targeted pytest: PASS** — exit_code=0

## Interpretation and limitations

- B and C are graph-ablation checks, not evidence of broad generalization.
- D checks whether baseline and graph-guided rankings use the same queries and targets.
- E tests whether the dataset validator rejects an invalid target without changing the original dataset.
- A validates the existing wording-perturbation output; it does not prove semantic paraphrase robustness.
- Review all generated CSV/JSON files and code before using results in a paper.
