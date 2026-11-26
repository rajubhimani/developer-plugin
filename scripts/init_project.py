"""Copy the standard project files for one language into a repo, without overwriting.

Usage: python3 scripts/init_project.py <repo folder> <language>
           [--kind KIND] [--name NAME] [--members name:kind,...] [--module PATH]
           [--structure best-practice|own] [--no-input]
       python3 scripts/init_project.py <repo folder> <language> --update [--dry-run]

Languages: python, go, rust, node, c, cpp, java. Each run reports which files it
created and which it kept because they already existed.

A *kind* says what the project is (library, web app, command line tool, monorepo...)
and decides the folder layout. In a terminal, a new project is asked once; the answer
is recorded in .developer-plugin/project.json and never asked again. Without a
terminal and without --kind, the generic layout is used. In a folder that already
holds a project the kind is recorded and only safe files are added; code is never
moved or replaced.

In an existing project the owner also chooses a *structure*: `best-practice` (move toward the
recommended layout; a plan is written and nothing moves without approval) or `own` (keep the
layout; it is recorded in docs/project-structure.md and the plugin works inside it). A
terminal asks once; without one an existing project keeps its own structure.

The files the plugin writes are recorded with a hash in .developer-plugin/scaffold.json. Later,
`--update` brings the project to this plugin version without touching your work: files you have
not edited are refreshed, edited ones are kept and shown as a diff, new ones are created, and
nothing is deleted. `--dry-run` shows the plan. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import project_kinds as pk  # noqa: E402
import scaffold as sc  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
USER_OWNED = {pk.NOTE_FILE, pk.PLAN_FILE}  # written from facts or edited by hand; never refreshed
TEMPLATES = ROOT / "templates"
LANGUAGES = ("python", "go", "rust", "node", "c", "cpp", "java")
SHARED = ("Dockerfile", "compose.yaml", ".dockerignore", ".editorconfig", ".gitignore",
          "AGENTS.md", "CLAUDE.md")
PYTHON_REFS = ROOT / "skills" / "lang-python" / "references"
# Python projects get a uv multi-stage image, a Compose stack, a Settings class and the
# check that its names agree with .env.example and the cluster. They replace the
# generic Dockerfile, compose.yaml and .dockerignore.
REPLACEMENTS = {
    "python": {
        "Dockerfile": PYTHON_REFS / "Dockerfile.python",
        "compose.yaml": PYTHON_REFS / "compose.python.yaml",
        ".dockerignore": PYTHON_REFS / "dockerignore.python",
    },
}
EXTRAS = {
    "python": [
        (PYTHON_REFS / "env.example", Path(".env.example")),
        (PYTHON_REFS / "settings.py", Path("src/app/settings.py")),
        (ROOT / "scripts" / "check_env.py", Path("scripts/check_env.py")),
    ],
}
HINTS = {
    "python": ("Python: run `uv add pydantic-settings` for src/app/settings.py, edit the "
               "<placeholders> in Dockerfile, remove compose services you do not need, and "
               "keep .env.example, the Settings fields and the cluster config in step "
               "(make check-env)."),
}


def plan(language: str, kind: pk.Kind | None = None) -> list[tuple[Path, Path]]:
    """Return (template, destination name) pairs for one language.

    With a kind, files the kind does not want (a library has no Dockerfile) are left
    out and the kind supplies its own container and settings files.
    """
    pairs = [(TEMPLATES / "makefiles" / f"{language}.mk", Path("Makefile"))]
    if kind is None:
        replaced = REPLACEMENTS.get(language, {})
        pairs += [(replaced.get(name, TEMPLATES / name), Path(name)) for name in SHARED]
        pairs += EXTRAS.get(language, [])
    else:
        pairs += [(TEMPLATES / name, Path(name)) for name in SHARED if name not in kind.skip_common]
    pairs.append((TEMPLATES / "alignment" / "test_alignment.py", Path("tests/alignment/test_alignment.py")))
    pairs.append((TEMPLATES / "docs" / "requirements.md", Path("docs/requirements.md")))
    pairs += [
        (TEMPLATES / "gitattributes", Path(".gitattributes")),
        (TEMPLATES / "gitmessage", Path(".gitmessage")),
        (TEMPLATES / "github" / "pull_request_template.md", Path(".github/pull_request_template.md")),
        (TEMPLATES / "CHANGELOG.md", Path("CHANGELOG.md")),
    ]
    pairs.append((TEMPLATES / "claude" / "settings.example.json", Path(".claude/settings.example.json")))
    pairs.append((ROOT / "scripts" / "tasks.py", Path("scripts/tasks.py")))
    pairs.append((ROOT / "scripts" / "check_tests_honest.py", Path("scripts/check_tests_honest.py")))
    pairs.append((ROOT / "skills" / "ci-cd" / "references" / "github-actions.yml",
                  Path(".github/workflows/ci.yml")))
    return pairs


HONEST_TARGET = """
honest-tests: ## Fail if this branch weakened the tests (BASE=<ref>, default origin/main)
\tpython3 scripts/check_tests_honest.py $(if $(BASE),--base $(BASE),)
"""

STRUCTURE_TARGET = """
structure-check: ## Check the layout matches the project kind (.developer-plugin/project.json)
\tpython3 scripts/check_structure.py .
"""


def with_structure_check(makefile: str) -> str:
    """Add a structure-check target and make `check` depend on it."""
    text = re.sub(r"(?m)^(check:[^#\n]*?)(\s*##.*|\s*)$", lambda m: f"{m.group(1).rstrip()} structure-check{m.group(2)}", makefile, count=1)
    text = re.sub(r"(?m)^(\.PHONY:.*)$", lambda m: m.group(1) + " structure-check honest-tests", text, count=1)
    return text.rstrip("\n") + "\n" + STRUCTURE_TARGET + HONEST_TARGET


def common_files(language: str, kind: pk.Kind | None) -> dict[str, str]:
    """Return {destination: text} for the files every project gets."""
    out: dict[str, str] = {}
    for source, relative in plan(language, kind):
        if not source.exists():
            raise FileNotFoundError(f"missing template: {source.relative_to(ROOT)}")
        out[relative.as_posix()] = source.read_text(encoding="utf-8")
    return out


def kind_files(language: str, repo: Path, kind: pk.Kind, kinds: dict[str, pk.Kind], name: str,
               members: list[dict[str, str]], module: str, adopting: bool) -> tuple[dict[str, str], dict[str, object]]:
    """Return ({destination: text}, profile) for a chosen kind."""
    package = pk.detect_package(repo, pk.snake(name)) if adopting and language == "python" else pk.snake(name)
    root_vars = {"name": name, "package": package, "title": pk.title_of(name), "scope": name,
                 "module": module or f"example.com/{name}", "member_rows": "", "gopkg": name.replace("-", ""),
                 "workspace_dependencies": "", "source_dirs": "", "go_use": "",
                 "package_upper": package.upper()}
    if language == "java":
        group = module or "com.example"  # --module sets the base package (Maven group)
        root_vars.update({"javagroup": group, "javapkg": f"{group}.{name.replace('-', '')}",
                          "javapath": f"{group}.{name.replace('-', '')}".replace(".", "/")})
    files: dict[str, str] = {}
    required = pk.resolved_required(kind, root_vars)
    if language == "node" and kind.name == "monorepo" and members and not any(m["kind"] == "config" for m in members):
        members = [*members, {"name": "config", "kind": "config"}]  # members extend its tsconfig files
    member_records: list[dict[str, str]] = []
    rows = []
    for member in members:
        mkind = kinds.get(member["kind"])
        if mkind is None or mkind.name == kind.name or member["kind"] not in kind.member_dirs:
            allowed = ", ".join(sorted(kind.member_dirs))
            raise ValueError(f"member '{member['name']}': kind '{member['kind']}' is not allowed here (use: {allowed})")
        dist, pkg = pk.names_for(language, name, member["name"])
        path = pk.member_path(kind, mkind, member["name"])
        member_vars = {**root_vars, "name": dist, "package": pkg, "title": pk.title_of(member["name"]),
                       "member": member["name"], "gopkg": member["name"].replace("-", ""), "package_upper": pkg.upper(),
                       "module": f"{root_vars['module']}/{path}"}
        only = tuple(pk.fill(p, member_vars) for p in mkind.adopt_safe) if adopting else None
        for dest, text in pk.render_tree(mkind, member_vars, workspace=True, only=only).items():
            files[f"{path}/{dest}"] = text
        for entry in mkind.shared:
            if entry.get("member"):
                dest = pk.fill(str(entry["to"]), member_vars)
                src = (ROOT / str(entry["from"])).read_text(encoding="utf-8")
                files[f"{path}/{dest}"] = src.replace("<package>", pkg)
        required += [f"{path}/{pk.fill(r, member_vars)}" for r in mkind.required
                     if r not in mkind.skip_common and not r.startswith(".github/")]
        member_records.append({"name": member["name"], "kind": member["kind"], "path": path,
                               "dist": dist, "package": pkg, "module": member_vars["module"]})
        rows.append(f"| {member['name']} | {member['kind']} | <what {member['name']} is for> |")
    root_vars["member_rows"] = "\n".join(rows)
    root_vars["source_dirs"] = ", ".join(f'"{m["path"]}/src"' for m in member_records)
    root_vars["go_use"] = "\n".join(f"\t./{m['path']}" for m in member_records)
    root_vars["workspace_dependencies"] = "\n".join(
        f'{m["dist"]} = {{ path = "{m["path"]}" }}' for m in member_records if m["kind"] == "library")
    only_root = tuple(pk.fill(p, root_vars) for p in kind.adopt_safe) if adopting else None
    files.update(pk.render_tree(kind, root_vars, workspace=False, only=only_root))
    files.update(pk.shared_files(kind, root_vars, adopting))
    if adopting:
        # Never create a folder under src/ that the project does not have: it would sit
        # beside the real code (a flat layout, or a package with another name).
        files = {dest: text for dest, text in files.items()
                 if not dest.startswith("src/") or (repo / dest).parent.is_dir()}
    if kind.makefile:
        files["Makefile"] = with_structure_check(
            pk.fill((TEMPLATES / "makefiles" / kind.makefile).read_text(encoding="utf-8"), root_vars))
    files["scripts/check_structure.py"] = (ROOT / "scripts" / "check_structure.py").read_text(encoding="utf-8")
    profile: dict[str, object] = {
        "version": 1, "language": language, "kind": kind.name, "name": name, "package": package,
        "members": member_records, "required": required, "adopted": adopting,
    }
    if language == "go":
        profile["module"] = root_vars["module"]
    return files, profile


def write_new(repo: Path, files: dict[str, str]) -> list[str]:
    """Create files that do not exist yet; report what was created and kept; return the created paths."""
    created = []
    for relative, text in files.items():
        target = repo / relative
        if target.exists():
            print(f"kept    {relative} (already exists)")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print(f"created {relative}")
        created.append(relative)
    return created


def plugin_version() -> str:
    """Return the plugin's own version."""
    import json
    return str(json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"])


def record_scaffold(repo: Path, written: list[str]) -> None:
    """Record the hash of each file the plugin wrote, as it is on disk now."""
    known = {str(k): str(v) for k, v in dict(sc.read(repo).get("files", {})).items()}  # type: ignore[call-overload]
    for relative in written:
        if relative not in USER_OWNED and (repo / relative).is_file():
            known[relative] = sc.file_hash(repo / relative)
    sc.write(repo, plugin_version(), known)


def clean_tree(repo: Path) -> bool:
    """True when the folder is not a git repository, or git shows no uncommitted change."""
    if not (repo / ".git").exists() or shutil.which("git") is None:
        return True
    done = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=False)
    return done.returncode != 0 or not done.stdout.strip()


