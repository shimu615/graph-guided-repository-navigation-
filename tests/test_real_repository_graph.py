import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "src")
)

from real_repository_graph import build_import_graph


class RealRepositoryGraphTests(unittest.TestCase):

    def test_relative_import_creates_connection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "requests"
            root.mkdir()

            init_file = root / "__init__.py"
            api_file = root / "api.py"
            utils_file = root / "utils.py"

            init_file.write_text("", encoding="utf-8")
            api_file.write_text(
                "from . import utils\n",
                encoding="utf-8"
            )
            utils_file.write_text(
                "def helper():\n    return True\n",
                encoding="utf-8"
            )

            files = [init_file, api_file, utils_file]

            module_map = {
                "requests": init_file,
                "requests.api": api_file,
                "requests.utils": utils_file,
            }

            graph = build_import_graph(files, module_map)

            self.assertIn(utils_file, graph[api_file])
            self.assertIn(api_file, graph[utils_file])

    def test_absolute_import_creates_connection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "requests"
            root.mkdir()

            api_file = root / "api.py"
            utils_file = root / "utils.py"

            api_file.write_text(
                "import requests.utils\n",
                encoding="utf-8"
            )
            utils_file.write_text(
                "VALUE = 1\n",
                encoding="utf-8"
            )

            files = [api_file, utils_file]

            module_map = {
                "requests.api": api_file,
                "requests.utils": utils_file,
            }

            graph = build_import_graph(files, module_map)

            self.assertIn(utils_file, graph[api_file])

    def test_unrelated_files_have_no_connection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "requests"
            root.mkdir()

            first = root / "first.py"
            second = root / "second.py"

            first.write_text("VALUE = 1\n", encoding="utf-8")
            second.write_text("VALUE = 2\n", encoding="utf-8")

            graph = build_import_graph(
                [first, second],
                {
                    "requests.first": first,
                    "requests.second": second,
                }
            )

            self.assertNotIn(second, graph.get(first, set()))


if __name__ == "__main__":
    unittest.main()
