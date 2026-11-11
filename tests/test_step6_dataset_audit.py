import tempfile
import unittest
from pathlib import Path

from src.step6_dataset_audit import audit_rows


class Step6DatasetAuditTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)

        (self.repo / "src" / "requests").mkdir(parents=True)

        for filename in [
            "api.py",
            "sessions.py",
            "auth.py",
            "adapters.py",
            "models.py",
            "exceptions.py",
            "cookies.py",
            "status_codes.py",
            "structures.py",
            "utils.py",
            "hooks.py",
            "__init__.py",
        ]:
            (self.repo / "src" / "requests" / filename).write_text(
                "# test fixture\n",
                encoding="utf-8",
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_rows(self):
        targets = [
            "api.py",
            "sessions.py",
            "auth.py",
            "adapters.py",
            "models.py",
            "exceptions.py",
            "cookies.py",
            "status_codes.py",
            "structures.py",
            "utils.py",
            "hooks.py",
            "__init__.py",
        ]

        return [
            {
                "query_id": f"IND-{i:03d}",
                "query": f"Find the implementation for component {i}",
                "proposed_target": f"src/requests/{target}",
                "review_status": "VERIFIED",
                "reviewer_notes": "Reviewed manually",
            }
            for i, target in enumerate(targets, start=1)
        ]

    def test_all_valid_rows_pass(self):
        result = audit_rows(self.make_rows(), self.repo)

        self.assertEqual(result["row_count"], 12)
        self.assertEqual(result["verified_count"], 12)
        self.assertEqual(result["target_exists_count"], 12)
        self.assertEqual(result["errors"], [])

    def test_missing_target_is_detected(self):
        rows = self.make_rows()
        rows[0]["proposed_target"] = "src/requests/missing.py"

        result = audit_rows(rows, self.repo)

        self.assertTrue(result["errors"])
        self.assertFalse(result["row_results"][0]["target_exists"])

    def test_unverified_label_is_detected(self):
        rows = self.make_rows()
        rows[0]["review_status"] = "NEEDS_REVIEW"

        result = audit_rows(rows, self.repo)

        self.assertTrue(
            any("expected VERIFIED" in error for error in result["errors"])
        )

    def test_duplicate_ids_are_detected(self):
        rows = self.make_rows()
        rows[1]["query_id"] = rows[0]["query_id"]

        result = audit_rows(rows, self.repo)

        self.assertIn(
            "IND-001",
            result["duplicate_query_ids"],
        )

    def test_duplicate_queries_are_detected(self):
        rows = self.make_rows()
        rows[1]["query"] = rows[0]["query"]

        result = audit_rows(rows, self.repo)

        self.assertTrue(result["duplicate_query_texts"])

    def test_unsafe_target_path_is_detected(self):
        rows = self.make_rows()
        rows[0]["proposed_target"] = "../outside.py"

        result = audit_rows(rows, self.repo)

        self.assertTrue(
            any("safe relative path" in error for error in result["errors"])
        )

    def test_blank_query_is_detected(self):
        rows = self.make_rows()
        rows[0]["query"] = ""

        result = audit_rows(rows, self.repo)

        self.assertTrue(
            any("Missing query text" in error for error in result["errors"])
        )

    def test_wrong_row_count_is_detected(self):
        rows = self.make_rows()[:11]

        result = audit_rows(rows, self.repo)

        self.assertTrue(
            any("Expected 12 rows" in error for error in result["errors"])
        )


if __name__ == "__main__":
    unittest.main()
