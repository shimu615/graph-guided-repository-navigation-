"""Step 12: Paired statistical analysis of repository retrieval results."""

from __future__ import annotations

import csv
import itertools
import json
import math
import random
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INPUT_CSV = ROOT / "results" / "step11-robustness-audited.csv"

OUTPUT_CSV = ROOT / "results" / "step12-statistical-audited.csv"
OUTPUT_JSON = ROOT / "results" / "step12-statistical-audited-summary.json"
OUTPUT_REPORT = ROOT / "notes" / "step12-statistical-audited-report.md"

EXPECTED_QUERY_COUNT = 12
PRIMARY_BOOST = 0.10
TOP_K = 5
BOOTSTRAP_REPETITIONS = 10000
RANDOM_SEED = 20261111


def safe_float(value, field):
    """Convert a CSV value to float and reject invalid or non-finite values."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid numeric value for {field}: {value!r}")

    if not math.isfinite(result):
        raise ValueError(f"Non-finite value for {field}: {value!r}")

    return result


def parse_optional_float(value, field):
    if value is None or str(value).strip() == "":
        return None
    return safe_float(value, field)


def load_step11_results():
    """Load and validate Step 11 query-level results."""
    if not INPUT_CSV.is_file():
        raise FileNotFoundError(f"Step 11 CSV not found: {INPUT_CSV}")

    required = {
        "experiment",
        "query_id",
        "boost",
        "dropout_rate",
        "seed",
        "target_rank",
        "top1",
        "recall_at_5",
        "mrr",
    }

    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual = set(reader.fieldnames or [])
        missing = required - actual

        if missing:
            raise ValueError(
                f"Step 11 CSV missing columns: {sorted(missing)}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError("Step 11 CSV contains no data rows.")

    parsed = []

    for row in rows:
        query_id = (row.get("query_id") or "").strip()
        experiment = (row.get("experiment") or "").strip().lower()

        if not query_id:
            raise ValueError("A row has an empty query_id.")

        if experiment not in {"baseline", "graph"}:
            raise ValueError(
                f"{query_id}: unexpected experiment value {experiment!r}"
            )

        boost = parse_optional_float(row.get("boost"), "boost")
        dropout_rate = parse_optional_float(
            row.get("dropout_rate"), "dropout_rate"
        )
        seed_text = (row.get("seed") or "").strip()
        seed = int(seed_text) if seed_text else None

        target_rank_text = (row.get("target_rank") or "").strip()
        target_rank = int(target_rank_text) if target_rank_text else None

        top1 = safe_float(row.get("top1"), "top1")
        recall = safe_float(row.get("recall_at_5"), "recall_at_5")
        mrr = safe_float(row.get("mrr"), "mrr")

        if top1 not in {0.0, 1.0}:
            raise ValueError(f"{query_id}: top1 must be 0 or 1.")

        if recall not in {0.0, 1.0}:
            raise ValueError(f"{query_id}: recall_at_5 must be 0 or 1.")

        if not 0.0 <= mrr <= 1.0:
            raise ValueError(f"{query_id}: MRR must be between 0 and 1.")

        if target_rank is not None and target_rank < 1:
            raise ValueError(f"{query_id}: target_rank must be positive.")

        if experiment == "baseline":
            # Step 11 evaluate() uses dropout_rate=0.0 and seed=0
            # as defaults, even for the lexical baseline.
            valid_dropout = (
                dropout_rate is None
                or math.isclose(dropout_rate, 0.0, abs_tol=1e-12)
            )
            valid_seed = seed is None or seed == 0

            if not valid_dropout or not valid_seed:
                raise ValueError(
                    f"{query_id}: unexpected baseline dropout/seed values: "
                    f"dropout_rate={dropout_rate}, seed={seed}"
                )

        parsed.append({
            "experiment": experiment,
            "query_id": query_id,
            "boost": boost,
            "dropout_rate": dropout_rate,
            "seed": seed,
            "target_rank": target_rank,
            "top1": top1,
            "recall_at_5": recall,
            "mrr": mrr,
        })

    return parsed


def select_primary_pairs(rows):
    """Match baseline and graph boost=0.10 rows by query ID."""
    baseline_rows = {}
    graph_rows = {}

    for row in rows:
        if row["experiment"] == "baseline":
            if row["query_id"] in baseline_rows:
                raise ValueError(
                    f"Duplicate baseline row: {row['query_id']}"
                )
            baseline_rows[row["query_id"]] = row

        elif (
            row["experiment"] == "graph"
            and (
                row["dropout_rate"] is None
                or math.isclose(row["dropout_rate"], 0.0, abs_tol=1e-12)
            )
            and (row["seed"] is None or row["seed"] == 0)
            and row["boost"] is not None
            and math.isclose(row["boost"], PRIMARY_BOOST, abs_tol=1e-9)
        ):
            if row["query_id"] in graph_rows:
                raise ValueError(
                    f"Duplicate primary graph row: {row['query_id']}"
                )
            graph_rows[row["query_id"]] = row

    if set(baseline_rows) != set(graph_rows):
        missing_graph = sorted(set(baseline_rows) - set(graph_rows))
        missing_baseline = sorted(set(graph_rows) - set(baseline_rows))
        raise ValueError(
            "Primary paired query IDs do not match. "
            f"Missing graph={missing_graph}; "
            f"missing baseline={missing_baseline}"
        )

    query_ids = sorted(baseline_rows)

    if len(query_ids) != EXPECTED_QUERY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_QUERY_COUNT} paired queries, "
            f"found {len(query_ids)}"
        )

    return [
        (baseline_rows[qid], graph_rows[qid])
        for qid in query_ids
    ]


def mean(values):
    if not values:
        raise ValueError("Cannot calculate mean of empty values.")
    return sum(values) / len(values)


def median(values):
    if not values:
        raise ValueError("Cannot calculate median of empty values.")
    return statistics.median(values)


def exact_sign_flip_permutation_test(differences):
    """
    Two-sided exact paired sign-flip permutation test.

    This tests the null that paired differences are exchangeable
    under sign changes. It is not a test of generalization to all repositories.
    """
    if not differences:
        raise ValueError("Permutation test requires paired differences.")

    nonzero = [d for d in differences if not math.isclose(d, 0.0, abs_tol=1e-15)]

    if not nonzero:
        return {
            "p_value_two_sided": 1.0,
            "permutations": 1,
            "nonzero_pairs": 0,
            "observed_mean_difference": mean(differences),
        }

    observed = abs(mean(differences))
    extreme = 0
    total = 0
    n = len(differences)

    for signs in itertools.product((-1.0, 1.0), repeat=len(nonzero)):
        permuted_sum = sum(
            sign * value for sign, value in zip(signs, nonzero)
        )
        permuted_mean = permuted_sum / n

        if abs(permuted_mean) >= observed - 1e-15:
            extreme += 1

        total += 1

    return {
        "p_value_two_sided": extreme / total,
        "permutations": total,
        "nonzero_pairs": len(nonzero),
        "observed_mean_difference": mean(differences),
    }


def exact_mcnemar_test(baseline, graph):
    """
    Exact two-sided McNemar test for paired binary outcomes.
    """
    if len(baseline) != len(graph) or not baseline:
        raise ValueError("McNemar test requires equal non-empty paired data.")

    graph_only = sum(
        b == 0 and g == 1 for b, g in zip(baseline, graph)
    )
    baseline_only = sum(
        b == 1 and g == 0 for b, g in zip(baseline, graph)
    )

    discordant = graph_only + baseline_only

    if discordant == 0:
        p_value = 1.0
    else:
        tail = sum(
            math.comb(discordant, k)
            for k in range(min(graph_only, baseline_only) + 1)
        ) / (2 ** discordant)
        p_value = min(1.0, 2.0 * tail)

    return {
        "graph_only_successes": graph_only,
        "baseline_only_successes": baseline_only,
        "discordant_pairs": discordant,
        "p_value_two_sided": p_value,
    }


def bootstrap_mean_difference_ci(
    differences,
    repetitions=BOOTSTRAP_REPETITIONS,
    seed=RANDOM_SEED,
):
    """Percentile bootstrap CI for the paired mean difference."""
    if not differences:
        raise ValueError("Bootstrap requires paired differences.")

    rng = random.Random(seed)
    n = len(differences)
    estimates = []

    for _ in range(repetitions):
        sample = [differences[rng.randrange(n)] for _ in range(n)]
        estimates.append(mean(sample))

    estimates.sort()

    lower_index = int(0.025 * repetitions)
    upper_index = min(
        repetitions - 1,
        int(0.975 * repetitions),
    )

    return {
        "confidence_level": 0.95,
        "method": "paired percentile bootstrap",
        "repetitions": repetitions,
        "lower": estimates[lower_index],
        "upper": estimates[upper_index],
        "seed": seed,
    }


def compare_metric(baseline_values, graph_values, metric_name):
    differences = [
        graph - baseline
        for baseline, graph in zip(baseline_values, graph_values)
    ]

    wins = sum(value > 0 for value in differences)
    losses = sum(value < 0 for value in differences)
    ties = sum(math.isclose(value, 0.0, abs_tol=1e-15) for value in differences)

    result = {
        "metric": metric_name,
        "query_count": len(differences),
        "baseline_mean": mean(baseline_values),
        "graph_mean": mean(graph_values),
        "mean_difference_graph_minus_baseline": mean(differences),
        "median_difference_graph_minus_baseline": median(differences),
        "wins": wins,
        "ties": ties,
        "losses": losses,
    }

    if metric_name == "mrr":
        result["exact_paired_permutation_test"] = (
            exact_sign_flip_permutation_test(differences)
        )
        result["bootstrap_95_ci"] = bootstrap_mean_difference_ci(differences)

    elif metric_name in {"top1", "recall_at_5"}:
        result["exact_mcnemar_test"] = exact_mcnemar_test(
            baseline_values, graph_values
        )

    return result


def descriptive_boost_summary(rows):
    groups = defaultdict(list)

    for row in rows:
        if (
            row["experiment"] == "graph"
            and (
                row["dropout_rate"] is None
                or math.isclose(row["dropout_rate"], 0.0, abs_tol=1e-12)
            )
            and (row["seed"] is None or row["seed"] == 0)
            and row["boost"] is not None
        ):
            groups[row["boost"]].append(row)

    output = []

    for boost in sorted(groups):
        group = groups[boost]

        if len(group) != EXPECTED_QUERY_COUNT:
            raise ValueError(
                f"Boost {boost}: expected {EXPECTED_QUERY_COUNT} rows, "
                f"found {len(group)}"
            )

        output.append({
            "boost": boost,
            "query_count": len(group),
            "top1_mean": mean([r["top1"] for r in group]),
            "recall_at_5_mean": mean([r["recall_at_5"] for r in group]),
            "mrr_mean": mean([r["mrr"] for r in group]),
        })

    return output


def descriptive_dropout_summary(rows):
    grouped = defaultdict(lambda: defaultdict(list))

    for row in rows:
        if (
            row["experiment"] == "graph"
            and row["dropout_rate"] is not None
            and row["dropout_rate"] > 0.0
            and row["seed"] is not None
        ):
            grouped[row["dropout_rate"]][row["seed"]].append(row)

    output = []

    for rate in sorted(grouped):
        seed_summaries = []

        for seed in sorted(grouped[rate]):
            group = grouped[rate][seed]

            if len(group) != EXPECTED_QUERY_COUNT:
                raise ValueError(
                    f"Dropout {rate}, seed {seed}: expected "
                    f"{EXPECTED_QUERY_COUNT} rows, found {len(group)}"
                )

            seed_summaries.append({
                "seed": seed,
                "top1": mean([r["top1"] for r in group]),
                "recall_at_5": mean([r["recall_at_5"] for r in group]),
                "mrr": mean([r["mrr"] for r in group]),
            })

        output.append({
            "dropout_rate": rate,
            "seed_count": len(seed_summaries),
            "seed_level_results": seed_summaries,
            "mean_seed_mrr": mean([x["mrr"] for x in seed_summaries]),
            "sd_seed_mrr": (
                statistics.stdev([x["mrr"] for x in seed_summaries])
                if len(seed_summaries) > 1 else 0.0
            ),
            "mean_seed_top1": mean([x["top1"] for x in seed_summaries]),
            "mean_seed_recall_at_5": mean(
                [x["recall_at_5"] for x in seed_summaries]
            ),
        })

    return output


def build_query_comparison(pairs):
    output = []

    for baseline, graph in pairs:
        output.append({
            "query_id": baseline["query_id"],
            "baseline_target_rank": baseline["target_rank"],
            "graph_target_rank": graph["target_rank"],
            "baseline_top1": int(baseline["top1"]),
            "graph_top1": int(graph["top1"]),
            "top1_difference": int(graph["top1"] - baseline["top1"]),
            "baseline_recall_at_5": int(baseline["recall_at_5"]),
            "graph_recall_at_5": int(graph["recall_at_5"]),
            "recall_at_5_difference": int(
                graph["recall_at_5"] - baseline["recall_at_5"]
            ),
            "baseline_mrr": baseline["mrr"],
            "graph_mrr": graph["mrr"],
            "mrr_difference": graph["mrr"] - baseline["mrr"],
        })

    return output


def create_report(summary):
    metrics = summary["primary_comparison"]
    mrr = metrics["mrr"]
    top1 = metrics["top1"]
    recall = metrics["recall_at_5"]

    lines = [
        "# Step 12 — Statistical Analysis",
        "",
        "## 1. Objective",
        "",
        "This analysis compares lexical baseline retrieval with "
        "graph-guided retrieval using a paired query-level design.",
        "",
        "The primary comparison uses graph boost = 0.10, with no "
        "edge dropout, on the same 12 manually reviewed queries.",
        "",
        "## 2. Primary MRR comparison",
        "",
        f"- Baseline mean MRR: {mrr['baseline_mean']:.4f}",
        f"- Graph mean MRR: {mrr['graph_mean']:.4f}",
        f"- Mean paired difference (graph - baseline): "
        f"{mrr['mean_difference_graph_minus_baseline']:.4f}",
        f"- Median paired difference: "
        f"{mrr['median_difference_graph_minus_baseline']:.4f}",
        f"- Wins / ties / losses: {mrr['wins']} / {mrr['ties']} / {mrr['losses']}",
        f"- Exact paired sign-flip permutation p-value: "
        f"{mrr['exact_paired_permutation_test']['p_value_two_sided']:.4f}",
        f"- Paired bootstrap 95% CI: "
        f"[{mrr['bootstrap_95_ci']['lower']:.4f}, "
        f"{mrr['bootstrap_95_ci']['upper']:.4f}]",
        "",
        "## 3. Binary retrieval metrics",
        "",
        "| Metric | Baseline | Graph | Difference | Exact McNemar p |",
        "|---|---:|---:|---:|---:|",
        (
            f"| Top-1 | {top1['baseline_mean']:.4f} | "
            f"{top1['graph_mean']:.4f} | "
            f"{top1['mean_difference_graph_minus_baseline']:.4f} | "
            f"{top1['exact_mcnemar_test']['p_value_two_sided']:.4f} |"
        ),
        (
            f"| Recall@5 | {recall['baseline_mean']:.4f} | "
            f"{recall['graph_mean']:.4f} | "
            f"{recall['mean_difference_graph_minus_baseline']:.4f} | "
            f"{recall['exact_mcnemar_test']['p_value_two_sided']:.4f} |"
        ),
        "",
        "## 4. Graph boost sensitivity",
        "",
        "| Boost | Top-1 | Recall@5 | MRR |",
        "|---:|---:|---:|---:|",
    ]

    for row in summary["boost_sensitivity"]:
        lines.append(
            f"| {row['boost']:.2f} | {row['top1_mean']:.4f} | "
            f"{row['recall_at_5_mean']:.4f} | {row['mrr_mean']:.4f} |"
        )

    lines += [
        "",
        "## 5. Edge dropout sensitivity",
        "",
        "| Dropout | Seeds | Mean seed MRR | SD across seeds |",
        "|---:|---:|---:|---:|",
    ]

    for row in summary["edge_dropout_sensitivity"]:
        lines.append(
            f"| {row['dropout_rate']:.2f} | {row['seed_count']} | "
            f"{row['mean_seed_mrr']:.4f} | {row['sd_seed_mrr']:.4f} |"
        )

    lines += [
        "",
        "## 6. Interpretation",
        "",
        "The primary comparison is paired by query. Positive MRR "
        "differences favor graph-guided retrieval; negative differences "
        "favor the lexical baseline.",
        "",
        "The exact sign-flip permutation test is reported for MRR. "
        "Exact McNemar tests are reported for Top-1 and Recall@5.",
        "",
        "The bootstrap interval is a descriptive uncertainty estimate "
        "for this small query sample and should not be interpreted as "
        "proof of performance on other repositories.",
        "",
        "Boost and edge-dropout analyses are descriptive sensitivity "
        "analyses. They are not treated as independent confirmatory tests.",
        "",
        "## 7. Limitations",
        "",
        "- Only one repository (psf/requests) was evaluated.",
        "- The paired evaluation contains 12 manually reviewed queries.",
        "- Query-level outcomes are not evidence of broad repository-level "
        "generalization.",
        "- Repeated dropout seeds are sensitivity runs, not additional "
        "independent queries.",
        "- Statistical results do not establish causal superiority.",
        "",
        "## 8. Reproducibility",
        "",
        f"- Source file: `{INPUT_CSV.relative_to(ROOT).as_posix()}`",
        f"- Query count: {summary['query_count']}",
        f"- Graph boost for primary comparison: {PRIMARY_BOOST:.2f}",
        f"- Bootstrap repetitions: {BOOTSTRAP_REPETITIONS}",
        f"- Random seed: {RANDOM_SEED}",
        "",
    ]

    return "\n".join(lines)


def main():
    output_paths = [OUTPUT_CSV, OUTPUT_JSON, OUTPUT_REPORT]

    existing = [str(path) for path in output_paths if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing Step 12 outputs: "
            + ", ".join(existing)
        )

    rows = load_step11_results()
    pairs = select_primary_pairs(rows)

    baseline_top1 = [b["top1"] for b, _ in pairs]
    graph_top1 = [g["top1"] for _, g in pairs]

    baseline_recall = [b["recall_at_5"] for b, _ in pairs]
    graph_recall = [g["recall_at_5"] for _, g in pairs]

    baseline_mrr = [b["mrr"] for b, _ in pairs]
    graph_mrr = [g["mrr"] for _, g in pairs]

    primary = {
        "top1": compare_metric(baseline_top1, graph_top1, "top1"),
        "recall_at_5": compare_metric(
            baseline_recall, graph_recall, "recall_at_5"
        ),
        "mrr": compare_metric(baseline_mrr, graph_mrr, "mrr"),
    }

    comparison_rows = build_query_comparison(pairs)

    summary = {
        "analysis_id": "STEP12-STATISTICAL-ANALYSIS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": INPUT_CSV.relative_to(ROOT).as_posix(),
        "query_count": len(pairs),
        "input_row_count": len(rows),
        "primary_method_comparison": {
            "baseline": "lexical baseline",
            "graph": "graph-guided retrieval",
            "graph_boost": PRIMARY_BOOST,
            "edge_dropout": None,
            "paired_by": "query_id",
        },
        "primary_comparison": primary,
        "boost_sensitivity": descriptive_boost_summary(rows),
        "edge_dropout_sensitivity": descriptive_dropout_summary(rows),
        "interpretation_scope": (
            "Exploratory paired statistical analysis on one repository "
            "and 12 manually reviewed queries. No broad superiority "
            "or cross-repository generalization claim is supported."
        ),
        "methods": {
            "mrr_test": "exact two-sided paired sign-flip permutation test",
            "binary_tests": "exact two-sided McNemar test",
            "confidence_interval": "paired percentile bootstrap 95% CI",
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "random_seed": RANDOM_SEED,
            "top_k": TOP_K,
        },
    }

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    fields = list(comparison_rows[0].keys())

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(comparison_rows)

    OUTPUT_JSON.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    OUTPUT_REPORT.write_text(
        create_report(summary),
        encoding="utf-8",
    )

    print("STEP 12 STATISTICAL ANALYSIS: SUCCESS")
    print(f"Input rows: {len(rows)}")
    print(f"Paired queries: {len(pairs)}")
    print("\nPrimary MRR comparison:")
    print(json.dumps(primary["mrr"], indent=2))
    print("\nCreated:")
    print(OUTPUT_CSV)
    print(OUTPUT_JSON)
    print(OUTPUT_REPORT)


if __name__ == "__main__":
    main()
