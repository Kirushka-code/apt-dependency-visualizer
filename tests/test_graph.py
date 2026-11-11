"""Tests for iterative DFS and graph structure."""

import unittest

from src.graph import build_graph


LONG_CHAIN_LENGTH = 2000


class GraphTests(unittest.TestCase):
    """Check cycles, branches, and traversal depth."""

    def test_chain(self):
        """Visit every vertex in a dependency chain."""
        packages = {"A": ["B"], "B": ["C"], "C": []}
        graph = build_graph("A", packages.__getitem__)
        self.assertEqual(graph, packages)

    def test_branch(self):
        """Expand a shared dependency only once."""
        packages = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": [],
        }
        calls = []

        def dependencies(name):
            """Record dependency requests."""
            calls.append(name)
            return packages[name]

        graph = build_graph("A", dependencies)
        self.assertEqual(graph, packages)
        self.assertEqual(calls, ["A", "B", "D", "C"])

    def test_cycle(self):
        """Preserve cycle edges and finish traversal."""
        packages = {"A": ["B"], "B": ["C"], "C": ["A"]}
        self.assertEqual(
            build_graph("A", packages.__getitem__),
            packages,
        )

    def test_self_dependency(self):
        """Handle a vertex depending on itself."""
        packages = {"A": ["A"]}
        self.assertEqual(
            build_graph("A", packages.__getitem__),
            packages,
        )

    def test_isolated(self):
        """Exclude vertices unreachable from the root."""
        packages = {"A": [], "B": []}
        self.assertEqual(
            build_graph("A", packages.__getitem__),
            {"A": []},
        )

    def test_long_chain(self):
        """Traverse a chain deeper than typical recursion limits."""
        packages = {
            str(number): [str(number + 1)]
            for number in range(LONG_CHAIN_LENGTH)
        }
        packages[str(LONG_CHAIN_LENGTH)] = []
        graph = build_graph("0", packages.__getitem__)
        self.assertEqual(graph, packages)


if __name__ == "__main__":
    unittest.main()