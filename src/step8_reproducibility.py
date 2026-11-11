from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RESULTS = ROOT / "results"
NOTES = ROOT / "notes"
CONFIG_PATH = ROOT / "configs" / "step7-experiment-config.json"
DATASET_PATH = RESULTS / "independent-query-set.csv"
REPOSITORY_PATH = ROOT / "external" / "requests"

EXPECTED_COMMIT = "611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60"
EXPECTED_DATASET_SHA256 = (
    "16eed990ed42c011b1d751366f7982357a4a5dbef641cf68a21a7fb954e198f3"
)
EXPECTED_QUERY_COUNT = 12
EXPECTED_GRAPH_BOOST = 0.10
TOP_K = 5

sys.path.insert(0, str(SRC))

from evaluate_independent_queries import (
    read_queries,
    build_index,
    rank_query,
)

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def git_output(args, cwd):
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()

def find_config_value(obj, wanted_key):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == wanted_key:
                return value
            found = find_config_value(value, wanted_key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_config_value(value, wanted_key)
            if found is not None:
                return found
    return None

def reciprocal(rank):
    return 1.0 / rank if rank else 0.0

def mean(values):
    return sum(values) / len(values) if values else 0.0

def main():
    RESULTS.mkdir(exist_ok=True)
    NOTES.mkdir(exist_ok=True)

    print("\n========== STEP 8 VALIDATION ==========")

    # 1. Configuration and frozen dataset checks
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    dataset_hash = sha256(DATASET_PATH)

    if dataset_hash != EXPECTED_DATASET_SHA256:
        raise RuntimeError(
            f"Dataset SHA-256 mismatch: {dataset_hash}"
        )

    configured_boost = find_config_value(config, "graph_boost")
    if configured_boost is None:
        raise RuntimeError(
            "graph_boost was not found in Step 7 configuration."
        )

    if float(configured_boost) != EXPECTED_GRAPH_BOOST:
        raise RuntimeError(
            f"Unexpected graph boost in config: {configured_boost}"
        )

    if not REPOSITORY_PATH.is_dir():
        raise RuntimeError("Pinned external repository is missing.")

    actual_commit = git_output(
        ["rev-parse", "HEAD"], REPOSITORY_PATH
    )

    if actual_commit != EXPECTED_COMMIT:
        raise RuntimeError(
            f"Repository commit mismatch: {actual_commit}"
        )

    dirty_status = git_output(
        ["status", "--porcelain"], REPOSITORY_PATH
    )
    if dirty_status:
        raise RuntimeError(
            "Pinned repository has local modifications. "
            "Restore a clean snapshot before running Step 8."
        )

    # 2. Verify implementation uses the frozen one-hop boost.
    evaluator_source = (
        SRC / "evaluate_independent_queries.py"
    ).read_text(encoding="utf-8-sig")

    if "0.10 * source_score" not in evaluator_source:
        raise RuntimeError(
            "Expected graph scoring expression was not found. "
            "Do not silently substitute a different method."
        )

    # 3. Use the existing evaluator's own data/index/ranking functions.
    rows = read_queries()
    if len(rows) != EXPECTED_QUERY_COUNT:
        raise RuntimeError(
            f"Expected 12 queries, found {len(rows)}."
        )

    ids = [row["query_id"] for row in rows]
    if len(set(ids)) != EXPECTED_QUERY_COUNT:
        raise RuntimeError("Duplicate query IDs found.")

    texts, imports = build_index()
    if not texts:
        raise RuntimeError("No repository Python files were indexed.")

    print(f"[PASS] Dataset SHA-256: {dataset_hash}")
    print(f"[PASS] Repository commit: {actual_commit}")
    print(f"[PASS] Graph boost: {configured_boost}")
    print(f"[PASS] Query count: {len(rows)}")
    print(f"[PASS] Python files indexed: {len(texts)}")

    # 4. Execute both methods on the same indexed snapshot.
    rankings = []

    for row in rows:
        query_id = row["query_id"]
        query = row["query"]
        target = (
            row["proposed_target"]
            .strip()
            .replace("\\", "/")
        )

        if target not in texts:
            raise RuntimeError(
                f"Ground-truth target not indexed: {query_id}: {target}"
            )

        start = time.perf_counter()
        baseline, graph, baseline_rank, graph_rank = rank_query(
            query, texts, imports, target
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        rankings.append({
            "query_id": query_id,
            "query": query,
            "verified_target": target,
            "baseline_rank": baseline_rank,
            "graph_rank": graph_rank,
            "baseline_top1": baseline_rank == 1,
            "graph_top1": graph_rank == 1,
            "baseline_recall_at_5": target in baseline[:TOP_K],
            "graph_recall_at_5": target in graph[:TOP_K],
            "baseline_reciprocal_rank": reciprocal(baseline_rank),
            "graph_reciprocal_rank": reciprocal(graph_rank),
            "baseline_top5_files": " | ".join(baseline[:TOP_K]),
            "graph_top5_files": " | ".join(graph[:TOP_K]),
            "combined_ranking_runtime_ms": round(elapsed_ms, 6),
        })

    n = len(rankings)

    baseline_top1 = mean([
        float(row["baseline_top1"]) for row in rankings
    ])
    graph_top1 = mean([
        float(row["graph_top1"]) for row in rankings
    ])

    baseline_recall = mean([
        float(row["baseline_recall_at_5"]) for row in rankings
    ])
    graph_recall = mean([
        float(row["graph_recall_at_5"]) for row in rankings
    ])

    baseline_mrr = mean([
        row["baseline_reciprocal_rank"] for row in rankings
    ])
    graph_mrr = mean([
        row["graph_reciprocal_rank"] for row in rankings
    ])

    improved = sum(
        row["graph_rank"] < row["baseline_rank"]
        for row in rankings
    )
    regressed = sum(
        row["graph_rank"] > row["baseline_rank"]
        for row in rankings
    )
    unchanged = n - improved - regressed

    # 5. Save raw query-level rankings.
    rankings_path = RESULTS / "step8-query-rankings.csv"
    with rankings_path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rankings[0].keys())
        )
        writer.writeheader()
        writer.writerows(rankings)

    # 6. Save aggregate summary.
    summary = {
        "step": 8,
        "project": "Graph-Guided Repository Navigation for Coding Agents",
        "execution_timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "repository": "psf/requests",
        "repository_commit": actual_commit,
        "repository_worktree_clean": True,
        "dataset_path": "results/independent-query-set.csv",
        "dataset_sha256": dataset_hash,
        "query_count": n,
        "python_files_indexed": len(texts),
        "import_graph_adjacency_entries": sum(
            len(neighbors) for neighbors in imports.values()
        ),
        "graph_boost": EXPECTED_GRAPH_BOOST,
        "top_k": TOP_K,
        "tie_breaking": "alphabetical relative file path",
        "metrics": {
            "baseline_top1_accuracy": baseline_top1,
            "graph_top1_accuracy": graph_top1,
            "baseline_recall_at_5": baseline_recall,
            "graph_recall_at_5": graph_recall,
            "baseline_mrr": baseline_mrr,
            "graph_mrr": graph_mrr,
            "graph_minus_baseline_top1": graph_top1 - baseline_top1,
            "graph_minus_baseline_recall_at_5": (
                graph_recall - baseline_recall
            ),
            "graph_minus_baseline_mrr": graph_mrr - baseline_mrr,
        },
        "query_rank_changes": {
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
        },
        "method": (
            "Existing evaluator functions read_queries(), build_index(), "
            "and rank_query() were reused. Baseline and graph rankings "
            "were generated from the same repository index."
        ),
        "runtime_note": (
            "Combined per-query call timing; not a controlled speed benchmark "
            "and not a separate latency comparison."
        ),
        "limitations": [
            "One repository and twelve manually reviewed queries.",
            "Exploratory evaluation only.",
            "No statistical significance claim.",
            "No parameter tuning on the evaluation query set.",
            "The graph method is not assumed to outperform the baseline."
        ]
    }

    summary_path = RESULTS / "step8-reproducibility-summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8"
    )

    # 7. Save environment manifest.
    try:
        pip_freeze = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
    except Exception:
        pip_freeze = ["Could not retrieve pip freeze output."]

    manifest = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "working_directory": str(ROOT),
        "project_git_commit": git_output(
            ["rev-parse", "HEAD"], ROOT
        ),
        "repository": "psf/requests",
        "repository_commit": actual_commit,
        "dataset_sha256": dataset_hash,
        "configuration_sha256": sha256(CONFIG_PATH),
        "pip_freeze": pip_freeze,
        "execution_script": "src/step8_reproducibility.py",
        "commands": [
            "python -m py_compile .\\src\\step8_reproducibility.py",
            "python .\\src\\step8_reproducibility.py",
            "python -m compileall -q .\\src .\\tests",
            "python -m pytest -q"
        ]
    }

    manifest_path = RESULTS / "step8-environment-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    # 8. Human-readable report.
    report = f"""# Step 8 — Experimental Execution & Reproducibility

## Execution status

Completed execution using the existing evaluator functions.

- Repository: psf/requests
- Pinned commit: `{actual_commit}`
- Dataset: `results/independent-query-set.csv`
- Dataset SHA-256: `{dataset_hash}`
- Query count: {n}
- Indexed Python files: {len(texts)}
- Graph boost: {EXPECTED_GRAPH_BOOST}
- Top-k: {TOP_K}
- Tie breaking: alphabetical relative file path

## Results

| Metric | Baseline | Graph |
|---|---:|---:|
| Top-1 Accuracy | {baseline_top1:.6f} | {graph_top1:.6f} |
| Recall@5 | {baseline_recall:.6f} | {graph_recall:.6f} |
| MRR | {baseline_mrr:.6f} | {graph_mrr:.6f} |

## Query rank changes

- Improved: {improved}
- Regressed: {regressed}
- Unchanged: {unchanged}

## Reproducibility artifacts

- `results/step8-query-rankings.csv`
- `results/step8-reproducibility-summary.json`
- `results/step8-environment-manifest.json`

## Interpretation

This is an exploratory comparison on one repository and twelve queries.
It does not establish general superiority or statistical significance.
The graph boost was kept fixed at 0.10; no tuning was performed on these
evaluation queries.

Per-query runtime is recorded only as combined call timing. It is not
a controlled performance benchmark.

## Next validation

Run the project compilation check and full test suite after this script.
"""

    report_path = NOTES / "step8-execution-report.md"
    report_path.write_text(report, encoding="utf-8")

    print("\n========== STEP 8 EXPERIMENT SUMMARY ==========")
    print(json.dumps(summary, indent=2))
    print("\nSaved:")
    print(rankings_path)
    print(summary_path)
    print(manifest_path)
    print(report_path)
    print("\nSTEP 8 EXPERIMENT EXECUTION COMPLETED.")
    print("Project test validation is still required.")

if __name__ == "__main__":
    main()
