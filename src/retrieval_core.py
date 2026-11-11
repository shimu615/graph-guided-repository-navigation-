import ast
import re
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__",
    "node_modules", "dist", "build"
}

def tokenize(text):
    return set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower()))

def lexical_score(query, relpath, source):
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0

    path_tokens = tokenize(
        str(relpath).replace("/", " ").replace("\\", " ").replace(".py", " ")
    )
    source_tokens = tokenize(source)

    return len(query_tokens & (path_tokens | source_tokens)) / len(query_tokens)

def collect_python_files(root):
    """Return legacy-compatible (Path, source) tuples."""
    root = Path(root).resolve()
    files = []

    for path in sorted(root.rglob("*.py")):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue

        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source = path.read_text(encoding="latin-1")
        except OSError:
            continue

        files.append((path, source))

    return files

def normalize_texts(root, files):
    """Convert collected tuples or a string-keyed mapping to relative-path mapping."""
    root = Path(root).resolve()

    if isinstance(files, dict):
        return {
            str(key).replace("\\", "/"): value
            for key, value in files.items()
        }

    return {
        Path(path).resolve().relative_to(root).as_posix(): source
        for path, source in files
    }

def build_import_graph(root, files):
    """Build an undirected local Python import graph."""
    root = Path(root).resolve()
    texts = normalize_texts(root, files)

    module_to_path = {}

    for relpath in texts:
        module = relpath[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[:-9]
        module_to_path[module] = relpath

    graph = {relpath: set() for relpath in texts}

    for relpath, source in texts.items():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        current_module = relpath[:-3].replace("/", ".")
        is_package = (
            relpath.endswith("/__init__.py")
            or relpath == "__init__.py"
        )

        if is_package and current_module.endswith(".__init__"):
            current_module = current_module[:-9]

        package = (
            current_module
            if is_package
            else current_module.rpartition(".")[0]
        )

        imported_names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.name for alias in node.names)

            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    parts = package.split(".") if package else []
                    keep = max(0, len(parts) - node.level + 1)
                    base = parts[:keep]

                    if node.module:
                        base.extend(node.module.split("."))

                    imported = ".".join(base)
                else:
                    imported = node.module or ""

                if imported:
                    imported_names.add(imported)

        for imported in imported_names:
            candidates = set()

            if imported in module_to_path:
                candidates.add(module_to_path[imported])

            for module, candidate in module_to_path.items():
                if (
                    module.startswith(imported + ".")
                    or imported.startswith(module + ".")
                ):
                    candidates.add(candidate)

            for candidate in candidates:
                if candidate != relpath:
                    graph[relpath].add(candidate)
                    graph[candidate].add(relpath)

    # Preserve Path keys when caller supplied legacy tuple-list input.
    if not isinstance(files, dict):
        return {
            (root / path): {root / neighbor for neighbor in neighbors}
            for path, neighbors in graph.items()
        }

    return graph

def rank_baseline(query, texts):
    scores = {
        path: lexical_score(query, path, source)
        for path, source in texts.items()
    }

    ranked = sorted(texts, key=lambda path: (-scores[path], path))
    return ranked, scores

def rank_graph(query, texts, graph, boost=0.10):
    _, direct_scores = rank_baseline(query, texts)
    graph_scores = {}

    for path in texts:
        neighbor_score = max(
            (direct_scores.get(neighbor, 0.0) for neighbor in graph[path]),
            default=0.0
        )
        graph_scores[path] = direct_scores[path] + boost * neighbor_score

    ranked = sorted(texts, key=lambda path: (-graph_scores[path], path))
    return ranked, graph_scores, direct_scores
