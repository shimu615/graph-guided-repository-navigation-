"""Evaluate baseline and graph search using the same labelled test queries."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from baseline_search import search_repository as baseline_search
from graph_search import search_repository as graph_search

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT / "experiments" / "sample_repo"
TEST_FILE = PROJECT_ROOT / "experiments" / "test_cases.json"
RESULTS_DIR = PROJECT_ROOT / "results"


def reciprocal_rank(ranked_files, expected_file):
    """Return 1/rank for the first correct result, or zero if not retrieved."""
    for rank, filename in enumerate(ranked_files, start=1):
        if filename == expected_file:
            return 1.0 / rank
    return 0.0


def evaluate_method(method_name, search_function, test_cases):
    """Evaluate one search method against the same expected file labels."""
    rows = []

    for case in test_cases:
        results = search_function(REPO_ROOT, case["query"])
        ranked_files = [item["file"] for item in results]
        expected = case["expected_file"]

        rank = ranked_files.index(expected) + 1 if expected in ranked_files else None

        rows.append({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "method": method_name,
            "case_id": case["id"],
            "query": case["query"],
            "expected_file": expected,
            "top1_file": ranked_files[0] if ranked_files else "",
            "expected_rank": rank if rank is not None else "",
            "top1_correct": int(bool(ranked_files) and ranked_files[0] == expected),
            "recall_at_5": int(expected in ranked_files[:5]),
            "reciprocal_rank": reciprocal_rank(ranked_files, expected),
            "ranked_files": " > ".join(ranked_files),
            "result_count": len(ranked_files),
        })

    return rows


def summarize(rows):
    """Calculate aggregate metrics for one method."""
    total = len(rows)
    if total == 0:
        return {"queries": 0, "top1_accuracy": 0.0, "recall_at_5": 0.0, "mrr": 0.0}

    return {
        "queries": total,
        "top1_accuracy": sum(row["top1_correct"] for row in rows) / total,
        "recall_at_5": sum(row["recall_at_5"] for row in rows) / total,
        "mrr": sum(row["reciprocal_rank"] for row in rows) / total,
    }


def main():
    if not REPO_ROOT.exists():
        raise SystemExit(f"Sample repository not found: {REPO_ROOT}")
    if not TEST_FILE.exists():
        raise SystemExit(f"Test cases file not found: {TEST_FILE}")

    test_cases = json.loads(TEST_FILE.read_text(encoding="utf-8-sig"))
    if not test_cases:
        raise SystemExit("No test cases found in test_cases.json")

    for case in test_cases:
        if not all(key in case for key in ("id", "query", "expected_file")):
            raise SystemExit(f"Invalid test case: {case}")

    baseline_rows = evaluate_method("baseline", baseline_search, test_cases)
    graph_rows = evaluate_method("graph", graph_search, test_cases)
    all_rows = baseline_rows + graph_rows

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS_DIR / "evaluation-results.csv"
    fieldnames = list(all_rows[0].keys())

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    summary_path = RESULTS_DIR / "evaluation-summary.json"
    summary = {
        "dataset": str(TEST_FILE.relative_to(PROJECT_ROOT)),
        "repository": str(REPO_ROOT.relative_to(PROJECT_ROOT)),
        "warning": (
            "Tiny synthetic demonstration only; not a reliable general benchmark. "
            "Recall@5 is weakly informative when the repository has only a few files."
        ),
        "baseline": summarize(baseline_rows),
        "graph": summarize(graph_rows),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== EVALUATION SUMMARY ===")
    for method in ("baseline", "graph"):
        metrics = summary[method]
        print(f"\n{method.upper()}")
        print(f'Queries:        {metrics["queries"]}')
        print(f'Top-1 accuracy: {metrics["top1_accuracy"]:.3f}')
        print(f'Recall@5:       {metrics["recall_at_5"]:.3f}')
        print(f'MRR:            {metrics["mrr"]:.3f}')

    print("\n=== PER-QUERY RESULTS ===")
    for row in all_rows:
        rank = row["expected_rank"] if row["expected_rank"] != "" else "not found"
        print(
            f'{row["method"]:8} {row["case_id"]}: '
            f'expected={row["expected_file"]}, rank={rank}, '
            f'top1_correct={row["top1_correct"]}'
        )

    print(f"\nSaved CSV: {csv_path}")
    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    main()
