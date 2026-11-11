import ast
from collections import defaultdict
from pathlib import Path


def build_import_graph(files, module_to_path):
    """
    Build an undirected graph from Python imports.
    Handles both absolute and relative imports.
    """
    graph = defaultdict(set)

    path_to_module = {
        path: module
        for module, path in module_to_path.items()
    }

    for path in files:
        current_module = path_to_module.get(path)

        if not current_module:
            continue

        # Determine the current Python package.
        if path.name == "__init__.py":
            current_package = current_module
        else:
            current_package = current_module.rpartition(".")[0]

        try:
            source = path.read_text(
                encoding="utf-8",
                errors="replace"
            )
            tree = ast.parse(source)
        except (SyntaxError, OSError):
            continue

        for node in ast.walk(tree):
            targets = []

            if isinstance(node, ast.Import):
                for alias in node.names:
                    targets.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    package_parts = (
                        current_package.split(".")
                        if current_package else []
                    )

                    remove_count = node.level - 1

                    if remove_count > len(package_parts):
                        continue

                    if remove_count:
                        package_parts = package_parts[:-remove_count]

                    if node.module:
                        package_parts.extend(node.module.split("."))

                    base_module = ".".join(package_parts)

                    if base_module:
                        targets.append(base_module)

                    # Handles statements such as:
                    # from . import adapters
                    if node.module is None:
                        for alias in node.names:
                            if alias.name != "*":
                                candidate = ".".join(
                                    package_parts + [alias.name]
                                )
                                if candidate:
                                    targets.append(candidate)

                elif node.module:
                    targets.append(node.module)

            for imported_module in targets:
                parts = imported_module.split(".")
                target_path = None

                # Match the longest known local module prefix.
                for end in range(len(parts), 0, -1):
                    prefix = ".".join(parts[:end])

                    if prefix in module_to_path:
                        target_path = module_to_path[prefix]
                        break

                if target_path is not None and target_path != path:
                    graph[path].add(target_path)
                    graph[target_path].add(path)

    return graph