def run_update(args: argparse.Namespace, repo: Path, planned: dict[str, str]) -> int:
    """Bring a project made by the plugin to this plugin version, never overwriting an edit."""
    if not args.dry_run and not clean_tree(repo):
        print("error: the working tree has uncommitted changes. Commit or stash them first so the update is "
              "its own change you can review (or add --dry-run to only look).", file=sys.stderr)
        return 1
    state = sc.read(repo)
    recorded = str(state.get("version", ""))
    now = plugin_version()
    older = bool(recorded) and tuple(int(x) for x in now.split(".")[:3]) < tuple(int(x) for x in recorded.split(".")[:3])
    if older and not args.confirm_update:
        print(f"error: this project was last updated by plugin {recorded}, which is newer than this copy ({now}). "
              "Updating would move it backwards. Add --confirm-update to do it anyway.", file=sys.stderr)
        return 1
    known = {str(k): str(v) for k, v in dict(state.get("files", {})).items()}  # type: ignore[call-overload]
    if "Makefile" in planned and TASK_MARKER not in planned["Makefile"]:
        # Task targets are appended after the Makefile is written; compare it in that final form.
        block = (TEMPLATES / "makefiles" / "tasks.mk").read_text(encoding="utf-8")
        planned = {**planned, "Makefile": planned["Makefile"].rstrip("\n") + "\n\n" + block}
    result = sc.classify(repo, planned, known, USER_OWNED)
    print(f"Updating to plugin {now}" + (f" (from {recorded})" if recorded else " (no earlier record)")
          + (" - dry run, nothing will be written" if args.dry_run else ""))
    for label, key in (("create ", "created"), ("refresh", "updated")):
        for relative in result[key]:
            print(f"{label} {relative}")
    for relative in result["edited"]:
        print(f"kept    {relative} (you edited it; the plugin's version differs)")
        print(sc.diff((repo / relative).read_text(encoding="utf-8", errors="replace"), planned[relative], relative))
    for relative in result["foreign"]:
        print(f"kept    {relative} (not written by the plugin)")
    for relative in result["orphans"]:
        print(f"orphan  {relative} (the plugin no longer writes it; delete it if you do not need it)")
    print(f"{len(result['created'])} to create, {len(result['updated'])} to refresh, {len(result['unchanged'])} unchanged, "
          f"{len(result['edited'])} edited by you, {len(result['foreign'])} not ours, {len(result['orphans'])} orphan(s)")
    if args.dry_run:
        return 0
    for relative in [*result["created"], *result["updated"]]:
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(planned[relative], encoding="utf-8")
    for message in add_task_tracking(repo):
        print(message)
    record_scaffold(repo, [*result["created"], *result["updated"], *result["unchanged"]])
    return 0


