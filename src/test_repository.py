"""Read and validate local test repositories."""

import json
import re
from pathlib import Path

from src.repository import RepositoryError


TEST_NAME_PATTERN = r"[A-Z]+"


def validate_packages(packages):
    """Validate names, dependency lists, and referenced packages."""
    if not isinstance(packages, dict) or not packages:
        raise RepositoryError("packages must be a non-empty object")
    for name, dependencies in packages.items():
        if not re.fullmatch(TEST_NAME_PATTERN, name):
            raise RepositoryError("Test package names must be uppercase")
        if not isinstance(dependencies, list):
            raise RepositoryError("Dependencies must be lists")
        for dependency in dependencies:
            if not isinstance(dependency, str):
                raise RepositoryError("Dependency names must be strings")
            if dependency not in packages:
                raise RepositoryError(
                    f"Unknown dependency {dependency} of {name}"
                )


def read_test_repository(path, version):
    """Read a JSON repository with one shared package version."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
        data = json.loads(text)
    except (OSError, UnicodeError, ValueError) as error:
        raise RepositoryError(
            f"Cannot read test repository: {error}"
        ) from error
    if not isinstance(data, dict):
        raise RepositoryError("Test repository must be an object")
    if data.get("version") != version:
        raise RepositoryError(
            f"Test repository version does not match {version}"
        )
    packages = data.get("packages")
    validate_packages(packages)
    return packages