"""Generate the tool-specific copies of rules/coding-standards.md.

The rules file is the single source. The skill (read by Claude Code, Codex and
GitHub Copilot) and GEMINI.md (always loaded by Gemini CLI) are generated from
it, so the copies cannot drift. Run with --check to fail on drift.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "rules" / "coding-standards.md"
SKILL = ROOT / "skills" / "coding-standards" / "SKILL.md"
GEMINI = ROOT / "GEMINI.md"

SKILL_HEADER = """---
name: coding-standards
description: Coding standards for every change: latest stable versions, structure, style, tests, docs and index pages, and git rules. Use whenever writing, changing or reviewing code or docs.
---

"""

GEMINI_HEADER = """# Developer plugin

Apply the rules below to every code or docs change. Skills in `skills/` hold
task-specific steps; read a skill's `SKILL.md` before following it.

"""


def body() -> str:
    """Return the rules text without the title line."""
    text = SOURCE.read_text(encoding="utf-8")
    return text.split("\n", 1)[1].lstrip("\n")


def expected() -> dict[Path, str]:
    """Return the generated content for each target file."""
    rules = body()
    return {SKILL: SKILL_HEADER + rules, GEMINI: GEMINI_HEADER + rules}


def main(argv: list[str]) -> int:
    """Write the generated files, or with --check only report drift."""
    check = "--check" in argv
    stale = []
    for path, content in expected().items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != content:
            stale.append(path)
            if not check:
                path.write_text(content, encoding="utf-8")
    if check:
        for path in stale:
            print("STALE", path.relative_to(ROOT), "- run make sync-rules")
        return 1 if stale else 0
    print("synced:", ", ".join(str(p.relative_to(ROOT)) for p in expected()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
