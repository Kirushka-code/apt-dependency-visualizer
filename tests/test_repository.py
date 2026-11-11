"""Tests for Ubuntu index parsing and repository access."""

import gzip
import io
import lzma
import unittest
from unittest.mock import patch
from urllib.error import URLError

from src.repository import (
    RepositoryError,
    direct_dependencies,
    download_index,
    find_package,
    parse_index,
)


INDEX = """Package: demo
Version: 1.0
Pre-Depends: base
Depends: libc6 (>= 2.34), first | second,
 extra
Description: Example package
 continued description

Package: demo
Version: 2.0
Depends: newer

Package: base
Version: 1.0

"""


class RepositoryTests(unittest.TestCase):
    """Check index parsing, exact versions, and download failures."""

    def test_exact_version(self):
        """Select the requested version instead of another version."""
        records = parse_index(INDEX)
        record = find_package(records, "demo", "1.0")
        self.assertEqual(record["Version"], "1.0")

    def test_dependencies(self):
        """Preserve constraints, alternatives, and folded fields."""
        record = find_package(parse_index(INDEX), "demo", "1.0")
        self.assertEqual(
            direct_dependencies(record),
            [
                "base",
                "libc6 (>= 2.34)",
                "first | second",
                "extra",
            ],
        )

    def test_no_dependencies(self):
        """Return an empty list for a package without dependencies."""
        record = find_package(parse_index(INDEX), "base", "1.0")
        self.assertEqual(direct_dependencies(record), [])

    def test_missing_package(self):
        """Report an unknown package."""
        with self.assertRaisesRegex(RepositoryError, "Package not found"):
            find_package(parse_index(INDEX), "missing", "1.0")

    def test_missing_version(self):
        """Report available versions when the exact version is absent."""
        with self.assertRaisesRegex(RepositoryError, "Available versions"):
            find_package(parse_index(INDEX), "demo", "9.0")

    def test_invalid_indexes(self):
        """Reject empty indexes and malformed package records."""
        cases = [
            "",
            "<html>Not a package index</html>",
            "Package: demo\n",
            " orphan continuation\n",
        ]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(RepositoryError):
                    parse_index(text)

    def test_supported_compression(self):
        """Read plain text, gzip, and xz without a network request."""
        raw = INDEX.encode("utf-8")
        payloads = [raw, gzip.compress(raw), lzma.compress(raw)]
        for payload in payloads:
            with self.subTest(signature=payload[:6]):
                with patch(
                    "src.repository.urlopen",
                    return_value=io.BytesIO(payload),
                ):
                    self.assertEqual(
                        download_index("https://example.org/Packages"),
                        INDEX,
                    )

    def test_network_error(self):
        """Convert network failures into application errors."""
        with patch(
            "src.repository.urlopen",
            side_effect=URLError("connection failed"),
        ):
            with self.assertRaises(RepositoryError):
                download_index("https://example.org/Packages")

    def test_corrupt_archive(self):
        """Report a damaged compressed index."""
        with patch(
            "src.repository.urlopen",
            return_value=io.BytesIO(b"\x1f\x8bbroken"),
        ):
            with self.assertRaises(RepositoryError):
                download_index("https://example.org/Packages.gz")


if __name__ == "__main__":
    unittest.main()