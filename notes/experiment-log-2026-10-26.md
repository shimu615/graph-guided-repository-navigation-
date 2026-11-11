# October 26 Experiment Log

## Project
Graph-Guided Repository Navigation for Coding Agents

## Repository
psf/requests

## Evaluation setup
- Reviewed query count: 20
- Python files indexed: 19
- Import graph edges: 68
- Evaluation type: exploratory prototype evaluation

## Baseline results
- Top-1 accuracy: 0.95
- Recall@5: 1.0
- Mean Reciprocal Rank: 0.975
- Mean query runtime (ms): 16.8531

## Graph-guided results
- Top-1 accuracy: 0.95
- Recall@5: 1.0
- Mean Reciprocal Rank: 0.975
- Mean query runtime (ms): 0.0526

## Interpretation
These results are exploratory and are not sufficient to establish
that graph-guided search is superior to keyword search.

The query set is small, and queries were selected from repository
source descriptions. This can inflate lexical overlap.

Runtime values are single-process prototype measurements and should
not be treated as a reliable speed benchmark.

Import graph edges must be checked before interpreting graph-based
results. If the edge count is zero, graph-guided behavior has not
been meaningfully evaluated.

## Limitations
- Only a small reviewed query set was evaluated.
- The evaluation uses a prototype implementation.
- The query set may contain lexical-selection bias.
- No generalization claim is supported by this experiment.
- More independent queries and repeated runtime trials are needed.

## Next steps
1. Confirm import graph connections are nonzero.
2. Inspect per-query rankings and error cases.
3. Add independent queries not copied from source descriptions.
4. Compare baseline and graph results on the same reviewed targets.
5. Repeat runtime measurements before drawing speed conclusions.
