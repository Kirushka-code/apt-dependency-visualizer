"""Tests for repository adapters and application integration."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.application import load_graph
from src.repository import RepositoryError
from src.test_repository import read_test_repository
from src.ubuntu_graph import dependency_names, make_dependency_reader


FIXTURES = Path(__file__).parent / "fixtures"


class SourceTests(unittest.TestCase):
    """Check local fixtures and Ubuntu dependency adaptation."""

    def test_fixture_graphs(self):
        """Load each fixture through the application entry point."""
        expected = {
            "chain": {"A": ["B"], "B": ["C"], "C": []},
            "branch": {
                "A": ["B", "C"],
                "B": ["D"],
                "D": [],
                "C": ["D"],
            },
            "cycle": {"A": ["B"], "B": ["C"], "C": ["A"]},
            "isolated": {"A": []},
        }
        for name, graph in expected.items():
            with self.subTest(name=name):
                arguments = SimpleNamespace(
                    package="A",
                    version="1.0",
                    repository=str(FIXTURES / f"{name}.json"),
                    test_mode=True,
                )
                self.assertEqual(load_graph(arguments), (graph, []))

    def test_invalid_test_repositories(self):
        """Reject invalid JSON, unknown references, and wrong versions."""
        cases = [
            "{",
            "[]",
            '{"version":"2.0","packages":{"A":[]}}',
            '{"version":"1.0","packages":{"a":[]}}',
            '{"version":"1.0","packages":{"A":["B"]}}',
            '{"version":"1.0","packages":{"A":"B"}}',
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repository.json"
            for text in cases:
                with self.subTest(text=text):
                    path.write_text(text, encoding="utf-8")
                    with self.assertRaises(RepositoryError):
                        read_test_repository(path, "1.0")

    def test_dependency_names(self):
        """Include alternatives and strip version and arch qualifiers."""
        record = {
            "Pre-Depends": "base",
            "Depends": "first:any (>= 1.0) | second, base",
        }
        self.assertEqual(
            dependency_names(record),
            ["base", "first", "second"],
        )

    def test_exact_root_version(self):
        """Use the requested root version when multiple versions exist."""
        records = [
            {"Package": "root", "Version": "1", "Depends": "other"},
            {"Package": "root", "Version": "2"},
            {"Package": "other", "Version": "1", "Depends": "root"},
        ]
        reader = make_dependency_reader(records, records[0])
        self.assertEqual(reader("root"), ["other"])
        self.assertEqual(reader("other"), ["root"])

    def test_ambiguous_dependency(self):
        """Reject ambiguous dependency records instead of guessing."""
        records = [
            {"Package": "root", "Version": "1"},
            {"Package": "other", "Version": "1"},
            {"Package": "other", "Version": "2"},
        ]
        reader = make_dependency_reader(records, records[0])
        with self.assertRaises(RepositoryError):
            reader("other")

    def test_unresolved_package(self):
        """Report dependencies absent from the selected index."""
        text = "Package: root\nVersion: 1\nDepends: missing\n"
        arguments = SimpleNamespace(
            package="root",
            version="1",
            repository="https://example.org/Packages",
            test_mode=False,
        )
        with patch("src.application.download_index", return_value=text):
            graph, unresolved = load_graph(arguments)
        self.assertEqual(graph, {"root": ["missing"], "missing": []})
        self.assertEqual(unresolved, ["missing"])


if __name__ == "__main__":
    unittest.main()