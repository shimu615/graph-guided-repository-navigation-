"""Step 10: Ablation and sensitivity analysis of graph-neighbor scoring."""

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from retrieval_core import (
    collect_python_files,
    normalize_texts,
    build_import_graph,
    rank_baseline,
    rank_graph,
)

REPO = ROOT / "external" / "requests"
DATASET = ROOT / "results" / "independent-query-set.csv"

OUTPUT_CSV = ROOT / "results" / "step10-ablation-query-results.csv"
OUTPUT_JSON = ROOT / "results" / "step10-ablation-summary.json"
OUTPUT_REPORT = ROOT / "notes" / "step10-ablation-report.md"

EXPECTED_QUERY_COUNT = 12
TOP_K = 5
BOOST_VALUES = (0.00, 0.05, 0.10, 0.20)

OUTPUT_PATHS = [OUTPUT_CSV, OUTPUT_JSON, OUTPUT_REPORT]


def reciprocal_rank(rank):
    return 1.0 / rank if rank is not None else 0.0


def rank_position(ranked, target):
    try:
        return ranked.index(target) + 1
    except ValueError:
        return None


def calculate_metrics(ranks):
    """Calculate retrieval metrics from a list of target ranks."""
    if not ranks:
        return {
            "top1_accuracy": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
        }

    count = len(ranks)

    return {
        "top1_accuracy": sum(rank == 1 for rank in ranks) / count,
        "recall_at_5": sum(
            rank is not None and rank <= TOP_K for rank in ranks
        ) / count,
        "mrr": sum(reciprocal_rank(rank) for rank in ranks) / count,
    }


