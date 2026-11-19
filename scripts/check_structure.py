"""Check that a project's layout follows the best practice for what it is.

Usage: python3 scripts/check_structure.py [REPO] [--strict]

Reads .developer-plugin/project.json (written by init_project.py when the project kind
was chosen) and reports:

  FAIL  a required folder or file is missing, or a layout rule is broken
  WARN  something that works but goes against the layout's advice
  TODO  a <placeholder> that still needs a real value

It never moves, edits or deletes anything. Code that sits in the wrong place needs a
person's decision; the message says what to do. To add missing standard files, run
init_project.py from the plugin again for the same language: it only creates files
that do not exist. Exit 1 on FAIL (and on WARN with --strict). Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROFILE = Path(".developer-plugin") / "project.json"
PLACEHOLDER = re.compile(r"<[a-z][a-z0-9 ,:@./\-]*[a-z0-9]>")
PLACEHOLDER_FILES = ("pyproject.toml", "Cargo.toml", "package.json", "go.mod", "go.work", "CMakeLists.txt",
                     "build.gradle.kts", "settings.gradle.kts", "libs.versions.toml", "Dockerfile", "compose.yaml")
SKIP_DIRS = {".git", ".venv", "node_modules", "target", "dist", "build", "__pycache__", ".developer-plugin"}
# Imports the domain layer must never use: web, storage and client libraries.
FRAMEWORKS = ("fastapi", "starlette", "flask", "django", "sqlalchemy", "httpx", "requests", "uvicorn",
              "pydantic_settings", "psycopg", "redis", "boto3")


@dataclass
class Report:
    """Findings, in the order found."""

    fails: list[str] = field(default_factory=list)
    warns: list[str] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)


def walk(folder: Path, suffix: str) -> list[Path]:
    """Return files with a suffix under a folder, skipping build and environment folders."""
    found = []
    for path in sorted(folder.rglob(f"*{suffix}")):
        if not any(part in SKIP_DIRS for part in path.relative_to(folder).parts):
            found.append(path)
    return found


# ---------------------------------------------------------------------------- Python

def module_name(src: Path, file: Path) -> str:
    """Return the dotted module name of a file under a src folder."""
    parts = list(file.relative_to(src).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def imports_of(file: Path, src: Path) -> set[str]:
    """Return the fully dotted names a Python file imports (relative imports resolved)."""
    try:
        tree = ast.parse(file.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    here = module_name(src, file).split(".")
    package = here if file.name == "__init__.py" else here[:-1]
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - (node.level - 1)] if node.level > 1 else package
                module = ".".join([*base, *( [node.module] if node.module else [] )])
            else:
                module = node.module or ""
            names.add(module)
            names.update(f"{module}.{alias.name}" for alias in node.names)
    return {n for n in names if n}


def under(name: str, prefix: str) -> bool:
    """True when a dotted name is the prefix or inside it."""
    return name == prefix or name.startswith(prefix + ".")


def check_python_layers(root: Path, package: str, report: Report) -> None:
    """The webapp layer rules: imports point one way."""
    src = root / "src"
    base = src / package
    rules = {
        "domain": (FRAMEWORKS + (f"{package}.api", f"{package}.services", f"{package}.adapters",
                                  f"{package}.settings", f"{package}.main"),
                   "the domain holds business rules only"),
        "services": (("fastapi", "starlette", f"{package}.api", f"{package}.adapters", f"{package}.main"),
                     "services must not know about HTTP or concrete adapters"),
        "adapters": ((f"{package}.api", f"{package}.main"), "adapters must not depend on the HTTP layer"),
        "api": ((f"{package}.adapters",), "routes call services, not adapters"),
    }
    for layer, (forbidden, why) in rules.items():
        folder = base / layer
        if not folder.is_dir():
            continue
        for file in walk(folder, ".py"):
            bad = sorted({n for n in imports_of(file, src) for f in forbidden if under(n, f)})
            for name in bad[:3]:
                report.fails.append(
                    f"{file.relative_to(root)} imports {name}: {why}. Move the logic down a layer, or "
                    f"depend on a port (a Protocol) defined in services/ and implemented in adapters/.")


def read_toml_text(path: Path) -> str:
    """Return a file's text, or an empty string."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def shown(path: Path, base: Path) -> str:
    """Return a path relative to the project, for messages."""
    try:
        return path.relative_to(base).as_posix() or "."
    except ValueError:
        return str(path)


