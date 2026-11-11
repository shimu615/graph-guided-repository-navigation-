import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import step9_error_analysis as step9


class Step9AnalysisTests(unittest.TestCase):

    def test_parse_bool(self):
        self.assertTrue(step9.parse_bool("True"))
        self.assertFalse(step9.parse_bool("false"))

    def test_parse_bool_invalid(self):
        with self.assertRaises(ValueError):
            step9.parse_bool("yes")

    def test_parse_rank(self):
        self.assertEqual(step9.parse_rank("1"), 1)
        self.assertEqual(step9.parse_rank("12"), 12)
        self.assertIsNone(step9.parse_rank(""))
        self.assertIsNone(step9.parse_rank("None"))

    def test_parse_rank_invalid(self):
        with self.assertRaises(ValueError):
            step9.parse_rank("0")

    def test_classify_improved(self):
        self.assertEqual(
            step9.classify_change(5, 2), "IMPROVED"
        )

    def test_classify_regressed(self):
        self.assertEqual(
            step9.classify_change(2, 5), "REGRESSED"
        )

    def test_classify_unchanged(self):
        self.assertEqual(
            step9.classify_change(3, 3), "UNCHANGED"
        )

    def test_classify_missing(self):
        self.assertEqual(
            step9.classify_change(None, None), "MISSING_BOTH"
        )
        self.assertEqual(
            step9.classify_change(None, 2), "GRAPH_RECOVERED"
        )
        self.assertEqual(
            step9.classify_change(2, None), "GRAPH_LOST"
        )

    def test_reciprocal_rank(self):
        self.assertEqual(step9.reciprocal_rank(1), 1.0)
        self.assertEqual(step9.reciprocal_rank(2), 0.5)
        self.assertEqual(step9.reciprocal_rank(None), 0.0)

    def test_calculate_metrics(self):
        rows = [
            {"baseline_rank": 1},
            {"baseline_rank": 2},
            {"baseline_rank": 6},
            {"baseline_rank": None},
        ]

        result = step9.calculate_metrics(rows, "baseline")

        self.assertEqual(result["top1_accuracy"], 0.25)
        self.assertEqual(result["recall_at_5"], 0.50)
        self.assertAlmostEqual(
            result["mrr"], (1 + 0.5 + 1 / 6) / 4
        )

    def test_empty_metrics(self):
        result = step9.calculate_metrics([], "graph")

        self.assertEqual(result["top1_accuracy"], 0.0)
        self.assertEqual(result["recall_at_5"], 0.0)
        self.assertEqual(result["mrr"], 0.0)

    def test_invalid_method(self):
        with self.assertRaises(ValueError):
            step9.calculate_metrics([], "unknown")

    def test_analyze_queries(self):
        rows = [{
            "query_id": "IND-001",
            "query": "Find request API",
            "target": "src/requests/api.py",
            "review_status": "VERIFIED",
            "baseline_rank": 5,
            "graph_rank": 2,
            "baseline_top1": False,
            "graph_top1": False,
            "baseline_top5": True,
            "graph_top5": True,
            "baseline_mrr": 0.2,
            "graph_mrr": 0.5,
            "baseline_target_score": 0.6,
            "direct_target_score": 0.6,
            "graph_target_score": 0.7,
            "baseline_top5_files": ["a.py", "b.py"],
            "graph_top5_files": ["b.py", "a.py"],
        }]

        details = step9.analyze_queries(rows)

        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]["change_category"], "IMPROVED")
        self.assertEqual(
            details[0]["rank_change_baseline_minus_graph"], 3
        )

    def test_summary_counts(self):
        rows = [
            {"baseline_rank": 5, "graph_rank": 2},
            {"baseline_rank": 2, "graph_rank": 5},
            {"baseline_rank": 3, "graph_rank": 3},
        ]

        details = [
            {"query_id": "Q1", "change_category": "IMPROVED"},
            {"query_id": "Q2", "change_category": "REGRESSED"},
            {"query_id": "Q3", "change_category": "UNCHANGED"},
        ]

        summary = step9.build_summary(rows, details)

        self.assertEqual(summary["query_count"], 3)
        self.assertEqual(summary["query_rank_changes"]["IMPROVED"], 1)
        self.assertEqual(summary["query_rank_changes"]["REGRESSED"], 1)
        self.assertEqual(summary["query_rank_changes"]["UNCHANGED"], 1)

    def test_read_step8_results_rejects_wrong_row_count(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_csv = Path(temp_dir) / "empty.csv"
            test_csv.write_text("query_id\n", encoding="utf-8")

            with patch.object(step9, "INPUT_CSV", test_csv):
                with self.assertRaises(ValueError):
                    step9.read_step8_results()


if __name__ == "__main__":
    unittest.main(verbosity=2)
