"""Step 5: Query-level error analysis for baseline vs graph retrieval."""

import csv
import json
from datetime import date
from pathlib import Path

from retrieval_core import (
    collect_python_files,
    normalize_texts,
    build_import_graph,
    rank_baseline,
    rank_graph,
)

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "requests"
DATASET = ROOT / "results" / "independent-query-set.csv"
STEP4_CSV = ROOT / "results" / "step4-independent-evaluation.csv"
RESULTS = ROOT / "results"

GRAPH_BOOST = 0.10
TOP_K = 5


def rank_position(ranked, target):
    """Return one-based rank, or None if absent."""
    try:
        return ranked.index(target) + 1
    except ValueError:
        return None


def classify_change(baseline_rank, graph_rank):
    """Classify whether graph retrieval improved the target rank."""
    if baseline_rank is None and graph_rank is None:
        return "MISSING_BOTH"
    if baseline_rank is None:
        return "GRAPH_RECOVERED"
    if graph_rank is None:
        return "GRAPH_LOST"

    if graph_rank < baseline_rank:
        return "IMPROVED"
    if graph_rank > baseline_rank:
        return "REGRESSED"
    return "UNCHANGED"


def reciprocal_rank(rank):
    return 1.0 / rank if rank is not None else 0.0


def calculate_metrics(rows, method):
    """Calculate Top-1, Recall@5, and MRR."""
    count = len(rows)

    if count == 0:
        return {
            "top1_accuracy": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
        }

    ranks = [row[f"{method}_rank"] for row in rows]

    return {
        "top1_accuracy": sum(
            rank == 1 for rank in ranks
        ) / count,
        "recall_at_5": sum(
            rank is not None and rank <= TOP_K
            for rank in ranks
        ) / count,
        "mrr": sum(
            reciprocal_rank(rank) for rank in ranks
        ) / count,
    }


def read_dataset():
    with DATASET.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    if len(rows) != 12:
        raise ValueError(
            f"Expected 12 verified queries, found {len(rows)}"
        )

    required = {
        "query_id",
        "query",
        "proposed_target",
        "review_status",
        "reviewer_notes",
    }

    missing = required - set(rows[0].keys())
    if missing:
        raise ValueError(f"Dataset columns missing: {sorted(missing)}")

    for row in rows:
        status = row["review_status"].strip().upper()

        if status not in {"VERIFIED", "CORRECTED"}:
            raise ValueError(
                f'{row["query_id"]} is not verified: {status}'
            )

        target = row["proposed_target"].strip().replace("\\", "/")
        target_path = (REPO / target).resolve()

        if not target_path.is_relative_to(REPO.resolve()):
            raise ValueError(f"Target escapes repository: {target}")

        if not target_path.is_file():
            raise FileNotFoundError(f"Target does not exist: {target}")

        row["proposed_target"] = target

    return rows


