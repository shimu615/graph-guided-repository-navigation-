"""Inspect incorrect top-1 rankings in the evaluation CSV."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_FILE = ROOT / "results" / "evaluation-results.csv"
OUTPUT_FILE = ROOT / "results" / "error-analysis.md"


def main():
    if not RESULTS_FILE.exists():
        raise SystemExit(
            f"Missing results file: {RESULTS_FILE}. Run evaluate.py first."
        )

    with RESULTS_FILE.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    errors = [
        row for row in rows
        if row["top1_correct"].strip() != "1"
    ]

    lines = [
        "# Error Analysis",
        "",
        f"- Evaluation rows: {len(rows)}",
        f"- Top-1 errors: {len(errors)}",
        "",
        "This report describes observed rankings; it does not establish",
        "that either retrieval method is generally better.",
        "",
    ]

    if not errors:
        lines.append("No top-1 errors were recorded in this run.")
    else:
        for row in errors:
            lines.extend([
                f'## {row["method"]} — {row["case_id"]}',
                "",
                f'- Query: `{row["query"]}`',
                f'- Expected file: `{row["expected_file"]}`',
                f'- Top-1 file: `{row["top1_file"]}`',
                f'- Expected rank: `{row["expected_rank"] or "not found"}`',
                f'- Ranked files: `{row["ranked_files"]}`',
                "",
                "### Initial interpretation",
                "",
                "Inspect whether the query contains an exact identifier,",
                "whether that identifier is imported or referenced in other",
                "files, and whether the ranking score distinguishes definition",
                "from usage. Treat this as a hypothesis to investigate.",
                "",
            ])

    OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved report: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
