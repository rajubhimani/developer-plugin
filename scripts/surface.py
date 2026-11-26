"""The plugin's public surface, and what a release must do about a change to it.

The surface is what a user can name: skills, agents, project kinds and make commands.
Comparing it with the last release tag gives the lowest version level the changes allow:

    removed something          major (minor while the major version is 0)
    added something            minor
    nothing added or removed   patch

A removal also needs one release of warning, or a major release: list the element in
deprecations.json first, say how to migrate, and remove it later. `make check` fails a
removal that has neither. `release.py bump` refuses a level below the floor.

    python3 scripts/surface.py            print the floor and why
    python3 scripts/surface.py --check    exit 1 on a removal the version does not allow

Standard library only. With no release tag there is nothing to compare, and it says so.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEPRECATIONS = "deprecations.json"
LEVELS = ("patch", "minor", "major")
KINDS = ("skill", "agent", "kind", "command")
TAG_PATTERN = "v[0-9]*.[0-9]*.[0-9]*"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

Element = tuple[str, str]


def git(root: Path, *args: str) -> str | None:
    """Run git in root and return its output, or None when it fails."""
    try:
        done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None
    return done.stdout if done.returncode == 0 else None


def elements(paths: list[str], makefile: str) -> set[Element]:
    """Return the surface named by repository paths (POSIX, relative) and the Makefile text."""
    found: set[Element] = set()
    for path in paths:
        parts = path.split("/")
        if len(parts) == 3 and parts[0] == "skills" and parts[2] == "SKILL.md":
            found.add(("skill", parts[1]))
        elif len(parts) == 2 and parts[0] == "agents" and parts[1].endswith(".md"):
            found.add(("agent", parts[1][:-3]))
        elif len(parts) == 5 and parts[:2] == ["templates", "kinds"] and parts[4] == "kind.json":
            found.add(("kind", f"{parts[2]}/{parts[3]}"))
    for line in makefile.splitlines():
        match = re.match(r"^([a-zA-Z0-9_-]+):.*## ", line)
        if match:
            found.add(("command", match.group(1)))
    return found


def tree_surface(root: Path = ROOT) -> set[Element]:
    """Return the surface of the working tree."""
    paths = [p.relative_to(root).as_posix() for pattern in ("skills/*/SKILL.md", "agents/*.md", "templates/kinds/*/*/kind.json")
             for p in root.glob(pattern)]
    makefile = root / "Makefile"
    return elements(paths, makefile.read_text(encoding="utf-8") if makefile.is_file() else "")


def ref_surface(ref: str, root: Path = ROOT) -> set[Element] | None:
    """Return the surface at a git ref, or None when git cannot read it."""
    listing = git(root, "ls-tree", "-r", "--name-only", ref)
    if listing is None:
        return None
    return elements(listing.splitlines(), git(root, "show", f"{ref}:Makefile") or "")


def last_tag(root: Path = ROOT) -> str | None:
    """Return the newest release tag reachable from HEAD, or None."""
    out = git(root, "describe", "--tags", "--abbrev=0", "--match", TAG_PATTERN)
    return out.strip() if out else None


def version_of(text: str | None) -> str | None:
    """Return the version in a plugin.json text."""
    try:
        return str(json.loads(text or "")["version"])
    except (ValueError, KeyError, TypeError):
        return None


def deprecated(text: str | None) -> set[Element]:
    """Return the (kind, name) pairs a deprecations.json text lists."""
    try:
        return {(str(e["kind"]), str(e["name"])) for e in json.loads(text or "")["deprecated"]}
    except (ValueError, KeyError, TypeError):
        return set()


def parts(version: str | None) -> tuple[int, int, int] | None:
    """Parse MAJOR.MINOR.PATCH, or None."""
    match = SEMVER.match(version or "")
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def step(old: str | None, new: str | None) -> str | None:
    """Return the level of the step from one version to another, or None when there is none."""
    a, b = parts(old), parts(new)
    if a is None or b is None or b <= a:
        return None
    return "major" if b[0] > a[0] else "minor" if b[1] > a[1] else "patch"


def floor(baseline_version: str | None, added: list[Element], removed: list[Element]) -> tuple[str, list[str]]:
    """Return (lowest allowed level, reasons)."""
    reasons = []
    if removed:
        level = "major"
        if (parts(baseline_version) or (1,))[0] == 0:
            level = "minor"  # before the first stable release a minor may break things
            reasons.append("breaking changes may ship in a minor release before 1.0")
        reasons.insert(0, "removed: " + ", ".join(f"{k} {n}" for k, n in removed))
        return level, reasons
    if added:
        return "minor", ["added: " + ", ".join(f"{k} {n}" for k, n in added)]
    return "patch", ["nothing added or removed"]


def compare(root: Path = ROOT) -> dict[str, object]:
    """Compare the working tree with the last release tag."""
    tag = last_tag(root)
    if tag is None:
        return {"tag": None}
    before = ref_surface(tag, root)
    if before is None:
        return {"tag": None}
    now = tree_surface(root)
    added, removed = sorted(now - before), sorted(before - now)
    base_version = tag.removeprefix("v")
    level, reasons = floor(base_version, added, removed)
    tree_version = version_of((root / "plugin.json").read_text(encoding="utf-8")) if (root / "plugin.json").is_file() else None
    return {"tag": tag, "base_version": base_version, "tree_version": tree_version, "added": added,
            "removed": removed, "floor": level, "reasons": reasons,
            "was_deprecated": deprecated(git(root, "show", f"{tag}:{DEPRECATIONS}")),
            "now_deprecated": deprecated((root / DEPRECATIONS).read_text(encoding="utf-8")
                                         if (root / DEPRECATIONS).is_file() else None)}


def problems(root: Path = ROOT) -> list[str]:
    """Return what `make check` fails on: a removal the version does not allow."""
    result = compare(root)
    if result["tag"] is None or not result["removed"]:
        return []
    allowed = step(str(result["base_version"]), str(result["tree_version"]))
    needed = str(result["floor"])
    if allowed is not None and LEVELS.index(allowed) >= LEVELS.index(needed):
        return []  # the release commit already carries the version that permits it
    gone = ", ".join(f"{k} {n}" for k, n in result["removed"])  # type: ignore[union-attr]
    return [f"{gone} removed since {result['tag']}. Keep it and list it in {DEPRECATIONS} for one release "
            f"(with its successor), or release a {needed} version"]


def main(argv: list[str]) -> int:
    """Print the floor, or check the surface."""
    result = compare()
    if result["tag"] is None:
        print("no release tag yet: the surface comparison starts after the first tag (vX.Y.Z)")
        return 0
    if "--check" in argv:
        found = problems()
        for line in found:
            print(f"FAIL {line}")
        return 1 if found else 0
    print(f"since {result['tag']}: lowest level {result['floor']} ({'; '.join(result['reasons'])})")  # type: ignore[arg-type]
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