def analyze_queries(rows, texts, graph):
    """Run both methods and collect query-level diagnostic evidence."""
    output = []

    for row in rows:
        query_id = row["query_id"].strip()
        query = row["query"].strip()
        target = row["proposed_target"].strip()

        baseline_ranked, baseline_scores = rank_baseline(query, texts)

        graph_ranked, graph_scores, direct_scores = rank_graph(
            query, texts, graph, boost=GRAPH_BOOST
        )

        baseline_position = rank_position(baseline_ranked, target)
        graph_position = rank_position(graph_ranked, target)

        neighbors = sorted(graph.get(target, set()))

        neighbor_scores = [
            (neighbor, direct_scores.get(neighbor, 0.0))
            for neighbor in neighbors
        ]

        neighbor_scores.sort(key=lambda item: (-item[1], item[0]))

        best_neighbor = (
            neighbor_scores[0][0] if neighbor_scores else ""
        )
        best_neighbor_score = (
            neighbor_scores[0][1] if neighbor_scores else 0.0
        )

        baseline_top5 = baseline_ranked[:TOP_K]
        graph_top5 = graph_ranked[:TOP_K]

        rank_change = (
            baseline_position - graph_position
            if baseline_position is not None
            and graph_position is not None
            else None
        )

        output.append({
            "query_id": query_id,
            "query": query,
            "target": target,
            "review_status": row["review_status"],
            "baseline_rank": baseline_position,
            "graph_rank": graph_position,
            "rank_change_baseline_minus_graph": rank_change,
            "change_category": classify_change(
                baseline_position, graph_position
            ),
            "baseline_top1": baseline_position == 1,
            "graph_top1": graph_position == 1,
            "baseline_top5": (
                baseline_position is not None
                and baseline_position <= TOP_K
            ),
            "graph_top5": (
                graph_position is not None
                and graph_position <= TOP_K
            ),
            "target_direct_score": direct_scores.get(target, 0.0),
            "target_neighbor_score": best_neighbor_score,
            "target_graph_score": graph_scores.get(target, 0.0),
            "target_neighbor_count": len(neighbors),
            "best_scoring_neighbor": best_neighbor,
            "best_neighbor_direct_score": best_neighbor_score,
            "baseline_top5_candidates": " ; ".join(baseline_top5),
            "graph_top5_candidates": " ; ".join(graph_top5),
            "target_in_baseline_top5": target in baseline_top5,
            "target_in_graph_top5": target in graph_top5,
        })

    return output


def build_summary(rows, details, texts, graph):
    baseline = calculate_metrics(details, "baseline")
    graph_metrics = calculate_metrics(details, "graph")

    categories = {}
    for row in details:
        category = row["change_category"]
        categories[category] = categories.get(category, 0) + 1

    improved = [
        row["query_id"] for row in details
        if row["change_category"] == "IMPROVED"
    ]
    regressed = [
        row["query_id"] for row in details
        if row["change_category"] == "REGRESSED"
    ]
    unchanged = [
        row["query_id"] for row in details
        if row["change_category"] == "UNCHANGED"
    ]

    return {
        "date": date.today().isoformat(),
        "repository": "psf/requests",
        "query_count": len(rows),
        "python_files_indexed": len(texts),
        "directed_import_graph_edges": sum(
            len(neighbors) for neighbors in graph.values()
        ),
        "graph_boost": GRAPH_BOOST,
        "top_k": TOP_K,
        "baseline_metrics": baseline,
        "graph_metrics": graph_metrics,
        "metric_differences_graph_minus_baseline": {
            key: graph_metrics[key] - baseline[key]
            for key in baseline
        },
        "query_rank_changes": categories,
        "improved_query_ids": improved,
        "regressed_query_ids": regressed,
        "unchanged_query_ids": unchanged,
        "top1_changes": {
            "baseline_top1_count": sum(
                row["baseline_top1"] for row in details
            ),
            "graph_top1_count": sum(
                row["graph_top1"] for row in details
            ),
        },
        "interpretation": (
            "This is an exploratory error analysis of one repository "
            "and twelve manually reviewed queries. It does not establish "
            "general superiority or statistical significance."
        ),
    }


def write_csv(details):
    path = RESULTS / "step5-query-error-analysis.csv"

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(details[0].keys())
        )
        writer.writeheader()
        writer.writerows(details)

    return path


def write_json(summary):
    path = RESULTS / "step5-error-analysis-summary.json"
    path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8"
    )
    return path


