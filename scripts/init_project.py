"""Copy the standard project files for one language into a repo, without overwriting.

Usage: python3 scripts/init_project.py <repo folder> <language>

Languages: python, go, rust, node, c, cpp, java. Each run reports which files it
created and which it kept because they already existed. Standard library only.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
LANGUAGES = ("python", "go", "rust", "node", "c", "cpp", "java")
SHARED = ("Dockerfile", "compose.yaml", ".dockerignore", ".editorconfig", ".gitignore",
          "AGENTS.md", "CLAUDE.md")


def plan(language: str) -> list[tuple[Path, Path]]:
    """Return (template, destination name) pairs for one language."""
    pairs = [(TEMPLATES / "makefiles" / f"{language}.mk", Path("Makefile"))]
    pairs += [(TEMPLATES / name, Path(name)) for name in SHARED]
    pairs.append((TEMPLATES / "alignment" / "test_alignment.py", Path("tests/alignment/test_alignment.py")))
    pairs.append((TEMPLATES / "docs" / "requirements.md", Path("docs/requirements.md")))
    pairs += [
        (TEMPLATES / "gitattributes", Path(".gitattributes")),
        (TEMPLATES / "gitmessage", Path(".gitmessage")),
        (TEMPLATES / "github" / "pull_request_template.md", Path(".github/pull_request_template.md")),
        (TEMPLATES / "CHANGELOG.md", Path("CHANGELOG.md")),
    ]
    pairs.append((ROOT / "scripts" / "tasks.py", Path("scripts/tasks.py")))
    pairs.append((ROOT / "skills" / "ci-cd" / "references" / "github-actions.yml",
                  Path(".github/workflows/ci.yml")))
    return pairs


GIT_MISSING = ("git is not installed. Install it, then run `git init` in the repo:\n"
               "  macOS:          xcode-select --install   or   brew install git\n"
               "  Debian/Ubuntu:  sudo apt install git\n"
               "  Windows:        winget install --id Git.Git")


def ensure_git(repo: Path) -> str:
    """Create a git repository if the folder is not one yet. Never commits."""
    if (repo / ".git").exists():
        return "git repository: already set up"
    if shutil.which("git") is None:
        return GIT_MISSING
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return "git repository: initialized (no commit yet; commit when ready)"


def set_commit_template(repo: Path) -> None:
    """Point the repo's commit template at .gitmessage, if git is available."""
    if shutil.which("git") and (repo / ".git").exists() and (repo / ".gitmessage").exists():
        subprocess.run(["git", "config", "commit.template", ".gitmessage"], cwd=repo, check=False)


TASK_MARKER = "# tasks: start"
TASK_STATUSES = ("backlog", "in-progress", "completed", "rejected")


def add_task_tracking(repo: Path) -> list[str]:
    """Add task folders and the task make targets, once; never duplicate them."""
    results = []
    folder = repo / "docs" / "tasks"
    for status in TASK_STATUSES:
        (folder / status).mkdir(parents=True, exist_ok=True)
        (folder / status / ".gitkeep").touch()
    (repo / "docs" / "features").mkdir(parents=True, exist_ok=True)
    makefile = repo / "Makefile"
    if makefile.exists() and TASK_MARKER not in makefile.read_text(encoding="utf-8"):
        block = (TEMPLATES / "makefiles" / "tasks.mk").read_text(encoding="utf-8")
        makefile.write_text(makefile.read_text(encoding="utf-8").rstrip("\n") + "\n\n" + block,
                            encoding="utf-8")
        results.append("added task targets to Makefile")
    return results


def main(argv: list[str]) -> int:
    """Copy missing template files into the target repo."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path)
    parser.add_argument("language", choices=LANGUAGES)
    args = parser.parse_args(argv)
    repo = args.repo.expanduser().resolve()
    if not repo.is_dir():
        print(f"not a folder: {repo}", file=sys.stderr)
        return 1
    for source, relative in plan(args.language):
        if not source.exists():
            print(f"missing template: {source.relative_to(ROOT)}", file=sys.stderr)
            return 1
        target = repo / relative
        if target.exists():
            print(f"kept    {relative} (already exists)")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"created {relative}")
    print(ensure_git(repo))
    set_commit_template(repo)
    for message in add_task_tracking(repo):
        print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
