# Evaluation Protocol

Project: Graph-Guided Repository Navigation for Coding Agents
Prepared: 2026-10-23
Author attribution: Built with Shimu

## 1. Research question

Does adding import-graph context to keyword-based repository search improve
the ranking of the file that a query is intended to locate?

## 2. Methods compared

- Baseline: the current keyword-based search implementation.
- Graph-guided method: the current prototype that adds a score contribution
  from directly connected Python files.

These are prototype implementations. The graph method is not assumed to be
better before evaluation.

## 3. Dataset

The current development dataset is:
- Repository: experiments/sample_repo
- Queries: experiments/test_cases.json
- Current known scale: a small synthetic repository and 12 queries.

This dataset is useful for checking code and the evaluation pipeline. It is
not, by itself, sufficient evidence of performance on real-world repositories.

## 4. Ground-truth verification

Before interpreting metrics, manually inspect every query and its expected
file. Confirm that the expected file actually answers the query by reading
its source code.

Record the review in notes/ground-truth-review.csv:
- reviewer_verified_label: enter the confirmed relative path only after review;
- reviewer_notes: explain ambiguity, corrections, or why the file is relevant.

Do not treat a file-existence check as proof that a label is correct.
If a query is ambiguous or the expected file is uncertain, mark that in notes
and resolve it before using the case for a performance claim.

## 5. Metrics

Report:
- Top-1 accuracy: fraction of queries with the expected file ranked first.
- Recall@5: fraction of queries where the expected file appears in the top five.
- Mean reciprocal rank (MRR): mean reciprocal rank of the expected file.
- Runtime: report measurement units and aggregation method.

If the expected file is not retrieved, its reciprocal rank is zero.
If a query's expected file is missing from the ranked candidates, it is a miss.

## 6. Reproducibility

From the project root, with the project virtual environment activated, run:

    python --version
    python -m unittest discover -s .\tests -v
    python .\src\audit_dataset.py
    python .\src\prepare_ground_truth_review.py
    python .\src\evaluate.py
    python .\src\error_analysis.py

Keep the dataset and code version fixed when comparing methods. Save generated
metrics and the Git commit hash with the experiment notes.

## 7. Runtime cautions

The current dataset is very small. Runtime measurements in milliseconds may
be affected by interpreter startup, filesystem cache, background processes,
and timer noise. Do not claim a speed improvement from a single run.
For a meaningful runtime comparison, run repeated trials, use the same machine
and conditions, and report the measurement procedure.

## 8. Limitations

- Small synthetic repository.
- Small query set.
- Labels require manual verification.
- The graph implementation currently depends on Python import relationships.
- Results may not generalize to other languages, repository sizes, or coding-agent tasks.

## 9. Reporting rule

Report the actual output, including failures and limitations. Do not invent
experiments, verified labels, datasets, citations, or performance gains.
