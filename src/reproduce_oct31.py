import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
NOTES = ROOT / "notes"

EVALUATOR = ROOT / "src" / "evaluate_independent_queries.py"
QUERY_CSV = RESULTS / "independent-query-set.csv"
EVALUATION_CSV = RESULTS / "oct29-independent-evaluation.csv"
SUMMARY_JSON = RESULTS / "oct29-independent-summary.json"

RUNS_DIR = RESULTS / "oct31-reproducibility"
REPORT_JSON = RESULTS / "oct31-reproducibility-summary.json"
REPORT_MD = NOTES / "experiment-log-2026-10-31.md"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_evaluator(run_number):
    print(f"\n=== Evaluation run {run_number} ===")

    completed = subprocess.run(
        [sys.executable, str(EVALUATOR)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    print(completed.stdout)

    if completed.stderr:
        print("STDERR:")
        print(completed.stderr)

    if completed.returncode != 0:
        raise RuntimeError(
            f"Evaluator failed on run {run_number}; "
            "reproducibility comparison cannot be completed."
        )

    for path in (EVALUATION_CSV, SUMMARY_JSON):
        if not path.is_file():
            raise FileNotFoundError(
                f"Expected evaluator output is missing: {path}"
            )

    run_dir = RUNS_DIR / f"run{run_number}"
    run_dir.mkdir(parents=True, exist_ok=True)

    csv_copy = run_dir / "evaluation.csv"
    json_copy = run_dir / "summary.json"

    csv_copy.write_bytes(EVALUATION_CSV.read_bytes())
    json_copy.write_bytes(SUMMARY_JSON.read_bytes())

    return {
        "run": run_number,
        "csv_path": str(csv_copy.relative_to(ROOT)),
        "json_path": str(json_copy.relative_to(ROOT)),
        "csv_sha256": sha256(csv_copy),
        "json_sha256": sha256(json_copy),
    }


def validate_inputs():
    required = [EVALUATOR, QUERY_CSV]

    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"Required input is missing: {path}")

    with QUERY_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = reader.fieldnames or []

    required_columns = {
        "query_id", "proposed_target", "review_status", "reviewer_notes"
    }

    if not required_columns.issubset(set(fields)):
        raise ValueError(
            f"Unexpected query CSV schema. Columns found: {fields}"
        )

    if len(rows) != 12:
        raise ValueError(
            f"Expected 12 independent queries, found {len(rows)}."
        )

    for row in rows:
        qid = row["query_id"].strip()
        status = row["review_status"].strip()
        notes = row["reviewer_notes"].strip()

        if status not in {"VERIFIED", "CORRECTED"} or not notes:
            raise ValueError(
                f"{qid} does not have an accepted review status and notes."
            )

    return {
        "query_count": len(rows),
        "query_csv_sha256": sha256(QUERY_CSV),
    }


def main():
    NOTES.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    input_info = validate_inputs()

    # Record the exact repository revision, when Git metadata is available.
    commit_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    commit = (
        commit_result.stdout.strip()
        if commit_result.returncode == 0
        else "UNAVAILABLE"
    )

    run1 = run_evaluator(1)
    run2 = run_evaluator(2)

    csv_same = run1["csv_sha256"] == run2["csv_sha256"]
    json_same = run1["json_sha256"] == run2["json_sha256"]

    result = {
        "date": "2026-10-31",
        "repository": "psf/requests",
        "repository_commit": commit,
        "query_count": input_info["query_count"],
        "query_csv_sha256": input_info["query_csv_sha256"],
        "run1": run1,
        "run2": run2,
        "evaluation_csv_identical": csv_same,
        "summary_json_identical": json_same,
        "reproducible": csv_same and json_same,
        "interpretation": (
            "Both runs produced byte-identical CSV and JSON outputs."
            if csv_same and json_same
            else
            "The outputs differed. Investigate the differences before "
            "claiming reproducibility."
        ),
        "limitations": [
            "This checks repeatability in the current environment only.",
            "It does not establish generalization to other repositories.",
            "The evaluation dataset is small.",
            "A matching output does not prove the scoring method is valid.",
        ],
    }

    REPORT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# October 31, 2026 — Reproducibility Check",
        "",
        "## Configuration",
        f"- Repository: psf/requests",
        f"- Repository commit: `{commit}`",
        f"- Independent queries: {input_info['query_count']}",
        f"- Query CSV SHA-256: `{input_info['query_csv_sha256']}`",
        "",
        "## Results",
        f"- Evaluation CSV identical across runs: {csv_same}",
        f"- Summary JSON identical across runs: {json_same}",
        f"- Reproducible under this check: {result['reproducible']}",
        "",
        "## Run fingerprints",
        f"- Run 1 CSV SHA-256: `{run1['csv_sha256']}`",
        f"- Run 2 CSV SHA-256: `{run2['csv_sha256']}`",
        f"- Run 1 JSON SHA-256: `{run1['json_sha256']}`",
        f"- Run 2 JSON SHA-256: `{run2['json_sha256']}`",
        "",
        "## Interpretation",
        result["interpretation"],
        "",
        "## Limitations",
        "- This checks repeatability in the current environment only.",
        "- It does not establish generalization to other repositories.",
        "- The query set is small.",
        "- Matching outputs do not prove the scoring method is valid.",
        "",
    ]

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("\n=== OCTOBER 31 REPRODUCIBILITY SUMMARY ===")
    print(json.dumps(result, indent=2))
    print(f"\nSaved: {REPORT_JSON}")
    print(f"Saved: {REPORT_MD}")

    if not result["reproducible"]:
        print(
            "\nWARNING: The two outputs differ. "
            "Do not claim reproducibility until the difference is understood."
        )


if __name__ == "__main__":
    main()
