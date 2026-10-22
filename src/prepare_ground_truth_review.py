"""Prepare a human-review CSV for retrieval evaluation labels.

Built with Shimu.
This script checks dataset structure; it does NOT certify labels as correct.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "experiments" / "test_cases.json"
REPO = ROOT / "experiments" / "sample_repo"
OUTPUT = ROOT / "notes" / "ground-truth-review.csv"


def first_value(item, possible_keys):
    """Return the first non-empty value found among candidate field names."""
    for key in possible_keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def main():
    if not DATASET.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET}")
    if not REPO.exists():
        raise FileNotFoundError(f"Repository folder not found: {REPO}")

    with DATASET.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)

    if isinstance(data, dict):
        cases = data.get("test_cases", data.get("cases", data.get("queries")))
        if cases is None:
            raise ValueError(
                "Could not find a list in the JSON. Expected a list or "
                "a dictionary containing test_cases, cases, or queries."
            )
    elif isinstance(data, list):
        cases = data
    else:
        raise ValueError("Unexpected test_cases.json format.")

    if not isinstance(cases, list):
        raise ValueError("The test-case collection must be a list.")

    repo_files = sorted(
        path for path in REPO.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    relative_files = [path.relative_to(REPO).as_posix() for path in repo_files]

    rows = []
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            print(f"WARNING: Case {index} is not a JSON object; skipping.")
            continue

        case_id = first_value(case, ["id", "case_id", "query_id", "qid"]) or f"CASE-{index:03d}"
        query = first_value(case, ["query", "question", "search_query", "description"])
        expected = first_value(
            case,
            ["expected_file", "target_file", "relevant_file", "ground_truth", "answer_file"]
        )

        normalized_expected = expected.replace("\\", "/").strip()
        expected_exists = ""
        if normalized_expected:
            expected_exists = str(
                normalized_expected in relative_files
                or any(path.endswith("/" + normalized_expected) for path in relative_files)
            )

        # Candidate list is supplied for reviewer convenience, not as a ranking.
        candidate_list = "; ".join(relative_files)

        rows.append({
            "case_id": case_id,
            "query": query,
            "expected_file_from_dataset": expected,
            "expected_file_exists": expected_exists,
            "available_python_files": candidate_list,
            "reviewer_verified_label": "",
            "reviewer_notes": "",
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "case_id",
            "query",
            "expected_file_from_dataset",
            "expected_file_exists",
            "available_python_files",
            "reviewer_verified_label",
            "reviewer_notes",
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Cases processed: {len(rows)}")
    print(f"Python files found: {len(relative_files)}")
    print(f"Review CSV written: {OUTPUT.relative_to(ROOT)}")
    print("IMPORTANT: Open the CSV and verify every label against the source code.")
    print("A blank reviewer_verified_label means the label has NOT been verified.")


if __name__ == "__main__":
    main()
