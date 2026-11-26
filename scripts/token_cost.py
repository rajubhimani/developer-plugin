"""Estimate what the plugin costs in context: always loaded versus loaded on use.

    python3 scripts/token_cost.py

Counts about four characters to a token, so treat the numbers as a guide. For the exact
figure Claude Code computes, run `claude plugin details developer-plugin`. That command
does not count agents listed in the manifest (they live in claude-agents/), so its total
is lower than this one by the agent descriptions.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fields(path: Path) -> tuple[dict[str, str], str]:
    """Return the front matter pairs and the whole text of a markdown file."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    pairs = {}
    for line in (match.group(1).splitlines() if match else []):
        key, _, value = line.partition(":")
        pairs[key.strip()] = value.strip()
    return pairs, text


def tokens(chars: int) -> int:
    """Return a rough token count for a number of characters."""
    return round(chars / 4)


def main() -> int:
    rows = []
    for kind, pattern in (("skill", "skills/*/SKILL.md"), ("agent", "claude-agents/*.md")):
        for path in sorted(ROOT.glob(pattern)):
            meta, text = fields(path)
            name = meta.get("name", path.stem)
            always = len(name) + len(meta.get("description", ""))
            rows.append((kind, name, tokens(always), tokens(len(text))))
    always_total = sum(row[2] for row in rows)
    print(f"always loaded in every session: about {always_total} tokens "
          f"({sum(1 for r in rows if r[0] == 'skill')} skills, {sum(1 for r in rows if r[0] == 'agent')} agents)")
    print("one dispatch of each agent (its prompt plus the skills it preloads):")
    sizes = {name: body for kind, name, _, body in rows if kind == "skill"}
    for path in sorted(ROOT.glob("claude-agents/*.md")):
        meta, text = fields(path)
        block = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        preload, grab = [], False
        for line in (block.group(1).splitlines() if block else []):
            if line.startswith("skills:"):
                grab = True
            elif grab and line.startswith("  - "):
                preload.append(line.strip(" -"))
            else:
                grab = False
        print(f"  {path.stem:<22} about {tokens(len(text)) + sum(sizes.get(n, 0) for n in preload)} tokens "
              f"({len(preload)} skills preloaded)")
    print("largest when used:")
    for kind, name, _, body in sorted(rows, key=lambda row: -row[3])[:8]:
        print(f"  {name:<28} {kind:<6} about {body} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
