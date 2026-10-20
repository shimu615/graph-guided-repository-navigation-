"""Unit tests for the repository-search prototypes."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from baseline_search import search_repository as baseline_search
from graph_search import (
    build_import_graph,
    collect_python_files,
    search_repository as graph_search,
)
from evaluate import reciprocal_rank

REPO = PROJECT_ROOT / "experiments" / "sample_repo"


class SearchTests(unittest.TestCase):
    def test_sample_repository_has_three_python_files(self):
        files = collect_python_files(REPO)
        names = {path.name for path, _ in files}
        self.assertTrue({"student.py", "report.py", "database.py"}.issubset(names))

    def test_baseline_returns_student_file(self):
        results = baseline_search(REPO, "calculate student grade marks")
        self.assertTrue(results)
        self.assertEqual(results[0]["file"], "student.py")

    def test_graph_search_returns_student_file(self):
        results = graph_search(REPO, "calculate student grade marks")
        self.assertTrue(results)
        self.assertEqual(results[0]["file"], "student.py")

    def test_report_import_creates_graph_connection(self):
        files = collect_python_files(REPO)
        graph = build_import_graph(REPO, files)
        report = next(path for path, _ in files if path.name == "report.py")
        student = next(path for path, _ in files if path.name == "student.py")
        self.assertIn(student, graph[report])
        self.assertIn(report, graph[student])

    def test_empty_query_returns_no_results(self):
        self.assertEqual(baseline_search(REPO, "   "), [])
        self.assertEqual(graph_search(REPO, "   "), [])

    def test_reciprocal_rank(self):
        self.assertEqual(reciprocal_rank(["a.py", "b.py"], "a.py"), 1.0)
        self.assertEqual(reciprocal_rank(["a.py", "b.py"], "b.py"), 0.5)
        self.assertEqual(reciprocal_rank(["a.py"], "missing.py"), 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
