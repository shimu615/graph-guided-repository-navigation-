import csv
import json
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
NOTES = ROOT / "notes"

EVALUATION_CSV = RESULTS / "oct29-independent-evaluation.csv"
SUMMARY_JSON = RESULTS / "oct29-independent-summary.json"
OUTPUT_CSV = RESULTS / "oct30-error-analysis.csv"
OUTPUT_JSON = RESULTS / "oct30-error-analysis-summary.json"
OUTPUT_MD = NOTES / "experiment-log-2026-10-30.md"


def normalize(name):
    return "".join(ch.lower() for ch in name if ch.isalnum())


def find_column(fieldnames, candidates):
    lookup = {normalize(name): name for name in fieldnames}
    for candidate in candidates:
        if normalize(candidate) in lookup:
            return lookup[normalize(candidate)]
    return None


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required input file is missing: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames or []

    if not rows:
        raise ValueError(f"No data rows found in {path}")

    return fields, rows


def parse_rank(value, column_name, query_id):
    try:
        number = float(str(value).strip())
    except (ValueError, TypeError):
        raise ValueError(
            f"Cannot parse rank in column '{column_name}' "
            f"for query {query_id}: {value!r}"
        )

    if number < 1 or not number.is_integer():
        raise ValueError(
            f"Expected a positive integer rank for {query_id}; got {value!r}"
        )

    return int(number)


def main():
    NOTES.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    fields, rows = read_csv(EVALUATION_CSV)
    _, summary = read_csv(SUMMARY_JSON) if False else (None, None)

    baseline_rank_col = find_column(
        fields,
        ["baseline_rank", "baseline_target_rank", "baseline_relevant_rank"]
    )
    graph_rank_col = find_column(
        fields,
        ["graph_rank", "graph_guided_rank", "graph_target_rank",
         "graph_relevant_rank"]
    )
    query_id_col = find_column(fields, ["query_id", "id", "qid"])
    query_col = find_column(fields, ["query", "user_query", "question"])
    target_col = find_column(
        fields, ["target", "proposed_target", "expected_target", "target_file"]
    )

    print("Evaluation CSV columns:")
    for field in fields:
        print(f" - {field}")

    if not baseline_rank_col or not graph_rank_col:
        raise ValueError(
            "Could not identify both rank columns. "
            "Review the column names printed above and update the aliases "
            "in analyze_oct30.py. No results were fabricated."
        )

    if not query_id_col:
        raise ValueError("Could not identify the query ID column.")

    analysis_rows = []

    for row in rows:
        query_id = row[query_id_col].strip()
        baseline_rank = parse_rank(
            row[baseline_rank_col], baseline_rank_col, query_id
        )
        graph_rank = parse_rank(
            row[graph_rank_col], graph_rank_col, query_id
        )

        # Positive means the graph-guided method ranked the target higher.
        rank_improvement = baseline_rank - graph_rank

        if rank_improvement > 0:
            outcome = "IMPROVED"
        elif rank_improvement < 0:
            outcome = "REGRESSED"
        else:
            outcome = "UNCHANGED"

        analysis_rows.append({
            "query_id": query_id,
            "query": row.get(query_col, "") if query_col else "",
            "target": row.get(target_col, "") if target_col else "",
            "baseline_rank": baseline_rank,
            "graph_rank": graph_rank,
            "rank_improvement": rank_improvement,
            "outcome": outcome,
            "baseline_reciprocal_rank": round(1 / baseline_rank, 6),
            "graph_reciprocal_rank": round(1 / graph_rank, 6),
        })

    if not analysis_rows:
        raise ValueError("No query rows could be analyzed.")

    counts = {
        "IMPROVED": sum(r["outcome"] == "IMPROVED" for r in analysis_rows),
        "REGRESSED": sum(r["outcome"] == "REGRESSED" for r in analysis_rows),
        "UNCHANGED": sum(r["outcome"] == "UNCHANGED" for r in analysis_rows),
    }

    n = len(analysis_rows)
    summary = {
        "analysis_date": "2026-10-30",
        "source_evaluation": str(EVALUATION_CSV.relative_to(ROOT)),
        "query_count": n,
        "improved_queries": counts["IMPROVED"],
        "regressed_queries": counts["REGRESSED"],
        "unchanged_queries": counts["UNCHANGED"],
        "baseline_top1_from_ranks": sum(
            r["baseline_rank"] == 1 for r in analysis_rows
        ) / n,
        "graph_top1_from_ranks": sum(
            r["graph_rank"] == 1 for r in analysis_rows
        ) / n,
        "baseline_mrr_from_ranks": sum(
            r["baseline_reciprocal_rank"] for r in analysis_rows
        ) / n,
        "graph_mrr_from_ranks": sum(
            r["graph_reciprocal_rank"] for r in analysis_rows
        ) / n,
        "interpretation": (
            "Exploratory analysis on a small query set. "
            "Rank changes describe these queries only and do not establish "
            "general superiority."
        ),
    }

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(analysis_rows[0].keys()))
        writer.writeheader()
        writer.writerows(analysis_rows)

    OUTPUT_JSON.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    lines = [
        "# October 30, 2026 — Query-Level Error Analysis",
        "",
        "## Scope",
        f"- Evaluation rows analyzed: {n}",
        "- Source: `results/oct29-independent-evaluation.csv`",
        "- Analysis compares the target rank from the baseline and graph-guided methods.",
        "",
        "## Outcomes",
        f"- Improved target rank: {counts['IMPROVED']}",
        f"- Regressed target rank: {counts['REGRESSED']}",
        f"- Unchanged target rank: {counts['UNCHANGED']}",
        "",
        "## Rank-derived metrics",
        f"- Baseline Top-1: {summary['baseline_top1_from_ranks']:.3f}",
        f"- Graph-guided Top-1: {summary['graph_top1_from_ranks']:.3f}",
        f"- Baseline MRR: {summary['baseline_mrr_from_ranks']:.3f}",
        f"- Graph-guided MRR: {summary['graph_mrr_from_ranks']:.3f}",
        "",
        "## Query-level details",
        "",
        "| Query | Baseline rank | Graph rank | Rank change | Outcome |",
        "|---|---:|---:|---:|---|",
    ]

    for r in analysis_rows:
        lines.append(
            f"| {r['query_id']} | {r['baseline_rank']} | "
            f"{r['graph_rank']} | {r['rank_improvement']:+d} | "
            f"{r['outcome']} |"
        )

    lines.extend([
        "",
        "## Limitations",
        "- This is a small, exploratory query set.",
        "- Rank improvement is defined as baseline rank minus graph-guided rank.",
        "- A positive value means the target moved closer to rank 1.",
        "- These results do not establish general superiority.",
        "- Inspect individual queries and graph construction before making claims.",
        "",
    ])

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("\n=== OCTOBER 30 ERROR ANALYSIS ===")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved: {OUTPUT_CSV}")
    print(f"Saved: {OUTPUT_JSON}")
    print(f"Saved: {OUTPUT_MD}")


if __name__ == "__main__":
    main()
