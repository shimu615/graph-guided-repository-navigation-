import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from evaluate_independent_queries import (
    ROOT,
    REPO,
    DATASET,
    GRAPH_BOOST,
    TOP_K,
    read_queries,
    get_rank,
    reciprocal_rank,
)

from retrieval_core import (
    collect_python_files,
    normalize_texts,
    build_import_graph,
    rank_baseline,
    rank_graph,
)


CONFIG_PATH = ROOT / "configs" / "step7-experiment-config.json"
OUTPUT_DIR = ROOT / "results"

OUTPUT_FILES = {
    "csv": OUTPUT_DIR / "step8-query-results.csv",
    "json": OUTPUT_DIR / "step8-experiment-summary.json",
    "manifest": OUTPUT_DIR / "step8-reproducibility-manifest.json",
    "report": ROOT / "notes" / "step8-experiment-report.md",
}


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(args, cwd):
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def verify_inputs():
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Missing config: {CONFIG_PATH}")

    if not DATASET.is_file():
        raise FileNotFoundError(f"Missing dataset: {DATASET}")

    if not REPO.is_dir():
        raise FileNotFoundError(f"Missing repository: {REPO}")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))

    expected_hash = config["dataset"]["expected_sha256"]
    actual_hash = sha256_file(DATASET)

    if actual_hash != expected_hash:
        raise ValueError(
            "Dataset SHA256 mismatch: "
            f"expected={expected_hash}, actual={actual_hash}"
        )

    expected_commit = config["repository"]["expected_commit"]
    actual_commit = git_output(["rev-parse", "HEAD"], REPO)

    if actual_commit != expected_commit:
        raise ValueError(
            "Repository commit mismatch: "
            f"expected={expected_commit}, actual={actual_commit}"
        )

    if float(config["methods"]["proposed"]["graph_boost"]) != GRAPH_BOOST:
        raise ValueError("Graph boost differs from the Step 7 config.")

    if int(config["ranking"]["top_k"]) != TOP_K:
        raise ValueError("Top-K differs from the Step 7 config.")

    rows = read_queries()

    expected_ids = config["dataset"]["expected_query_ids"]
    actual_ids = [row["query_id"].strip() for row in rows]

    if actual_ids != expected_ids:
        raise ValueError(
            "Query IDs/order differ from the Step 7 configuration."
        )

    return config, rows, actual_hash, actual_commit


def calculate_metrics(records, prefix):
    count = len(records)

    if count == 0:
        raise ValueError("Cannot calculate metrics for zero queries.")

    return {
        f"{prefix}_top1_accuracy": sum(
            row[f"{prefix}_rank"] == 1 for row in records
        ) / count,
        f"{prefix}_recall_at_5": sum(
            row[f"{prefix}_rank"] is not None
            and row[f"{prefix}_rank"] <= TOP_K
            for row in records
        ) / count,
        f"{prefix}_mrr": sum(
            row[f"{prefix}_mrr"] for row in records
        ) / count,
    }


def run_experiment(rows):
    files = collect_python_files(REPO)
    texts = normalize_texts(REPO, files)

    if not texts:
        raise ValueError("No Python source files were indexed.")

    graph = build_import_graph(REPO, texts)

    if set(graph) != set(texts):
        raise ValueError("Import graph nodes do not match indexed files.")

    records = []

    for row in rows:
        query_id = row["query_id"].strip()
        query = row["query"].strip()
        target = row["proposed_target"].strip().replace("\\", "/")

        if target not in texts:
            raise ValueError(
                f"Target file is not indexed for {query_id}: {target}"
            )

        baseline_ranked, baseline_scores = rank_baseline(query, texts)

        graph_ranked, graph_scores, direct_scores = rank_graph(
            query,
            texts,
            graph,
            boost=GRAPH_BOOST,
        )

        baseline_position = get_rank(baseline_ranked, target)
        graph_position = get_rank(graph_ranked, target)

        records.append({
            "query_id": query_id,
            "query": query,
            "verified_target": target,
            "review_status": row["review_status"],
            "baseline_rank": baseline_position,
            "graph_rank": graph_position,
            "baseline_top1": baseline_position == 1,
            "graph_top1": graph_position == 1,
            "baseline_top5": (
                baseline_position is not None
                and baseline_position <= TOP_K
            ),
            "graph_top5": (
                graph_position is not None
                and graph_position <= TOP_K
            ),
            "baseline_mrr": reciprocal_rank(baseline_position),
            "graph_mrr": reciprocal_rank(graph_position),
            "baseline_target_score": baseline_scores[target],
            "graph_target_score": graph_scores[target],
            "direct_target_score": direct_scores[target],
            "baseline_top5_files": json.dumps(
                baseline_ranked[:TOP_K]
            ),
            "graph_top5_files": json.dumps(
                graph_ranked[:TOP_K]
            ),
        })

    return records, len(texts), sum(len(v) for v in graph.values())


def write_csv(path, records):
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(records[0].keys()),
        )
        writer.writeheader()
        writer.writerows(records)


