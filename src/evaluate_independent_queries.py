import csv
import json
from datetime import date
from pathlib import Path

from retrieval_core import (
    collect_python_files,
    normalize_texts,
    build_import_graph,
    rank_baseline,
    rank_graph
)

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "requests"
DATASET = ROOT / "results" / "independent-query-set.csv"
RESULTS = ROOT / "results"

GRAPH_BOOST = 0.10
TOP_K = 5

def read_queries():
    with DATASET.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    if len(rows) != 12:
        raise ValueError(f"Expected 12 queries; found {len(rows)}")

    ids = [row["query_id"].strip() for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate query IDs found.")

    for row in rows:
        status = row.get("review_status", "").strip().upper()

        if status not in {"VERIFIED", "CORRECTED"}:
            raise ValueError(f'{row["query_id"]} is not reviewed: {status}')

        if not row.get("reviewer_notes", "").strip():
            raise ValueError(f'{row["query_id"]} needs reviewer notes.')

        target = (REPO / row["proposed_target"]).resolve()

        if not target.is_relative_to(REPO.resolve()) or not target.is_file():
            raise ValueError(f'Invalid target for {row["query_id"]}: {target}')

    return rows

def get_rank(ranked_files, target):
    try:
        return ranked_files.index(target) + 1
    except ValueError:
        return None

def reciprocal_rank(rank):
    return 1.0 / rank if rank is not None else 0.0

def main():
    RESULTS.mkdir(parents=True, exist_ok=True)

    rows = read_queries()
    files = collect_python_files(REPO)
    texts = normalize_texts(REPO, files)

    if not texts:
        raise ValueError("No Python files indexed.")

    graph = build_import_graph(REPO, texts)
    output = []

    for row in rows:
        query = row["query"].strip()
        target = row["proposed_target"].strip().replace("\\", "/")

        baseline_ranked, _ = rank_baseline(query, texts)
        graph_ranked, _, _ = rank_graph(
            query, texts, graph, boost=GRAPH_BOOST
        )

        baseline_position = get_rank(baseline_ranked, target)
        graph_position = get_rank(graph_ranked, target)

        output.append({
            "query_id": row["query_id"],
            "query": query,
            "verified_target": target,
            "baseline_rank": baseline_position,
            "graph_rank": graph_position,
            "baseline_top1": baseline_position == 1,
            "graph_top1": graph_position == 1,
            "baseline_top5": (
                baseline_position is not None and baseline_position <= TOP_K
            ),
            "graph_top5": (
                graph_position is not None and graph_position <= TOP_K
            ),
            "baseline_mrr": reciprocal_rank(baseline_position),
            "graph_mrr": reciprocal_rank(graph_position),
            "review_status": row["review_status"]
        })

    count = len(output)

    summary = {
        "date": date.today().isoformat(),
        "repository": "psf/requests",
        "query_count": count,
        "python_files_indexed": len(texts),
        "import_graph_edges_directed": sum(len(v) for v in graph.values()),
        "graph_boost": GRAPH_BOOST,
        "baseline_top1_accuracy": sum(r["baseline_top1"] for r in output) / count,
        "graph_top1_accuracy": sum(r["graph_top1"] for r in output) / count,
        "baseline_recall_at_5": sum(r["baseline_top5"] for r in output) / count,
        "graph_recall_at_5": sum(r["graph_top5"] for r in output) / count,
        "baseline_mrr": sum(r["baseline_mrr"] for r in output) / count,
        "graph_mrr": sum(r["graph_mrr"] for r in output) / count,
        "warning": (
            "Exploratory evaluation on one repository and twelve manually "
            "reviewed queries. Results do not establish general superiority."
        )
    }

    csv_path = RESULTS / "step4-independent-evaluation.csv"
    json_path = RESULTS / "step4-independent-summary.json"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(output[0].keys()))
        writer.writeheader()
        writer.writerows(output)

    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n=== STEP 4 INDEPENDENT EVALUATION ===")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved CSV: {csv_path}")
    print(f"Saved JSON: {json_path}")

if __name__ == "__main__":
    main()
