import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.evaluate_independent_queries import (
    read_queries,
    build_index,
    rank_query,
    reciprocal,
)

rows = read_queries()
texts, imports = build_index()

print("Queries:", len(rows))
print("Indexed files:", len(texts))
print("Import graph edges:", sum(len(v) for v in imports.values()))
print()

for row in rows[:3]:
    target = row["proposed_target"].strip().replace("\\", "/")

    baseline, graph, baseline_rank, graph_rank = rank_query(
        row["query"], texts, imports, target
    )

    print("Query:", row["query_id"])
    print("Target:", target)
    print("Baseline rank:", baseline_rank)
    print("Graph rank:", graph_rank)
    print("Baseline top 3:", baseline[:3])
    print("Graph top 3:", graph[:3])
    print("Baseline reciprocal rank:", reciprocal(baseline_rank))
    print("Graph reciprocal rank:", reciprocal(graph_rank))
    print("-" * 60)
