from __future__ import annotations

import csv
import json
import random
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from retrieval_core import (
    collect_python_files,
    normalize_texts,
    build_import_graph,
    rank_baseline,
    rank_graph,
)

REPO = PROJECT_ROOT / "external" / "requests"
DATASET = PROJECT_ROOT / "results" / "independent-query-set.csv"

CSV_OUT = PROJECT_ROOT / "results" / "step11-robustness-audited.csv"
JSON_OUT = PROJECT_ROOT / "results" / "step11-robustness-audited-summary.json"
REPORT_OUT = PROJECT_ROOT / "notes" / "step11-robustness-audited-report.md"

EXPECTED_COMMIT = "611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60"

BOOST_VALUES = (0.00, 0.05, 0.10, 0.20)
DROPOUT_RATES = (0.10, 0.25, 0.50)
SEEDS = (11, 22, 33, 44, 55)
TOP_K = 5


def normalize_path(value):
    return str(value).replace("\\", "/").strip().removeprefix("./")


def load_dataset():
    if not DATASET.exists():
        raise FileNotFoundError(f"Dataset missing: {DATASET}")

    rows = []
    with DATASET.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        required = {
            "query_id",
            "query",
            "proposed_target",
            "review_status",
            "reviewer_notes",
        }

        actual = set(reader.fieldnames or [])
        missing = required - actual

        if missing:
            raise ValueError(
                f"Dataset columns missing: {sorted(missing)}. "
                f"Found: {sorted(actual)}"
            )

        for row in reader:
            query_id = row["query_id"].strip()
            query = row["query"].strip()
            target = normalize_path(row["proposed_target"])
            status = row["review_status"].strip().upper()
            notes = row["reviewer_notes"].strip()

            if not query_id or not query or not target:
                raise ValueError(f"Blank required field: {row}")

            if status not in {"VERIFIED", "CORRECTED"}:
                raise ValueError(
                    f"Query {query_id} has unreviewed status: {status}"
                )

            if not notes:
                raise ValueError(
                    f"Query {query_id} has blank reviewer_notes"
                )

            rows.append({
                "query_id": query_id,
                "query": query,
                "target": target,
            })

    if len(rows) != 12:
        raise ValueError(
            f"Expected 12 reviewed queries, found {len(rows)}"
        )

    ids = [r["query_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate query IDs found")

    return rows


def resolve_targets(queries, texts):
    indexed = {normalize_path(path): path for path in texts}

    for item in queries:
        target = item["target"]

        if target not in indexed:
            raise ValueError(
                f"Target not found in indexed repository: {target}"
            )

        item["target_key"] = indexed[target]


def metrics(ranked, target):
    ranked = list(ranked)

    try:
        rank = ranked.index(target) + 1
    except ValueError:
        rank = 0

    return {
        "target_rank": rank,
        "top1": int(rank == 1),
        "recall_at_5": int(1 <= rank <= TOP_K),
        "mrr": (1.0 / rank) if rank else 0.0,
    }


def aggregate(rows):
    if not rows:
        raise ValueError("Cannot aggregate an empty result list")

    return {
        "top1": statistics.mean(r["top1"] for r in rows),
        "recall_at_5": statistics.mean(
            r["recall_at_5"] for r in rows
        ),
        "mrr": statistics.mean(r["mrr"] for r in rows),
    }


def complete_graph_nodes(graph, texts):
    """Ensure every indexed source file has a graph entry."""
    valid_nodes = set(texts)
    completed = {}

    for node in texts:
        neighbors = graph.get(node, set())
        completed[node] = {
            neighbor for neighbor in neighbors
            if neighbor in valid_nodes and neighbor != node
        }

    return completed


def make_symmetric_graph(graph):
    result = {node: set(neighbors) for node, neighbors in graph.items()}

    for node in list(result):
        for neighbor in list(result[node]):
            result.setdefault(neighbor, set())
            result[neighbor].add(node)

    return result


def perturb_graph(graph, dropout_rate, seed):
    if not 0.0 <= dropout_rate < 1.0:
        raise ValueError("Dropout rate must be >= 0 and < 1")

    symmetric = make_symmetric_graph(graph)
    nodes = sorted(symmetric, key=str)

    edges = []
    seen = set()

    for node in nodes:
        for neighbor in symmetric[node]:
            if node == neighbor:
                continue

            pair = tuple(sorted((str(node), str(neighbor))))

            if pair not in seen:
                seen.add(pair)
                edges.append((node, neighbor))

    rng = random.Random(seed)
    shuffled = list(edges)
    rng.shuffle(shuffled)

    remove_count = int(len(shuffled) * dropout_rate)
    removed = {
        tuple(sorted((str(a), str(b))))
        for a, b in shuffled[:remove_count]
    }

    result = {node: set() for node in nodes}

    for left, right in edges:
        pair = tuple(sorted((str(left), str(right))))

        if pair in removed:
            continue

        result[left].add(right)
        result[right].add(left)

    return result


def evaluate(queries, texts, graph, method, boost=0.10,
             dropout_rate=0.0, seed=0):
    output = []

    for item in queries:
        if method == "baseline":
            ranked, _ = rank_baseline(item["query"], texts)
        elif method == "graph":
            ranked, _, _ = rank_graph(
                item["query"], texts, graph, boost=boost
            )
        else:
            raise ValueError(f"Unknown method: {method}")

        result = metrics(ranked, item["target_key"])

        output.append({
            "experiment": method,
            "query_id": item["query_id"],
            "boost": boost,
            "dropout_rate": dropout_rate,
            "seed": seed,
            **result,
        })

    return output


def run_boost_experiments(queries, texts, graph):
    results = []

    for boost in BOOST_VALUES:
        rows = evaluate(
            queries, texts, graph,
            method="graph", boost=boost
        )

        results.append({
            "boost": boost,
            **aggregate(rows),
        })

    return results


def run_dropout_experiments(queries, texts, graph):
    results = []

    for rate in DROPOUT_RATES:
        for seed in SEEDS:
            changed_graph = perturb_graph(graph, rate, seed)

            rows = evaluate(
                queries, texts, changed_graph,
                method="graph",
                boost=0.10,
                dropout_rate=rate,
                seed=seed,
            )

            results.append({
                "dropout_rate": rate,
                "seed": seed,
                **aggregate(rows),
            })

    return results


def run_stability(queries, texts, graph):
    repetitions = 5
    details = []

    for item in queries:
        rankings = []

        for _ in range(repetitions):
            ranked, _, _ = rank_graph(
                item["query"], texts, graph, boost=0.10
            )
            rankings.append([str(p) for p in ranked])

        details.append({
            "query_id": item["query_id"],
            "stable": all(r == rankings[0] for r in rankings[1:]),
        })

    stable_count = sum(x["stable"] for x in details)

    return {
        "repetitions_per_query": repetitions,
        "query_count": len(queries),
        "stable_query_count": stable_count,
        "stability_rate": stable_count / len(queries),
        "details": details,
    }


def create_report(baseline, boosts, dropouts, stability):
    lines = [
        "# Step 11 — Robustness Analysis",
        "",
        "## 1. Objective",
        "",
        "This step evaluates the sensitivity of graph-guided file retrieval "
        "to graph edge removal, graph boost values, and repeated execution.",
        "",
        "## 2. Lexical baseline",
        "",
        f"- Top-1: {baseline['top1']:.4f}",
        f"- Recall@5: {baseline['recall_at_5']:.4f}",
        f"- MRR: {baseline['mrr']:.4f}",
        "",
        "## 3. Boost sensitivity",
        "",
        "| Boost | Top-1 | Recall@5 | MRR |",
        "|---:|---:|---:|---:|",
    ]

    for row in boosts:
        lines.append(
            f"| {row['boost']:.2f} | {row['top1']:.4f} | "
            f"{row['recall_at_5']:.4f} | {row['mrr']:.4f} |"
        )

    lines += [
        "",
        "## 4. Edge dropout",
        "",
        "| Dropout | Runs | Mean Top-1 | Mean Recall@5 | Mean MRR |",
        "|---:|---:|---:|---:|---:|",
    ]

    for rate in DROPOUT_RATES:
        selected = [r for r in dropouts if r["dropout_rate"] == rate]

        lines.append(
            f"| {rate:.0%} | {len(selected)} | "
            f"{statistics.mean(r['top1'] for r in selected):.4f} | "
            f"{statistics.mean(r['recall_at_5'] for r in selected):.4f} | "
            f"{statistics.mean(r['mrr'] for r in selected):.4f} |"
        )

    lines += [
        "",
        "## 5. Ranking stability",
        "",
        f"- Repetitions per query: {stability['repetitions_per_query']}",
        f"- Stable queries: {stability['stable_query_count']}/"
        f"{stability['query_count']}",
        f"- Stability rate: {stability['stability_rate']:.4f}",
        "",
        "## 6. Threats to validity",
        "",
        "### Dataset validity",
        "",
        "The evaluation contains 12 manually reviewed queries. "
        "This small sample may not represent all repository-navigation tasks.",
        "",
        "### Repository validity",
        "",
        "Only one pinned Python repository, psf/requests, is evaluated. "
        "The findings cannot automatically generalize to other repositories "
        "or programming languages.",
        "",
        "### Construct validity",
        "",
        "File retrieval metrics do not measure code generation correctness, "
        "patch quality, task completion, or developer productivity.",
        "",
        "### Internal validity",
        "",
        "Results depend on the lexical scoring method and import graph "
        "construction. Synthetic edge dropout is only one model of graph noise.",
        "",
        "### Parameter sensitivity",
        "",
        "Only the listed boost values and dropout rates were tested. "
        "These experiments do not identify a universally optimal parameter.",
        "",
        "### Statistical validity",
        "",
        "The sample is small. The reported metrics are descriptive and "
        "should not be interpreted as statistically significant evidence.",
        "",
        "## 7. Interpretation",
        "",
        "The results describe this repository and query set only. "
        "They do not establish general superiority of graph-guided retrieval. "
        "The lexical baseline remains the comparison reference.",
        "",
        "## 8. Reproducibility settings",
        "",
        f"- Boost values: {list(BOOST_VALUES)}",
        f"- Dropout rates: {list(DROPOUT_RATES)}",
        f"- Seeds: {list(SEEDS)}",
        f"- Top-K: {TOP_K}",
        "",
    ]

    return "\n".join(lines)


def main():
    outputs = (CSV_OUT, JSON_OUT, REPORT_OUT)

    existing = [str(p) for p in outputs if p.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing outputs: " + ", ".join(existing)
        )

    if not REPO.is_dir():
        raise FileNotFoundError(f"Repository not found: {REPO}")

    commit = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        text=True,
    ).strip()

    if commit != EXPECTED_COMMIT:
        raise RuntimeError(
            f"Repository commit mismatch: expected {EXPECTED_COMMIT}, "
            f"found {commit}"
        )

    queries = load_dataset()

    files = collect_python_files(REPO)
    texts = normalize_texts(REPO, files)
    graph = build_import_graph(REPO, texts)

    # Some indexed files may have no import-graph entry.
    # Add an empty adjacency set for every indexed source file.
    graph = complete_graph_nodes(graph, texts)

    resolve_targets(queries, texts)

    baseline_rows = evaluate(
        queries, texts, graph, method="baseline"
    )
    baseline = aggregate(baseline_rows)

    boost_results = run_boost_experiments(queries, texts, graph)
    dropout_results = run_dropout_experiments(queries, texts, graph)
    stability = run_stability(queries, texts, graph)

    all_rows = list(baseline_rows)

    for boost in BOOST_VALUES:
        all_rows.extend(
            evaluate(
                queries, texts, graph,
                method="graph", boost=boost
            )
        )

    for rate in DROPOUT_RATES:
        for seed in SEEDS:
            changed_graph = perturb_graph(graph, rate, seed)
            all_rows.extend(
                evaluate(
                    queries, texts, changed_graph,
                    method="graph",
                    boost=0.10,
                    dropout_rate=rate,
                    seed=seed,
                )
            )

    summary = {
        "step": 11,
        "experiment": "Robustness Analysis",
        "repository": "psf/requests",
        "repository_commit": commit,
        "query_count": len(queries),
        "python_files_indexed": len(texts),
        "graph_node_count": len(graph),
        "baseline": baseline,
        "boost_sensitivity": boost_results,
        "edge_dropout": dropout_results,
        "ranking_stability": stability,
        "parameters": {
            "boost_values": list(BOOST_VALUES),
            "dropout_rates": list(DROPOUT_RATES),
            "seeds": list(SEEDS),
            "top_k": TOP_K,
        },
        "claim_scope": (
            "Exploratory descriptive evaluation on one repository "
            "and 12 manually reviewed queries."
        ),
    }

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "experiment", "query_id", "boost", "dropout_rate",
        "seed", "target_rank", "top1", "recall_at_5", "mrr",
    ]

    with CSV_OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    JSON_OUT.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    REPORT_OUT.write_text(
        create_report(
            baseline, boost_results, dropout_results, stability
        ),
        encoding="utf-8",
    )

    print("STEP 11 ROBUSTNESS ANALYSIS: SUCCESS")
    print(f"Repository commit: {commit}")
    print(f"Queries: {len(queries)}")
    print(f"Python files: {len(texts)}")
    print(f"Graph nodes: {len(graph)}")
    print("\nBaseline:")
    print(json.dumps(baseline, indent=2))
    print("\nRanking stability:")
    print(json.dumps(stability, indent=2))
    print("\nCreated:")
    print(CSV_OUT)
    print(JSON_OUT)
    print(REPORT_OUT)


if __name__ == "__main__":
    main()
