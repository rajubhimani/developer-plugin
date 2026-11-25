"""Project kinds: the folder layout that fits what a project is meant to be.

A library, a web app, a command line tool and a monorepo need different files, so
`init_project.py` asks what the project is (once), copies the layout for that kind
and records the answer in `.developer-plugin/project.json`. `check_structure.py`
reads that record later. Kinds live in `templates/kinds/<language>/<kind>/`:

    kind.json        title, when to use it, required paths, shared files, options
    files/           the files to create ({{name}}, {{package}} ... are filled in)
    workspace_files/ files that replace the ones above when the kind is a monorepo member

Standard library only.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
KINDS_DIR = ROOT / "templates" / "kinds"
PROFILE = Path(".developer-plugin") / "project.json"
NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
MANIFESTS = {
    "python": ("pyproject.toml",), "node": ("package.json",), "go": ("go.mod",),
    "rust": ("Cargo.toml",), "java": ("pom.xml", "build.gradle", "build.gradle.kts"),
    "c": ("CMakeLists.txt",), "cpp": ("CMakeLists.txt",),
}


@dataclass(frozen=True)
class Kind:
    """One project kind, loaded from its kind.json."""

    language: str
    name: str
    title: str
    summary: str
    use_when: str
    standalone: bool
    required: tuple[str, ...]
    adopt_safe: tuple[str, ...]
    skip_common: tuple[str, ...]
    shared: tuple[dict[str, object], ...]
    makefile: str | None
    member_dirs: dict[str, str]
    default_members: tuple[dict[str, str], ...]
    path: Path = field(compare=False)


def snake(name: str) -> str:
    """Return a valid identifier for a kebab-case name."""
    return name.replace("-", "_")


def title_of(name: str) -> str:
    """Return a readable title for a kebab-case name."""
    return " ".join(part.capitalize() for part in name.split("-"))


def load_kinds(language: str) -> dict[str, Kind]:
    """Return the kinds defined for a language, by name."""
    kinds: dict[str, Kind] = {}
    folder = KINDS_DIR / language
    if not folder.is_dir():
        return kinds
    # A sensible menu order: what people most often build first, monorepo last.
    order = ("library", "webapp", "service", "ui", "cli", "binary", "monorepo", "workspace")
    specs = sorted(folder.glob("*/kind.json"),
                   key=lambda s: (order.index(s.parent.name) if s.parent.name in order else len(order), s.parent.name))
    for spec in specs:
        data = json.loads(spec.read_text(encoding="utf-8"))
        kinds[spec.parent.name] = Kind(
            language=language, name=spec.parent.name, title=data["title"],
            summary=data["summary"], use_when=data["use_when"],
            standalone=data.get("standalone", True),
            required=tuple(data.get("required", ())),
            adopt_safe=tuple(data.get("adopt_safe", ())),
            skip_common=tuple(data.get("skip_common", ())),
            shared=tuple(data.get("shared", ())),
            makefile=data.get("makefile"),
            member_dirs=dict(data.get("member_dirs", {})),
            default_members=tuple(data.get("default_members", ())),
            path=spec.parent,
        )
    return kinds


def parse_members(text: str) -> list[dict[str, str]]:
    """Parse 'web:webapp,core:library' into member dicts."""
    members = []
    for item in filter(None, (part.strip() for part in text.split(","))):
        name, _, kind = item.partition(":")
        if not NAME_RE.match(name) or not kind:
            raise ValueError(f"member '{item}' must look like name:kind (name in kebab-case)")
        members.append({"name": name, "kind": kind})
    if not members:
        raise ValueError("a monorepo needs at least one member")
    if len({m["name"] for m in members}) != len(members):
        raise ValueError("member names must be unique")
    return members


def names_for(language: str, root: str, member: str | None) -> tuple[str, str]:
    """Return (name, package) for the project or a member of it."""
    if member is None:
        return root, snake(root)
    if language == "node":
        return f"@{root}/{member}", snake(f"{root}-{member}")
    return f"{root}-{member}", snake(f"{root}-{member}")


def member_path(monorepo: Kind, member_kind: Kind, member: str) -> str:
    """Return the folder a member lives in, such as apps/web."""
    return f"{monorepo.member_dirs.get(member_kind.name, 'packages')}/{member}"


def fill(text: str, variables: dict[str, str]) -> str:
    """Replace {{key}} placeholders."""
    for key, value in variables.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def strip_tool_sections(text: str) -> str:
    """Remove shared-tool tables from a member's pyproject; the workspace root owns them."""
    out: list[str] = []
    skipping = False
    for line in text.splitlines():
        header = re.match(r"^\[([^\]]+)\]\s*$", line)
        if header:
            skipping = header.group(1).startswith(("tool.ruff", "tool.pyright", "tool.pytest",
                                                   "dependency-groups"))
        if not skipping:
            out.append(line)
    return "\n".join(out).rstrip("\n") + "\n"


