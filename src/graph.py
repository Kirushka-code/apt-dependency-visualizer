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

def reverse_graph(graph):
    """Reverse every edge while preserving all graph vertices."""
    reversed_graph = {package: [] for package in graph}
    for package, dependencies in graph.items():
        for dependency in dependencies:
            parents = reversed_graph.setdefault(dependency, [])
            if package not in parents:
                parents.append(package)
    return reversed_graph