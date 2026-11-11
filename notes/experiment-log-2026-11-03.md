# Experiment Log — November 3, 2026

## Experiment
Query Wording Robustness — Exploratory Test A

## Objective
Examine whether simple changes to query wording affect baseline and
graph-guided repository-file rankings.

## Setup
- Repository: psf/requests
- Original queries: 12
- Variants: original, wording_1, wording_2
- Total evaluations: 36
- Evaluator: src/evaluate_independent_queries.py
- Graph scoring: one-hop import-neighbor score boost of 0.10 times
  the source file's lexical score.

## Results

| Variant | Method | Top-1 Accuracy | MRR |
|---|---|---:|---:|
| Original | Baseline | 0.2500 | 0.4213 |
| Original | Graph-guided | 0.3333 | 0.4621 |
| Wording 1 | Baseline | 0.3333 | 0.4118 |
| Wording 1 | Graph-guided | 0.3333 | 0.4151 |
| Wording 2 | Baseline | 0.2500 | 0.4272 |
| Wording 2 | Graph-guided | 0.3333 | 0.4680 |

## Output Validation
- CSV contains 36 evaluation rows.
- Each of the three variants contains 12 rows.
- No missing baseline or graph ranks were observed.

## Interpretation
Results varied across the tested wording variants. Graph-guided ranking
had higher Top-1 accuracy than baseline for the original and wording_2
variants, while both methods had equal Top-1 accuracy for wording_1.
MRR differences also varied.

## Limitations
- This is an exploratory test using 12 queries from one repository.
- The wording changes prepend generic phrases; they are not independently
  authored semantic paraphrases.
- Added words may change lexical token overlap.
- Results depend on the query set, verified targets, lexical scoring,
  and import graph construction.
- This experiment does not establish general superiority or broad
  robustness.
- The evaluator's scoring implementation is distinct from the separate
  src/graph_search.py implementation.

## Status
Executed; output row counts and rank presence validated.
Further semantic-paraphrase testing and broader evaluation remain future work.
