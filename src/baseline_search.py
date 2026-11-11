import argparse
from pathlib import Path

from retrieval_core import (
    collect_python_files,
    normalize_texts,
    rank_baseline
)

def search_repository(root, query):
    if not query.strip():
        return []

    files = collect_python_files(root)
    texts = normalize_texts(root, files)
    ranked, scores = rank_baseline(query, texts)

    return [
        {
            "file": Path(path).name,
            "path": path,
            "score": scores[path]
        }
        for path in ranked
        if scores[path] > 0
    ]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--query", required=True)
    args = parser.parse_args()

    for result in search_repository(args.root, args.query):
        print(
            f'{result["file"]} | {result["path"]} | '
            f'score={result["score"]:.4f}'
        )

if __name__ == "__main__":
    main()