def tree(folder: Path) -> dict[str, Path]:
    """Return {relative path: source file} for a template folder."""
    if not folder.is_dir():
        return {}
    return {p.relative_to(folder).as_posix(): p for p in sorted(folder.rglob("*")) if p.is_file()}


def render_tree(kind: Kind, variables: dict[str, str], workspace: bool,
                only: tuple[str, ...] | None = None) -> dict[str, str]:
    """Return {relative destination: content} for a kind's own files.

    `only` limits the result to those (already filled-in) paths; used when adopting an
    existing project, where creating a source skeleton would sit beside real code.
    """
    files = tree(kind.path / "files")
    if workspace:
        files.update(tree(kind.path / "workspace_files"))
    rendered: dict[str, str] = {}
    for relative, source in files.items():
        # A .tmpl suffix keeps editors and tools from parsing a template as a real file.
        destination = fill(relative.removesuffix(".tmpl"), variables)
        if workspace and destination.startswith(".github/"):
            continue  # GitHub reads workflows only from the repository root
        if only is not None and destination not in only:
            continue
        text = fill(source.read_text(encoding="utf-8"), variables)
        if workspace and destination.endswith("pyproject.toml"):
            text = strip_tool_sections(text)
        rendered[destination] = text
    return rendered


def shared_files(kind: Kind, variables: dict[str, str], adopting: bool) -> dict[str, str]:
    """Return {destination: content} for files a kind borrows from the plugin."""
    out: dict[str, str] = {}
    for entry in kind.shared:
        if adopting and not entry.get("adopt", True):
            continue
        source = ROOT / str(entry["from"])
        text = source.read_text(encoding="utf-8").replace("<package>", variables["package"])
        out[fill(str(entry["to"]), variables)] = text
    return out


def resolved_required(kind: Kind, variables: dict[str, str]) -> list[str]:
    """Return the kind's required paths with names filled in."""
    return [fill(path, variables) for path in kind.required]


def read_profile(repo: Path) -> dict[str, object] | None:
    """Return the recorded project profile, or None."""
    path = repo / PROFILE
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_profile(repo: Path, profile: dict[str, object]) -> None:
    """Record the choice so nobody is asked again."""
    path = repo / PROFILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")


def detect_existing(repo: Path, language: str) -> bool:
    """True when the folder already holds a project of this language."""
    return any((repo / name).exists() for name in MANIFESTS.get(language, ()))


def detect_package(repo: Path, fallback: str) -> str:
    """Return the import name of an existing Python package, else the fallback.

    Looks in src/ first, then for one folder with an __init__.py beside pyproject.toml
    (a flat layout).
    """
    skip = ("tests", "test", "docs", "scripts", "examples")
    under_src = [p.name for p in (repo / "src").glob("*") if p.is_dir() and not p.name.startswith(("_", "."))]
    if len(under_src) == 1:
        return under_src[0]
    flat = [p.parent.name for p in repo.glob("*/__init__.py") if p.parent.name not in skip
            and not p.parent.name.startswith((".", "_"))]
    return flat[0] if len(flat) == 1 else fallback


STRUCTURES = ("best-practice", "own")
NOTE_FILE = "docs/project-structure.md"
PLAN_FILE = "docs/structure-plan.md"
SKIP_FOLDERS = {"node_modules", "target", "build", "dist", "vendor", "venv", "env", "__pycache__", "site-packages"}
TEST_FOLDERS = ("tests", "test", "__tests__", "spec", "src/test")


def describe_layout(repo: Path, language: str) -> list[str]:
    """Return short facts about how an existing project is laid out, for the structure note."""
    facts = []
    folders = sorted(p.name for p in repo.iterdir()
                     if p.is_dir() and not p.name.startswith(".") and p.name not in SKIP_FOLDERS)
    facts.append("top-level folders: " + (", ".join(folders) if folders else "none"))
    found = [name for name in MANIFESTS.get(language, ()) if (repo / name).exists()]
    facts.append("manifest: " + (", ".join(found) if found else "none"))
    if language == "python":
        package = detect_package(repo, "")
        if package and (repo / "src" / package).is_dir():
            facts.append(f"layout: src layout, package `{package}` under src/")
        elif package:
            facts.append(f"layout: flat layout, package `{package}` beside the manifest")
        else:
            facts.append("layout: no single package found")
    tests = [name for name in TEST_FOLDERS if (repo / name).is_dir()]
    facts.append("tests: " + (", ".join(tests) if tests else "no test folder found"))
    tooling = [name for name in ("Makefile", "Dockerfile", "compose.yaml", ".github/workflows", "AGENTS.md")
               if (repo / name).exists()]
    facts.append("already present: " + (", ".join(tooling) if tooling else "none of Makefile, Dockerfile, compose, CI, AGENTS.md"))
    return facts


