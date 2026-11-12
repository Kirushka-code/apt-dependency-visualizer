"""Find reverse dependencies across a complete repository."""

from src.graph import build_graph, reverse_graph
from src.repository import (
    RepositoryError,
    download_index,
    find_package,
    parse_index,
)
from src.test_repository import read_test_repository
from src.ubuntu_graph import make_dependency_reader


def load_repository_graph(arguments):
    """Read the complete repository graph before reversing edges."""
    if arguments.test_mode:
        graph = read_test_repository(
            arguments.repository,
            arguments.version,
        )
        if arguments.package not in graph:
            raise RepositoryError(
                f"Package not found: {arguments.package}"
            )
        return graph

    records = parse_index(download_index(arguments.repository))
    root = find_package(
        records,
        arguments.package,
        arguments.version,
    )
    reader = make_dependency_reader(records, root)
    names = dict.fromkeys(record["Package"] for record in records)
    return {name: reader(name) for name in names}


def load_reverse_graph(arguments):
    """Find reachable dependents using the existing iterative DFS."""
    graph = load_repository_graph(arguments)
    reversed_graph = reverse_graph(graph)
    return build_graph(
        arguments.package,
        reversed_graph.__getitem__,
    )