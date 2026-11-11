"""Download and parse Ubuntu repository package indexes."""

import gzip
import lzma
from urllib.error import URLError
from urllib.request import urlopen


DOWNLOAD_TIMEOUT = 60
GZIP_SIGNATURE = b"\x1f\x8b"
XZ_SIGNATURE = b"\xfd7zXZ\x00"


class RepositoryError(Exception):
    """Report repository access and package lookup errors."""


def download_index(url):
    """Download an index and decompress gzip or xz when needed."""
    try:
        with urlopen(url, timeout=DOWNLOAD_TIMEOUT) as response:
            data = response.read()
        if data.startswith(GZIP_SIGNATURE):
            data = gzip.decompress(data)
        elif data.startswith(XZ_SIGNATURE):
            data = lzma.decompress(data)
        return data.decode("utf-8")
    except (URLError, OSError, EOFError, ValueError) as error:
        raise RepositoryError(
            f"Cannot load repository index: {error}"
        ) from error
    except lzma.LZMAError as error:
        raise RepositoryError("Invalid xz repository index") from error


def parse_paragraph(paragraph):
    """Parse one Debian control paragraph, including continuations."""
    fields = {}
    current_field = None
    for line in paragraph.splitlines():
        if line.startswith((" ", "\t")):
            if current_field is None:
                raise RepositoryError("Continuation without a field")
            fields[current_field] += " " + line.strip()
        else:
            name, separator, value = line.partition(":")
            if not separator or not name.strip():
                raise RepositoryError("Invalid repository field")
            current_field = name.strip()
            fields[current_field] = value.strip()
    return fields


def parse_index(text):
    """Parse package records from a Debian Packages index."""
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        raise RepositoryError("Repository index is empty")
    records = []
    for paragraph in normalized.split("\n\n"):
        if not paragraph.strip():
            continue
        record = parse_paragraph(paragraph)
        if "Package" not in record or "Version" not in record:
            raise RepositoryError("Record lacks Package or Version")
        records.append(record)
    return records


def find_package(records, name, version):
    """Find a package by exact name and version."""
    available = set()
    for record in records:
        if record["Package"] != name:
            continue
        available.add(record["Version"])
        if record["Version"] == version:
            return record
    if available:
        versions = ", ".join(sorted(available))
        raise RepositoryError(
            f"Version {version} not found for {name}. "
            f"Available versions: {versions}"
        )
    raise RepositoryError(f"Package not found: {name}")


def load_package(url, name, version):
    """Load an index and return the exact requested package record."""
    text = download_index(url)
    records = parse_index(text)
    return find_package(records, name, version)


def direct_dependencies(record):
    """Return mandatory dependency groups with alternatives preserved."""
    dependencies = []
    for field in ("Pre-Depends", "Depends"):
        value = record.get(field, "")
        dependencies.extend(
            group.strip()
            for group in value.split(",")
            if group.strip()
        )
    return dependencies