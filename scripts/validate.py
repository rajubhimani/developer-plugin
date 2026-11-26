"""Check that the plugin manifests agree and every skill has valid frontmatter."""

import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import surface  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = [ROOT / "plugin.json", ROOT / ".claude-plugin" / "plugin.json"]
MAX_AGE_DAYS = 90
MAX_DESCRIPTION = 300  # characters; descriptions load into every session
MAX_BODY_LINES = 500  # a skill body past this should move detail into references/
MAX_PRELOAD_TOKENS = 3000  # skills an agent starts with, at about four characters a token
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


def agent_skills(path: Path) -> tuple[list[str], list[str]]:
    """Return (the skills an agent preloads, the skills its Load on demand section names)."""
    text = path.read_text(encoding="utf-8")
    block = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    preload, grab = [], False
    for line in (block.group(1).splitlines() if block else []):
        if line.startswith("skills:"):
            grab = True
        elif grab and line.startswith("  - "):
            preload.append(line.strip(" -"))
        else:
            grab = False
    section = text.partition("## Load on demand")[2]
    return preload, re.findall(r"(?m)^- `([a-z0-9-]+)`:", section)


def main() -> int:
    problems = []
    docs = [load(p) for p in MANIFESTS]
    names = {d["name"] for d in docs}
    versions = {d["version"] for d in docs}
    if len(names) != 1:
        problems.append(f"names differ: {sorted(names)}")
    if len(versions) != 1:
        problems.append(f"versions differ: {sorted(versions)}")

    # What a stranger sees when they add the marketplace: it must name an owner and say
    # what it offers, and it must list this plugin under the plugin's own name.
    market = load(ROOT / ".claude-plugin" / "marketplace.json")
    if not market.get("owner", {}).get("name"):
        problems.append("marketplace.json: owner.name is missing")
    if not market.get("metadata", {}).get("description"):
        problems.append("marketplace.json: metadata.description is missing")
    if [entry.get("name") for entry in market.get("plugins", [])] != sorted(names):
        problems.append("marketplace.json: plugins must list this plugin by its manifest name")
    for doc in docs:
        for key in ("author", "homepage", "repository"):
            if not doc.get(key):
                problems.append(f"plugin manifest: {key} is missing (needed to share the plugin)")

    for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
        fields = frontmatter(skill)
        folder = skill.parent.name
        if fields.get("name") != folder:
            problems.append(f"{folder}: name '{fields.get('name')}' must match folder")
        if not NAME_RE.match(folder):
            problems.append(f"{folder}: name must be kebab-case")
        if not fields.get("description"):
            problems.append(f"{folder}: description missing")
        elif len(fields["description"]) > MAX_DESCRIPTION:
            problems.append(f"{folder}: description is {len(fields['description'])} characters; keep it under "
                            f"{MAX_DESCRIPTION} (it loads into every session)")
        lines = len(skill.read_text(encoding="utf-8").splitlines())
        if lines > MAX_BODY_LINES:
            problems.append(f"{folder}: SKILL.md is {lines} lines; keep it under {MAX_BODY_LINES} and move detail to references/")
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
        elif len(fields["description"]) > MAX_DESCRIPTION:
            problems.append(f"agents/{agent.stem}: description is {len(fields['description'])} characters; "
                            f"keep it under {MAX_DESCRIPTION} (it loads into every session)")
        if not fields.get("tools"):
            problems.append(f"agents/{agent.stem}: tools must be listed explicitly")
        if "memory" in fields:
            problems.append(f"agents/{agent.stem}: no memory field; lasting notes live in files")
        preload, on_demand = agent_skills(agent)
        known = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
        for name in [*preload, *on_demand]:
            if name not in known:
                problems.append(f"agents/{agent.stem}: names the skill '{name}', which does not exist")
        weight = sum(len((ROOT / "skills" / n / "SKILL.md").read_text(encoding="utf-8")) // 4
                     for n in preload if n in known)
        if weight > MAX_PRELOAD_TOKENS:
            problems.append(f"agents/{agent.stem}: preloads about {weight} tokens of skills (limit {MAX_PRELOAD_TOKENS}); "
                            "move the rest to Load on demand")
        if on_demand and "Skill" not in [t.strip() for t in fields.get("tools", "").split(",")]:
            problems.append(f"agents/{agent.stem}: has a Load on demand section but no Skill tool")

    problems += surface.problems(ROOT)

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