def choose(args: argparse.Namespace, repo: Path, kinds: dict[str, pk.Kind],
           profile: dict[str, object] | None) -> dict[str, object] | None:
    """Work out the kind, name and members: flags, then the record, then (in a terminal) ask."""
    if profile and not args.kind:
        return {"kind": profile["kind"], "name": profile["name"],
                "members": [{"name": m["name"], "kind": m["kind"]} for m in profile.get("members", [])],  # type: ignore[union-attr]
                "module": profile.get("module", "")}
    default_name = re.sub(r"[^a-z0-9]+", "-", repo.name.lower()).strip("-") or "app"
    if args.kind:
        kind = kinds.get(args.kind)
        if kind is None or not kind.standalone:
            raise ValueError(f"unknown kind '{args.kind}' for {args.language}; use one of: "
                             + ", ".join(k for k, v in kinds.items() if v.standalone))
        members = pk.parse_members(args.members) if args.members else [dict(m) for m in kind.default_members]
        return {"kind": args.kind, "name": args.name or default_name, "members": members, "module": args.module or ""}
    if not kinds:
        return None
    interactive = sys.stdin.isatty() and sys.stdout.isatty() and not args.no_input
    if interactive:
        answer = pk.intake(args.language, repo.name, input, print)
        if answer:
            answer["module"] = args.module or ""
            return answer
    return None


