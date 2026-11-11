from pathlib import Path
from datetime import datetime
import csv
import json
import shutil
import sys
import traceback
import importlib.util

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
RESULTS = ROOT / "results"
NOTES = ROOT / "notes"

RESULTS.mkdir(exist_ok=True)
NOTES.mkdir(exist_ok=True)

EVALUATOR = SRC / "evaluate_independent_queries.py"
DATASET = RESULTS / "independent-query-set.csv"

stamp = datetime.now().strftime("%Y-%m-%d")
run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

report = {
    "run_date": stamp,
    "run_id": run_id,
    "project": "Graph-Guided Repository Navigation for Coding Agents",
    "repository": "psf/requests",
    "tests": {},
    "limitations": [
        "Results are limited to the current repository and query dataset.",
        "Synthetic graph ablations do not establish general superiority.",
        "A test is marked PASS only when its check actually succeeds."
    ]
}

def status(name, passed, details):
    report["tests"][name] = {
        "status": "PASS" if passed else "FAIL",
        "details": details
    }
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {details}")

def load_module(path, name):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def reciprocal(rank):
    try:
        rank = int(rank)
        return 1.0 / rank if rank > 0 else 0.0
    except (TypeError, ValueError):
        return 0.0

def mrr(values):
    return sum(reciprocal(v) for v in values) / len(values) if values else 0.0

def top1(values):
    return sum(1 for v in values if str(v) == "1") / len(values) if values else 0.0

def edge_count(graph):
    if not isinstance(graph, dict):
        return None
    total = 0
    for value in graph.values():
        if isinstance(value, (list, tuple, set)):
            total += len(value)
        elif isinstance(value, dict):
            total += len(value)
        elif value is not None:
            try:
                total += len(value)
            except TypeError:
                pass
    return total

def empty_graph_like(graph):
    if not isinstance(graph, dict):
        raise TypeError(f"Expected import graph dict, got {type(graph).__name__}")
    return {key: type(value)() if isinstance(value, (list, set, tuple, dict)) else []
            for key, value in graph.items()}

def remove_half_edges(graph):
    if not isinstance(graph, dict):
        raise TypeError(f"Expected import graph dict, got {type(graph).__name__}")
    changed = {}
    for key, value in graph.items():
        if isinstance(value, list):
            changed[key] = value[::2]
        elif isinstance(value, tuple):
            changed[key] = value[::2]
        elif isinstance(value, set):
            ordered = sorted(value, key=str)
            changed[key] = set(ordered[::2])
        elif isinstance(value, dict):
            ordered = sorted(value.items(), key=lambda item: str(item[0]))
            changed[key] = dict(ordered[::2])
        elif value is None:
            changed[key] = []
        else:
            try:
                changed[key] = list(value)[::2]
            except TypeError:
                changed[key] = []
    return changed

def extract_ranks(result):
    # Existing evaluator has previously been used as:
    # baseline_rank, graph_rank = rank_query(...)
    if isinstance(result, (tuple, list)) and len(result) >= 2:
        return result[0], result[1]
    if isinstance(result, dict):
        baseline = result.get("baseline_rank")
        graph = result.get("graph_rank")
        if baseline is not None and graph is not None:
            return baseline, graph
    raise TypeError(
        "Unsupported rank_query return format. "
        f"Received {type(result).__name__}: {str(result)[:300]}"
    )

def normalise_rank(rank):
    # Accept a rank integer or a ranked list of paths.
    if isinstance(rank, int):
        return rank
    if isinstance(rank, str) and rank.isdigit():
        return int(rank)
    if isinstance(rank, (list, tuple)):
        return len(rank) if len(rank) else 0
    raise TypeError(f"Cannot interpret rank value: {rank!r}")

def run_evaluation(evaluator, queries, texts, graph, variant):
    rows = []
    for q in queries:
        query = q.get("query", "")
        target = q.get("target", "")
        qid = q.get("query_id", q.get("id", "UNKNOWN"))
        baseline_rank, graph_rank = extract_ranks(
            evaluator.rank_query(query, texts, graph, target)
        )
        baseline_rank = normalise_rank(baseline_rank)
        graph_rank = normalise_rank(graph_rank)
        rows.append({
            "query_id": qid,
            "variant": variant,
            "query": query,
            "target": target,
            "baseline_rank": baseline_rank,
            "graph_rank": graph_rank,
            "baseline_top1": int(baseline_rank == 1),
            "graph_top1": int(graph_rank == 1),
            "baseline_reciprocal_rank": reciprocal(baseline_rank),
            "graph_reciprocal_rank": reciprocal(graph_rank)
        })
    return rows

