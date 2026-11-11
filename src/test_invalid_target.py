from pathlib import Path
import csv
import importlib.util
import json
from datetime import datetime

ROOT = Path.cwd()
DATASET = ROOT / "results" / "independent-query-set.csv"
EVALUATOR_PATH = ROOT / "src" / "evaluate_independent_queries.py"
RESULTS = ROOT / "results"

spec = importlib.util.spec_from_file_location("evaluator_test_e", EVALUATOR_PATH)
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)

with DATASET.open("r", encoding="utf-8-sig", newline="") as f:
    original_rows = list(csv.DictReader(f))
    fieldnames = list(original_rows[0].keys()) if original_rows else []

print("Dataset columns:", fieldnames)

target_col = "target" if "target" in fieldnames else (
    "proposed_target" if "proposed_target" in fieldnames else None
)

if not target_col:
    raise SystemExit("FAIL: Could not find target or proposed_target column.")

invalid_rows = [dict(row) for row in original_rows]
invalid_rows[0][target_col] = "THIS_PATH_MUST_NOT_EXIST/invalid_target.py"

temp_path = RESULTS / "_temporary_invalid_target_test.csv"

try:
    with temp_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(invalid_rows)

    old_dataset = getattr(evaluator, "DATASET", None)
    evaluator.DATASET = temp_path

    rejected = False
    error_message = ""

    try:
        evaluator.read_queries()
    except Exception as exc:
        rejected = True
        error_message = f"{type(exc).__name__}: {exc}"
    finally:
        if old_dataset is not None:
            evaluator.DATASET = old_dataset

    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "test": "E - Invalid target rejection",
        "target_column": target_col,
        "invalid_target_rejected": rejected,
        "status": "PASS" if rejected else "FAIL",
        "error": error_message,
        "original_dataset_modified": False
    }

    out = RESULTS / "test_E_invalid_target_summary.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    print("Summary saved to:", out)

finally:
    if temp_path.exists():
        temp_path.unlink()