def check_python_package(root: Path, kind: str, report: Report, base: Path | None = None) -> None:
    """Rules for one Python project folder (standalone, or one monorepo member)."""
    base = base or root
    text = read_toml_text(root / "pyproject.toml")
    if not text:
        return
    for legacy in ("setup.py", "setup.cfg", "requirements.txt"):
        if (root / legacy).exists():
            report.warns.append(f"{shown(root / legacy, base)}: legacy packaging file; keep dependencies in pyproject.toml and uv.lock")
    flat = [p.parent.name for p in root.glob("*/__init__.py") if p.parent.name not in ("tests", "docs", "scripts")]
    if flat and not (root / "src").is_dir():
        report.fails.append(
            f"{shown(root, base)}: flat layout (package '{flat[0]}' sits beside pyproject.toml). Move it to "
            f"src/{flat[0]}/ so tests import the installed package, not the working copy (a manual step).")
    if "[build-system]" not in text:
        report.fails.append(f"{shown(root / 'pyproject.toml', base)}: no [build-system] table; the project cannot be built")
    if "requires-python" not in text:
        report.warns.append(f"{shown(root / 'pyproject.toml', base)}: no requires-python; say which Python releases you support")
    packages = [p for p in (root / "src").glob("*") if p.is_dir() and not p.name.startswith((".", "_"))]
    if kind == "library":
        for pkg in packages:
            if not (pkg / "py.typed").exists():
                report.fails.append(f"{shown(pkg, base)}/py.typed is missing; add an empty file so type checkers use your hints")
            init = read_toml_text(pkg / "__init__.py")
            if "__all__" not in init:
                report.warns.append(f"{shown(pkg, base)}/__init__.py has no __all__; list the public API explicitly")
    if kind == "cli" and "[project.scripts]" not in text:
        report.fails.append(f"{shown(root / 'pyproject.toml', base)}: no [project.scripts]; the command is not installed")


def check_python_monorepo(root: Path, profile: dict[str, object], report: Report) -> None:
    """Workspace rules: one lock file, shared tool settings, one-way dependencies."""
    text = read_toml_text(root / "pyproject.toml")
    if "[tool.uv.workspace]" not in text:
        report.fails.append("pyproject.toml has no [tool.uv.workspace] table listing the members")
    members = [m for m in profile.get("members", []) if isinstance(m, dict)]  # type: ignore[union-attr]
    packages = {str(m["package"]): m for m in members}
    for member in members:
        folder = root / str(member["path"])
        if (folder / "uv.lock").exists():
            report.fails.append(f"{shown(folder / 'uv.lock', root)}: a member must not have its own lock file; delete it, the root uv.lock covers all")
        member_text = read_toml_text(folder / "pyproject.toml")
        if re.search(r"(?m)^\[tool\.(ruff|pyright|pytest)", member_text):
            report.warns.append(f"{shown(folder / 'pyproject.toml', root)}: tool settings belong in the root pyproject.toml")
        check_python_package(folder, str(member["kind"]), report, base=root)
        src = folder / "src"
        is_app = str(member["path"]).startswith("apps/")
        for file in walk(src, ".py") if src.is_dir() else []:
            for name in sorted(imports_of(file, src)):
                top = name.split(".")[0]
                other = packages.get(top)
                if other is None or top == member["package"]:
                    continue
                other_is_app = str(other["path"]).startswith("apps/")
                if other_is_app:
                    who = "an app" if is_app else "a package"
                    report.fails.append(
                        f"{file.relative_to(root)} imports {name}: {who} must not import an app. "
                        f"Move the shared code into a package that both can use.")
                elif name.count(".") >= 1 and any(part.startswith("_") for part in name.split(".")[1:]):
                    report.fails.append(
                        f"{file.relative_to(root)} imports {name}: use the other package's public API "
                        f"(its __init__), not a private module.")


# ---------------------------------------------------------------------------- Node

def package_jsons(root: Path, folders: list[str]) -> dict[str, tuple[Path, dict[str, object]]]:
    """Return {package name: (folder, parsed package.json)} for member folders."""
    out: dict[str, tuple[Path, dict[str, object]]] = {}
    for rel in folders:
        path = root / rel / "package.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        out[str(data.get("name", rel))] = (root / rel, data)
    return out


