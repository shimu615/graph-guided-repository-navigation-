from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = PROJECT_ROOT / "results" / "independent-query-set.csv"
REPOSITORY_PATH = PROJECT_ROOT / "external" / "requests"

EXPECTED_REPOSITORY_COMMIT = (
    "611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60"
)

EXPECTED_DATASET_SHA256 = (
    "16eed990ed42c011b1d751366f7982357a4a5dbef641cf68a21a7fb954e198f3"
)

REQUIRED_COLUMNS = {
    "query_id",
    "query",
    "proposed_target",
    "review_status",
    "reviewer_notes",
}

EXPECTED_QUERY_COUNT = 12
EXPECTED_QUERY_IDS = {
    f"IND-{number:03d}" for number in range(1, 13)
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def get_git_commit(repository_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def load_dataset(dataset_path: Path) -> tuple[list[dict], list[str]]:
    errors = []

    if not dataset_path.exists():
        return [], [f"Dataset file not found: {dataset_path}"]

    try:
        with dataset_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                return [], ["CSV has no header row"]

            missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)

            if missing_columns:
                errors.append(
                    "Missing required columns: "
                    + ", ".join(sorted(missing_columns))
                )

            rows = list(reader)

        return rows, errors

    except (OSError, UnicodeDecodeError, csv.Error) as error:
        return [], [f"Could not read CSV: {error}"]


def audit_rows(
    rows: list[dict],
    repository_path: Path,
) -> dict:
    errors = []
    warnings = []
    row_results = []

    query_ids = []
    normalized_queries = []
    normalized_targets = []

    for index, row in enumerate(rows, start=2):
        query_id = (row.get("query_id") or "").strip()
        query = (row.get("query") or "").strip()
        target = (row.get("proposed_target") or "").strip()
        status = (row.get("review_status") or "").strip().upper()
        reviewer_notes = (row.get("reviewer_notes") or "").strip()

        row_errors = []

        if not query_id:
            row_errors.append("Missing query_id")

        if not query:
            row_errors.append("Missing query text")

        if not target:
            row_errors.append("Missing proposed_target")

        if not status:
            row_errors.append("Missing review_status")
        elif status != "VERIFIED":
            row_errors.append(
                f"Review status is {status}, expected VERIFIED"
            )

        # Only allow repository-relative paths.
        target_path = Path(target.replace("\\", "/"))

        if target_path.is_absolute() or ".." in target_path.parts:
            row_errors.append("Target path is not a safe relative path")
            target_exists = False
        else:
            target_exists = (
                repository_path / target_path
            ).is_file()

            if not target_exists:
                row_errors.append(
                    f"Target file does not exist: {target}"
                )

        query_ids.append(query_id)
        normalized_queries.append(query.casefold())
        normalized_targets.append(target.replace("\\", "/").casefold())

        row_results.append({
            "row_number": index,
            "query_id": query_id,
            "query": query,
            "proposed_target": target,
            "review_status": status,
            "reviewer_notes_present": bool(reviewer_notes),
            "target_exists": target_exists,
            "row_valid": len(row_errors) == 0,
            "errors": row_errors,
        })

        for message in row_errors:
            errors.append(f"Row {index} ({query_id}): {message}")

    # Duplicate checks
    id_counts = Counter(query_ids)
    duplicate_ids = sorted(
        value for value, count in id_counts.items() if count > 1
    )

    query_counts = Counter(normalized_queries)
    duplicate_queries = sorted(
        value for value, count in query_counts.items() if count > 1
    )

    target_counts = Counter(normalized_targets)
    repeated_targets = sorted(
        value for value, count in target_counts.items() if count > 1
    )

    if duplicate_ids:
        errors.append(f"Duplicate query IDs: {duplicate_ids}")

    if duplicate_queries:
        errors.append("Duplicate query texts detected")

    if len(rows) != EXPECTED_QUERY_COUNT:
        errors.append(
            f"Expected {EXPECTED_QUERY_COUNT} rows, found {len(rows)}"
        )

    missing_ids = sorted(EXPECTED_QUERY_IDS - set(query_ids))
    unexpected_ids = sorted(set(query_ids) - EXPECTED_QUERY_IDS)

    if missing_ids:
        errors.append(f"Missing query IDs: {missing_ids}")

    if unexpected_ids:
        errors.append(f"Unexpected query IDs: {unexpected_ids}")

    if repeated_targets:
        warnings.append(
            "Some queries share target files: "
            + ", ".join(repeated_targets)
        )

    verified_count = sum(
        1 for row in rows
        if (row.get("review_status") or "").strip().upper() == "VERIFIED"
    )

    target_exists_count = sum(
        1 for result in row_results if result["target_exists"]
    )

    return {
        "row_count": len(rows),
        "verified_count": verified_count,
        "target_exists_count": target_exists_count,
        "duplicate_query_ids": duplicate_ids,
        "duplicate_query_texts": duplicate_queries,
        "repeated_target_files": repeated_targets,
        "missing_query_ids": missing_ids,
        "unexpected_query_ids": unexpected_ids,
        "row_results": row_results,
        "errors": errors,
        "warnings": warnings,
    }


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_row_csv(path: Path, row_results: list[dict]) -> None:
    fields = [
        "row_number",
        "query_id",
        "query",
        "proposed_target",
        "review_status",
        "reviewer_notes_present",
        "target_exists",
        "row_valid",
        "errors",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for row in row_results:
            output = dict(row)
            output["errors"] = "; ".join(row["errors"])
            writer.writerow(output)


def write_markdown_report(path: Path, audit: dict) -> None:
    dataset = audit["dataset"]
    repository = audit["repository"]
    checks = audit["checks"]

    lines = [
        "# Step 6 — Dataset Audit Report",
        "",
        f"Audit date: {audit['audit_timestamp_utc']}",
        "",
        "## 1. Dataset",
        "",
        f"- Dataset: `{dataset['path']}`",
        f"- Query count: {dataset['row_count']}",
        f"- SHA-256: `{dataset['sha256']}`",
        f"- Matches recorded SHA-256: {dataset['hash_matches_recorded']}",
        "",
        "## 2. Repository snapshot",
        "",
        f"- Repository: `{repository['name']}`",
        f"- Actual commit: `{repository['actual_commit']}`",
        f"- Expected commit: `{repository['expected_commit']}`",
        f"- Snapshot matches: {repository['snapshot_matches']}",
        "",
        "## 3. Validation",
        "",
        f"- Required columns present: {checks['required_columns_present']}",
        f"- Expected query count: {checks['expected_query_count']}",
        f"- All query IDs present: {checks['all_expected_ids_present']}",
        f"- All labels VERIFIED: {checks['all_labels_verified']}",
        f"- All target files exist: {checks['all_target_files_exist']}",
        f"- No duplicate query IDs: {checks['no_duplicate_ids']}",
        f"- No duplicate query texts: {checks['no_duplicate_queries']}",
        f"- No blank required fields: {checks['no_blank_required_fields']}",
        "",
        "## 4. Query-level results",
        "",
        "| Query ID | Target | Status | Target exists | Valid |",
        "|---|---|---|---|---|",
    ]

    for row in audit["row_results"]:
        lines.append(
            f"| {row['query_id']} | `{row['proposed_target']}` "
            f"| {row['review_status']} | {row['target_exists']} "
            f"| {row['row_valid']} |"
        )

    lines.extend([
        "",
        "## 5. Errors",
        "",
    ])

    if audit["errors"]:
        lines.extend(f"- {error}" for error in audit["errors"])
    else:
        lines.append("- No structural validation errors.")

    lines.extend([
        "",
        "## 6. Warnings",
        "",
    ])

    if audit["warnings"]:
        lines.extend(f"- {warning}" for warning in audit["warnings"])
    else:
        lines.append("- No warnings.")

    lines.extend([
        "",
        "## 7. Manual semantic review limitation",
        "",
        "The VERIFIED labels are treated as existing human-review records. "
        "This script checks file existence and dataset structure; it does "
        "not independently prove that each query semantically matches its "
        "proposed target. A human reviewer must inspect query intent and "
        "target-file contents before claiming semantic correctness.",
        "",
        "## 8. Final status",
        "",
        f"**Audit passed: {audit['audit_pass']}**",
        "",
    ])

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    print("\n=== STEP 6: DATASET AUDIT ===")

    rows, load_errors = load_dataset(DATASET_PATH)

    if load_errors:
        for error in load_errors:
            print(f"[ERROR] {error}")
        return 1

    if not REPOSITORY_PATH.is_dir():
        print(f"[ERROR] Repository directory not found: {REPOSITORY_PATH}")
        return 1

    dataset_hash = sha256_file(DATASET_PATH)
    actual_commit = get_git_commit(REPOSITORY_PATH)

    row_audit = audit_rows(rows, REPOSITORY_PATH)

    required_columns_present = True
    all_expected_ids_present = (
        not row_audit["missing_query_ids"]
        and not row_audit["unexpected_query_ids"]
    )
    all_labels_verified = (
        row_audit["verified_count"] == EXPECTED_QUERY_COUNT
    )
    all_target_files_exist = (
        row_audit["target_exists_count"] == EXPECTED_QUERY_COUNT
    )
    no_duplicate_ids = not row_audit["duplicate_query_ids"]
    no_duplicate_queries = not row_audit["duplicate_query_texts"]
    no_blank_required_fields = all(
        row["query_id"] and row["query"] and row["proposed_target"]
        and row["review_status"]
        for row in rows
    )

    snapshot_matches = (
        actual_commit == EXPECTED_REPOSITORY_COMMIT
    )

    hash_matches = dataset_hash == EXPECTED_DATASET_SHA256

    if not snapshot_matches:
        row_audit["errors"].append(
            "Repository commit does not match the recorded snapshot"
        )

    if not hash_matches:
        row_audit["warnings"].append(
            "Dataset SHA-256 differs from the previously recorded hash. "
            "Inspect the dataset changes before using it."
        )

    checks = {
        "required_columns_present": required_columns_present,
        "expected_query_count": row_audit["row_count"] == EXPECTED_QUERY_COUNT,
        "all_expected_ids_present": all_expected_ids_present,
        "all_labels_verified": all_labels_verified,
        "all_target_files_exist": all_target_files_exist,
        "no_duplicate_ids": no_duplicate_ids,
        "no_duplicate_queries": no_duplicate_queries,
        "no_blank_required_fields": no_blank_required_fields,
        "repository_snapshot_matches": snapshot_matches,
    }

    audit_pass = (
        all(checks.values())
        and not row_audit["errors"]
    )

    audit = {
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "project": "Graph-Guided Repository Navigation for Coding Agents",
        "dataset": {
            "path": str(DATASET_PATH),
            "row_count": row_audit["row_count"],
            "sha256": dataset_hash,
            "expected_sha256": EXPECTED_DATASET_SHA256,
            "hash_matches_recorded": hash_matches,
        },
        "repository": {
            "name": "psf/requests",
            "path": str(REPOSITORY_PATH),
            "actual_commit": actual_commit,
            "expected_commit": EXPECTED_REPOSITORY_COMMIT,
            "snapshot_matches": snapshot_matches,
        },
        "checks": checks,
        "verified_count": row_audit["verified_count"],
        "target_exists_count": row_audit["target_exists_count"],
        "duplicate_query_ids": row_audit["duplicate_query_ids"],
        "duplicate_query_texts": row_audit["duplicate_query_texts"],
        "repeated_target_files": row_audit["repeated_target_files"],
        "row_results": row_audit["row_results"],
        "errors": row_audit["errors"],
        "warnings": row_audit["warnings"],
        "manual_semantic_review_required": True,
        "audit_pass": audit_pass,
    }

    results_dir = PROJECT_ROOT / "results"
    notes_dir = PROJECT_ROOT / "notes"

    json_path = results_dir / "step6-dataset-audit.json"
    csv_path = results_dir / "step6-dataset-audit.csv"
    report_path = notes_dir / "step6-dataset-audit-report.md"

    write_json(json_path, audit)
    write_row_csv(csv_path, row_audit["row_results"])
    write_markdown_report(report_path, audit)

    print("\n=== DATASET SUMMARY ===")
    print(f"Rows: {row_audit['row_count']}")
    print(f"Verified labels: {row_audit['verified_count']}")
    print(f"Target files found: {row_audit['target_exists_count']}")
    print(f"Dataset SHA-256 matches record: {hash_matches}")
    print(f"Repository commit: {actual_commit}")
    print(f"Repository snapshot matches: {snapshot_matches}")

    print("\n=== VALIDATION CHECKS ===")
    for name, passed in checks.items():
        print(f"{'[PASS]' if passed else '[FAIL]'} {name}")

    print("\n=== ERRORS ===")
    if audit["errors"]:
        for error in audit["errors"]:
            print(f"[ERROR] {error}")
    else:
        print("No errors.")

    print("\n=== WARNINGS ===")
    if audit["warnings"]:
        for warning in audit["warnings"]:
            print(f"[WARNING] {warning}")
    else:
        print("No warnings.")

    print("\n=== OUTPUT FILES ===")
    print(f"JSON: {json_path}")
    print(f"CSV: {csv_path}")
    print(f"Markdown: {report_path}")

    print("\n=== FINAL RESULT ===")
    print("STEP 6 AUDIT PASSED" if audit_pass else "STEP 6 AUDIT NEEDS REVIEW")

    return 0 if audit_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
