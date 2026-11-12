"""Compare application graphs with apt-cache dotty on Linux."""

import re
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

from src.application import load_graph


REPOSITORY = (
    "https://archive.ubuntu.com/ubuntu/dists/"
    "jammy/main/binary-amd64/Packages.gz"
)
PACKAGES = {
    "hello": "2.10-2ubuntu4",
    "gzip": "1.10-4ubuntu4",
    "sed": "4.8-1ubuntu2",
}
DOT_EDGE_PATTERN = r'"([^"]+)"\s*->\s*"([^"]+)"'


def run_command(arguments):
    """Run a comparison tool and report failures."""
    result = subprocess.run(
        arguments,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def apt_options(directory):
    """Configure an isolated apt index and empty installed state."""
    sources = directory / "sources.list"
    sources.write_text(
        "deb [arch=amd64] "
        "https://archive.ubuntu.com/ubuntu jammy main\n",
        encoding="utf-8",
    )
    status = directory / "status"
    status.write_text("", encoding="utf-8")
    lists = directory / "lists"
    (lists / "partial").mkdir(parents=True)
    return [
        "-o", f"Dir::Etc::sourcelist={sources}",
        "-o", "Dir::Etc::sourceparts=-",
        "-o", f"Dir::State::lists={lists}",
        "-o", f"Dir::State::status={status}",
        "-o", "Dir::Cache::pkgcache=",
        "-o", "Dir::Cache::srcpkgcache=",
        "-o", "APT::Get::List-Cleanup=0",
        "-o", "APT::Update::Error-Mode=any",
        "-o", "APT::Architecture=amd64",
    ]


def application_edges(name, version):
    """Read edges using the application's own repository parser."""
    arguments = SimpleNamespace(
        package=name,
        version=version,
        repository=REPOSITORY,
        test_mode=False,
    )
    graph, unresolved = load_graph(arguments)
    edges = {
        (source, target)
        for source, targets in graph.items()
        for target in targets
    }
    return edges, unresolved


def describe_edges(edges):
    """Format a set of edges for a Markdown report."""
    if not edges:
        return ["- None"]
    return [
        f"- `{source} -> {target}`"
        for source, target in sorted(edges)
    ]


def compare_package(name, version, options, output):
    """Save native DOT output and compare directed package pairs."""
    metadata = run_command(
        ["apt-cache", *options, "show", f"{name}={version}"]
    )
    if f"Version: {version}" not in metadata.splitlines():
        raise RuntimeError(f"apt does not contain {name}={version}")
    dot = run_command(["apt-cache", *options, "dotty", name])
    (output / f"{name}.dot").write_text(dot, encoding="utf-8")
    native = set(re.findall(DOT_EDGE_PATTERN, dot))
    own, unresolved = application_edges(name, version)
    lines = [
        f"## {name} {version}",
        "",
        f"Application edges: {len(own)}",
        f"apt-cache dotty edges: {len(native)}",
        f"Unresolved packages: {', '.join(unresolved) or 'none'}",
        "",
        "### Only in application",
        "",
        *describe_edges(own - native),
        "",
        "### Only in apt-cache dotty",
        "",
        *describe_edges(native - own),
        "",
    ]
    return lines


def main():
    """Compare three packages against an isolated Jammy apt cache."""
    output = Path("comparison")
    output.mkdir(exist_ok=True)
    report = ["# Comparison with apt-cache dotty", ""]
    with tempfile.TemporaryDirectory() as temporary:
        options = apt_options(Path(temporary))
        run_command(["apt-get", *options, "update"])
        for name, version in PACKAGES.items():
            report.extend(
                compare_package(name, version, options, output)
            )
    text = "\n".join(report)
    (output / "report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()