def check_node_monorepo(root: Path, profile: dict[str, object], report: Report) -> None:
    """Workspace rules: pnpm workspace file, one-way dependencies, workspace protocol."""
    if not (root / "pnpm-workspace.yaml").exists():
        report.fails.append("pnpm-workspace.yaml is missing; it lists the member folders")
    members = [m for m in profile.get("members", []) if isinstance(m, dict)]  # type: ignore[union-attr]
    found = package_jsons(root, [str(m["path"]) for m in members])
    is_app = {name: folder.relative_to(root).as_posix().startswith("apps/") for name, (folder, _) in found.items()}
    for name, (folder, data) in found.items():
        deps: dict[str, str] = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            section = data.get(key)
            if isinstance(section, dict):
                deps.update({str(k): str(v) for k, v in section.items()})
        for dep, spec in deps.items():
            if dep not in found:
                continue
            if is_app[dep]:
                report.fails.append(f"{folder.relative_to(root)}/package.json: {name} depends on app {dep}. "
                                    f"Nothing may depend on an app; move shared code into a package.")
            if not spec.startswith("workspace:"):
                report.warns.append(f"{folder.relative_to(root)}/package.json: {dep} is a sibling; use \"workspace:*\" "
                                    f"so it always links the local copy")
    if (root / "package-lock.json").exists() or (root / "yarn.lock").exists():
        report.warns.append("a lock file other than pnpm-lock.yaml exists; use one package manager")


def check_node_package(root: Path, kind: str, report: Report, base: Path | None = None) -> None:
    """Rules for a library package."""
    base = base or root
    try:
        data = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if kind in ("library", "ui") and "exports" not in data:
        report.fails.append(f"{shown(root / 'package.json', base)}: no \"exports\" map; say exactly what consumers may import")
    if kind in ("library", "ui") and "files" not in data and not data.get("private"):
        report.warns.append(f"{shown(root / 'package.json', base)}: no \"files\" list; the whole folder would be published")
    if data.get("type") != "module":
        report.warns.append(f"{shown(root / 'package.json', base)}: \"type\" is not \"module\"; new packages should use ES modules")


# ---------------------------------------------------------------------------- Go and Rust

def check_go_monorepo(root: Path, profile: dict[str, object], report: Report) -> None:
    """Workspace rules: go.work, one module per member, one-way imports, no replace directives."""
    if not (root / "go.work").exists():
        report.fails.append("go.work is missing; it lists the modules developed together")
    members = [m for m in profile.get("members", []) if isinstance(m, dict)]  # type: ignore[union-attr]
    for member in members:
        folder = root / str(member["path"])
        if not (folder / "go.mod").exists():
            report.fails.append(f"{member['path']}/go.mod is missing; every member is its own module")
            continue
        if re.search(r"(?m)^\s*replace\b", read_toml_text(folder / "go.mod")):
            report.warns.append(f"{member['path']}/go.mod has a replace directive; go.work resolves sibling modules locally")
        texts = {f: read_toml_text(f) for f in walk(folder, ".go")}
        for other in members:
            if other is member or "module" not in other:
                continue
            pattern = re.compile(r'"' + re.escape(str(other["module"])) + r'(?:/[^"]*)?"')
            if not str(other["path"]).startswith("apps/"):
                continue
            for file, text in texts.items():
                if pattern.search(text):
                    who = "an app" if str(member["path"]).startswith("apps/") else "a package"
                    report.fails.append(f"{file.relative_to(root)} imports {other['module']}: {who} must not import an app. "
                                        f"Move the shared code into a package that both can use.")
                    break


