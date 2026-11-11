"""Step 9: Reproducible query-level error analysis from Step 8 results."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_CSV = ROOT / "results" / "step8-query-results.csv"
OUTPUT_CSV = ROOT / "results" / "step9-query-error-analysis.csv"
OUTPUT_JSON = ROOT / "results" / "step9-error-analysis-summary.json"
OUTPUT_REPORT = ROOT / "notes" / "step9-error-analysis-report.md"

EXPECTED_QUERY_COUNT = 12
TOP_K = 5

OUTPUT_PATHS = [OUTPUT_CSV, OUTPUT_JSON, OUTPUT_REPORT]


def parse_bool(value):
    """Convert CSV boolean text into a Python boolean."""
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def parse_rank(value):
    """Convert a rank to a positive integer or None."""
    normalized = str(value).strip()
    if normalized.lower() in {"", "none", "null"}:
        return None

    rank = int(normalized)
    if rank < 1:
        raise ValueError(f"Rank must be positive: {rank}")
    return rank


def classify_change(baseline_rank, graph_rank):
    """Classify target-rank changes; lower rank is better."""
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
    """Calculate Top-1 accuracy, Recall@5, and MRR."""
    if method not in {"baseline", "graph"}:
        raise ValueError("method must be 'baseline' or 'graph'")

    if not rows:
        return {
            "top1_accuracy": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
        }

    ranks = [row[f"{method}_rank"] for row in rows]
    count = len(ranks)

    return {
        "top1_accuracy": sum(rank == 1 for rank in ranks) / count,
        "recall_at_5": sum(
            rank is not None and rank <= TOP_K for rank in ranks
        ) / count,
        "mrr": sum(reciprocal_rank(rank) for rank in ranks) / count,
    }


def read_step8_results():
    """Load and validate the Step 8 query-level results."""
    if not INPUT_CSV.is_file():
        raise FileNotFoundError(
            f"Step 8 CSV not found: {INPUT_CSV}"
        )

    with INPUT_CSV.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        required = {
            "query_id",
            "query",
            "verified_target",
            "review_status",
            "baseline_rank",
            "graph_rank",
            "baseline_top1",
            "graph_top1",
            "baseline_top5",
            "graph_top5",
            "baseline_mrr",
            "graph_mrr",
            "baseline_target_score",
            "graph_target_score",
            "direct_target_score",
            "baseline_top5_files",
            "graph_top5_files",
        }

        available = set(reader.fieldnames or [])
        missing = required - available
        if missing:
            raise ValueError(
                f"Step 8 CSV missing columns: {sorted(missing)}"
            )

        raw_rows = list(reader)

    if len(raw_rows) != EXPECTED_QUERY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_QUERY_COUNT} rows, found {len(raw_rows)}"
        )

    query_ids = [row["query_id"].strip() for row in raw_rows]
    if len(query_ids) != len(set(query_ids)):
        raise ValueError("Duplicate query IDs found.")

    rows = []

    for raw in raw_rows:
        query_id = raw["query_id"].strip()
        query = raw["query"].strip()
        target = raw["verified_target"].strip().replace("\\", "/")
        status = raw["review_status"].strip().upper()

        if not query_id or not query or not target:
            raise ValueError(
                f"{query_id or 'Unknown query'} has a blank required field."
            )

        if status not in {"VERIFIED", "CORRECTED"}:
            raise ValueError(
                f"{query_id} has unapproved review status: {status}"
            )

        baseline_rank = parse_rank(raw["baseline_rank"])
        graph_rank = parse_rank(raw["graph_rank"])

        baseline_top1 = parse_bool(raw["baseline_top1"])
        graph_top1 = parse_bool(raw["graph_top1"])
        baseline_top5 = parse_bool(raw["baseline_top5"])
        graph_top5 = parse_bool(raw["graph_top5"])

        # Check that the saved flags agree with the saved ranks.
        if baseline_top1 != (baseline_rank == 1):
            raise ValueError(f"{query_id}: baseline_top1 conflicts with rank.")
        if graph_top1 != (graph_rank == 1):
            raise ValueError(f"{query_id}: graph_top1 conflicts with rank.")

        if baseline_top5 != (
            baseline_rank is not None and baseline_rank <= TOP_K
        ):
            raise ValueError(f"{query_id}: baseline_top5 conflicts with rank.")
        if graph_top5 != (
            graph_rank is not None and graph_rank <= TOP_K
        ):
            raise ValueError(f"{query_id}: graph_top5 conflicts with rank.")

        baseline_mrr = float(raw["baseline_mrr"])
        graph_mrr = float(raw["graph_mrr"])

        if abs(baseline_mrr - reciprocal_rank(baseline_rank)) > 1e-9:
            raise ValueError(f"{query_id}: baseline MRR conflicts with rank.")
        if abs(graph_mrr - reciprocal_rank(graph_rank)) > 1e-9:
            raise ValueError(f"{query_id}: graph MRR conflicts with rank.")

        baseline_top5_files = json.loads(raw["baseline_top5_files"])
        graph_top5_files = json.loads(raw["graph_top5_files"])

        if not isinstance(baseline_top5_files, list):
            raise ValueError(f"{query_id}: baseline Top-5 is not a JSON list.")
        if not isinstance(graph_top5_files, list):
            raise ValueError(f"{query_id}: graph Top-5 is not a JSON list.")

        rows.append({
            "query_id": query_id,
            "query": query,
            "target": target,
            "review_status": status,
            "baseline_rank": baseline_rank,
            "graph_rank": graph_rank,
            "baseline_top1": baseline_top1,
            "graph_top1": graph_top1,
            "baseline_top5": baseline_top5,
            "graph_top5": graph_top5,
            "baseline_mrr": baseline_mrr,
            "graph_mrr": graph_mrr,
            "baseline_target_score": float(raw["baseline_target_score"]),
            "graph_target_score": float(raw["graph_target_score"]),
            "direct_target_score": float(raw["direct_target_score"]),
            "baseline_top5_files": baseline_top5_files,
            "graph_top5_files": graph_top5_files,
        })

    return rows


def analyze_queries(rows):
    """Build query-level comparisons using the recorded Step 8 results."""
    details = []

    for row in rows:
        baseline_rank = row["baseline_rank"]
        graph_rank = row["graph_rank"]

        if baseline_rank is None or graph_rank is None:
            rank_change = None
        else:
            rank_change = baseline_rank - graph_rank

        category = classify_change(baseline_rank, graph_rank)

        details.append({
            "query_id": row["query_id"],
            "query": row["query"],
            "verified_target": row["target"],
            "review_status": row["review_status"],
            "baseline_rank": baseline_rank,
            "graph_rank": graph_rank,
            "rank_change_baseline_minus_graph": rank_change,
            "change_category": category,
            "baseline_top1": row["baseline_top1"],
            "graph_top1": row["graph_top1"],
            "baseline_top5": row["baseline_top5"],
            "graph_top5": row["graph_top5"],
            "baseline_mrr": row["baseline_mrr"],
            "graph_mrr": row["graph_mrr"],
            "mrr_difference_graph_minus_baseline": (
                row["graph_mrr"] - row["baseline_mrr"]
            ),
            "baseline_target_score": row["baseline_target_score"],
            "direct_target_score": row["direct_target_score"],
            "graph_target_score": row["graph_target_score"],
            "baseline_top5_files": json.dumps(
                row["baseline_top5_files"]
            ),
            "graph_top5_files": json.dumps(
                row["graph_top5_files"]
            ),
        })

    return details


def build_summary(rows, details):
    """Create aggregate metrics and query-change counts."""
    baseline = calculate_metrics(rows, "baseline")
    graph = calculate_metrics(rows, "graph")

    categories = {
        "IMPROVED": 0,
        "REGRESSED": 0,
        "UNCHANGED": 0,
        "GRAPH_RECOVERED": 0,
        "GRAPH_LOST": 0,
        "MISSING_BOTH": 0,
    }

    for row in details:
        categories[row["change_category"]] += 1

    return {
        "analysis_id": "STEP9-ERROR-ANALYSIS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": "results/step8-query-results.csv",
        "analysis_type": "Post-experiment query-level error analysis",
        "query_count": len(rows),
        "top_k": TOP_K,
        "baseline_metrics": baseline,
        "graph_metrics": graph,
        "metric_differences_graph_minus_baseline": {
            key: graph[key] - baseline[key] for key in baseline
        },
        "query_rank_changes": categories,
        "improved_query_ids": [
            row["query_id"] for row in details
            if row["change_category"] in {"IMPROVED", "GRAPH_RECOVERED"}
        ],
        "regressed_query_ids": [
            row["query_id"] for row in details
            if row["change_category"] in {"REGRESSED", "GRAPH_LOST"}
        ],
        "unchanged_query_ids": [
            row["query_id"] for row in details
            if row["change_category"] == "UNCHANGED"
        ],
        "interpretation": (
            "This analysis uses the recorded Step 8 query-level results. "
            "It does not rerun retrieval or tune parameters. The evaluation "
            "contains one Python repository and twelve manually reviewed "
            "queries, so it is exploratory and does not establish general "
            "superiority or statistical significance."
        ),
        "limitations": [
            "Only one Python repository was evaluated.",
            "The dataset contains twelve manually reviewed queries.",
            "This analysis reuses Step 8 outputs rather than rerunning retrieval.",
            "No statistical significance claim is made.",
            "Recorded scores do not independently prove semantic correctness "
            "of every query-target pair.",
        ],
    }


def write_csv(details):
    fields = list(details[0].keys())

    with OUTPUT_CSV.open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(details)


def write_json(summary):
    OUTPUT_JSON.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )


def write_report(summary, details):
    baseline = summary["baseline_metrics"]
    graph = summary["graph_metrics"]
    differences = summary["metric_differences_graph_minus_baseline"]
    categories = summary["query_rank_changes"]

    lines = [
        "# Step 9: Query-Level Error Analysis",
        "",
        f'Generated at (UTC): {summary["generated_at_utc"]}',
        "",
        "## 1. Purpose",
        "",
        "This analysis investigates query-level ranking changes between "
        "the lexical baseline and graph-guided retrieval using the recorded "
        "Step 8 experiment results.",
        "",
        "No retrieval experiment is rerun and no parameter is tuned.",
        "",
        "## 2. Dataset and evaluation scope",
        "",
        f'- Source: `{summary["source_file"]}`',
        f'- Query count: {summary["query_count"]}',
        f'- Evaluation cutoff: Top-{summary["top_k"]}',
        "",
        "## 3. Aggregate metric comparison",
        "",
        "| Metric | Baseline | Graph-guided | Difference |",
        "|---|---:|---:|---:|",
    ]

    for key, label in [
        ("top1_accuracy", "Top-1 Accuracy"),
        ("recall_at_5", "Recall@5"),
        ("mrr", "Mean Reciprocal Rank"),
    ]:
        lines.append(
            f'| {label} | {baseline[key]:.6f} | {graph[key]:.6f} '
            f'| {differences[key]:+.6f} |'
        )

    lines.extend([
        "",
        "## 4. Query-level ranking changes",
        "",
        "| Query | Baseline rank | Graph rank | Rank change | Classification |",
        "|---|---:|---:|---:|---|",
    ])

    for row in details:
        change = row["rank_change_baseline_minus_graph"]
        change_text = "N/A" if change is None else f"{change:+d}"
        baseline_rank = (
            "Not found" if row["baseline_rank"] is None
            else str(row["baseline_rank"])
        )
        graph_rank = (
            "Not found" if row["graph_rank"] is None
            else str(row["graph_rank"])
        )

        lines.append(
            f'| {row["query_id"]} | {baseline_rank} | {graph_rank} '
            f'| {change_text} | {row["change_category"]} |'
        )

    lines.extend([
        "",
        "## 5. Change classification",
        "",
    ])

    for category, count in categories.items():
        lines.append(f"- {category}: {count}")

    lines.extend([
        "",
        "## 6. Query-level score diagnostics",
        "",
        "| Query | Baseline target score | Direct target score | Graph target score |",
        "|---|---:|---:|---:|",
    ])

    for row in details:
        lines.append(
            f'| {row["query_id"]} '
            f'| {row["baseline_target_score"]:.6f} '
            f'| {row["direct_target_score"]:.6f} '
            f'| {row["graph_target_score"]:.6f} |'
        )

    lines.extend([
        "",
        "## 7. Interpretation",
        "",
        "A higher target score does not necessarily mean a better rank. "
        "Ranking also depends on the scores of competing files. Therefore, "
        "the verified target rank and aggregate retrieval metrics are used "
        "to assess retrieval outcomes.",
        "",
        "The graph-guided method can change target scores without changing "
        "the target's position. Query-level rank changes are therefore "
        "reported separately from score changes.",
        "",
        "## 8. Limitations",
        "",
    ])

    lines.extend(
        f"- {item}" for item in summary["limitations"]
    )

    lines.extend([
        "",
        "## 9. Conclusion",
        "",
        "The results should be interpreted as an exploratory analysis of "
        "this repository and query set. They do not establish that either "
        "method is generally superior.",
        "",
    ])

    OUTPUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main():
    for path in OUTPUT_PATHS:
        if path.exists():
            raise FileExistsError(
                f"Refusing to overwrite existing Step 9 output: {path}"
            )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    rows = read_step8_results()
    details = analyze_queries(rows)
    summary = build_summary(rows, details)

    write_csv(details)
    write_json(summary)
    write_report(summary, details)

    print("\n========== STEP 9 ERROR ANALYSIS ==========")
    print(json.dumps(summary, indent=2))

    print("\n========== CREATED OUTPUTS ==========")
    for path in OUTPUT_PATHS:
        print(f"{path.relative_to(ROOT)}")

    print("\n========== QUERY CLASSIFICATION ==========")
    for row in details:
        print(
            f'{row["query_id"]}: '
            f'baseline={row["baseline_rank"]}, '
            f'graph={row["graph_rank"]}, '
            f'{row["change_category"]}'
        )

    print("\nSTEP 9 ERROR ANALYSIS: SUCCESS")


if __name__ == "__main__":
    main()