def resolve_structure(args: argparse.Namespace, repo: Path, profile: dict[str, object] | None, kind: pk.Kind,
                      existing: bool) -> tuple[str, str]:
    """Return (structure, how it was decided): the flag, the record, a question, or a default.

    A new, empty project gets the recommended layout. An existing project is never changed
    to fit the plugin unless its owner says so: it keeps its own structure by default.
    """
    if args.structure:
        return args.structure, "flag"
    if profile is not None and profile.get("structure") in pk.STRUCTURES:
        return str(profile["structure"]), "record"
    if profile is not None:
        return "best-practice", "record"  # recorded before the choice existed: behaviour is unchanged
    if not existing:
        return "best-practice", "default"
    if sys.stdin.isatty() and sys.stdout.isatty() and not args.no_input:
        return pk.ask_structure(input, print, args.language, kind.title, pk.describe_layout(repo, args.language)), "asked"
    return "own", "default"


def write_structure_plan(repo: Path, name: str, language: str, kind_title: str) -> None:
    """Write docs/structure-plan.md from the checker's findings, so the move is a list of small steps."""
    import check_structure as cs  # noqa: PLC0415 - only needed here
    report, _ = cs.check(repo)
    target = repo / pk.PLAN_FILE
    if not (report.fails or report.warns):
        print("The layout already matches the recommended one; no plan needed.")
        return
    if target.exists():
        print(f"kept    {pk.PLAN_FILE} (already exists)")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(pk.structure_plan(name, language, kind_title, report.fails, report.warns), encoding="utf-8")
    print(f"created {pk.PLAN_FILE}: {len(report.fails)} broken, {len(report.warns)} against advice. "
          "Nothing was moved; do each step with the owner's approval (see the project-structure skill).")


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
    parser.add_argument("--kind", help="what the project is (library, webapp, cli, monorepo ...)")
    parser.add_argument("--name", help="project name, lower-case words joined by hyphens")
    parser.add_argument("--members", help="monorepo members as name:kind,name:kind")
    parser.add_argument("--module", help="Go module path, such as github.com/you/project")
    parser.add_argument("--structure", choices=pk.STRUCTURES,
                        help="in an existing project: follow best practice, or keep its own structure")
    parser.add_argument("--no-input", action="store_true", help="never ask questions")
    parser.add_argument("--update", action="store_true",
                        help="bring a project made by the plugin to this plugin version, keeping your edits")
    parser.add_argument("--dry-run", action="store_true", help="with --update: show the plan, write nothing")
    parser.add_argument("--confirm-update", action="store_true", help="with --update: allow moving a project backwards")
    args = parser.parse_args(argv)
    if args.dry_run and not args.update:
        print("error: --dry-run goes with --update", file=sys.stderr)
        return 1
    repo = args.repo.expanduser().resolve()
    if not repo.is_dir():
        print(f"not a folder: {repo}", file=sys.stderr)
        return 1
    kinds = pk.load_kinds(args.language)
    profile = pk.read_profile(repo)
    if args.update and profile is None:
        print(f"error: {pk.PROFILE.as_posix()} not found. --update is for a project the plugin already set up; "
              "run without --update first.", file=sys.stderr)
        return 1
    if profile and args.kind and (args.kind != profile.get("kind") or args.language != profile.get("language")):
        print(f"error: this project is recorded as a {profile.get('language')} {profile.get('kind')} "
              f"({pk.PROFILE.as_posix()}). To change it, delete that file and run again; existing files are kept.",
              file=sys.stderr)
        return 1
    try:
        choice = choose(args, repo, kinds, profile)
        if args.name and not pk.NAME_RE.match(args.name):
            raise ValueError("--name must be lower-case words joined by hyphens, such as my-app")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if choice is None:
        files = common_files(args.language, None)
        write_new(repo, files)
        if kinds:
            standalone = ", ".join(k for k, v in kinds.items() if v.standalone)
            print(f"No project kind was chosen, so the generic layout was used. For a layout that fits "
                  f"the project, re-run with --kind <{standalone}> (or run in a terminal to be asked once).")
        else:
            print(f"No kinds are defined for {args.language} yet; the generic layout was used.")
        profile_record = None
    else:
        kind = kinds[str(choice["kind"])]
        existing = pk.detect_existing(repo, args.language)
        structure, decided = resolve_structure(args, repo, profile, kind, existing)
        adopting = existing
        if profile is not None:
            adopting = bool(profile.get("adopted", adopting))
        adopting = adopting or structure == "own"  # honouring a layout means never creating one
        members = [dict(m) for m in choice["members"]]  # type: ignore[union-attr]
        try:
            files, profile_record = kind_files(args.language, repo, kind, kinds, str(choice["name"]), members,
                                               str(choice.get("module", "")), adopting)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        profile_record["structure"] = structure
        common = common_files(args.language, kind)
        for relative, text in files.items():
            common[relative] = text
        facts = pk.describe_layout(repo, args.language)
        if structure == "own":
            common["AGENTS.md"] = (TEMPLATES / "AGENTS.own-structure.md").read_text(encoding="utf-8")
            common[pk.NOTE_FILE] = pk.structure_note(str(choice["name"]), args.language, kind.title, facts)
            profile_record["required"] = [pk.NOTE_FILE]
            profile_record["layout"] = facts
        if args.update:
            return run_update(args, repo, common)
        print(f"Project kind: {kind.title} ({kind.name}); structure: "
              + ("keep its own" if structure == "own" else "best practice")
              + (" - existing project, adding safe files only" if adopting else ""))
        if structure == "own" and decided == "default" and existing:
            print("This project already has code, so its own structure is kept. To move toward the "
                  "recommended layout instead, run again with --structure best-practice.")
        created = write_new(repo, common)
        if profile is None:
            pk.write_profile(repo, profile_record)
            print(f"recorded {pk.PROFILE.as_posix()} (you will not be asked again)")
        elif profile.get("structure") not in (None, structure):
            pk.write_profile(repo, {**profile, "structure": structure,
                                    **({"layout": facts, "required": [pk.NOTE_FILE]} if structure == "own" else
                                       {"required": profile_record["required"]})})
            print(f"structure changed to {structure} in {pk.PROFILE.as_posix()}")
        if structure == "best-practice" and existing:
            write_structure_plan(repo, str(choice["name"]), args.language, kind.title)
    if args.language in HINTS and (choice is None or choice["kind"] == "webapp"):
        print(HINTS[args.language])
    print(ensure_git(repo))
    set_commit_template(repo)
    for message in add_task_tracking(repo):
        print(message)
    if choice is not None:
        record_scaffold(repo, created)
    if profile_record is not None:
        print("Next: fill the <placeholders> (run `python3 scripts/check_structure.py .` to list them), "
              "then `make install` and `make check`.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