def check_cmake(root: Path, kind: str, report: Report) -> None:
    """C and C++ rules: warnings are errors, sanitizers are an option, a library has no main."""
    text = read_toml_text(root / "CMakeLists.txt")
    if not text:
        return
    if "-Werror" not in text and "/WX" not in text:
        report.warns.append("CMakeLists.txt: warnings are not errors; add -Werror (and /WX for MSVC) so deprecated calls and new warnings fail the build")
    if "-fsanitize" not in text:
        report.warns.append("CMakeLists.txt: no sanitizer option; add an address and undefined-behaviour sanitizer build and run the tests under it")
    if not (root / "CMakePresets.json").exists():
        report.warns.append("CMakePresets.json is missing; presets give everyone the same debug, sanitizer and release builds")
    if kind == "library":
        for source in [*walk(root / "src", ".c"), *walk(root / "src", ".cpp")] if (root / "src").is_dir() else []:
            if re.search(r"(?m)^\s*int\s+main\s*\(", read_toml_text(source)):
                report.fails.append(f"{source.relative_to(root)} defines main in a library; put the program in an executable target")


JAVA_IMPORT = re.compile(r"(?m)^import\s+(?:static\s+)?([\w.]+)")


def check_java(root: Path, kind: str, report: Report) -> None:
    """Java rules: warnings are errors, the wrapper is committed, a service keeps its layers apart."""
    build = read_toml_text(root / "build.gradle.kts")
    if build and "-Werror" not in build:
        report.warns.append("build.gradle.kts: warnings are not errors; add -Xlint:all and -Werror so deprecated calls fail the build")
    if build and not (root / "gradlew").exists():
        report.warns.append("the Gradle wrapper is missing; run `gradle wrapper` once and commit it")
    if build and not (root / "gradle" / "libs.versions.toml").exists():
        report.warns.append("gradle/libs.versions.toml is missing; keep every dependency version in one catalog")
    if kind != "service":
        return
    # {pkg} is the project's own base package, read from each file's path.
    rules = {
        "domain": (("org.springframework", "jakarta.", "{pkg}.web", "{pkg}.adapter", "{pkg}.service"),
                   "the domain holds business rules only"),
        "service": (("org.springframework.web", "{pkg}.web", "{pkg}.adapter"),
                    "services must not know about HTTP or concrete adapters"),
        "web": (("{pkg}.adapter",), "controllers call services, not adapters"),
        "adapter": (("{pkg}.web",), "adapters must not depend on the HTTP layer"),
    }
    source = root / "src" / "main" / "java"
    for file in walk(source, ".java"):
        parts = file.relative_to(source).parts[:-1]
        layer = next((i for i, part in enumerate(parts) if part in rules), None)
        if layer is None:
            continue
        forbidden, why = rules[parts[layer]]
        base = ".".join(parts[:layer])
        blocked = [f.format(pkg=base) for f in forbidden]
        for name in sorted(set(JAVA_IMPORT.findall(read_toml_text(file)))):
            if any(name == b or name.startswith(b + ".") or (b.endswith(".") and name.startswith(b)) for b in blocked):
                report.fails.append(f"{file.relative_to(root)} imports {name}: {why}. "
                                    f"Move the logic down a layer or depend on a port (an interface).")
                break


def check_go(root: Path, kind: str, report: Report) -> None:
    """Go rules: main packages live under cmd/, library code is importable."""
    stray = [p for p in root.glob("*.go") if re.search(r"(?m)^package main\b", read_toml_text(p))]
    if kind == "library" and stray:
        report.fails.append(f"{stray[0].name}: a library must not contain package main; put commands under cmd/")
    if kind in ("service", "cli"):
        if not list((root / "cmd").glob("*/main.go")):
            report.fails.append("cmd/<name>/main.go is missing; the entry point lives under cmd/")
        for main in (root / "cmd").glob("*/main.go"):
            lines = len(read_toml_text(main).splitlines())
            if lines > 80:
                report.warns.append(f"{main.relative_to(root)} has {lines} lines; keep main thin and put logic in internal/")
        if stray:
            report.warns.append(f"{stray[0].name}: package main at the root; move it to cmd/<name>/")


