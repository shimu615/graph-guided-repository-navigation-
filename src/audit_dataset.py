"""Validate the test-set structure and expected-file labels."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "experiments" / "sample_repo"
TEST_FILE = ROOT / "experiments" / "test_cases.json"


def main():
    cases = json.loads(TEST_FILE.read_text(encoding="utf-8-sig"))
    errors = []
    seen_ids = set()

    if not cases:
        errors.append("The test set is empty.")

    for case in cases:
        case_id = case.get("id", "")
        query = case.get("query", "").strip()
        expected = case.get("expected_file", "").strip()

        if not case_id or not query or not expected:
            errors.append(f"Missing required field: {case}")
            continue

        if case_id in seen_ids:
            errors.append(f"Duplicate case ID: {case_id}")
        seen_ids.add(case_id)

        expected_path = REPO / expected
        if not expected_path.is_file():
            errors.append(
                f"{case_id}: expected file does not exist: {expected}"
            )

        print(f'{case_id}: expected={expected} | query={query}')

    print(f"\nCases checked: {len(cases)}")
    print(f"Unique IDs: {len(seen_ids)}")

    if errors:
        print("\nAUDIT FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("STRUCTURAL AUDIT PASSED")
    print("Note: this checks file existence and structure, not label correctness.")
    print("Manually inspect whether each expected file truly answers its query.")


if __name__ == "__main__":
    main()