def read_dataset():
    """Read and validate the manually reviewed query dataset."""
    if not DATASET.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATASET}")

    with DATASET.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)
        required = {
            "query_id",
            "query",
            "proposed_target",
            "review_status",
            "reviewer_notes",
        }

        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Dataset columns missing: {sorted(missing)}"
            )

        rows = list(reader)

    if len(rows) != EXPECTED_QUERY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_QUERY_COUNT} queries, found {len(rows)}"
        )

    ids = [row["query_id"].strip() for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate query IDs found.")

    validated = []

    for row in rows:
        query_id = row["query_id"].strip()
        query = row["query"].strip()
        target = row["proposed_target"].strip().replace("\\", "/")
        status = row["review_status"].strip().upper()
        notes = row["reviewer_notes"].strip()

        if not query_id or not query or not target or not notes:
            raise ValueError(f"{query_id}: blank required field.")

        if status not in {"VERIFIED", "CORRECTED"}:
            raise ValueError(
                f"{query_id}: unapproved review status {status}"
            )

        target_path = (REPO / target).resolve()
        if not target_path.is_relative_to(REPO.resolve()):
            raise ValueError(f"{query_id}: target escapes repository.")

        if not target_path.is_file():
            raise FileNotFoundError(
                f"{query_id}: target file not found: {target}"
            )

        validated.append({
            "query_id": query_id,
            "query": query,
            "target": target,
            "review_status": status,
        })

    return validated


def evaluate_configuration(rows, texts, graph, boost):
    """Evaluate one graph boost setting on the same query set."""
    details = []

    for row in rows:
        query = row["query"]
        target = row["target"]

        if boost == 0.0:
            ranked, scores = rank_baseline(query, texts)
            target_scores = scores
        else:
            ranked, graph_scores, direct_scores = rank_graph(
                query, texts, graph, boost=boost
            )
            target_scores = graph_scores

        position = rank_position(ranked, target)
        top5 = ranked[:TOP_K]

        direct_score = None
        graph_score = target_scores.get(target, 0.0)

        if boost == 0.0:
            direct_score = scores.get(target, 0.0)
        else:
            direct_score = direct_scores.get(target, 0.0)

        details.append({
            "query_id": row["query_id"],
            "query": query,
            "verified_target": target,
            "review_status": row["review_status"],
            "graph_boost": boost,
            "target_rank": position,
            "target_reciprocal_rank": reciprocal_rank(position),
            "top1": position == 1,
            "top5": position is not None and position <= TOP_K,
            "direct_target_score": direct_score,
            "final_target_score": graph_score,
            "top5_files": json.dumps(top5),
        })

    return details


def run_ablation(rows, texts, graph):
    """Run all fixed configurations without changing other variables."""
    all_details = []
    summaries = {}

    for boost in BOOST_VALUES:
        details = evaluate_configuration(rows, texts, graph, boost)
        ranks = [row["target_rank"] for row in details]
        metrics = calculate_metrics(ranks)

        key = f"{boost:.2f}"
        summaries[key] = {
            "graph_boost": boost,
            "metrics": metrics,
            "query_count": len(details),
        }

        all_details.extend(details)

    baseline = summaries["0.00"]["metrics"]

    for result in summaries.values():
        result["metric_difference_vs_lexical"] = {
            metric: result["metrics"][metric] - baseline[metric]
            for metric in baseline
        }

    return all_details, summaries


def build_report(summary, details):
    lines = [
        "# Step 10: Ablation Study and Component Analysis",
        "",
        f'Generated at (UTC): {summary["generated_at_utc"]}',
        "",
        "## 1. Objective",
        "",
        "This study examines the contribution of one-hop import-neighbor "
        "scoring by comparing fixed graph boost values while keeping the "
        "repository, queries, ranking implementation, and Top-K cutoff "
        "constant.",
        "",
        "## 2. Experimental configurations",
        "",
        "| Configuration | Graph boost |",
        "|---|---:|",
    ]

    labels = {
        "0.00": "Lexical-only",
        "0.05": "Graph-low",
        "0.10": "Graph-original",
        "0.20": "Graph-high",
    }

    for key, result in summary["configurations"].items():
        lines.append(
            f'| {labels[key]} | {result["graph_boost"]:.2f} |'
        )

    lines.extend([
        "",
        "## 3. Aggregate results",
        "",
        "| Configuration | Top-1 | Recall@5 | MRR | Δ MRR vs lexical |",
        "|---|---:|---:|---:|---:|",
    ])

    for key, result in summary["configurations"].items():
        metrics = result["metrics"]
        delta = result["metric_difference_vs_lexical"]["mrr"]

        lines.append(
            f'| {labels[key]} '
            f'| {metrics["top1_accuracy"]:.4f} '
            f'| {metrics["recall_at_5"]:.4f} '
            f'| {metrics["mrr"]:.6f} '
            f'| {delta:+.6f} |'
        )

    lines.extend([
        "",
        "## 4. Query-level results",
        "",
        "| Query | Boost | Target rank | Reciprocal rank | Top-5 |",
        "|---|---:|---:|---:|---|",
    ])

    for row in details:
        rank = (
            "Not found" if row["target_rank"] is None
            else str(row["target_rank"])
        )
        lines.append(
            f'| {row["query_id"]} | {row["graph_boost"]:.2f} '
            f'| {rank} | {row["target_reciprocal_rank"]:.6f} '
            f'| {row["top5"]} |'
        )

    lines.extend([
        "",
        "## 5. Interpretation",
        "",
        "The lexical-only configuration represents the absence of the "
        "graph-neighbor contribution. The other configurations add a "
        "scaled one-hop neighbor score to the direct lexical score.",
        "",
        "A change in target score does not necessarily produce a change "
        "in target rank because competing files may also receive high "
        "scores. Aggregate metrics and per-query ranks are therefore "
        "reported separately.",
        "",
        "The boost values are fixed sensitivity settings, not a statistically "
        "validated hyperparameter search. The results must not be used to "
        "claim that one setting is universally optimal.",
        "",
        "## 6. Limitations",
        "",
    ])

    lines.extend(f"- {item}" for item in summary["limitations"])

    lines.extend([
        "",
        "## 7. Conclusion",
        "",
        "This is an exploratory ablation and sensitivity analysis on one "
        "Python repository and twelve manually reviewed queries. It does "
        "not establish general superiority or statistical significance.",
        "",
    ])

    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    for path in OUTPUT_PATHS:
        if path.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing Step 10 output: {path}"
            )

    if not REPO.is_dir():
        raise FileNotFoundError(f"Repository not found: {REPO}")

    rows = read_dataset()

    files = collect_python_files(REPO)
    texts = normalize_texts(REPO, files)

    if not texts:
        raise ValueError("No Python files were indexed.")

    graph = build_import_graph(REPO, texts)

    details, configurations = run_ablation(rows, texts, graph)

    summary = {
        "analysis_id": "STEP10-ABLATION-STUDY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": "psf/requests",
        "query_count": len(rows),
        "python_files_indexed": len(texts),
        "directed_import_graph_entries": sum(
            len(neighbors) for neighbors in graph.values()
        ),
        "top_k": TOP_K,
        "configurations": configurations,
        "limitations": [
            "Only one Python repository was evaluated.",
            "The dataset contains twelve manually reviewed queries.",
            "The analysis uses fixed graph boost values.",
            "No statistical significance claim is made.",
            "The experiment does not establish a universally optimal boost.",
        ],
    }

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(details[0].keys()),
        )
        writer.writeheader()
        writer.writerows(details)

    OUTPUT_JSON.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    build_report(summary, details)

    print("\n========== STEP 10 ABLATION SUMMARY ==========")
    print(json.dumps(summary, indent=2))

    print("\n========== OUTPUT FILES ==========")
    for path in OUTPUT_PATHS:
        print(path.relative_to(ROOT))

    print("\nSTEP 10 ABLATION STUDY: SUCCESS")


if __name__ == "__main__":
    main()
