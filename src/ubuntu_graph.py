"""Adapt Ubuntu package records to graph traversal."""

import re

from src.repository import RepositoryError, direct_dependencies


DEPENDENCY_NAME_PATTERN = r"([a-z0-9][a-z0-9+.-]*)(?::[a-z0-9-]+)?"


def dependency_names(record):
    """Extract package names from all declared dependency alternatives."""
    names = []
    for group in direct_dependencies(record):
        for alternative in group.split("|"):
            match = re.match(
                DEPENDENCY_NAME_PATTERN,
                alternative.strip(),
            )
            if match is None:
                raise RepositoryError(
                    f"Unsupported dependency: {alternative}"
                )
            names.append(match.group(1))
    return list(dict.fromkeys(names))


def index_records(records):
    """Group package records by package name."""
    indexed = {}
    for record in records:
        indexed.setdefault(record["Package"], []).append(record)
    return indexed


def make_dependency_reader(records, root_record):
    """Create a dependency reader with the exact requested root version."""
    indexed = index_records(records)
    root_name = root_record["Package"]

    def get_dependencies(name):
        """Read one package or preserve an unresolved name as a leaf."""
        if name == root_name:
            return dependency_names(root_record)
        candidates = indexed.get(name, [])
        if not candidates:
            return []
        if len(candidates) != 1:
            raise RepositoryError(
                f"Multiple records for dependency {name}; "
                "use an index with one version per dependency"
            )
        return dependency_names(candidates[0])

    return get_dependencies