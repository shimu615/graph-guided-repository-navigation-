import ast
import csv
import json
import re
import sys
import time
from pathlib import Path
from collections import defaultdict

PROJECT = Path(__file__).resolve().parent.parent
DATASET = PROJECT / "results" / "real-repository-query-review.csv"
REPO_ROOT = PROJECT / "external" / "requests"
SOURCE_ROOT = REPO_ROOT / "src" / "requests"
RESULTS = PROJECT / "results"

STOPWORDS = {
    "a", "an", "the", "to", "of", "for", "and", "or", "in", "on",
    "with", "by", "is", "are", "be", "into", "from", "it", "this",
    "that", "as", "at", "or", "not", "if", "all", "over", "default",
    "returns", "return", "request", "requests", "string", "object"
}


def tokenize(text):
    words = re.findall(r"[a-zA-Z_][a-zA-Z_0-9]*", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def load_reviewed_queries():
    with DATASET.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if len(rows) != 20:
        raise ValueError(f"Expected 20 reviewed rows; found {len(rows)}.")

    pending = [
        r.get("candidate_id", "")
        for r in rows
        if r.get("review_status", "").strip().upper() != "VERIFIED"
    ]
    if pending:
        raise ValueError(f"Unreviewed rows remain: {pending}")

    for row in rows:
        target = (row.get("verified_target") or "").strip().replace("\\", "/")
        if not target:
            raise ValueError(
                f"{row.get('candidate_id')} has an empty verified_target."
            )

        target_path = REPO_ROOT / target
        if not target_path.is_file():
            raise FileNotFoundError(
                f"Target file does not exist: {target_path}"
            )

        row["verified_target"] = target

    return rows


def discover_python_files():
    files = sorted(SOURCE_ROOT.rglob("*.py"))
    if not files:
        raise RuntimeError(f"No Python files found under {SOURCE_ROOT}")

    rel_paths = {}
    contents = {}
    module_to_path = {}

    for path in files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        rel_paths[path] = rel
        contents[path] = path.read_text(encoding="utf-8", errors="replace")

        # Example: requests.adapters
        parts = list(path.relative_to(REPO_ROOT / "src").with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        module_to_path[".".join(parts)] = path

    return files, rel_paths, contents, module_to_path


def build_import_graph(files, module_to_path):
    from real_repository_graph import build_import_graph as improved_builder
    return improved_builder(files, module_to_path)

def score_query(query, files, contents):
    terms = set(tokenize(query))
    scores = {}

    for path in files:
        source_terms = set(tokenize(contents[path]))
        if not terms:
            score = 0.0
        else:
            score = len(terms & source_terms) / len(terms)
        scores[path] = score

    # Deterministic tie-breaking by repository-relative path.
    return sorted(files, key=lambda p: (-scores[p], str(p))), scores


def rank_graph_guided(files, base_scores, graph):
    ranked = []

    for path in files:
        neighbors = graph.get(path, set())
        neighbor_score = max(
            (base_scores.get(n, 0.0) for n in neighbors),
            default=0.0
        )
        graph_score = base_scores[path] + 0.25 * neighbor_score
        ranked.append((path, graph_score))

    ranked.sort(key=lambda item: (-item[1], str(item[0])))
    return [path for path, _ in ranked]


def metric_summary(results, method):
    total = len(results)
    top1 = sum(r[f"{method}_rank"] == 1 for r in results) / total
    recall5 = sum(
        r[f"{method}_rank"] is not None and r[f"{method}_rank"] <= 5
        for r in results
    ) / total
    mrr = sum(
        1 / r[f"{method}_rank"] if r[f"{method}_rank"] else 0
        for r in results
    ) / total

    runtimes = [r[f"{method}_runtime_ms"] for r in results]

    return {
        "method": method,
        "query_count": total,
        "top1_accuracy": round(top1, 4),
        "recall_at_5": round(recall5, 4),
        "mean_reciprocal_rank": round(mrr, 4),
        "mean_query_runtime_ms": round(sum(runtimes) / total, 4),
        "runtime_note": (
            "Single-process prototype measurements; not a reliable "
            "benchmark of speed."
        )
    }


def main():
    RESULTS.mkdir(exist_ok=True)

    rows = load_reviewed_queries()
    files, rel_paths, contents, module_to_path = discover_python_files()
    graph = build_import_graph(files, module_to_path)

    evaluation_rows = []

    for row in rows:
        query = row["query"].strip()
        target_rel = row["verified_target"]
        target_path = REPO_ROOT / target_rel

        start = time.perf_counter()
        baseline_ranked, baseline_scores = score_query(
            query, files, contents
        )
        baseline_runtime = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        graph_ranked = rank_graph_guided(
            files, baseline_scores, graph
        )
        graph_runtime = (time.perf_counter() - start) * 1000

        try:
            baseline_rank = baseline_ranked.index(target_path) + 1
        except ValueError:
            baseline_rank = None

        try:
            graph_rank = graph_ranked.index(target_path) + 1
        except ValueError:
            graph_rank = None

        evaluation_rows.append({
            "candidate_id": row["candidate_id"],
            "query": query,
            "verified_target": target_rel,
            "baseline_rank": baseline_rank,
            "baseline_top1": baseline_rank == 1,
            "baseline_recall_at_5": (
                baseline_rank is not None and baseline_rank <= 5
            ),
            "baseline_runtime_ms": round(baseline_runtime, 6),
            "baseline_top5": " | ".join(
                rel_paths[p] for p in baseline_ranked[:5]
            ),
            "graph_rank": graph_rank,
            "graph_top1": graph_rank == 1,
            "graph_recall_at_5": (
                graph_rank is not None and graph_rank <= 5
            ),
            "graph_runtime_ms": round(graph_runtime, 6),
            "graph_top5": " | ".join(
                rel_paths[p] for p in graph_ranked[:5]
            )
        })

    csv_path = RESULTS / "real-repository-evaluation.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=evaluation_rows[0].keys())
        writer.writeheader()
        writer.writerows(evaluation_rows)

    summaries = [
        metric_summary(evaluation_rows, "baseline"),
        metric_summary(evaluation_rows, "graph")
    ]

    summary = {
        "project": "Graph-Guided Repository Navigation for Coding Agents",
        "repository": "psf/requests",
        "dataset_rows": len(rows),
        "python_files_indexed": len(files),
        "import_graph_edges": sum(len(v) for v in graph.values()) // 2,
        "evaluation_type": "exploratory prototype evaluation",
        "method_note": (
            "This script implements a separate keyword-overlap baseline "
            "and an import-neighbor score boost. It does not call the "
            "existing baseline_search.py or graph_search.py implementations."
        ),
        "validity_warning": (
            "Queries were selected from repository source descriptions, so "
            "lexical overlap may be inflated. Results are exploratory and "
            "do not establish generalization or superiority."
        ),
        "metrics": summaries
    }

    summary_path = RESULTS / "real-repository-evaluation-summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    errors = [
        r for r in evaluation_rows
        if r["baseline_rank"] != 1 or r["graph_rank"] != 1
    ]
    error_path = RESULTS / "real-repository-error-analysis.csv"
    with error_path.open("w", encoding="utf-8-sig", newline="") as f:
        if errors:
            writer = csv.DictWriter(f, fieldnames=errors[0].keys())
            writer.writeheader()
            writer.writerows(errors)
        else:
            f.write("No top-1 errors for either method.\n")

    print("\n=== REAL REPOSITORY EVALUATION ===")
    print(f"Reviewed queries: {len(rows)}")
    print(f"Python files indexed: {len(files)}")
    print(f"Import graph edges: {summary['import_graph_edges']}")
    print("\nMetrics:")
    for item in summaries:
        print(json.dumps(item, indent=2))

    print("\nSaved:")
    print(csv_path)
    print(summary_path)
    print(error_path)
    print("\nWARNING: Exploratory results only; read the validity notes.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

