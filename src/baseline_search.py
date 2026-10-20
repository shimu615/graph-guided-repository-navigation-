"""Baseline keyword search for the repository-navigation study."""

import argparse
import re
from pathlib import Path

EXCLUDED_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist"}


def tokenize(text):
    """Return lowercase word tokens."""
    return set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower()))


def collect_files(root):
    """Collect repository text/code files while skipping generated folders."""
    root = Path(root)
    allowed = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".md", ".json"}
    files = []

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in allowed:
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        files.append((path, content))

    return files


def search_repository(root, query):
    """Rank files by overlap between query words and file path/content."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    results = []
    for path, content in collect_files(root):
        searchable = f"{path.name} {path.stem} {content}"
        matched = sorted(query_tokens & tokenize(searchable))
        if matched:
            results.append({
                "file": path.name,
                "path": path.as_posix(),
                "score": len(matched),
                "matched_tokens": matched,
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
            f'{result["file"]} | score={result["score"]} | '
            f'matched={",".join(result["matched_tokens"])}'
        )


if __name__ == "__main__":
    main()
