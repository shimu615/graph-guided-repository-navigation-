import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from step11_robustness import (
    normalize_path,
    metrics,
    aggregate,
    make_symmetric_graph,
    perturb_graph,
)


def test_normalize_path():
    assert normalize_path(r".\src\requests\api.py") == "src/requests/api.py"


def test_top1_metric():
    result = metrics(["a.py", "b.py"], "a.py")
    assert result["target_rank"] == 1
    assert result["top1"] == 1
    assert result["recall_at_5"] == 1
    assert result["mrr"] == 1.0


def test_rank_five_metric():
    result = metrics(
        ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py"],
        "e.py",
    )
    assert result["target_rank"] == 5
    assert result["top1"] == 0
    assert result["recall_at_5"] == 1
    assert result["mrr"] == 0.2


def test_rank_six_metric():
    result = metrics(
        ["a.py", "b.py", "c.py", "d.py", "e.py", "f.py"],
        "f.py",
    )
    assert result["target_rank"] == 6
    assert result["recall_at_5"] == 0
    assert result["mrr"] == 1 / 6


def test_missing_target_metric():
    result = metrics(["a.py", "b.py"], "missing.py")
    assert result["target_rank"] == 0
    assert result["top1"] == 0
    assert result["recall_at_5"] == 0
    assert result["mrr"] == 0.0


def test_aggregate_metrics():
    rows = [
        {"top1": 1, "recall_at_5": 1, "mrr": 1.0},
        {"top1": 0, "recall_at_5": 1, "mrr": 0.5},
    ]
    result = aggregate(rows)
    assert result["top1"] == 0.5
    assert result["recall_at_5"] == 1.0
    assert result["mrr"] == 0.75


def test_aggregate_empty_rejected():
    try:
        aggregate([])
    except ValueError:
        return
    assert False, "Expected ValueError for empty rows"


def test_symmetric_graph():
    graph = {
        "a.py": {"b.py"},
        "b.py": set(),
        "c.py": set(),
    }
    result = make_symmetric_graph(graph)
    assert "b.py" in result["a.py"]
    assert "a.py" in result["b.py"]
    assert "c.py" in result


def test_zero_dropout_keeps_graph():
    graph = {
        "a.py": {"b.py"},
        "b.py": {"a.py", "c.py"},
        "c.py": {"b.py"},
    }
    result = perturb_graph(graph, 0.0, 11)
    assert result == graph


def test_dropout_preserves_nodes():
    graph = {
        "a.py": {"b.py"},
        "b.py": {"a.py"},
        "isolated.py": set(),
    }
    result = perturb_graph(graph, 0.5, 33)
    assert set(result) == set(graph)


def test_dropout_preserves_symmetry():
    graph = {
        "a.py": {"b.py", "c.py"},
        "b.py": {"a.py", "c.py"},
        "c.py": {"a.py", "b.py"},
    }
    result = perturb_graph(graph, 0.5, 44)

    for node, neighbors in result.items():
        for neighbor in neighbors:
            assert node in result[neighbor]


def test_dropout_is_deterministic():
    graph = {
        "a.py": {"b.py", "c.py"},
        "b.py": {"a.py", "c.py"},
        "c.py": {"a.py", "b.py"},
    }
    first = perturb_graph(graph, 0.5, 22)
    second = perturb_graph(graph, 0.5, 22)
    assert first == second


def test_different_seeds_can_change_graph():
    graph = {
        "a.py": {"b.py", "c.py", "d.py"},
        "b.py": {"a.py", "c.py", "d.py"},
        "c.py": {"a.py", "b.py", "d.py"},
        "d.py": {"a.py", "b.py", "c.py"},
    }
    first = perturb_graph(graph, 0.5, 11)
    second = perturb_graph(graph, 0.5, 22)
    assert first != second


def test_invalid_negative_dropout():
    graph = {"a.py": set()}
    try:
        perturb_graph(graph, -0.1, 11)
    except ValueError:
        return
    assert False, "Expected ValueError"


def test_invalid_full_dropout():
    graph = {"a.py": set()}
    try:
        perturb_graph(graph, 1.0, 11)
    except ValueError:
        return
    assert False, "Expected ValueError"


def test_graph_has_no_self_edges_after_dropout():
    graph = {
        "a.py": {"a.py", "b.py"},
        "b.py": {"a.py"},
    }
    result = perturb_graph(graph, 0.0, 11)

    for node, neighbors in result.items():
        assert node not in neighbors


def test_complete_graph_nodes_adds_missing_files():
    from step11_robustness import complete_graph_nodes

    texts = {
        "a.py": "source a",
        "b.py": "source b",
        "isolated.py": "source isolated",
    }

    graph = {
        "a.py": {"b.py"},
        "b.py": {"a.py"},
    }

    result = complete_graph_nodes(graph, texts)

    assert set(result) == set(texts)
    assert result["isolated.py"] == set()
    assert "b.py" in result["a.py"]
    assert "a.py" in result["b.py"]
