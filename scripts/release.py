"""Versioning for the developer plugin: bump, verify and extract release notes.

Versions follow semantic versioning (MAJOR.MINOR.PATCH). The manifests share one
version; the changelog's "## [Unreleased]" section becomes the new release.

    python3 scripts/release.py bump major|minor|patch   update files; you commit and tag
    python3 scripts/release.py verify vX.Y.Z           check manifests and changelog match
    python3 scripts/release.py notes vX.Y.Z            print that release's changelog section

Standard library only. This script never commits or tags.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = [ROOT / "plugin.json", ROOT / ".claude-plugin" / "plugin.json"]
CHANGELOG = ROOT / "CHANGELOG.md"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def manifest_versions() -> dict[str, str]:
    """Return the version each manifest declares."""
    return {str(p.relative_to(ROOT)): str(json.loads(p.read_text(encoding="utf-8"))["version"])
            for p in MANIFESTS}


def current_version() -> str:
    """Return the shared version, or fail if the manifests disagree."""
    versions = set(manifest_versions().values())
    if len(versions) != 1:
        raise SystemExit(f"manifests disagree on the version: {manifest_versions()}")
    return versions.pop()


def bump(version: str, level: str) -> str:
    """Return the next version for a major, minor or patch release."""
    match = SEMVER.match(version)
    if not match:
        raise SystemExit(f"not a MAJOR.MINOR.PATCH version: {version}")
    major, minor, patch = (int(x) for x in match.groups())
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    if level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise SystemExit("level must be major, minor or patch")


def section(text: str, heading: str) -> str:
    """Return the body of a changelog section, without its heading."""
    match = re.search(rf"^## \[{re.escape(heading)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.S | re.M)
    return match.group(1).strip() if match else ""


def write_manifests(version: str) -> None:
    """Set the version in every manifest, keeping the rest of each file."""
    for path in MANIFESTS:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["version"] = version
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def bump_release(level: str, date: str) -> str:
    """Bump the version and close the Unreleased section into a dated release."""
    text = CHANGELOG.read_text(encoding="utf-8")
    if "## [Unreleased]" not in text:
        raise SystemExit("CHANGELOG.md has no '## [Unreleased]' section")
    if not section(text, "Unreleased"):
        raise SystemExit("nothing to release: the Unreleased section is empty")
    new = bump(current_version(), level)
    if f"## [{new}]" in text:
        raise SystemExit(f"version {new} is already in the changelog")
    CHANGELOG.write_text(text.replace("## [Unreleased]", f"## [Unreleased]\n\n## [{new}] - {date}", 1),
                         encoding="utf-8")
    write_manifests(new)
    return new


def verify(version: str) -> None:
    """Fail unless the manifests and changelog both describe this version."""
    versions = set(manifest_versions().values())
    if versions != {version}:
        raise SystemExit(f"manifests say {sorted(versions)}, expected {version}")
    if not section(CHANGELOG.read_text(encoding="utf-8"), version):
        raise SystemExit(f"CHANGELOG.md has no notes for {version}")
    print(f"ok: {version} matches the manifests and the changelog")


def main(argv: list[str]) -> int:
    """Run one release command."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    bump_cmd = commands.add_parser("bump")
    bump_cmd.add_argument("level", choices=("major", "minor", "patch"))
    bump_cmd.add_argument("--date", default=dt.date.today().isoformat())
    verify_cmd = commands.add_parser("verify")
    verify_cmd.add_argument("version")
    notes_cmd = commands.add_parser("notes")
    notes_cmd.add_argument("version")
    args = parser.parse_args(argv)
    if args.command == "bump":
        new = bump_release(args.level, args.date)
        print(f"version {new}: manifests and CHANGELOG.md updated.")
        print("Next: review the diff, commit it, then tag:  git tag -a v" + new + " -m 'v" + new + "'")
    elif args.command == "verify":
        verify(args.version)
    else:
        print(section(CHANGELOG.read_text(encoding="utf-8"), args.version))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
