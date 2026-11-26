"""Keep track of the files the plugin wrote into a project, so an update never clobbers edits.

`init_project.py` records a hash of every file it creates in .developer-plugin/scaffold.json.
`init_project.py --update` then compares each file the plugin would write today with the file on
disk and with that record:

    missing                        created
    on disk equals today's text    unchanged (and adopted into the record)
    on disk equals the record      untouched since we wrote it, so it is refreshed
    on disk differs from record    edited by you: kept, and a diff is shown
    on disk, never recorded        not ours: kept

A file the plugin used to write and no longer does is reported, never deleted. Hashes ignore the
difference between Windows and Unix line endings. Standard library only.
"""

from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path

MANIFEST = Path(".developer-plugin") / "scaffold.json"


def text_hash(text: str) -> str:
    """Return the sha256 of text with line endings normalised."""
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    """Return the sha256 of a text file, line endings normalised."""
    return text_hash(path.read_text(encoding="utf-8", errors="replace"))


def read(repo: Path) -> dict[str, object]:
    """Return the recorded {version, files}, or an empty record when there is none or it is unreadable."""
    try:
        data = json.loads((repo / MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) and isinstance(data.get("files"), dict) else {}


def write(repo: Path, version: str, files: dict[str, str]) -> None:
    """Record the plugin version and the hash of each file the plugin wrote."""
    path = repo / MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": version, "files": dict(sorted(files.items()))}, indent=2) + "\n",
                    encoding="utf-8")


def classify(repo: Path, planned: dict[str, str], known: dict[str, str], skip: set[str]) -> dict[str, list[str]]:
    """Sort every planned file into created, updated, unchanged, edited or foreign; list orphans."""
    out: dict[str, list[str]] = {"created": [], "updated": [], "unchanged": [], "edited": [], "foreign": [],
                                 "orphans": []}
    for relative, text in planned.items():
        if relative in skip:
            continue
        target = repo / relative
        if not target.is_file():
            out["created"].append(relative)
            continue
        disk, wanted = file_hash(target), text_hash(text)
        if disk == wanted:
            out["unchanged"].append(relative)
        elif known.get(relative) == disk:
            out["updated"].append(relative)
        elif relative in known:
            out["edited"].append(relative)
        else:
            out["foreign"].append(relative)
    out["orphans"] = sorted(r for r in known if r not in planned and (repo / r).is_file())
    return out


def diff(old: str, new: str, name: str, limit: int = 20) -> str:
    """Return a short unified diff from the file on disk to what the plugin would write."""
    lines = list(difflib.unified_diff(old.replace("\r\n", "\n").splitlines(), new.replace("\r\n", "\n").splitlines(),
                                      f"{name} (yours)", f"{name} (plugin)", lineterm="", n=1))
    shown = lines[:limit]
    if len(lines) > limit:
        shown.append(f"... {len(lines) - limit} more line(s)")
    return "\n".join(shown)
