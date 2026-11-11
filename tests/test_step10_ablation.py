import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import step10_ablation_study as step10


class Step10AblationTests(unittest.TestCase):

    def test_reciprocal_rank(self):
        self.assertEqual(step10.reciprocal_rank(1), 1.0)
        self.assertEqual(step10.reciprocal_rank(2), 0.5)
        self.assertEqual(step10.reciprocal_rank(None), 0.0)

    def test_rank_position(self):
        ranked = ["a.py", "b.py", "c.py"]
        self.assertEqual(step10.rank_position(ranked, "a.py"), 1)
        self.assertEqual(step10.rank_position(ranked, "c.py"), 3)
        self.assertIsNone(step10.rank_position(ranked, "missing.py"))

    def test_calculate_metrics(self):
        ranks = [1, 2, 6, None]
        metrics = step10.calculate_metrics(ranks)

        self.assertEqual(metrics["top1_accuracy"], 0.25)
        self.assertEqual(metrics["recall_at_5"], 0.50)
        self.assertAlmostEqual(
            metrics["mrr"], (1 + 0.5 + 1 / 6) / 4
        )

    def test_empty_metrics(self):
        metrics = step10.calculate_metrics([])

        self.assertEqual(metrics["top1_accuracy"], 0.0)
        self.assertEqual(metrics["recall_at_5"], 0.0)
        self.assertEqual(metrics["mrr"], 0.0)

    def test_boost_values_are_fixed(self):
        self.assertEqual(
            step10.BOOST_VALUES,
            (0.00, 0.05, 0.10, 0.20),
        )

    def test_evaluate_lexical_only(self):
        rows = [{
            "query_id": "Q1",
            "query": "find request",
            "target": "target.py",
            "review_status": "VERIFIED",
        }]

        with patch.object(
            step10, "rank_baseline",
            return_value=(["other.py", "target.py"], {
                "other.py": 0.8, "target.py": 0.6
            })
        ):
            result = step10.evaluate_configuration(
                rows, {"target.py": "text"}, {}, 0.0
            )

        self.assertEqual(result[0]["target_rank"], 2)
        self.assertEqual(result[0]["graph_boost"], 0.0)
        self.assertEqual(result[0]["target_reciprocal_rank"], 0.5)

    def test_evaluate_graph_configuration(self):
        rows = [{
            "query_id": "Q1",
            "query": "find request",
            "target": "target.py",
            "review_status": "VERIFIED",
        }]

        with patch.object(
            step10, "rank_graph",
            return_value=(
                ["target.py", "other.py"],
                {"target.py": 0.9, "other.py": 0.7},
                {"target.py": 0.6, "other.py": 0.7},
            )
        ):
            result = step10.evaluate_configuration(
                rows, {"target.py": "text"}, {}, 0.10
            )

        self.assertEqual(result[0]["target_rank"], 1)
        self.assertTrue(result[0]["top1"])
        self.assertEqual(result[0]["direct_target_score"], 0.6)
        self.assertEqual(result[0]["final_target_score"], 0.9)

    def test_run_ablation_has_all_configurations(self):
        rows = [{
            "query_id": "Q1",
            "query": "find request",
            "target": "target.py",
            "review_status": "VERIFIED",
        }]

        with patch.object(
            step10, "evaluate_configuration",
            side_effect=[
                [{"query_id": "Q1", "target_rank": 2}],
                [{"query_id": "Q1", "target_rank": 2}],
                [{"query_id": "Q1", "target_rank": 1}],
                [{"query_id": "Q1", "target_rank": 3}],
            ]
        ):
            details, summaries = step10.run_ablation(
                rows, {"target.py": "text"}, {}
            )

        self.assertEqual(len(details), 4)
        self.assertEqual(
            set(summaries),
            {"0.00", "0.05", "0.10", "0.20"},
        )
        self.assertEqual(
            summaries["0.10"]["metrics"]["top1_accuracy"], 1.0
        )
        self.assertEqual(
            summaries["0.10"]["metric_difference_vs_lexical"]["mrr"],
            0.5,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
