"""Analyze a cloned Python repository and generate candidate search queries.

Built with Shimu.
Generated queries are candidates, not verified ground-truth labels.
Only Python standard-library modules are used.
"""

import ast
import csv
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "external" / "requests"
NOTES = ROOT / "notes"
RESULTS = ROOT / "results"

MANIFEST = NOTES / "real-repository-manifest.json"
MODULE_CSV = RESULTS / "real-repository-modules.csv"
CANDIDATES = RESULTS / "real-repository-query-candidates.csv"
REPORT = NOTES / "real-repository-analysis.md"


def git_output(*args):
    result = subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def is_ignored_path(path):
    ignored_parts = {
        ".git", ".venv", "venv", "__pycache__",
        "build", "dist", "site-packages",
    }
    return any(part in ignored_parts for part in path.parts)


def main():
    if not (REPO / ".git").exists():
        raise SystemExit(f"Git repository not found at {REPO}")

    commit = git_output("rev-parse", "HEAD")
    remote = git_output("remote", "get-url", "origin")
    files = sorted(
        p for p in REPO.rglob("*.py")
        if not is_ignored_path(p.relative_to(REPO))
    )

    module_rows = []
    query_rows = []
    parse_errors = []
    import_edges = Counter()
    function_count = 0

    for path in files:
        rel = path.relative_to(REPO).as_posix()

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel)
        except (OSError, UnicodeError, SyntaxError) as exc:
            parse_errors.append({"file": rel, "error": str(exc)})
            continue

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add("." * node.level + node.module)

        module_rows.append({
            "file": rel,
            "sha256": sha256_file(path),
            "imports": "; ".join(sorted(imports)),
            "line_count": len(source.splitlines()),
        })

        for imported in imports:
            import_edges[(rel, imported)] += 1

        # Only top-level functions are used for initial candidates.
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            function_count += 1
            docstring = ast.get_docstring(node) or ""
            first_sentence = docstring.strip().splitlines()[0].strip() if docstring.strip() else ""

            # Candidate natural-language query is derived from source identifiers
            # and docstrings; it still needs human review.
            candidate_query = first_sentence or node.name.replace("_", " ")

            query_rows.append({
                "candidate_id": f"CAND-{len(query_rows) + 1:04d}",
                "query": candidate_query,
                "candidate_file": rel,
                "function_name": node.name,
                "source_line": node.lineno,
                "docstring_available": bool(docstring.strip()),
                "review_status": "UNREVIEWED",
                "review_notes": "",
            })

    if not files:
        raise SystemExit("No Python files found in the repository.")

    NOTES.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)

    with MODULE_CSV.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["file", "sha256", "imports", "line_count"],
        )
        writer.writeheader()
        writer.writerows(module_rows)

    with CANDIDATES.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id", "query", "candidate_file", "function_name",
                "source_line", "docstring_available", "review_status",
                "review_notes",
            ],
        )
        writer.writeheader()
        writer.writerows(query_rows)

    manifest = {
        "repository_name": "Requests",
        "remote": remote,
        "commit": commit,
        "analysis_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_file_count": len(files),
        "parsed_file_count": len(module_rows),
        "parse_error_count": len(parse_errors),
        "top_level_function_count": function_count,
        "import_edge_count": sum(import_edges.values()),
        "python_version": subprocess.run(
            ["python", "--version"], capture_output=True, text=True
        ).stdout.strip(),
        "warning": (
            "Generated function queries are candidates only. "
            "Human review is required before evaluation."
        ),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = [
        "# Real Repository Analysis",
        "",
        "Project: Graph-Guided Repository Navigation for Coding Agents",
        "Repository: Requests (psf/requests)",
        f"- Commit: `{commit}`",
        f"- Remote: `{remote}`",
        f"- Analysis time (UTC): `{manifest['analysis_timestamp_utc']}`",
        f"- Python files discovered: {len(files)}",
        f"- Files parsed successfully: {len(module_rows)}",
        f"- Parse errors: {len(parse_errors)}",
        f"- Top-level functions found: {function_count}",
        f"- Import statements/references counted: {sum(import_edges.values())}",
        "",
        "## Outputs",
        "",
        "- `notes/real-repository-manifest.json`",
        "- `results/real-repository-modules.csv`",
        "- `results/real-repository-query-candidates.csv`",
        "",
        "## Limitations",
        "",
        "- Candidate queries are generated from code/docstrings and are not verified.",
        "- Import references are syntactic names; this is not a complete resolved dependency graph.",
        "- Test, generated, or vendored files may still be present in the repository.",
        "- A discovered function does not prove that its file is the only relevant answer.",
        "- Do not report benchmark accuracy until query targets have been reviewed.",
        "",
        "## Parse errors",
        "",
    ]

    if parse_errors:
        lines.extend(f"- `{item['file']}`: {item['error']}" for item in parse_errors)
    else:
        lines.append("No Python parse errors were recorded.")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n=== ANALYSIS COMPLETE ===")
    print(f"Repository commit: {commit}")
    print(f"Python files discovered: {len(files)}")
    print(f"Files parsed: {len(module_rows)}")
    print(f"Parse errors: {len(parse_errors)}")
    print(f"Top-level functions: {function_count}")
    print(f"Import references: {sum(import_edges.values())}")
    print(f"Candidate queries: {len(query_rows)}")
    print("Candidate labels are UNREVIEWED; do not treat them as ground truth.")
    print(f"Manifest: {MANIFEST.relative_to(ROOT)}")
    print(f"Module inventory: {MODULE_CSV.relative_to(ROOT)}")
    print(f"Candidate queries: {CANDIDATES.relative_to(ROOT)}")
    print(f"Report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

