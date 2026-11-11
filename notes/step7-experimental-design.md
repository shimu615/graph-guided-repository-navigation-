# Step 7 — Experimental Design

## 1. Research Objective

This experiment investigates whether graph-guided repository navigation
improves source-file retrieval effectiveness compared with lexical search.

The study compares a lexical baseline with a deterministic
graph-augmented retrieval method.

The experiment is exploratory. It is not designed to establish that
graph-guided retrieval is universally superior.

## 2. Research Question

Does graph-guided repository navigation improve source-file retrieval
effectiveness compared with lexical search in software repositories?

## 3. Repository and Dataset

- Repository: psf/requests
- Repository snapshot:
  611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60
- Dataset: results/independent-query-set.csv
- Number of queries: 12
- Query identifiers: IND-001 through IND-012
- Dataset SHA-256:
  16eed990ed42c011b1d751366f7982357a4a5dbef641cf68a21a7fb954e198f3

The repository snapshot and query dataset are fixed for this experiment.

The dataset audit confirmed that the expected rows, identifiers,
labels, target-file paths, and repository snapshot were present.
However, automated structural validation does not independently
establish the semantic correctness of every query-target pair.
Manual semantic review remains necessary.

## 4. Compared Methods

### 4.1 Lexical Baseline

The baseline ranks source files using direct lexical matching
between query tokens and file content.

The baseline provides the reference condition for comparison.

### 4.2 Graph-Augmented Search

The proposed method combines the direct lexical score with a
one-hop import-neighbor score.

The scoring rule is:

GraphScore(file) =
    DirectLexicalScore(file)
    + 0.10 * MaximumDirectScoreAmongOneHopNeighbors(file)

The graph boost is fixed at 0.10 for this evaluation.

The value will not be tuned using the same 12 evaluation queries.
Any future parameter sensitivity study must be reported separately
and must not be presented as independent confirmation.

## 5. Controlled Experimental Conditions

To make the comparison fair, both methods must use:

1. The same repository snapshot.
2. The same source-file collection.
3. The same 12 queries.
4. The same ground-truth target files.
5. The same text preprocessing.
6. The same tokenization and lexical scoring.
7. The same top-K cutoff.
8. The same alphabetical file-path tie-breaking rule.

The methods differ only in whether the one-hop graph-neighbor
boost is applied.

## 6. Evaluation Metrics

### 6.1 Top-1 Accuracy

The proportion of queries for which the correct target file
appears at rank 1.

Top-1 Accuracy = Number of correct rank-1 results / Number of queries

### 6.2 Recall@5

The proportion of queries for which the correct target file
appears within the first five retrieved files.

Recall@5 = Number of queries with target in top 5 / Number of queries

### 6.3 Mean Reciprocal Rank (MRR)

For each query, reciprocal rank is the inverse of the rank of
the first correct target result.

RR = 1 / rank

If the target is not retrieved, RR = 0.

MRR = Sum of reciprocal ranks / Number of queries

All three metrics will be calculated for both methods.

## 7. Per-Query Comparison

Aggregate metrics alone may hide individual regressions.

Therefore, the experiment will also report:

- Query identifier
- Baseline target rank
- Graph target rank
- Rank change
- Whether the graph method improved, regressed, or remained unchanged

A method will not be described as better solely because of
one aggregate metric if other metrics or individual queries
show a different pattern.

## 8. Reproducibility

The experiment records:

- Repository name and exact commit
- Dataset path and SHA-256
- Query count and query identifiers
- Scoring formula and graph boost
- Ranking and tie-breaking policy
- Evaluation metrics
- Generated output files

The repository and dataset must be checked before any
subsequent experiment run.

## 9. Statistical Interpretation

The evaluation contains only 12 queries from one repository.

Consequently:

- Results will be treated as exploratory.
- No broad generalization will be made.
- No claim of statistical significance will be made.
- Individual query-level results will be reported.
- Further evaluation across more repositories and queries
  is needed to support stronger conclusions.

## 10. Existing Pilot Results

The previously verified Step 4 and Step 5 results are:

| Metric | Lexical Baseline | Graph-Augmented |
|---|---:|---:|
| Top-1 Accuracy | 0.250000 | 0.250000 |
| Recall@5 | 0.583333 | 0.583333 |
| MRR | 0.421261 | 0.420406 |

The graph method did not improve these aggregate metrics.

Step 5 query-level analysis found:

- 11 queries unchanged
- 1 query regressed
- 0 queries improved
- IND-008 target rank changed from 13 to 15

These are pilot results from the current implementation.
They are not evidence of general graph-method superiority.

## 11. Threats to Validity

### Internal Validity

The graph boost and ranking implementation may affect the outcome.
Both methods must be run using the same repository and dataset.

### Construct Validity

Lexical retrieval and one-hop import relationships represent
only limited aspects of repository navigation.

### External Validity

One repository and 12 queries cannot represent the diversity
of software repositories or coding-agent tasks.

### Ground-Truth Validity

Automated checks establish dataset structure and file existence,
but manual review is needed to assess whether each target file
is semantically appropriate for its query.

## 12. Design Freeze

The following settings are fixed for the primary comparison:

- Repository commit: 611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60
- Dataset size: 12 queries
- Graph boost: 0.10
- Top-K: 5
- Metrics: Top-1 Accuracy, Recall@5, MRR
- Tie-breaking: alphabetical file path

No evaluation-set parameter tuning is permitted in the primary experiment.

## 13. Step 7 Completion Criteria

- [ ] Experiment configuration created.
- [ ] Experimental design documented.
- [ ] Dataset fingerprint verified.
- [ ] Repository commit verified.
- [ ] Previous evaluation outputs found.
- [ ] Design validation script passes.
- [ ] Design freeze reviewed.

Step 7 is complete only after the validation script succeeds
and the user reviews the design.
