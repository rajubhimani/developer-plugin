"""Write the split project docs for a folder, in a docs/ folder beside the repos.

Layout (umbrella = the folder that holds the repos). Root stays short; each
project carries its own index and files:

    <umbrella>/docs/INDEX.md                      one row per project
    <umbrella>/docs/links.md                      which projects depend on which
    <umbrella>/docs/notes.md                      common notes, written by you
    <umbrella>/docs/projects/<name>/INDEX.md      entry point for the project
    <umbrella>/docs/projects/<name>/commands.md   build, test, run (generated)
    <umbrella>/docs/projects/<name>/notes.md      your notes (never generated)
    <umbrella>/docs/projects/<name>/*.md          any other topic files you add

Generated sections are rewritten on each run; anything you write outside them
is kept. Project folder mode (one repo) refreshes only that repo's files, using
its parent folder as the umbrella unless the parent is home.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_navigator import (  # noqa: E402  (import after path setup)
    DOCS_DIR, Project, find_repos, inspect, resolve_links,
)

INDEX_FILE = "INDEX.md"
LINKS_FILE = "links.md"
NOTES_FILE = "notes.md"
PROJECTS_DIR = "projects"
COMMANDS_FILE = "commands.md"
PROJECT_NOTES_FILE = "notes.md"
BEGIN = "<!-- auto:begin (rewritten by init_workspace; edit below the end marker) -->"
END = "<!-- auto:end -->"
TARGET_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):", re.M)


def commands(project: Project) -> list[str]:
    """List the make targets and package.json scripts a project offers."""
    found: list[str] = []
    makefile = project.path / "Makefile"
    if makefile.exists():
        targets = TARGET_RE.findall(makefile.read_text(encoding="utf-8", errors="replace"))
        found += [f"make {t}" for t in targets if not t.startswith(".")]
    package = project.path / "package.json"
    if package.exists():
        try:
            scripts = json.loads(package.read_text(encoding="utf-8")).get("scripts", {})
        except (OSError, ValueError):
            scripts = {}
        found += [f"npm run {s}" for s in scripts]
    return found


def index_auto(project: Project, links: list[str], others: list[str]) -> str:
    """Render the generated part of a project's INDEX.md."""
    lines = [
        BEGIN, "",
        f"# {project.name}", "",
        f"- Path: `{project.path}`",
        f"- Remote: {project.remote or 'none'}",
        f"- Stack: {', '.join(project.stack) or '-'}",
        f"- Depends on: {', '.join(links) or 'none'}",
    ]
    lines += ["", "## Read first (in the repo)", ""]
    lines += [f"- [{name}](../../../{project.name}/{name})" for name in project.context_files]
    lines += ["", "## Files in this folder", ""]
    lines += [f"- [{name}]({name})" for name in others] or ["- none yet"]
    lines += ["", END, ""]
    return "\n".join(lines)


def write_index(folder: Path, project: Project, links: list[str]) -> str:
    """Create or refresh a project's INDEX.md, keeping anything outside the markers."""
    others = sorted(p.name for p in folder.glob("*.md") if p.name != INDEX_FILE)
    auto = index_auto(project, links, others)
    path = folder / INDEX_FILE
    if not path.exists():
        path.write_text(auto, encoding="utf-8")
        return "created"
    text = path.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        return "kept (no auto markers; add them to let the tool refresh it)"
    head, rest = text.split(BEGIN, 1)
    tail = rest.split(END, 1)[1]
    new_auto = auto.split(BEGIN, 1)[1].split(END, 1)[0]
    new = head + BEGIN + new_auto + END + tail
    if new == text:
        return "unchanged"
    path.write_text(new, encoding="utf-8")
    return "refreshed"


def write_generated(path: Path, text: str) -> None:
    """Write a fully generated file, skipping the write when nothing changed."""
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def project_commands_text(project: Project) -> str:
    """Render one project's commands file."""
    lines = [f"# Commands: {project.name}", "", "Generated. Edit the project, not this file.", ""]
    cmds = commands(project)
    lines += [f"- `{c}`" for c in cmds] or ["- none found"]
    return "\n".join(lines) + "\n"


def write_project_files(docs: Path, project: Project, links: list[str]) -> str:
    """Write a project's folder: INDEX (refreshed), commands (generated), notes (yours)."""
    folder = docs / PROJECTS_DIR / project.name
    folder.mkdir(parents=True, exist_ok=True)
    write_generated(folder / COMMANDS_FILE, project_commands_text(project))
    result = write_index(folder, project, links)
    notes = folder / PROJECT_NOTES_FILE
    if not notes.exists():
        notes.write_text(f"# Notes: {project.name}\n\nAdd facts you want kept here. "
                         "Generated files never edit this file.\n", encoding="utf-8")
    return result


