import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from evaluate_independent_queries import (
    read_queries,
    build_index,
    rank_query,
    reciprocal,
)

RESULTS = ROOT / "results"

def make_variants(query):
    return [
        ("original", query),
        ("wording_1", "Which part of the code handles this task: " + query),
        ("wording_2", "I want to locate the implementation. " + query),
    ]

def main():
    rows = read_queries()
    texts, imports = build_index()

    output = []

    for row in rows:
        target = row["proposed_target"].strip().replace("\\", "/")

        for variant_name, variant_query in make_variants(row["query"]):
            baseline, graph, baseline_rank, graph_rank = rank_query(
                variant_query, texts, imports, target
            )

            output.append({
                "query_id": row["query_id"],
                "variant": variant_name,
                "query": variant_query,
                "target": target,
                "baseline_rank": baseline_rank,
                "graph_rank": graph_rank,
                "baseline_top1": baseline_rank == 1,
                "graph_top1": graph_rank == 1,
                "baseline_reciprocal_rank": reciprocal(baseline_rank),
                "graph_reciprocal_rank": reciprocal(graph_rank),
            })

    csv_path = RESULTS / "nov03-query-wording-robustness.csv"
    json_path = RESULTS / "nov03-query-wording-robustness-summary.json"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0].keys()))
        writer.writeheader()
        writer.writerows(output)

    variants = sorted({r["variant"] for r in output})
    summary = {
        "date": "2026-11-03",
        "repository": "psf/requests",
        "original_query_count": len(rows),
        "variants_per_query": len(variants),
        "total_evaluations": len(output),
        "variant_metrics": {},
        "limitations": [
            "Exploratory wording perturbations, not a comprehensive paraphrase benchmark.",
            "All queries target files in one repository.",
            "Results depend on the lexical scoring and import graph implementation.",
            "The added prefixes may change query token overlap; they do not guarantee semantic equivalence."
        ],
    }

    for variant in variants:
        subset = [r for r in output if r["variant"] == variant]
        n = len(subset)
        summary["variant_metrics"][variant] = {
            "query_count": n,
            "baseline_top1_accuracy": sum(r["baseline_top1"] for r in subset) / n,
            "graph_top1_accuracy": sum(r["graph_top1"] for r in subset) / n,
            "baseline_mrr": sum(r["baseline_reciprocal_rank"] for r in subset) / n,
            "graph_mrr": sum(r["graph_reciprocal_rank"] for r in subset) / n,
        }

    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== QUERY WORDING ROBUSTNESS TEST ===")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved CSV: {csv_path}")
    print(f"Saved summary: {json_path}")

if __name__ == "__main__":
    main()
