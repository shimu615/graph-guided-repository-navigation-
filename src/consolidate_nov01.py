import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
results = root / "results"

independent = json.loads(
    (results / "oct29-independent-summary.json").read_text(encoding="utf-8")
)

error = json.loads(
    (results / "oct30-error-analysis-summary.json").read_text(encoding="utf-8")
)

repro = json.loads(
    (results / "oct31-reproducibility-summary.json").read_text(encoding="utf-8")
)

output = results / "nov01-consolidated-results.csv"

fields = [
    "experiment_date", "experiment", "query_count",
    "baseline_top1", "graph_top1",
    "baseline_recall_at_5", "graph_recall_at_5",
    "baseline_mrr", "graph_mrr", "notes"
]

rows = [
    {
        "experiment_date": "2026-10-29",
        "experiment": "Independent evaluation",
        "query_count": independent["query_count"],
        "baseline_top1": independent["baseline_top1_accuracy"],
        "graph_top1": independent["graph_top1_accuracy"],
        "baseline_recall_at_5": independent["baseline_recall_at_5"],
        "graph_recall_at_5": independent["graph_recall_at_5"],
        "baseline_mrr": independent["baseline_mrr"],
        "graph_mrr": independent["graph_mrr"],
        "notes": "Exploratory evaluation; small query set."
    },
    {
        "experiment_date": "2026-10-30",
        "experiment": "Error analysis of Oct 29 evaluation",
        "query_count": error["query_count"],
        "baseline_top1": error["baseline_top1_from_ranks"],
        "graph_top1": error["graph_top1_from_ranks"],
        "baseline_recall_at_5": "",
        "graph_recall_at_5": "",
        "baseline_mrr": error["baseline_mrr_from_ranks"],
        "graph_mrr": error["graph_mrr_from_ranks"],
        "notes": (
            f'Improved={error["improved_queries"]}; '
            f'Regressed={error["regressed_queries"]}; '
            f'Unchanged={error["unchanged_queries"]}. '
            "Analysis of Oct 29 data, not a new independent experiment."
        )
    },
    {
        "experiment_date": "2026-10-31",
        "experiment": "Reproducibility check",
        "query_count": repro["query_count"],
        "baseline_top1": "",
        "graph_top1": "",
        "baseline_recall_at_5": "",
        "graph_recall_at_5": "",
        "baseline_mrr": "",
        "graph_mrr": "",
        "notes": (
            f'Reproducible={repro["reproducible"]}; '
            f'CSV identical={repro["evaluation_csv_identical"]}; '
            f'JSON identical={repro["summary_json_identical"]}. '
            "Repeatability check, not a new accuracy experiment."
        )
    }
]

with output.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"Created: {output}")
print(f"Rows: {len(rows)}")
