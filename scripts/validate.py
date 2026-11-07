"""Check that the plugin manifests agree and every skill has valid frontmatter."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = [ROOT / "plugin.json", ROOT / ".claude-plugin" / "plugin.json", ROOT / "gemini-extension.json"]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def load(path: Path) -> dict:
    """Parse a JSON manifest, failing with the file name on error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL {path.relative_to(ROOT)}: {exc}")


def frontmatter(path: Path) -> dict:
    """Return the simple key: value pairs at the top of a SKILL.md file."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise SystemExit(f"FAIL {path.relative_to(ROOT)}: missing frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def main() -> int:
    problems = []
    docs = [load(p) for p in MANIFESTS]
    names = {d["name"] for d in docs}
    versions = {d["version"] for d in docs}
    if len(names) != 1:
        problems.append(f"names differ: {sorted(names)}")
    if len(versions) != 1:
        problems.append(f"versions differ: {sorted(versions)}")

    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        fields = frontmatter(skill)
        folder = skill.parent.name
        if fields.get("name") != folder:
            problems.append(f"{folder}: name '{fields.get('name')}' must match folder")
        if not NAME_RE.match(folder):
            problems.append(f"{folder}: name must be kebab-case")
        if not fields.get("description"):
            problems.append(f"{folder}: description missing")

    for p in problems:
        print("FAIL", p)
    if not problems:
        print("OK: manifests agree and skills are valid")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
