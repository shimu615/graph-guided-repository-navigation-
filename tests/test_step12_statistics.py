"""Tests for Step 12 statistical analysis."""

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import step12_statistical_analysis as stats


def test_mean():
    assert stats.mean([1, 2, 3]) == 2


def test_median_odd():
    assert stats.median([1, 3, 2]) == 2


def test_median_even():
    assert stats.median([1, 2, 3, 4]) == 2.5


def test_mean_rejects_empty():
    with pytest.raises(ValueError):
        stats.mean([])


def test_optional_float_empty():
    assert stats.parse_optional_float("", "boost") is None


def test_optional_float_valid():
    assert stats.parse_optional_float("0.10", "boost") == 0.10


def test_safe_float_rejects_invalid():
    with pytest.raises(ValueError):
        stats.safe_float("abc", "mrr")


def test_safe_float_rejects_infinity():
    with pytest.raises(ValueError):
        stats.safe_float("inf", "mrr")


def test_exact_permutation_all_ties():
    result = stats.exact_sign_flip_permutation_test([0, 0, 0])
    assert result["p_value_two_sided"] == 1.0
    assert result["nonzero_pairs"] == 0


def test_exact_permutation_symmetric_difference():
    result = stats.exact_sign_flip_permutation_test([0.1, -0.1])
    assert result["permutations"] == 4
    assert 0.0 <= result["p_value_two_sided"] <= 1.0


def test_exact_permutation_all_positive():
    result = stats.exact_sign_flip_permutation_test([1, 1, 1])
    assert result["p_value_two_sided"] == pytest.approx(0.25)


def test_mcnemar_no_discordant_pairs():
    result = stats.exact_mcnemar_test([1, 0, 1], [1, 0, 1])
    assert result["discordant_pairs"] == 0
    assert result["p_value_two_sided"] == 1.0


def test_mcnemar_one_direction():
    result = stats.exact_mcnemar_test([0, 0, 0], [1, 0, 0])
    assert result["graph_only_successes"] == 1
    assert result["baseline_only_successes"] == 0
    assert result["p_value_two_sided"] == 1.0


def test_mcnemar_balanced_discordance():
    result = stats.exact_mcnemar_test([1, 0], [0, 1])
    assert result["discordant_pairs"] == 2
    assert result["p_value_two_sided"] == 1.0


def test_bootstrap_is_reproducible():
    values = [0.1, -0.1, 0.2, 0.0]
    first = stats.bootstrap_mean_difference_ci(
        values, repetitions=1000, seed=123
    )
    second = stats.bootstrap_mean_difference_ci(
        values, repetitions=1000, seed=123
    )
    assert first == second


def test_bootstrap_interval_contains_point_estimate():
    values = [0.1, 0.2, 0.3, 0.4]
    result = stats.bootstrap_mean_difference_ci(
        values, repetitions=2000, seed=42
    )
    observed = stats.mean(values)
    assert result["lower"] <= observed <= result["upper"]


def test_compare_metric_reports_wins_ties_losses():
    result = stats.compare_metric(
        [0.1, 0.2, 0.3],
        [0.2, 0.2, 0.1],
        "mrr",
    )
    assert result["wins"] == 1
    assert result["ties"] == 1
    assert result["losses"] == 1
    assert "exact_paired_permutation_test" in result
    assert "bootstrap_95_ci" in result


def test_primary_pairs_match_query_ids():
    rows = []

    for index in range(12):
        qid = f"IND-{index + 1:03d}"

        rows.append({
            "experiment": "baseline",
            "query_id": qid,
            "boost": None,
            "dropout_rate": None,
            "seed": None,
            "target_rank": 1,
            "top1": 1.0,
            "recall_at_5": 1.0,
            "mrr": 1.0,
        })

        rows.append({
            "experiment": "graph",
            "query_id": qid,
            "boost": 0.10,
            "dropout_rate": None,
            "seed": None,
            "target_rank": 2,
            "top1": 0.0,
            "recall_at_5": 1.0,
            "mrr": 0.5,
        })

    pairs = stats.select_primary_pairs(rows)

    assert len(pairs) == 12
    assert pairs[0][0]["query_id"] == "IND-001"
    assert pairs[0][1]["query_id"] == "IND-001"


def test_primary_pairs_reject_missing_graph_query():
    rows = []

    for index in range(12):
        qid = f"IND-{index + 1:03d}"

        rows.append({
            "experiment": "baseline",
            "query_id": qid,
            "boost": None,
            "dropout_rate": None,
            "seed": None,
            "target_rank": 1,
            "top1": 1.0,
            "recall_at_5": 1.0,
            "mrr": 1.0,
        })

        if index != 0:
            rows.append({
                "experiment": "graph",
                "query_id": qid,
                "boost": 0.10,
                "dropout_rate": None,
                "seed": None,
                "target_rank": 1,
                "top1": 1.0,
                "recall_at_5": 1.0,
                "mrr": 1.0,
            })

    with pytest.raises(ValueError):
        stats.select_primary_pairs(rows)


def test_load_step11_results_validates_csv(tmp_path, monkeypatch):
    csv_path = tmp_path / "step11.csv"

    fields = [
        "experiment", "query_id", "boost", "dropout_rate",
        "seed", "target_rank", "top1", "recall_at_5", "mrr",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "experiment": "baseline",
            "query_id": "IND-001",
            "boost": "",
            "dropout_rate": "",
            "seed": "",
            "target_rank": "1",
            "top1": "1",
            "recall_at_5": "1",
            "mrr": "1",
        })

    monkeypatch.setattr(stats, "INPUT_CSV", csv_path)

    rows = stats.load_step11_results()

    assert len(rows) == 1
    assert rows[0]["query_id"] == "IND-001"
    assert rows[0]["mrr"] == 1.0


def test_load_step11_results_rejects_bad_metric(tmp_path, monkeypatch):
    csv_path = tmp_path / "bad.csv"

    fields = [
        "experiment", "query_id", "boost", "dropout_rate",
        "seed", "target_rank", "top1", "recall_at_5", "mrr",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow({
            "experiment": "baseline",
            "query_id": "IND-001",
            "boost": "",
            "dropout_rate": "",
            "seed": "",
            "target_rank": "1",
            "top1": "2",
            "recall_at_5": "1",
            "mrr": "1",
        })

    monkeypatch.setattr(stats, "INPUT_CSV", csv_path)

    with pytest.raises(ValueError):
        stats.load_step11_results()
