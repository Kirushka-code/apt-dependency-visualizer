"""Build dependency graphs using iterative depth-first search."""


def build_graph(root, get_dependencies):
    """Visit reachable packages with an explicit stack."""
    graph = {}
    stack = [root]
    while stack:
        package = stack.pop()
        if package in graph:
            continue
        dependencies = list(dict.fromkeys(get_dependencies(package)))
        graph[package] = dependencies
        stack.extend(reversed(dependencies))
    return graph