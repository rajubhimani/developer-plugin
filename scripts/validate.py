"""Check that the plugin manifests agree and every skill has valid frontmatter."""

import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = [ROOT / "plugin.json", ROOT / ".claude-plugin" / "plugin.json"]
MAX_AGE_DAYS = 90
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
        checked = fields.get("verified", "")
        try:
            age = (dt.date.today() - dt.date.fromisoformat(checked)).days
        except ValueError:
            problems.append(f"{folder}: 'verified' date missing or not YYYY-MM-DD")
        else:
            if age > MAX_AGE_DAYS:
                problems.append(f"{folder}: last verified {age} days ago; re-check against current docs")

    for agent in sorted((ROOT / "agents").glob("*.md")):
        fields = frontmatter(agent)
        if fields.get("name") != agent.stem:
            problems.append(f"agents/{agent.stem}: name '{fields.get('name')}' must match file")
        if not NAME_RE.match(agent.stem):
            problems.append(f"agents/{agent.stem}: name must be kebab-case")
        if not fields.get("description"):
            problems.append(f"agents/{agent.stem}: description missing")
        if not fields.get("tools"):
            problems.append(f"agents/{agent.stem}: tools must be listed explicitly")
        if "memory" in fields:
            problems.append(f"agents/{agent.stem}: no memory field; lasting notes live in files")

    version_re = re.compile(r"(?<![\w.])\d+\.\d+(\.\d+)?(?![\w.])|\b(?:C|C\+\+)\d{2}\b|\bJDK ?\d+|\bJava \d+|\bPython 3\.\d+|\bNode\.?js? \d+|\bGo 1\.\d+")
    allowed = ("Agent Plugins 1.0",)  # a published specification's name, not a tool version
    doc_files = [ROOT / "README.md"] + sorted((ROOT / "docs").glob("*.md"))
    for doc in doc_files:
        for number, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            if any(a in line for a in allowed):
                continue
            if version_re.search(line):
                problems.append(f"{doc.relative_to(ROOT)}:{number}: hard-coded version or standard; say 'current' and look it up")
    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        full = skill.read_text(encoding="utf-8")
        body = "\n".join(line for line in full.splitlines() if not line.startswith("verified:"))
        for number, line in enumerate(body.splitlines(), 1):
            if version_re.search(line):
                problems.append(f"{skill.parent.name}:{number}: hard-coded version number; look it up instead")

    for p in problems:
        print("FAIL", p)
    if not problems:
        print("OK: manifests agree and skills are valid")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