def index_text(root: Path, projects: list[Project]) -> str:
    """Render the short root entry point: one row per project."""
    lines = [
        "# Projects index", "",
        f"Folder: `{root}`. Regenerate with `make navigator`.", "",
        "| Project | Purpose | Open |",
        "|---|---|---|",
    ]
    for p in projects:
        purpose = (p.summary.split(". ")[0][:90] or "-").replace("|", "/")
        target = f"{PROJECTS_DIR}/{p.name}/{INDEX_FILE}"
        lines.append(f"| {p.name} | {purpose} | [{target}]({target}) |")
    lines += [
        "", "## Shared", "",
        f"- [{LINKS_FILE}]({LINKS_FILE}): which projects depend on which",
        f"- [{NOTES_FILE}]({NOTES_FILE}): common notes you keep (never generated)",
        "",
    ]
    return "\n".join(lines)


def links_text(links: dict[str, list[str]]) -> str:
    """Render only the dependency links between projects."""
    lines = ["# Links between projects", "", "Generated from local path dependencies.", ""]
    if not links:
        lines.append("- None found.")
    for src, dsts in sorted(links.items()):
        lines.append(f"- `{src}` depends on " + ", ".join(f"`{d}`" for d in dsts))
    return "\n".join(lines) + "\n"


def notes_default() -> str:
    """Starting text for the user's common notes file."""
    return ("# Common notes\n\nFacts shared across projects. Generated files never "
            "edit this file.\n\n## Commands\n\n## Conventions\n\n## How projects connect\n")


def workspace_file(root: Path, projects: list[Project]) -> str:
    """Create or update the VS Code multi-root workspace for the folder.

    The folder list is rewritten on every run so it matches the repos. Any
    other keys (settings, extensions) the user added are kept.
    """
    name = f"{root.name or 'Projects'}.code-workspace"
    target = root / name
    data: dict = {}
    if target.exists():
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except ValueError:
            return f"{name}: kept (not valid JSON; fix or delete it to regenerate)"
    folders = [{"path": p.name} for p in projects] + [{"path": DOCS_DIR}]
    data["folders"] = folders
    data.setdefault("settings", {})
    new = json.dumps(data, indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") == new:
        return f"{name}: unchanged"
    target.write_text(new, encoding="utf-8")
    return f"{name}: written"


LONG_LINES = 100
UMBRELLA_AGENTS = """# Projects folder

This folder holds several repos. Do not scan it; use the docs instead.

- Start at `docs/INDEX.md` for the list of projects.
- Then open the project's `docs/projects/<name>/INDEX.md`.
- Shared rules: `docs/notes.md`. Links between projects: `docs/links.md`.
- Each repo has its own AGENTS.md, CLAUDE.md or README.md; read those for rules.
"""
UMBRELLA_CLAUDE = "@AGENTS.md\n"


def write_umbrella_agent_files(root: Path) -> list[str]:
    """Create the umbrella AGENTS.md and CLAUDE.md once; never overwrite edits."""
    created = []
    for name, text in (("AGENTS.md", UMBRELLA_AGENTS), ("CLAUDE.md", UMBRELLA_CLAUDE)):
        path = root / name
        if not path.exists():
            path.write_text(text, encoding="utf-8")
            created.append(name)
    return [f"umbrella agent files: {', '.join(created)} created"] if created else []


def long_files(docs: Path) -> list[str]:
    """Name docs over LONG_LINES that lack a contents list."""
    flagged = []
    for path in sorted(docs.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if text.count("\n") > LONG_LINES and "## Contents" not in text:
            flagged.append(f"long file, add a '## Contents' list: {path.relative_to(docs.parent)}")
    return flagged


def write_umbrella(root: Path, projects: list[Project], links: dict[str, list[str]]) -> list[str]:
    """Write the root files, every project folder, and the workspace file."""
    docs = root / DOCS_DIR
    docs.mkdir(exist_ok=True)
    write_generated(docs / INDEX_FILE, index_text(root, projects))
    write_generated(docs / LINKS_FILE, links_text(links))
    notes = docs / NOTES_FILE
    if not notes.exists():
        notes.write_text(notes_default(), encoding="utf-8")
    results = [f"{p.name}: {write_project_files(docs, p, links.get(p.name, []))}"
               for p in projects]
    results.append(workspace_file(root, projects))
    results.extend(write_umbrella_agent_files(root))
    results.extend(long_files(docs))
    return results


def main(argv: list[str]) -> int:
    """Detect umbrella or project mode for the folder and write the docs."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--quiet", action="store_true", help="print nothing when nothing applies")
    args = parser.parse_args(argv)
    root = args.folder.expanduser().resolve()
    if root == Path.home():
        if not args.quiet:
            print("home folder: not scanned; run from an umbrella or project folder")
        return 0

    if (root / ".git").exists():
        umbrella = root.parent if root.parent != Path.home() else root
        project = inspect(root, root.parent)
        results = [f"{project.name}: " + write_project_files(umbrella / DOCS_DIR, project, [])]
        mode = "project"
        docs = umbrella / DOCS_DIR
    else:
        repos = find_repos(root)
        if not repos:
            if not args.quiet:
                print(f"no repos under {root}; nothing to do")
            return 0
        projects = [inspect(path, root) for path in repos]
        links = resolve_links(projects)
        results = write_umbrella(root, projects, links)
        mode = "umbrella"
        docs = root / DOCS_DIR
    if not args.quiet:
        for line in results:
            print(f"{mode}: {line}")
        print(f"done: {mode} mode, docs in {docs}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
