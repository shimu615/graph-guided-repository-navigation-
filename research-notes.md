
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

## Progress Update — 21 October 2026

- Audited the local Git repository and project structure.
- Expanded the synthetic test set from six to twelve queries.
- Added a structural audit for query IDs and expected-file existence.
- Added unit tests for baseline search, graph search, import relationships,
  empty queries, and reciprocal rank.
- Re-ran evaluation using the same queries for both retrieval methods.
- Limitation: the repository remains a small synthetic demonstration.
- Ground-truth labels require manual review; structural validation alone
  does not prove that each label is semantically correct.
- Next step: improve test diversity and evaluate on a more representative
  repository before making comparative performance claims.

## Progress Update — 22 October 2026

- Investigated the Q10 top-1 ranking error.
- Added an error-analysis report based on evaluation CSV results.
- Extended evaluation output with local runtime measurements.
- Added a ground-truth review checklist for all twelve synthetic queries.
- Re-ran unit tests, dataset audit, evaluation, and error analysis.
- Limitation: three synthetic files are insufficient for general conclusions.
- Runtime measurements on this tiny repository are preliminary.
- Next step: manually verify labels and prepare a more representative
  repository and query set for further evaluation.

## Research Definition — Finalized 5 November 2026

### Final Research Question
Does graph-guided repository navigation improve source-file
retrieval effectiveness compared with lexical search in
software repositories?

### Research Objectives
1. Develop a lexical search baseline for repository navigation.
2. Develop a graph-guided source-file retrieval approach using
   import dependencies.
3. Evaluate both approaches using the same verified query set.
4. Compare Top-1 Accuracy, Recall@5, and Mean Reciprocal Rank.
5. Analyze the effect of graph connectivity and query wording.
6. Identify limitations and failure cases.

### Research Hypotheses
- H1: Graph-guided retrieval may improve Top-1 accuracy
  compared with lexical search.
- H2: Graph-guided retrieval may improve Mean Reciprocal Rank.
- H3: Retrieval performance may vary when import-graph
  connections are removed or reduced.

### Scope
The current evaluation uses the psf/requests repository
and a manually reviewed set of 12 queries.

The study evaluates source-file retrieval, not complete
coding-agent task completion.

### Research Limitations
The current evidence comes from one repository and a small
query set. Results should be interpreted as exploratory.
No general superiority claim is established.

### Step 2 Status
- [x] Research question defined
- [x] Research objectives defined
- [x] Research hypotheses defined
- [x] Scope and limitations documented

