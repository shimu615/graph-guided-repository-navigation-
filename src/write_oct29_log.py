import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
summary_path = root / "results" / "oct29-independent-summary.json"
note_path = root / "notes" / "experiment-log-2026-10-29.md"

if not summary_path.exists():
    raise FileNotFoundError("Run the independent evaluator first.")

data = json.loads(summary_path.read_text(encoding="utf-8"))

note = f"""# October 29, 2026 — Independent Evaluation

## Dataset
- Queries evaluated: {data['query_count']}
- Python files indexed: {data['python_files_indexed']}
- Import graph edges: {data['import_graph_edges']}

## Results

| Metric | Baseline | Graph-guided |
|---|---:|---:|
| Top-1 accuracy | {data['baseline_top1_accuracy']:.3f} | {data['graph_top1_accuracy']:.3f} |
| Recall@5 | {data['baseline_recall_at_5']:.3f} | {data['graph_recall_at_5']:.3f} |
| MRR | {data['baseline_mrr']:.3f} | {data['graph_mrr']:.3f} |

## Limitations
{data['warning']}

The small dataset does not support broad generalization claims.
The evaluator is a prototype and its graph score requires further
validation. Results must be interpreted alongside individual queries.
"""

note_path.write_text(note, encoding="utf-8")
print(f"Saved: {note_path}")
print(note)
