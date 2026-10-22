"""Evaluate baseline and graph search with ranking metrics and runtime."""

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from baseline_search import search_repository as baseline_search
from graph_search import search_repository as graph_search

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT / "experiments" / "sample_repo"
TEST_FILE = PROJECT_ROOT / "experiments" / "test_cases.json"
RESULTS_DIR = PROJECT_ROOT / "results"


def reciprocal_rank(ranked_files, expected_file):
    """Return reciprocal rank, or zero if the target is not retrieved."""
    for rank, filename in enumerate(ranked_files, start=1):
        if filename == expected_file:
            return 1.0 / rank
    return 0.0


def evaluate_method(method_name, search_function, test_cases):
    """Run a method on every query and preserve per-query measurements."""
    rows = []

    for case in test_cases:
        start = time.perf_counter()
        results = search_function(REPO_ROOT, case["query"])
        elapsed_ms = (time.perf_counter() - start) * 1000

        ranked_files = [item["file"] for item in results]
        expected = case["expected_file"]
        rank = (
            ranked_files.index(expected) + 1
            if expected in ranked_files
            else None
        )

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
            "runtime_ms": round(elapsed_ms, 4),
            "ranked_files": " > ".join(ranked_files),
            "result_count": len(ranked_files),
        })

    return rows


def summarize(rows):
    """Aggregate ranking metrics and timing for one method."""
    total = len(rows)
    if not total:
        return {
            "queries": 0,
            "top1_accuracy": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
            "mean_runtime_ms": 0.0,
        }

    return {
        "queries": total,
        "top1_accuracy": sum(int(r["top1_correct"]) for r in rows) / total,
        "recall_at_5": sum(int(r["recall_at_5"]) for r in rows) / total,
        "mrr": sum(float(r["reciprocal_rank"]) for r in rows) / total,
        "mean_runtime_ms": sum(float(r["runtime_ms"]) for r in rows) / total,
    }


def main():
    if not REPO_ROOT.exists():
        raise SystemExit(f"Sample repository not found: {REPO_ROOT}")
    if not TEST_FILE.exists():
        raise SystemExit(f"Test cases file not found: {TEST_FILE}")

    test_cases = json.loads(TEST_FILE.read_text(encoding="utf-8-sig"))
    if not test_cases:
        raise SystemExit("No test cases found.")

    seen_ids = set()
    for case in test_cases:
        if not all(key in case for key in ("id", "query", "expected_file")):
            raise SystemExit(f"Invalid test case: {case}")
        if case["id"] in seen_ids:
            raise SystemExit(f"Duplicate test ID: {case['id']}")
        seen_ids.add(case["id"])
        if not (REPO_ROOT / case["expected_file"]).is_file():
            raise SystemExit(
                f'{case["id"]}: expected file does not exist: '
                f'{case["expected_file"]}'
            )

    baseline_rows = evaluate_method("baseline", baseline_search, test_cases)
    graph_rows = evaluate_method("graph", graph_search, test_cases)
    all_rows = baseline_rows + graph_rows

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS_DIR / "evaluation-results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    summary = {
        "dataset": str(TEST_FILE.relative_to(PROJECT_ROOT)),
        "repository": str(REPO_ROOT.relative_to(PROJECT_ROOT)),
        "warning": (
            "Tiny synthetic demonstration, not a general benchmark. "
            "Recall@5 is weakly informative with only three source files. "
            "Runtime is measured locally and may vary between runs."
        ),
        "baseline": summarize(baseline_rows),
        "graph": summarize(graph_rows),
    }

    summary_path = RESULTS_DIR / "evaluation-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== EVALUATION SUMMARY ===")
    for method in ("baseline", "graph"):
        metrics = summary[method]
        print(f"\n{method.upper()}")
        print(f'Queries:          {metrics["queries"]}')
        print(f'Top-1 accuracy:   {metrics["top1_accuracy"]:.3f}')
        print(f'Recall@5:         {metrics["recall_at_5"]:.3f}')
        print(f'MRR:              {metrics["mrr"]:.3f}')
        print(f'Mean runtime (ms): {metrics["mean_runtime_ms"]:.4f}')

    print("\n=== PER-QUERY RESULTS ===")
    for row in all_rows:
        rank = row["expected_rank"] or "not found"
        status = "CORRECT" if row["top1_correct"] else "TOP-1 ERROR"
        print(
            f'{row["method"]:8} {row["case_id"]}: '
            f'expected={row["expected_file"]}, '
            f'top1={row["top1_file"]}, rank={rank}, '
            f'{status}, runtime={row["runtime_ms"]:.4f} ms'
        )

    print(f"\nSaved CSV: {csv_path}")
    print(f"Saved summary: {summary_path}")


if __name__ == "__main__":
    main()
