"""Integration tests for reverse dependency CLI mode."""

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


class ReverseCliTests(unittest.TestCase):
    """Check reverse mode using complete local repositories."""

    def run_reverse(self, package, fixture):
        """Run the application and capture its output."""
        arguments = [
            "--package", package,
            "--repository", str(FIXTURES / fixture),
            "--version", "1.0",
            "--test-mode",
            "--reverse",
        ]
        output = io.StringIO()
        with redirect_stdout(output):
            result = main(arguments)
        self.assertEqual(result, 0)
        return output.getvalue()

    def test_chain(self):
        """Find dependents outside the root's forward graph."""
        output = self.run_reverse("C", "chain.json")
        self.assertEqual(
            output.splitlines(),
            [
                "package=C",
                "version=1.0",
                "Reverse dependency graph:",
                "  C -> B",
                "  B -> A",
                "  A -> (none)",
            ],
        )

    def test_cycle(self):
        """Complete reverse traversal of a cycle."""
        output = self.run_reverse("A", "cycle.json")
        self.assertIn("  A -> C\n", output)
        self.assertIn("  C -> B\n", output)
        self.assertIn("  B -> A\n", output)

    def test_no_dependents(self):
        """Keep the root when it has no dependents."""
        output = self.run_reverse("A", "chain.json")
        self.assertEqual(
            output.splitlines(),
            [
                "package=A",
                "version=1.0",
                "Reverse dependency graph:",
                "  A -> (none)",
            ],
        )


if __name__ == "__main__":
    unittest.main()