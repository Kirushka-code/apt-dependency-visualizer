"""Tests for reverse dependency traversal."""

import unittest

from src.graph import build_graph, reverse_graph


class ReverseGraphTests(unittest.TestCase):
    """Check reversed edges and iterative reverse traversal."""

    def test_reverse_edges(self):
        """Reverse dependencies and preserve isolated vertices."""
        graph = {"A": ["B"], "B": [], "C": []}
        self.assertEqual(
            reverse_graph(graph),
            {"A": [], "B": ["A"], "C": []},
        )

    def test_transitive_dependencies(self):
        """Find direct and transitive dependents."""
        graph = {"A": ["B"], "B": ["C"], "C": []}
        reversed_graph = reverse_graph(graph)
        result = build_graph("C", reversed_graph.__getitem__)
        self.assertEqual(
            result,
            {"C": ["B"], "B": ["A"], "A": []},
        )

    def test_branch(self):
        """Find both parents of a shared dependency."""
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": [],
        }
        reversed_graph = reverse_graph(graph)
        result = build_graph("D", reversed_graph.__getitem__)
        self.assertEqual(
            result,
            {
                "D": ["B", "C"],
                "B": ["A"],
                "A": [],
                "C": ["A"],
            },
        )

    def test_cycle(self):
        """Traverse reversed cyclic dependencies without looping."""
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        reversed_graph = reverse_graph(graph)
        result = build_graph("A", reversed_graph.__getitem__)
        self.assertEqual(
            result,
            {"A": ["C"], "C": ["B"], "B": ["A"]},
        )

    def test_no_dependents(self):
        """Return only the root when no package depends on it."""
        graph = {"A": ["B"], "B": []}
        reversed_graph = reverse_graph(graph)
        self.assertEqual(
            build_graph("A", reversed_graph.__getitem__),
            {"A": []},
        )


if __name__ == "__main__":
    unittest.main()