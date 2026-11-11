# October 27 Experiment Log

## Project
Graph-Guided Repository Navigation for Coding Agents

## Dataset and graph
- Reviewed queries: 20
- Evaluated queries: 20
- Python files indexed: 19
- Import graph edges: 68

## Per-query ranking comparison
- Graph target rank improved: 0
- Baseline target rank improved: 0
- Both methods gave the same target rank: 20
- Baseline top-1 count: 19
- Graph top-1 count: 19
- Queries where top-1 status changed: 0

## Outcome counts
{
  "Both top-1": 19,
  "Same rank; neither top-1": 1
}

## Interpretation
This is an exploratory analysis of the existing reviewed queries.
The dataset is small and queries were selected from repository source
descriptions, so lexical overlap may be inflated.

The results do not establish that graph-guided search is superior.
Per-query rank differences must be inspected alongside the query and
its verified target.

Single-run runtime measurements are not a reliable speed benchmark.

## Limitations
- Small reviewed query set.
- Possible lexical-selection bias.
- Prototype graph and scoring implementation.
- No claim of generalization or superiority is justified.

## Next steps
1. Manually inspect cases where neither method ranks the target first.
2. Create independent queries not copied from source descriptions.
3. Review graph construction and scoring.
4. Repeat experiments with a documented protocol.
