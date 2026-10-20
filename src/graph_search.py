"""Prototype graph-guided search using local Python import relationships."""

import argparse
import ast
import re
from pathlib import Path

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist"}


def tokenize(text):
    """Return lowercase word tokens."""
    return set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower()))


def collect_python_files(root):
    """Find Python files without scanning virtual environments or Git data."""
    root = Path(root)
    files = []

    for path in root.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        files.append((path, content))

    return files


def build_import_graph(root, files):
    """Build an undirected graph of local Python module imports."""
    root = Path(root)
    module_to_path = {}

    for path, _ in files:
        relative = path.relative_to(root).with_suffix("")
        module = ".".join(relative.parts)
        if module.endswith(".__init__"):
            module = module[:-9]
        module_to_path[module] = path

        # Also support imports by a simple filename module name.
        module_to_path.setdefault(path.stem, path)

    graph = {path: set() for path, _ in files}

    for path, content in files:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        for module in imported_modules:
            target = module_to_path.get(module)
            if target is not None and target != path:
                graph[path].add(target)
                graph[target].add(path)

    return graph


def search_repository(root, query):
    """Combine direct keyword score with the best score among graph neighbors."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    files = collect_python_files(root)
    graph = build_import_graph(root, files)
    contents = {path: content for path, content in files}
    direct_scores = {}
    matched_tokens = {}

    for path, content in files:
        searchable = f"{path.name} {path.stem} {content}"
        matched = sorted(query_tokens & tokenize(searchable))
        direct_scores[path] = len(matched)
        matched_tokens[path] = matched

    results = []
    for path, content in files:
        direct = direct_scores[path]
        # Keep only files with direct query matches; neighbors influence ranking.
        if direct == 0:
            continue

        neighbor_score = max(
            (direct_scores.get(neighbor, 0) for neighbor in graph[path]),
            default=0,
        )
        combined = direct + 0.25 * neighbor_score

        results.append({
            "file": path.name,
            "path": path.as_posix(),
            "score": combined,
            "direct_score": direct,
            "neighbor_score": neighbor_score,
            "matched_tokens": matched_tokens[path],
        })

    results.sort(key=lambda item: (-item["score"], item["path"]))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Repository directory")
    parser.add_argument("--query", required=True, help="Search query")
    args = parser.parse_args()

    for result in search_repository(args.root, args.query):
        print(
            f'{result["file"]} | score={result["score"]:.2f} | '
            f'direct={result["direct_score"]} | '
            f'neighbor={result["neighbor_score"]} | '
            f'matched={",".join(result["matched_tokens"])}'
        )


if __name__ == "__main__":
    main()