def write_report(summary, details):
    path = RESULTS / "step5-error-analysis-report.md"

    baseline = summary["baseline_metrics"]
    graph = summary["graph_metrics"]
    differences = summary["metric_differences_graph_minus_baseline"]

    lines = [
        "# Step 5: Experimental Analysis and Error Investigation",
        "",
        f'Date: {summary["date"]}',
        "",
        "## 1. Experimental setup",
        "",
        f'- Repository: `{summary["repository"]}`',
        f'- Queries: {summary["query_count"]}',
        f'- Python files indexed: {summary["python_files_indexed"]}',
        f'- Directed graph edges: {summary["directed_import_graph_edges"]}',
        f'- Graph boost: {summary["graph_boost"]}',
        "",
        "## 2. Aggregate comparison",
        "",
        "| Metric | Baseline | Graph | Difference |",
        "|---|---:|---:|---:|",
    ]

    for key, label in [
        ("top1_accuracy", "Top-1 Accuracy"),
        ("recall_at_5", "Recall@5"),
        ("mrr", "MRR"),
    ]:
        lines.append(
            f'| {label} | {baseline[key]:.4f} '
            f'| {graph[key]:.4f} | {differences[key]:+.4f} |'
        )

    lines.extend([
        "",
        "## 3. Query-level ranking changes",
        "",
        "| Query | Baseline rank | Graph rank | Change | Category |",
        "|---|---:|---:|---:|---|",
    ])

    for row in details:
        change = row["rank_change_baseline_minus_graph"]
        change_text = "N/A" if change is None else f"{change:+d}"

        lines.append(
            f'| {row["query_id"]} | {row["baseline_rank"]} '
            f'| {row["graph_rank"]} | {change_text} '
            f'| {row["change_category"]} |'
        )

    lines.extend([
        "",
        "## 4. Error investigation",
        "",
        "### Improved queries",
        "",
    ])

    lines.extend(
        [f"- {item}" for item in summary["improved_query_ids"]]
        or ["- None"]
    )

    lines.extend(["", "### Regressed queries", ""])
    lines.extend(
        [f"- {item}" for item in summary["regressed_query_ids"]]
        or ["- None"]
    )

    lines.extend(["", "### Unchanged queries", ""])
    lines.extend(
        [f"- {item}" for item in summary["unchanged_query_ids"]]
        or ["- None"]
    )

    lines.extend([
        "",
        "## 5. Interpretation and limitations",
        "",
        "The graph method adds a one-hop neighbor score to the direct "
        "lexical score. This can raise files that are connected to "
        "lexically relevant files, even when the target itself has "
        "little direct lexical evidence.",
        "",
        "A ranking change is not automatically an improvement in "
        "retrieval quality. The verified target rank is the evaluation "
        "reference used here.",
        "",
        "This experiment uses one repository and twelve manually "
        "reviewed queries. It is exploratory and does not establish "
        "statistical significance or general superiority.",
        "",
        "No parameter tuning was performed in this analysis.",
        "",
        "## 6. Query-level score diagnostics",
        "",
        "| Query | Direct score | Best neighbor score | Graph score | Neighbor count |",
        "|---|---:|---:|---:|---:|",
    ])

    for row in details:
        lines.append(
            f'| {row["query_id"]} '
            f'| {row["target_direct_score"]:.4f} '
            f'| {row["target_neighbor_score"]:.4f} '
            f'| {row["target_graph_score"]:.4f} '
            f'| {row["target_neighbor_count"]} |'
        )

    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)

    if not REPO.is_dir():
        raise FileNotFoundError(f"Repository not found: {REPO}")

    if not DATASET.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATASET}")

    if not STEP4_CSV.is_file():
        raise FileNotFoundError(
            "Step 4 evaluation CSV not found. Run Step 4 first."
        )

    rows = read_dataset()

    files = collect_python_files(REPO)
    texts = normalize_texts(REPO, files)

    if not texts:
        raise ValueError("No Python files were indexed.")

    graph = build_import_graph(REPO, texts)

    details = analyze_queries(rows, texts, graph)
    summary = build_summary(rows, details, texts, graph)

    csv_path = write_csv(details)
    json_path = write_json(summary)
    report_path = write_report(summary, details)

    print("\n=== STEP 5: ERROR ANALYSIS ===")
    print(json.dumps(summary, indent=2))

    print("\n=== OUTPUT FILES ===")
    print(f"CSV report: {csv_path}")
    print(f"JSON summary: {json_path}")
    print(f"Markdown report: {report_path}")

    print("\n=== QUERY CLASSIFICATION ===")
    for row in details:
        print(
            f'{row["query_id"]}: '
            f'baseline={row["baseline_rank"]}, '
            f'graph={row["graph_rank"]}, '
            f'{row["change_category"]}'
        )


if __name__ == "__main__":
    main()
