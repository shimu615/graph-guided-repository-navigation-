import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from step5_error_analysis import (
    rank_position,
    classify_change,
    reciprocal_rank,
    calculate_metrics,
)


class Step5AnalysisTests(unittest.TestCase):

    def test_rank_position(self):
        self.assertEqual(rank_position(["a.py", "b.py"], "a.py"), 1)
        self.assertEqual(rank_position(["a.py", "b.py"], "b.py"), 2)
        self.assertIsNone(rank_position(["a.py"], "missing.py"))

    def test_improved_classification(self):
        self.assertEqual(classify_change(5, 2), "IMPROVED")

    def test_regressed_classification(self):
        self.assertEqual(classify_change(2, 5), "REGRESSED")

    def test_unchanged_classification(self):
        self.assertEqual(classify_change(3, 3), "UNCHANGED")

    def test_missing_classification(self):
        self.assertEqual(classify_change(None, 2), "GRAPH_RECOVERED")
        self.assertEqual(classify_change(2, None), "GRAPH_LOST")
        self.assertEqual(classify_change(None, None), "MISSING_BOTH")

    def test_reciprocal_rank(self):
        self.assertEqual(reciprocal_rank(1), 1.0)
        self.assertEqual(reciprocal_rank(2), 0.5)
        self.assertEqual(reciprocal_rank(None), 0.0)

    def test_calculate_metrics(self):
        rows = [
            {"baseline_rank": 1},
            {"baseline_rank": 2},
            {"baseline_rank": 6},
            {"baseline_rank": None},
        ]

        metrics = calculate_metrics(rows, "baseline")

        self.assertEqual(metrics["top1_accuracy"], 0.25)
        self.assertEqual(metrics["recall_at_5"], 0.50)
        self.assertAlmostEqual(metrics["mrr"], (1 + 0.5 + (1 / 6)) / 4)

    def test_empty_metrics(self):
        metrics = calculate_metrics([], "baseline")
        self.assertEqual(metrics["top1_accuracy"], 0.0)
        self.assertEqual(metrics["recall_at_5"], 0.0)
        self.assertEqual(metrics["mrr"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

