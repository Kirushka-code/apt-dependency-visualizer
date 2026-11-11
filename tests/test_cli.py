"""Tests for command-line configuration and validation."""

import io
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from src.cli import main, parse_arguments


class CliTests(unittest.TestCase):
    """Check valid configurations and invalid command-line arguments."""

    def make_arguments(self, **changes):
        """Build a valid argument list with optional replacements."""
        values = {
            "--package": "bash",
            "--repository": "https://example.org/Packages.gz",
            "--version": "1.0",
        }
        values.update(changes)
        return [
            item
            for option, value in values.items()
            for item in (option, value)
        ]

    def assert_rejected(self, arguments):
        """Check that invalid arguments produce an argparse error."""
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as context:
                parse_arguments(arguments)
        self.assertEqual(context.exception.code, 2)

    def test_valid_configuration(self):
        """Accept an HTTP repository and an Ubuntu package name."""
        arguments = parse_arguments(self.make_arguments())
        self.assertEqual(arguments.package, "bash")
        self.assertEqual(arguments.version, "1.0")
        self.assertFalse(arguments.test_mode)

    def test_output(self):
        """Print the requested package and its direct dependencies."""
        record = {
            "Package": "bash",
            "Version": "1.0",
            "Depends": "libc6 (>= 2.34)",
        }
        output = io.StringIO()
        with patch("src.cli.load_package", return_value=record):
            with redirect_stdout(output):
                result = main(self.make_arguments())
        self.assertEqual(result, 0)
        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "package=bash",
                "version=1.0",
                "Direct dependencies:",
                "  libc6 (>= 2.34)",
            ],
        )

    def test_invalid_values(self):
        """Reject malformed names, versions, and repository URLs."""
        cases = [
            {"--package": ""},
            {"--package": "Bad Name"},
            {"--version": ""},
            {"--version": "latest"},
            {"--repository": "not-a-url"},
            {"--repository": "ftp://example.org/Packages"},
            {"--repository": "https://example.org:bad/Packages"},
            {"--repository": "https://example.org/a b"},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                self.assert_rejected(self.make_arguments(**changes))

    def test_missing_parameters(self):
        """Reject omission of each required parameter."""
        arguments = self.make_arguments()
        for position in range(0, len(arguments), 2):
            with self.subTest(position=position):
                remaining = arguments[:position] + arguments[position + 2:]
                self.assert_rejected(remaining)

    def test_invalid_test_mode(self):
        """Reject a value passed to the boolean test-mode flag."""
        arguments = self.make_arguments() + ["--test-mode=false"]
        self.assert_rejected(arguments)

    def test_test_repository(self):
        """Accept a local file and uppercase names in test mode."""
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repository.json"
            repository.write_text("{}", encoding="utf-8")
            arguments = self.make_arguments(
                **{
                    "--package": "A",
                    "--repository": str(repository),
                }
            )
            parsed = parse_arguments(arguments + ["--test-mode"])
            self.assertTrue(parsed.test_mode)

    def test_invalid_test_repository(self):
        """Reject a missing file and a directory in test mode."""
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory), Path(directory) / "missing.json"]
            for path in paths:
                with self.subTest(path=path):
                    arguments = self.make_arguments(
                        **{"--package": "A", "--repository": str(path)}
                    )
                    self.assert_rejected(arguments + ["--test-mode"])


if __name__ == "__main__":
    unittest.main()