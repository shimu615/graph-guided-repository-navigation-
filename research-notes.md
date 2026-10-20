
# Research Notes — 19 October 2026

## Project
Graph-Guided Repository Navigation for Coding Agents

## Research Question
Can graph-guided repository navigation help a coding agent locate relevant source files more effectively than standard text-based search?

## Motivation
Large software repositories contain many files, functions, and dependencies. Finding the right source file can be difficult when a question refers to behaviour spread across multiple modules.

## Hypotheses
- H1: Graph-guided retrieval may improve Top-1 or Recall@5 performance.
- H2: Results may vary across repository structures and question types.
- H3: Graph construction may increase runtime or preprocessing costs.

## Research Tasks
- Review related literature.
- Select a small, appropriately licensed repository.
- Create test questions and verify expected files.
- Implement a baseline search method.
- Implement graph-guided retrieval.
- Compare methods using the same test cases.

## Evaluation Metrics
- Top-1 accuracy
- Recall@5
- Runtime
- Failure-case analysis

## Today's Progress
- [ ] Official competition requirements reviewed
- [ ] Research question defined
- [ ] Related papers collected
- [ ] Project folders created
- [ ] Python environment checked

## Open Questions
1. Which repository provides suitable test cases?
2. How will code dependencies be extracted?
3. How can evaluation avoid biased test questions?

## Important
No experimental results have been collected yet. Do not report performance claims until experiments have been completed.

## Progress Update � 19 October 2026

- Created three sample Python files.
- Implemented baseline keyword search.
- Test 1: Query "calculate student grade marks" ranked student.py first with score 4.
- Test 2: Query "generate report student performance" ranked report.py first with score 4.
- Status: Both sample search tests passed.
- Limitation: Only two sample queries have been tested; this is not a research benchmark.
- Next: Review related papers and prepare a documented evaluation dataset.

## Progress Update — 19 October 2026

- Set up the Python virtual environment and project structure.
- Implemented and tested baseline keyword search.
- Implemented a prototype import-dependency graph search.
- Ran both methods on a small sample repository.
- Verified that both methods return ranked source files.
- Literature review notes created.
- Research limitation: Only a small demonstration has been tested.
- Next task: Build a documented evaluation dataset and compare
  both methods using identical test queries.
## Evaluation Update — 20 October 2026

- Created an initial labelled test set containing six queries.
- Implemented a baseline keyword-retrieval method.
- Implemented a prototype import-graph-guided retrieval method.
- Added an evaluation script for Top-1 Accuracy, Recall@5, and MRR.
- Saved per-query results to results/evaluation-results.csv.
- Saved aggregate metrics to results/evaluation-summary.json.
- Limitation: the current evaluation uses a tiny synthetic repository.
- The results do not establish general superiority of either method.
- Next step: expand the repository and test set, verify every expected
  file label, and run more representative experiments.
