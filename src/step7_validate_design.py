from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "step7-experiment-config.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def read_git_commit(repository_path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def load_csv_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames or []
        rows = list(reader)

    return headers, rows


def find_query_id_column(headers: list[str]) -> str | None:
    aliases = {"query_id", "queryid", "id"}

    for header in headers:
        normalized = header.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in aliases:
            return header

    return None


def main() -> int:
    checks: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        })

        if not passed:
            errors.append(f"{name}: {detail}")

        print(
            f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}"
        )

    if not CONFIG_PATH.exists():
        print(f"[FAIL] Configuration not found: {CONFIG_PATH}")
        return 1

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))

    repository = ROOT / config["repository"]["local_path"]
    dataset = ROOT / config["dataset"]["path"]

    # 1. Repository exists
    record(
        "repository_exists",
        repository.is_dir(),
        str(repository)
    )

    if not repository.is_dir():
        return write_report(checks, errors, warnings, config)

    # 2. Repository commit matches
    try:
        actual_commit = read_git_commit(repository)
        expected_commit = config["repository"]["expected_commit"]

        record(
            "repository_commit_matches",
            actual_commit == expected_commit,
            f"expected={expected_commit}; actual={actual_commit}"
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        actual_commit = None
        record(
            "repository_commit_matches",
            False,
            str(exc)
        )

    # 3. Dataset exists
    record(
        "dataset_exists",
        dataset.is_file(),
        str(dataset)
    )

    if not dataset.is_file():
        return write_report(checks, errors, warnings, config)

    # 4. Dataset fingerprint
    actual_hash = sha256_file(dataset)
    expected_hash = config["dataset"]["expected_sha256"]

    record(
        "dataset_sha256_matches",
        actual_hash == expected_hash,
        f"expected={expected_hash}; actual={actual_hash}"
    )

    # 5. Dataset row count
    headers, rows = load_csv_rows(dataset)
    expected_rows = config["dataset"]["expected_rows"]

    record(
        "dataset_row_count_matches",
        len(rows) == expected_rows,
        f"expected={expected_rows}; actual={len(rows)}"
    )

    # 6. Query IDs
    id_column = find_query_id_column(headers)

    if id_column is None:
        record(
            "query_ids_match",
            False,
            f"No query ID column found. Headers: {headers}"
        )
    else:
        actual_ids = [
            (row.get(id_column) or "").strip()
            for row in rows
        ]

        expected_ids = config["dataset"]["expected_query_ids"]

        record(
            "query_ids_match",
            actual_ids == expected_ids,
            f"column={id_column}; actual_ids={actual_ids}"
        )

        record(
            "query_ids_unique",
            len(actual_ids) == len(set(actual_ids)),
            f"unique={len(set(actual_ids))}; total={len(actual_ids)}"
        )

    # 7. Method and parameter configuration
    graph_boost = config["methods"]["proposed"]["graph_boost"]

    record(
        "graph_boost_is_frozen",
        graph_boost == 0.10,
        f"configured graph_boost={graph_boost}"
    )

    record(
        "top_k_is_five",
        config["ranking"]["top_k"] == 5,
        f"configured top_k={config['ranking']['top_k']}"
    )

    record(
        "both_methods_share_controls",
        all([
            config["ranking"]["same_repository_snapshot"],
            config["ranking"]["same_query_dataset"],
            config["ranking"]["same_preprocessing"],
            config["ranking"]["same_ground_truth"]
        ]),
        "Repository, dataset, preprocessing and ground truth must match."
    )

    # 8. Metric definitions
    expected_metrics = {
        "Top-1 Accuracy",
        "Recall@5",
        "Mean Reciprocal Rank"
    }

    configured_metrics = set(config["metrics"])

    record(
        "evaluation_metrics_defined",
        expected_metrics.issubset(configured_metrics),
        f"configured={sorted(configured_metrics)}"
    )

    # 9. Earlier outputs exist
    required_outputs = [
        ROOT / "results" / "step4-independent-evaluation.csv",
        ROOT / "results" / "step4-independent-summary.json",
        ROOT / "results" / "step5-query-error-analysis.csv",
        ROOT / "results" / "step5-error-analysis-summary.json",
        ROOT / "results" / "step6-dataset-audit.json",
        ROOT / "notes" / "step6-dataset-audit-report.md"
    ]

    missing_outputs = [
        str(path.relative_to(ROOT))
        for path in required_outputs
        if not path.is_file()
    ]

    record(
        "previous_step_outputs_exist",
        len(missing_outputs) == 0,
        "All required Step 4-6 outputs found."
        if not missing_outputs
        else f"Missing: {missing_outputs}"
    )

    # 10. Design document exists
    design_path = ROOT / "notes" / "step7-experimental-design.md"

    record(
        "design_document_exists",
        design_path.is_file(),
        str(design_path.relative_to(ROOT))
    )

    return write_report(
        checks,
        errors,
        warnings,
        config,
        actual_hash=actual_hash,
        actual_commit=actual_commit,
        row_count=len(rows)
    )


def write_report(
    checks: list[dict],
    errors: list[str],
    warnings: list[str],
    config: dict,
    actual_hash: str | None = None,
    actual_commit: str | None = None,
    row_count: int | None = None
) -> int:

    passed = sum(item["status"] == "PASS" for item in checks)
    failed = sum(item["status"] == "FAIL" for item in checks)

    status = "STEP 7 DESIGN VALIDATION PASSED" if failed == 0 else \
        "STEP 7 DESIGN VALIDATION FAILED"

    report = {
        "step": 7,
        "title": "Experimental Design Validation",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "experiment_id": config.get("experiment_id"),
        "repository_commit": actual_commit,
        "dataset_sha256": actual_hash,
        "dataset_rows": row_count,
        "checks_passed": passed,
        "checks_failed": failed,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "interpretation": (
            "This validates the experiment design and its inputs. "
            "It does not run a new retrieval experiment or establish "
            "that graph-guided retrieval is superior."
        )
    }

    output_json = ROOT / "results" / "step7-design-validation.json"
    output_md = ROOT / "notes" / "step7-design-validation-report.md"

    output_json.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    lines = [
        "# Step 7 — Design Validation Report",
        "",
        f"**Status:** {status}",
        "",
        f"- Experiment: {config.get('experiment_id')}",
        f"- Checks passed: {passed}",
        f"- Checks failed: {failed}",
        f"- Repository commit: {actual_commit}",
        f"- Dataset SHA-256: {actual_hash}",
        f"- Dataset rows: {row_count}",
        "",
        "## Validation Checks",
        ""
    ]

    for item in checks:
        lines.append(
            f"- [{item['status']}] {item['check']}: {item['detail']}"
        )

    lines.extend([
        "",
        "## Errors",
        ""
    ])

    if errors:
        lines.extend([f"- {error}" for error in errors])
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Interpretation",
        "",
        report["interpretation"],
        ""
    ])

    output_md.write_text("\n".join(lines), encoding="utf-8")

    print("\n----------------------------------------")
    print(status)
    print(f"Checks passed: {passed}")
    print(f"Checks failed: {failed}")
    print(f"JSON report: {output_json}")
    print(f"Markdown report: {output_md}")
    print("----------------------------------------")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
