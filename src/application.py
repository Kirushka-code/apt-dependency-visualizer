"""Load repositories and build reachable dependency graphs."""

from src.graph import build_graph
from src.repository import (
    RepositoryError,
    download_index,
    find_package,
    parse_index,
)
from src.test_repository import read_test_repository
from src.ubuntu_graph import make_dependency_reader


def load_graph(arguments):
    """Return the reachable graph and names absent from the index."""
    if arguments.test_mode:
        packages = read_test_repository(
            arguments.repository,
            arguments.version,
        )
        if arguments.package not in packages:
            raise RepositoryError(
                f"Package not found: {arguments.package}"
            )
        return build_graph(arguments.package, packages.__getitem__), []

    records = parse_index(download_index(arguments.repository))
    root_record = find_package(
        records,
        arguments.package,
        arguments.version,
    )
    reader = make_dependency_reader(records, root_record)
    graph = build_graph(arguments.package, reader)
    available = {record["Package"] for record in records}
    unresolved = sorted(set(graph) - available)
    return graph, unresolved