import argparse
from pathlib import Path

from retrieval_core import (
    collect_python_files,
    normalize_texts,
    build_import_graph,
    rank_graph
)

GRAPH_BOOST = 0.10

def search_repository(root, query):
    if not query.strip():
        return []

    files = collect_python_files(root)
    texts = normalize_texts(root, files)
    graph = build_import_graph(root, texts)

    ranked, graph_scores, direct_scores = rank_graph(
        query, texts, graph, boost=GRAPH_BOOST
    )

    results = []

    for path in ranked:
        if graph_scores[path] <= 0:
            continue

        neighbor_score = max(
            (direct_scores.get(n, 0.0) for n in graph[path]),
            default=0.0
        )

        results.append({
            "file": Path(path).name,
            "path": path,
            "score": graph_scores[path],
            "direct_score": direct_scores[path],
            "neighbor_score": neighbor_score
        })

    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--query", required=True)
    args = parser.parse_args()

    for result in search_repository(args.root, args.query):
        print(
            f'{result["file"]} | {result["path"]} | '
            f'score={result["score"]:.4f} | '
            f'direct={result["direct_score"]:.4f} | '
            f'neighbor={result["neighbor_score"]:.4f}'
        )

if __name__ == "__main__":
    main()
