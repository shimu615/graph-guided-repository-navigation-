import sys
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evaluate_independent_queries import (
    read_queries,
    build_index,
    rank_query,
    reciprocal,
)

rows = read_queries()
texts, imports = build_index()

results = []

for row in rows:
    target = row["proposed_target"].strip().replace("\\", "/")

    baseline, graph, baseline_rank, graph_rank = rank_query(
        row["query"], texts, imports, target
    )

    results.append({
        "query_id": row["query_id"],
        "target": target,
        "baseline_rank": baseline_rank,
        "graph_rank": graph_rank,
        "baseline_top1": baseline_rank == 1,
        "graph_top1": graph_rank == 1,
        "baseline_reciprocal_rank": reciprocal(baseline_rank),
        "graph_reciprocal_rank": reciprocal(graph_rank),
    })

n = len(results)

summary = {
    "date": "2026-10-30",
    "repository": "psf/requests",
    "query_count": n,
    "python_files_indexed": len(texts),
    "import_graph_edges": sum(len(v) for v in imports.values()),
    "baseline_top1_accuracy": sum(r["baseline_top1"] for r in results) / n,
    "graph_top1_accuracy": sum(r["graph_top1"] for r in results) / n,
    "baseline_mrr": sum(r["baseline_reciprocal_rank"] for r in results) / n,
    "graph_mrr": sum(r["graph_reciprocal_rank"] for r in results) / n,
    "improved_queries": sum(r["graph_rank"] < r["baseline_rank"] for r in results),
    "regressed_queries": sum(r["graph_rank"] > r["baseline_rank"] for r in results),
    "unchanged_queries": sum(r["graph_rank"] == r["baseline_rank"] for r in results),
    "status": "DIAGNOSTIC_COMPLETE_REVIEW_REQUIRED",
    "warning": "This reruns the existing evaluator; it does not independently validate the scoring method."
}

csv_path = ROOT / "results" / "oct30-test-d-verified-metrics.csv"
json_path = ROOT / "results" / "oct30-test-d-verified-summary.json"

with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)

json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

print(json.dumps(summary, indent=2))
print("\nPer-query results:")
for r in results:
    print(
        r["query_id"],
        "| baseline:", r["baseline_rank"],
        "| graph:", r["graph_rank"]
    )

print("\nSaved:", csv_path)
print("Saved:", json_path)