def check_rust(root: Path, kind: str, report: Report) -> None:
    """Rust rules: a virtual workspace manifest with listed members, or a lib and bin split."""
    text = read_toml_text(root / "Cargo.toml")
    if kind == "workspace":
        if "[workspace]" not in text:
            report.fails.append("Cargo.toml has no [workspace] table")
        if "[package]" in text:
            report.warns.append("the root Cargo.toml has a [package]; a virtual workspace keeps only [workspace]")
        if "resolver" not in text:
            report.fails.append("Cargo.toml: set the resolver explicitly (a virtual manifest cannot infer it)")
        if "[workspace.dependencies]" not in text:
            report.warns.append("Cargo.toml: declare shared dependency versions once in [workspace.dependencies]")
        if not list((root / "crates").glob("*/Cargo.toml")):
            report.fails.append("crates/*/Cargo.toml: no member crates found")
    if kind == "library" and not (root / "src" / "lib.rs").exists():
        report.fails.append("src/lib.rs is missing")
    if kind == "binary":
        if not (root / "src" / "main.rs").exists():
            report.fails.append("src/main.rs is missing")
        if not (root / "src" / "lib.rs").exists():
            report.warns.append("src/lib.rs is missing; put logic in a library and keep main.rs thin so it can be tested")


# ---------------------------------------------------------------------------- run

def infer(root: Path) -> str:
    """Describe what an unrecorded project looks like, to help the person choose."""
    text = read_toml_text(root / "pyproject.toml")
    if text:
        if "[tool.uv.workspace]" in text:
            return "python monorepo"
        if "[project.scripts]" in text:
            return "python cli"
        if re.search(r"fastapi|flask|django", text, re.I):
            return "python webapp"
        return "python library"
    if (root / "pnpm-workspace.yaml").exists():
        return "node monorepo"
    if (root / "go.mod").exists():
        return "go (service, library or cli)"
    if (root / "Cargo.toml").exists():
        return "rust (library, binary or workspace)"
    if (root / "package.json").exists():
        return "node (webapp or library)"
    return "unknown"


def check(root: Path) -> tuple[Report, dict[str, object] | None]:
    """Run every applicable check and return the findings."""
    report = Report()
    try:
        profile = json.loads((root / PROFILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return report, None
    language, kind = str(profile["language"]), str(profile["kind"])
    adopted = bool(profile.get("adopted"))
    for relative in profile.get("required", []):
        if not (root / relative).exists():
            how = ("add it by hand: init never creates source files in an existing project"
                   if adopted else "run init_project.py again to add it")
            report.fails.append(f"{relative} is missing (required for a {kind}); {how}")
    for name in PLACEHOLDER_FILES:
        for file in [root / name, *root.glob(f"*/*/{name}")]:
            if file.is_file():
                for found in sorted(set(PLACEHOLDER.findall(read_toml_text(file))))[:4]:
                    report.todos.append(f"{file.relative_to(root)}: replace {found}")
    package = str(profile.get("package", ""))
    if language == "python":
        if kind == "monorepo":
            check_python_monorepo(root, profile, report)
        else:
            check_python_package(root, kind, report)
            if kind == "webapp":
                check_python_layers(root, package, report)
    elif language == "node":
        if kind == "monorepo":
            check_node_monorepo(root, profile, report)
            for member in profile.get("members", []):
                check_node_package(root / member["path"], member["kind"], report, base=root)
        else:
            check_node_package(root, kind, report)
    elif language == "go":
        if kind == "monorepo":
            check_go_monorepo(root, profile, report)
        else:
            check_go(root, kind, report)
    elif language == "rust":
        check_rust(root, kind, report)
    elif language in ("c", "cpp"):
        check_cmake(root, kind, report)
    elif language == "java":
        check_java(root, kind, report)
    return report, profile


def main(argv: list[str]) -> int:
    """Print the findings; return 1 when the layout is broken."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--strict", action="store_true", help="treat WARN as FAIL")
    args = parser.parse_args(argv)
    root = args.repo.resolve()
    report, profile = check(root)
    if profile is None:
        print(f"structure-check: no {PROFILE.as_posix()} here. This looks like: {infer(root)}.")
        print("Say what the project is by running init_project.py from the plugin with --kind "
              "(it records the answer and, in an existing project, adds only safe files).")
        return 0
    for line in report.fails:
        print(f"FAIL {line}")
    for line in report.warns:
        print(f"WARN {line}")
    for line in report.todos:
        print(f"TODO {line}")
    label = f"{profile['language']} {profile['kind']}"
    broken = bool(report.fails) or (args.strict and bool(report.warns))
    if not (report.fails or report.warns or report.todos):
        print(f"structure-check: the layout matches a {label}")
    else:
        print(f"structure-check ({label}): {len(report.fails)} fail, {len(report.warns)} warn, {len(report.todos)} to fill")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
