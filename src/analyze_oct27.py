import csv
import json
import sys
from pathlib import Path
from collections import Counter


PROJECT = Path(__file__).resolve().parent.parent
RESULTS = PROJECT / "results"
NOTES = PROJECT / "notes"

REVIEW_FILE = RESULTS / "real-repository-query-review.csv"
EVALUATION_FILE = RESULTS / "real-repository-evaluation.csv"
SUMMARY_FILE = RESULTS / "real-repository-evaluation-summary.json"


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_rank(value):
    value = str(value or "").strip()

    if not value or value.lower() in {"none", "null"}:
        return None

    return int(value)


def as_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def main():
    review_rows = read_csv(REVIEW_FILE)
    evaluation_rows = read_csv(EVALUATION_FILE)

    with SUMMARY_FILE.open("r", encoding="utf-8-sig") as handle:
        original_summary = json.load(handle)

    if not review_rows:
        raise ValueError("Review dataset is empty.")

    if not evaluation_rows:
        raise ValueError("Evaluation dataset is empty.")

    review_by_id = {
        row["candidate_id"].strip(): row
        for row in review_rows
    }

    evaluation_by_id = {
        row["candidate_id"].strip(): row
        for row in evaluation_rows
    }

    if len(review_by_id) != len(review_rows):
        raise ValueError("Duplicate candidate IDs in review CSV.")

    if len(evaluation_by_id) != len(evaluation_rows):
        raise ValueError("Duplicate candidate IDs in evaluation CSV.")

    if set(review_by_id) != set(evaluation_by_id):
        missing_eval = sorted(set(review_by_id) - set(evaluation_by_id))
        missing_review = sorted(set(evaluation_by_id) - set(review_by_id))

        raise ValueError(
            "Review/evaluation candidate IDs do not match. "
            f"Missing evaluations: {missing_eval}; "
            f"missing reviews: {missing_review}"
        )

    pending = [
        row["candidate_id"]
        for row in review_rows
        if row.get("review_status", "").strip().upper() != "VERIFIED"
    ]

    if pending:
        raise ValueError(f"Unverified review rows found: {pending}")

    audit_rows = []

    baseline_better = 0
    graph_better = 0
    same_rank = 0
    baseline_top1 = 0
    graph_top1 = 0
    top1_changed = 0

    for candidate_id, evaluation in evaluation_by_id.items():
        review = review_by_id[candidate_id]

        if (
            review.get("verified_target", "").strip()
            != evaluation.get("verified_target", "").strip()
        ):
            raise ValueError(
                f"Target mismatch for {candidate_id}: "
                "review CSV and evaluation CSV disagree."
            )

        b_rank = as_rank(evaluation.get("baseline_rank"))
        g_rank = as_rank(evaluation.get("graph_rank"))

        if b_rank is None or g_rank is None:
            raise ValueError(
                f"Missing target rank for candidate {candidate_id}."
            )

        # Positive delta means Graph ranks the target higher.
        # Negative delta means Baseline ranks the target higher.
        delta = b_rank - g_rank

        if delta > 0:
            graph_better += 1
        elif delta < 0:
            baseline_better += 1
        else:
            same_rank += 1

        b_top1 = b_rank == 1
        g_top1 = g_rank == 1

        baseline_top1 += int(b_top1)
        graph_top1 += int(g_top1)
        top1_changed += int(b_top1 != g_top1)

        if b_rank == 1 and g_rank == 1:
            outcome = "Both top-1"
        elif b_rank == 1:
            outcome = "Baseline top-1 only"
        elif g_rank == 1:
            outcome = "Graph top-1 only"
        elif delta > 0:
            outcome = "Graph rank improved"
        elif delta < 0:
            outcome = "Baseline rank improved"
        else:
            outcome = "Same rank; neither top-1"

        audit_rows.append({
            "candidate_id": candidate_id,
            "query": evaluation.get("query", ""),
            "verified_target": evaluation.get("verified_target", ""),
            "baseline_rank": b_rank,
            "graph_rank": g_rank,
            "rank_delta_baseline_minus_graph": delta,
            "baseline_top1": b_top1,
            "graph_top1": g_top1,
            "top1_changed": b_top1 != g_top1,
            "outcome": outcome,
            "baseline_top5": evaluation.get("baseline_top5", ""),
            "graph_top5": evaluation.get("graph_top5", ""),
            "review_status": review.get("review_status", "")
        })

    audit_rows.sort(key=lambda row: row["candidate_id"])

    audit_file = RESULTS / "oct27-query-ranking-audit.csv"

    with audit_file.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(audit_rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(audit_rows)

    outcomes = Counter(row["outcome"] for row in audit_rows)

    count = len(audit_rows)

    comparison = {
        "date": "2026-10-27",
        "project": "Graph-Guided Repository Navigation for Coding Agents",
        "repository": original_summary.get("repository"),
        "evaluation_type": "exploratory per-query analysis",
        "reviewed_query_count": len(review_rows),
        "evaluated_query_count": count,
        "all_review_rows_verified": len(pending) == 0,
        "python_files_indexed": original_summary.get("python_files_indexed"),
        "import_graph_edges": original_summary.get("import_graph_edges"),
        "ranking_comparison": {
            "graph_target_rank_improved": graph_better,
            "baseline_target_rank_improved": baseline_better,
            "same_target_rank": same_rank,
            "baseline_top1_count": baseline_top1,
            "graph_top1_count": graph_top1,
            "top1_status_changed": top1_changed,
            "outcome_counts": dict(outcomes)
        },
        "interpretation_warning": (
            "Exploratory analysis only. The query set is small and was "
            "selected from repository source descriptions. These results "
            "do not establish generalization or superiority."
        ),
        "runtime_warning": (
            "Do not compare single-run runtime values as a reliable "
            "performance benchmark."
        ),
        "next_steps": [
            "Manually inspect cases where neither method ranks the target first.",
            "Create a separate set of independent queries.",
            "Review graph construction and scoring before making superiority claims.",
            "Repeat experiments with a documented protocol."
        ]
    }

    comparison_file = RESULTS / "oct27-comparison-summary.json"

    comparison_file.write_text(
        json.dumps(comparison, indent=2),
        encoding="utf-8"
    )

    NOTES.mkdir(exist_ok=True)

    note = f"""# October 27 Experiment Log

## Project
Graph-Guided Repository Navigation for Coding Agents

## Dataset and graph
- Reviewed queries: {len(review_rows)}
- Evaluated queries: {count}
- Python files indexed: {original_summary.get("python_files_indexed")}
- Import graph edges: {original_summary.get("import_graph_edges")}

## Per-query ranking comparison
- Graph target rank improved: {graph_better}
- Baseline target rank improved: {baseline_better}
- Both methods gave the same target rank: {same_rank}
- Baseline top-1 count: {baseline_top1}
- Graph top-1 count: {graph_top1}
- Queries where top-1 status changed: {top1_changed}

## Outcome counts
{json.dumps(dict(outcomes), indent=2)}

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
"""

    note_file = NOTES / "experiment-log-2026-10-27.md"
    note_file.write_text(note, encoding="utf-8")

    print("\n=== OCTOBER 27 QUERY ANALYSIS ===")
    print(f"Reviewed queries: {len(review_rows)}")
    print(f"Evaluated queries: {count}")
    print(f"Import graph edges: {original_summary.get('import_graph_edges')}")
    print(f"Graph rank improved: {graph_better}")
    print(f"Baseline rank improved: {baseline_better}")
    print(f"Same target rank: {same_rank}")
    print(f"Baseline top-1: {baseline_top1}/{count}")
    print(f"Graph top-1: {graph_top1}/{count}")
    print(f"Top-1 status changed: {top1_changed}")

    print("\nSaved:")
    print(audit_file)
    print(comparison_file)
    print(note_file)

    print(
        "\nWARNING: This analysis does not establish graph-method "
        "superiority or generalization."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