def ask_structure(ask: Callable[[str], str], say: Callable[[str], None], language: str, kind_title: str,
                  facts: list[str]) -> str:
    """Ask whether to follow best practice or keep the project's own structure. Enter keeps it."""
    say(f"This folder already holds a {language} project. What should the plugin do about its structure?")
    for fact in facts:
        say(f"  found: {fact}")
    say(f"  1) best-practice  Move toward the recommended layout for a {kind_title}. The plugin lists what differs and")
    say("                    writes a step-by-step plan; nothing is moved without your approval.")
    say("  2) own            Keep the structure as it is. The plugin records it and works inside it (default).")
    while True:
        answer = ask("Choose 1-2 [2]: ").strip().lower()
        if answer in ("", "2", "own"):
            return "own"
        if answer in ("1", "best-practice", "best practice", "best"):
            return "best-practice"
        say("  not a choice; try again")


def structure_note(name: str, language: str, kind_title: str, facts: list[str]) -> str:
    """Return the note that tells people and agents to work inside the project's own structure."""
    found = "\n".join(f"- {fact}" for fact in facts)
    return f"""# Project structure: {name}

The owner chose to keep this project's own structure. This note is what the plugin and
every agent follow. Edit it when a convention changes, so it stays true.

## What was found ({language}, treated as a {kind_title})

{found}

## Conventions to follow

- Put new code beside similar code; do not create a new top-level folder for one file.
- Match the naming, error handling and test style already used nearby.
- Put each test where the existing tests for that area live.
- Do not move, rename or reorganise existing files as part of another change. If a move
  would help, say so and let the owner decide.
- Add to this list any rule the team already follows that is not obvious from the code.

## What the plugin will not do here

It will not enforce a layout (`make structure-check` only lists placeholders to fill), create
source folders, or restructure code.

## Switching to the recommended layout later

Run the plugin's `init_project.py` again with `--structure best-practice`. It then writes
`docs/structure-plan.md`, the steps to take; each step is its own approved, tested commit.
"""


def structure_plan(name: str, language: str, kind_title: str, fails: list[str], warns: list[str]) -> str:
    """Return the step-by-step plan to reach the recommended layout, from the checker's findings."""
    def rows(items: list[str]) -> str:
        return "\n".join(f"- [ ] {item}" for item in items) or "- none"
    return f"""# Structure plan: {name}

The owner chose to move this {language} project toward the recommended layout for a {kind_title}.
Nothing is moved until the owner approves each step. Do one step per commit, with the tests
green before and after, and run `make structure-check` to see what is left (see the
`project-structure` and `refactoring` skills).

## Broken boundaries and missing files (do first)

{rows(fails)}

## Against advice

{rows(warns)}

## Done when

`make structure-check` prints no FAIL and no WARN. Then delete this file.
"""


def intake(language: str, folder_name: str, ask: Callable[[str], str],
           say: Callable[[str], None]) -> dict[str, object] | None:
    """Ask what the project is. Returns {kind, name, members} or None when no kinds exist."""
    kinds = {k: v for k, v in load_kinds(language).items() if v.standalone}
    if not kinds:
        return None
    names = list(kinds)
    say(f"What are you building? ({language})")
    for index, key in enumerate(names, 1):
        say(f"  {index}) {key:<9} {kinds[key].summary}")
        say(f"     use it when: {kinds[key].use_when}")
    kind = ""
    while not kind:
        answer = ask(f"Choose 1-{len(names)} or a name: ").strip().lower()
        if answer.isdigit() and 1 <= int(answer) <= len(names):
            kind = names[int(answer) - 1]
        elif answer in kinds:
            kind = answer
        else:
            say("  not a choice; try again")
    default_name = re.sub(r"[^a-z0-9]+", "-", folder_name.lower()).strip("-") or "app"
    name = ask(f"Project name [{default_name}]: ").strip() or default_name
    while not NAME_RE.match(name):
        name = ask("  use lower-case words joined by hyphens: ").strip()
    members: list[dict[str, str]] = []
    chosen = kinds[kind]
    if chosen.default_members:
        shown = ",".join(f"{m['name']}:{m['kind']}" for m in chosen.default_members)
        say("Members are name:kind pairs. Kinds you can use: "
            + ", ".join(k for k in load_kinds(language) if k != kind))
        while not members:
            text = ask(f"Members [{shown}]: ").strip() or shown
            try:
                members = parse_members(text)
            except ValueError as exc:
                say(f"  {exc}")
    return {"kind": kind, "name": name, "members": members}
