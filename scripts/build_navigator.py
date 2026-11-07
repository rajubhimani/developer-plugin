"""Scan a projects folder for git repos and read what each one declares.

Library module used by init_workspace.py, which writes the docs. Finds repos
up to MAX_DEPTH deep, reads their manifests and context files, and resolves
links between projects from local path dependencies. Standard library only.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

DOCS_DIR = "docs"
SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", "target", ".next",
    DOCS_DIR,
}
MANIFESTS = ("pyproject.toml", "package.json", "Cargo.toml", "go.mod", "plugin.json")
CONTEXT_FILES = ("CLAUDE.md", "AGENTS.md", "README.md")
SUMMARY_SOURCES = ("README.md", "CLAUDE.md", "AGENTS.md")
MAX_DEPTH = 3
INFO_FILE = "PROJECT-INFO.md"
PATH_DEP_RE = re.compile(r"""(?:file:|path\s*=\s*|["'])(\.{1,2}/[^"'\s,)]+)""")


@dataclass
class Project:
    """One discovered repository and what its files say about it."""

    name: str
    path: Path
    stack: list[str] = field(default_factory=list)
    summary: str = ""
    remote: str = ""
    last_commit: str = ""
    context_files: list[str] = field(default_factory=list)
    local_deps: set[str] = field(default_factory=set)


def find_repos(root: Path) -> list[Path]:
    """Return folders under root that contain .git, up to MAX_DEPTH deep."""
    found: list[Path] = []
    stack = [(root, 0)]
    while stack:
        folder, depth = stack.pop()
        if (folder / ".git").exists() and folder != root:
            found.append(folder)
            continue
        if depth >= MAX_DEPTH:
            continue
        for child in sorted(folder.iterdir()):
            if child.is_dir() and child.name not in SKIP_DIRS and not child.name.startswith("."):
                stack.append((child, depth + 1))
    return sorted(found)


def git(path: Path, *args: str) -> str:
    """Run a read-only git command and return its stripped output, or ''."""
    try:
        out = subprocess.run(
            ["git", "-C", str(path), *args],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def first_paragraph(text: str) -> str:
    """Return the first non-heading paragraph of a Markdown file."""
    for block in text.split("\n\n"):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if lines and not lines[0].startswith("#"):
            return " ".join(lines)[:200]
    return ""


def inspect(path: Path, root: Path) -> Project:
    """Read the manifests and context files of one repo."""
    project = Project(name=path.relative_to(root).as_posix(), path=path)
    project.remote = git(path, "remote", "get-url", "origin")
    project.last_commit = git(path, "log", "-1", "--format=%cs")
    for name in MANIFESTS:
        manifest = path / name
        if manifest.exists():
            project.stack.append(name)
            text = manifest.read_text(encoding="utf-8", errors="replace")
            project.local_deps.update(PATH_DEP_RE.findall(text))
    for name in CONTEXT_FILES:
        doc = path / name
        if doc.exists():
            project.context_files.append(name)
    for name in SUMMARY_SOURCES:
        doc = path / name
        if not project.summary and doc.exists():
            project.summary = first_paragraph(doc.read_text(encoding="utf-8", errors="replace"))
    return project


def resolve_links(projects: list[Project]) -> dict[str, list[str]]:
    """Map each project to the other projects its local paths point at."""
    by_path = {p.path.resolve(): p.name for p in projects}
    links: dict[str, list[str]] = {}
    for project in projects:
        targets = set()
        for rel in project.local_deps:
            target = (project.path / rel).resolve()
            for known, name in by_path.items():
                if target == known or known in target.parents:
                    if name != project.name:
                        targets.add(name)
        if targets:
            links[project.name] = sorted(targets)
    return links
