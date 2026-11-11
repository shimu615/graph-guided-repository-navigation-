import json
from pathlib import Path

root = Path.cwd()

original = json.loads(
    (root / "results" / "oct29-independent-summary.json").read_text(encoding="utf-8")
)

verified = json.loads(
    (root / "results" / "oct30-test-d-verified-summary.json").read_text(encoding="utf-8")
)

keys = [
    "query_count",
    "python_files_indexed",
    "import_graph_edges",
    "baseline_top1_accuracy",
    "graph_top1_accuracy",
    "baseline_mrr",
    "graph_mrr",
]

all_match = True

for key in keys:
    same = original.get(key) == verified.get(key)
    print(f"{key}: {'MATCH' if same else 'MISMATCH'}")
    if not same:
        print("  Original:", original.get(key))
        print("  Verified:", verified.get(key))
        all_match = False

print("\nSUMMARY:", "PASS" if all_match else "REVIEW REQUIRED")
