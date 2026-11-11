"""Command-line configuration for the dependency visualizer."""

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit


PACKAGE_PATTERN = r"[a-z0-9][a-z0-9+.-]*"
TEST_PACKAGE_PATTERN = r"[A-Z]+"
VERSION_PATTERN = r"(?:[0-9]+:)?[0-9][A-Za-z0-9.+:~\-]*"


def build_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Ubuntu package dependency visualizer.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--package",
        required=True,
        help="Package name; uppercase letters in test mode.",
    )
    parser.add_argument(
        "--repository",
        required=True,
        help="Repository index URL or test repository file path.",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Read a local test repository instead of a URL.",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Exact package version, for example 1.0.",
    )
    return parser


def validate_package(parser, arguments):
    """Validate the package name for the selected mode."""
    pattern = PACKAGE_PATTERN
    if arguments.test_mode:
        pattern = TEST_PACKAGE_PATTERN
    if not re.fullmatch(pattern, arguments.package):
        parser.error("invalid package name for the selected mode")


def validate_version(parser, version):
    """Validate the basic syntax of a Debian package version."""
    if not re.fullmatch(VERSION_PATTERN, version):
        parser.error("invalid version; expected a value such as 1.0")


def validate_test_repository(parser, repository):
    """Check that a test repository is a readable local file."""
    try:
        path = Path(repository)
        if not path.is_file():
            parser.error("test repository must be an existing file")
        with path.open("rb") as source:
            source.read(1)
    except (OSError, ValueError):
        parser.error("test repository file cannot be read")


def validate_repository_url(parser, repository):
    """Check the structure of an HTTP or HTTPS repository URL."""
    try:
        parts = urlsplit(repository)
        hostname = parts.hostname
        parts.port
    except ValueError:
        parser.error("invalid repository URL")
    if parts.scheme not in ("http", "https") or not hostname:
        parser.error("repository must be an HTTP or HTTPS URL")
    if any(character.isspace() for character in repository):
        parser.error("repository URL must not contain whitespace")
    if parts.username is not None or parts.password is not None:
        parser.error("repository URL must not contain credentials")
    if parts.fragment:
        parser.error("repository URL must not contain a fragment")


def parse_arguments(argv=None):
    """Parse arguments and validate all configurable parameters."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    validate_package(parser, arguments)
    validate_version(parser, arguments.version)
    if arguments.test_mode:
        validate_test_repository(parser, arguments.repository)
    else:
        validate_repository_url(parser, arguments.repository)
    return arguments


def main(argv=None):
    """Print the validated configuration as key-value pairs."""
    arguments = parse_arguments(argv)
    print(f"package={arguments.package}")
    print(f"repository={arguments.repository}")
    print(f"test_mode={str(arguments.test_mode).lower()}")
    print(f"version={arguments.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())