def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def main():
    print("=" * 65)
    print("ROBUSTNESS TESTS — SAFE RUN")
    print(f"Project: {ROOT}")
    print(f"Run date: {stamp}")
    print("=" * 65)

    # Basic preflight
    required = [EVALUATOR, DATASET, ROOT / "external" / "requests"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        status("Preflight", False, f"Missing required paths: {missing}")
        raise SystemExit(2)

    status("Preflight", True, "Evaluator, dataset and external repository exist")

    try:
        evaluator = load_module(EVALUATOR, "independent_evaluator_for_robustness")
        queries = evaluator.read_queries()
        texts, imports = evaluator.build_index()
        status(
            "Dataset and index",
            len(queries) == 12 and isinstance(texts, dict) and isinstance(imports, dict),
            f"queries={len(queries)}, indexed_files={len(texts)}, "
            f"graph_nodes={len(imports)}, graph_edges={edge_count(imports)}"
        )
    except Exception as exc:
        status("Dataset and index", False, f"{type(exc).__name__}: {exc}")
        report["fatal_error"] = traceback.format_exc()
        save_report(report)
        raise SystemExit(2)

    # TEST A: validate the existing wording-robustness results.
    try:
        a_csv = RESULTS / "oct30-query-wording-robustness.csv"
        a_json = RESULTS / "oct30-query-wording-robustness-summary.json"
        if not a_csv.exists():
            a_csv = RESULTS / "nov03-query-wording-robustness.csv"
        if not a_json.exists():
            a_json = RESULTS / "nov03-query-wording-robustness-summary.json"

        a_rows = read_csv(a_csv)
        counts = {}
        for row in a_rows:
            counts[row.get("variant", "")] = counts.get(row.get("variant", ""), 0) + 1

        valid = (
            len(a_rows) == 36
            and counts.get("original") == 12
            and counts.get("wording_1") == 12
            and counts.get("wording_2") == 12
            and all(row.get("baseline_rank") and row.get("graph_rank") for row in a_rows)
        )
        status("A — Existing query wording results", valid,
               f"rows={len(a_rows)}, variant_counts={counts}, file={a_csv.name}")
    except Exception as exc:
        status("A — Existing query wording results", False,
               f"{type(exc).__name__}: {exc}")

    # TEST B: remove all graph connections and rerun the same queries.
    try:
        disconnected = empty_graph_like(imports)
        b_rows = run_evaluation(evaluator, queries, texts, disconnected, "no_graph_edges")
        b_path = RESULTS / f"robustness_B_no_graph_edges_{run_id}.csv"
        write_csv(b_path, b_rows)
        status("B — Missing graph connections", len(b_rows) == len(queries),
               f"evaluated={len(b_rows)}, output={b_path.name}, "
               f"remaining_edges={edge_count(disconnected)}")
    except Exception as exc:
        status("B — Missing graph connections", False,
               f"{type(exc).__name__}: {exc}")

    # TEST C: keep a deterministic half of the edges.
    try:
        reduced = remove_half_edges(imports)
        c_rows = run_evaluation(evaluator, queries, texts, reduced, "half_graph_edges")
        c_path = RESULTS / f"robustness_C_half_graph_edges_{run_id}.csv"
        write_csv(c_path, c_rows)
        status("C — Missing import edges", len(c_rows) == len(queries),
               f"evaluated={len(c_rows)}, original_edges={edge_count(imports)}, "
               f"remaining_edges={edge_count(reduced)}, output={c_path.name}")
    except Exception as exc:
        status("C — Missing import edges", False,
               f"{type(exc).__name__}: {exc}")

    # TEST D: compare both methods on the exact same query and target rows.
    try:
        d_rows = run_evaluation(evaluator, queries, texts, imports, "full_graph")
        same_rows = len(d_rows) == len(queries)
        valid_ranks = all(
            isinstance(r["baseline_rank"], int) and r["baseline_rank"] > 0
            and isinstance(r["graph_rank"], int) and r["graph_rank"] > 0
            for r in d_rows
        )
        same_targets = all(
            str(r["target"]).strip() == str(q.get("target", "")).strip()
            and str(r["query"]).strip() == str(q.get("query", "")).strip()
            for r, q in zip(d_rows, queries)
        )
        d_path = RESULTS / f"robustness_D_fair_comparison_{run_id}.csv"
        write_csv(d_path, d_rows)

        metrics = {
            "query_count": len(d_rows),
            "baseline_top1_accuracy": sum(r["baseline_top1"] for r in d_rows) / len(d_rows) if d_rows else None,
            "graph_top1_accuracy": sum(r["graph_top1"] for r in d_rows) / len(d_rows) if d_rows else None,
            "baseline_mrr": mrr([r["baseline_rank"] for r in d_rows]),
            "graph_mrr": mrr([r["graph_rank"] for r in d_rows])
        }
        report["fair_comparison_metrics"] = metrics
        status("D — Fair comparison checks", same_rows and valid_ranks and same_targets,
               f"same_queries={same_rows}, valid_ranks={valid_ranks}, "
               f"same_query_text_and_targets={same_targets}, metrics={metrics}")
    except Exception as exc:
        status("D — Fair comparison checks", False,
               f"{type(exc).__name__}: {exc}")

    # TEST E: test that the dataset validator rejects a deliberately invalid target.
    # The original dataset is never modified.
    try:
        original_rows = read_csv(DATASET)
        if not original_rows:
            raise ValueError("Dataset CSV is empty")

        fieldnames = list(original_rows[0].keys())
        target_col = "target" if "target" in fieldnames else None
        if not target_col:
            raise ValueError(f"No target column found. Columns: {fieldnames}")

        invalid_rows = [dict(row) for row in original_rows]
        invalid_rows[0][target_col] = "THIS_PATH_MUST_NOT_EXIST/invalid_target.py"

        temp_dataset = RESULTS / f"_temporary_invalid_target_{run_id}.csv"
        try:
            with temp_dataset.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(invalid_rows)

            # Temporarily redirect only this in-memory module's dataset path.
            original_dataset_path = getattr(evaluator, "DATASET", None)
            evaluator.DATASET = temp_dataset
            rejected = False
            rejection_message = ""

            try:
                evaluator.read_queries()
            except Exception as exc:
                rejected = True
                rejection_message = f"{type(exc).__name__}: {exc}"
            finally:
                if original_dataset_path is not None:
                    evaluator.DATASET = original_dataset_path

            status("E — Invalid target rejection", rejected,
                   rejection_message if rejected else
                   "Validator accepted an invalid target; inspect read_queries() validation.")
        finally:
            if temp_dataset.exists():
                temp_dataset.unlink()
    except Exception as exc:
        status("E — Invalid target rejection", False,
               f"{type(exc).__name__}: {exc}")

    # Save a uniquely named summary, preserving previous reports.
    save_report(report)

    # Run the two known targeted test files.
    import subprocess
    test_files = [
        ROOT / "tests" / "test_search.py",
        ROOT / "tests" / "test_real_repository_graph.py"
    ]
    if all(p.exists() for p in test_files):
        cmd = [
            sys.executable, "-m", "pytest", "-q",
            str(test_files[0]), str(test_files[1])
        ]
        completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        report["targeted_pytest"] = {
            "return_code": completed.returncode,
            "stdout": completed.stdout[-8000:],
            "stderr": completed.stderr[-4000:]
        }
        save_report(report)
        print("\nTARGETED PYTEST OUTPUT")
        print(completed.stdout)
        if completed.stderr:
            print(completed.stderr)
        status("Targeted pytest", completed.returncode == 0,
               f"exit_code={completed.returncode}")
    else:
        status("Targeted pytest", False,
               "Expected test files not found under project tests/")

    log_path = NOTES / f"robustness-test-run-{run_id}.md"
    lines = [
        f"# Robustness Test Run — {stamp}",
        "",
        f"- Project root: `{ROOT}`",
        f"- Run ID: `{run_id}`",
        "",
        "## Test status",
        ""
    ]
    for name, item in report["tests"].items():
        lines.append(f"- **{name}: {item['status']}** — {item['details']}")
    lines += [
        "",
        "## Interpretation and limitations",
        "",
        "- B and C are graph-ablation checks, not evidence of broad generalization.",
        "- D checks whether baseline and graph-guided rankings use the same queries and targets.",
        "- E tests whether the dataset validator rejects an invalid target without changing the original dataset.",
        "- A validates the existing wording-perturbation output; it does not prove semantic paraphrase robustness.",
        "- Review all generated CSV/JSON files and code before using results in a paper.",
        ""
    ]
    log_path.write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "=" * 65)
    print("RUN FINISHED")
    print(f"Summary JSON: {RESULTS / f'robustness-test-summary-{run_id}.json'}")
    print(f"Experiment log: {log_path}")
    print("Check each PASS/FAIL status above before claiming completion.")
    print("=" * 65)

def save_report(report_data):
    out = RESULTS / f"robustness-test-summary-{run_id}.json"
    out.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