def write_report(path, summary):
    lines = [
        "# Step 8 — Reproducible Experiment Report",
        "",
        f"- Run date (UTC): {summary['run_timestamp_utc']}",
        f"- Repository: {summary['repository']}",
        f"- Repository commit: `{summary['repository_commit']}`",
        f"- Query count: {summary['query_count']}",
        f"- Python files indexed: {summary['python_files_indexed']}",
        f"- Directed import-graph adjacency entries: "
        f"{summary['import_graph_edges_directed']}",
        f"- Graph boost: {summary['graph_boost']}",
        f"- Top-K: {summary['top_k']}",
        "",
        "## Results",
        "",
        "| Metric | Lexical baseline | Graph-augmented |",
        "|---|---:|---:|",
        f"| Top-1 Accuracy | "
        f"{summary['baseline_top1_accuracy']:.4f} | "
        f"{summary['graph_top1_accuracy']:.4f} |",
        f"| Recall@5 | "
        f"{summary['baseline_recall_at_5']:.4f} | "
        f"{summary['graph_recall_at_5']:.4f} |",
        f"| MRR | "
        f"{summary['baseline_mrr']:.4f} | "
        f"{summary['graph_mrr']:.4f} |",
        "",
        "## Interpretation and limitations",
        "",
        "This is an exploratory evaluation on one Python repository "
        "and twelve manually reviewed queries. It does not establish "
        "general superiority. No parameter tuning was performed on "
        "the evaluation query set.",
        "",
        "The graph method uses the existing one-hop import-neighbor "
        "ranking implementation with the pre-fixed boost. The lexical "
        "baseline and graph method use the same repository snapshot, "
        "query set, target labels, and indexed source files.",
        "",
        "## Output files",
        "",
        "- `results/step8-query-results.csv`",
        "- `results/step8-experiment-summary.json`",
        "- `results/step8-reproducibility-manifest.json`",
        "- `notes/step8-experiment-report.md`",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "notes").mkdir(parents=True, exist_ok=True)

    # Protect earlier results and avoid silently overwriting Step 8 files.
    existing = [str(path) for path in OUTPUT_FILES.values() if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing Step 8 output(s): "
            + ", ".join(existing)
        )

    config, rows, dataset_hash, repo_commit = verify_inputs()

    records, file_count, graph_edges = run_experiment(rows)

    baseline_metrics = calculate_metrics(records, "baseline")
    graph_metrics = calculate_metrics(records, "graph")

    timestamp = datetime.now(timezone.utc).isoformat()

    summary = {
        "experiment_id": config["experiment_id"],
        "project_title": config["project_title"],
        "run_timestamp_utc": timestamp,
        "repository": config["repository"]["name"],
        "repository_commit": repo_commit,
        "dataset_path": str(DATASET.relative_to(ROOT)),
        "dataset_sha256": dataset_hash,
        "query_count": len(records),
        "python_files_indexed": file_count,
        "import_graph_edges_directed": graph_edges,
        "graph_boost": GRAPH_BOOST,
        "top_k": TOP_K,
        **baseline_metrics,
        **graph_metrics,
        "limitations": config["limitations"],
        "warning": (
            "Exploratory evaluation on one repository and twelve "
            "manually reviewed queries. Results do not establish "
            "general superiority."
        ),
    }

    manifest = {
        "run_timestamp_utc": timestamp,
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "working_project_root": str(ROOT),
        "repository": config["repository"]["name"],
        "repository_path": str(REPO.relative_to(ROOT)),
        "repository_commit": repo_commit,
        "dataset_path": str(DATASET.relative_to(ROOT)),
        "dataset_sha256": dataset_hash,
        "config_path": str(CONFIG_PATH.relative_to(ROOT)),
        "config_sha256": sha256_file(CONFIG_PATH),
        "query_count": len(records),
        "python_files_indexed": file_count,
        "graph_boost": GRAPH_BOOST,
        "top_k": TOP_K,
        "ranking_tie_breaking": config["ranking"]["tie_breaking"],
        "method_implementation": {
            "baseline": "retrieval_core.rank_baseline",
            "proposed": "retrieval_core.rank_graph",
            "graph_construction": "retrieval_core.build_import_graph",
        },
        "note": (
            "This manifest records the inputs and runtime environment. "
            "It does not claim bitwise reproducibility across all platforms."
        ),
    }

    write_csv(OUTPUT_FILES["csv"], records)
    OUTPUT_FILES["json"].write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    OUTPUT_FILES["manifest"].write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    write_report(OUTPUT_FILES["report"], summary)

    print("\n========== STEP 8 EXPERIMENT SUMMARY ==========")
    print(json.dumps(summary, indent=2))

    print("\n========== CREATED OUTPUTS ==========")
    for name, path in OUTPUT_FILES.items():
        print(f"{name}: {path}")

    print("\nSTEP 8 EXPERIMENT EXECUTION: SUCCESS")


if __name__ == "__main__":
    main()

