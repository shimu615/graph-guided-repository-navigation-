# Robustness Test Plan — November 2, 2026

## Objective
Evaluate the reliability and limitations of graph-guided repository navigation.

## Test A: Query Wording
Check whether small changes in query wording change the retrieved target ranking.

Status: PLANNED

## Test B: Missing Graph Connections
Investigate behavior when the target file has no relevant import-graph connection.

Status: PLANNED

## Test C: Missing Import Edges
Check whether retrieval remains usable when relevant import relationships are not detected.

Status: PLANNED

## Test D: Fair Comparison
Confirm that baseline and graph-guided methods use the same queries, target files, and ranking metrics.

Status: PARTIALLY REVIEWED

## Test E: Invalid Target
Check whether the evaluator handles a missing or invalid target path safely.

Status: PLANNED

## Limitations
The current independent evaluation uses 12 queries from one repository.
Planned tests are not experimental results.
Do not report a test as passed until it has actually been executed.

## Next Steps
Execute the planned tests, record observed results, and update each status.
