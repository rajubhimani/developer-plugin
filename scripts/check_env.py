"""Check that the Settings class, .env.example and the cluster manifests agree.

Usage: python3 scripts/check_env.py [--root DIR] [--settings FILE] [--example FILE]
                                    [--k8s DIR ...]

A setting added in one place and forgotten in another is a start-up failure in a
cluster. This reads the Settings class with the ast module (pydantic need not be
installed) and compares names:

  * every field must appear in .env.example, and every prefixed key in it must be a
    field;
  * if cluster manifests exist (default folders: k8s, deploy, helm, kustomize), each
    required field must be supplied there, each prefixed key must be a field, and a
    credential (SecretStr) must not be given as a plain value or in a ConfigMap.

Exit 0 when they agree or there is no Settings class, 1 on a mismatch. Standard
library only.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

CLUSTER_DIRS = ("k8s", "deploy", "helm", "kustomize")
KEY_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")
YAML_KEY = re.compile(r"^(\s+)([A-Za-z_][A-Za-z0-9_.\-]*)\s*:")


@dataclass(frozen=True)
class Field:
    """One settings field and how it is supplied."""

    name: str
    env: str
    required: bool
    secret: bool


@dataclass(frozen=True)
class Cluster:
    """Names found in the cluster manifests."""

    config: set[str]
    secret: set[str]
    plain_secret_manifests: list[str]


def find_settings(root: Path) -> Path | None:
    """Return the first src/<package>/settings.py, or None."""
    matches = sorted(root.glob("src/*/settings.py"))
    return matches[0] if matches else None


def has_default(value: ast.expr | None) -> bool:
    """True when an assignment gives a field a default."""
    if value is None:
        return False
    if isinstance(value, ast.Call) and ast.unparse(value.func).split(".")[-1] == "Field":
        if any(k.arg in ("alias", "validation_alias") for k in value.keywords):
            raise ValueError("Field aliases are not supported; use the plain field name")
        if value.args:
            return not (isinstance(value.args[0], ast.Constant) and value.args[0].value is Ellipsis)
        return any(k.arg in ("default", "default_factory") for k in value.keywords)
    return True


def read_settings(path: Path) -> tuple[str, list[Field]]:
    """Return (env prefix, fields) from the BaseSettings subclass in a file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(ast.unparse(b).split(".")[-1] == "BaseSettings" for b in node.bases):
            continue
        prefix = ""
        fields: list[Field] = []
        for item in node.body:
            if isinstance(item, (ast.Assign, ast.AnnAssign)):
                target = item.targets[0] if isinstance(item, ast.Assign) else item.target
                if isinstance(target, ast.Name) and target.id == "model_config":
                    call = item.value
                    if isinstance(call, ast.Call):
                        for kw in call.keywords:
                            if kw.arg == "env_prefix" and isinstance(kw.value, ast.Constant):
                                prefix = str(kw.value.value)
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                name = item.target.id
                if name.startswith("_") or name == "model_config":
                    continue
                annotation = ast.unparse(item.annotation)
                if annotation.startswith("ClassVar"):
                    continue
                fields.append(Field(name=name, env="", required=not has_default(item.value),
                                    secret="Secret" in annotation))
        return prefix, [Field(f.name, (prefix + f.name).upper(), f.required, f.secret) for f in fields]
    raise ValueError(f"no BaseSettings subclass in {path}")


def read_env_keys(path: Path) -> set[str]:
    """Return the variable names assigned in an env-style file."""
    keys = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("#"):
            continue
        match = KEY_LINE.match(line)
        if match:
            keys.add(match.group(1).upper())
    return keys


def map_keys(lines: list[str], header: str) -> set[str]:
    """Return the keys directly under a `header:` line in a YAML document."""
    keys: set[str] = set()
    for index, line in enumerate(lines):
        if re.match(rf"^{header}\s*:\s*(#.*)?$", line):
            indent = None
            for follow in lines[index + 1:]:
                if not follow.strip() or follow.lstrip().startswith("#"):
                    continue
                match = YAML_KEY.match(follow)
                if not follow.startswith(" "):
                    break
                if match:
                    indent = indent or match.group(1)
                    if match.group(1) == indent:
                        keys.add(match.group(2).upper())
    return keys


def read_cluster(folders: list[Path]) -> Cluster | None:
    """Collect variable names from manifests and env files in the folders."""
    config: set[str] = set()
    secret: set[str] = set()
    plain: list[str] = []
    found = False
    for folder in folders:
        for file in sorted(folder.rglob("*")):
            if not file.is_file():
                continue
            if file.suffix == ".env":
                found = True
                config |= read_env_keys(file)
            elif file.suffix in (".yaml", ".yml"):
                found = True
                text = file.read_text(encoding="utf-8")
                for document in re.split(r"(?m)^---\s*$", text):
                    lines = document.splitlines()
                    kind = next((m.group(1) for line in lines if (m := re.match(r"^kind:\s*(\S+)", line))), "")
                    if kind == "ConfigMap":
                        config |= map_keys(lines, "data")
                    elif kind == "Secret":
                        plain.append(str(file))
                    # Lookahead, so one match does not swallow the next; stop at the next list item.
                    for match in re.finditer(r"secretKeyRef:(?=(.{0,200}))", "\n".join(lines), re.S):
                        block = re.split(r"\n\s*-\s", match.group(1))[0]
                        key = re.search(r"key:\s*([^\s,}]+)", block)
                        if key:
                            secret.add(key.group(1).upper())
                    for match in re.finditer(r"-\s*name:\s*(\w+)\s*\n\s+value:", document):
                        config.add(match.group(1).upper())
    return Cluster(config, secret, plain) if found else None


def compare(prefix: str, fields: list[Field], example: set[str], cluster: Cluster | None) -> list[str]:
    """Return a list of mismatches; empty when everything agrees."""
    problems: list[str] = []
    by_env = {f.env: f for f in fields}

    def ours(names: set[str]) -> set[str]:
        """Names that belong to the app. Without a prefix we cannot tell, so none."""
        return {n for n in names if prefix and n.startswith(prefix.upper())}

    for env in sorted(set(by_env) - example):
        problems.append(f".env.example is missing {env}")
    for env in sorted(ours(example) - set(by_env)):
        problems.append(f".env.example has {env}, which is not a Settings field")
    if cluster is not None:
        supplied = cluster.config | cluster.secret
        for field in fields:
            if field.required and field.env not in supplied:
                problems.append(f"cluster manifests never supply required {field.env}")
            if field.secret and field.env in cluster.config:
                problems.append(f"{field.env} is a credential but is given as plain config")
        for env in sorted(ours(supplied) - set(by_env)):
            problems.append(f"cluster manifests set {env}, which is not a Settings field")
    return problems


def main(argv: list[str]) -> int:
    """Run the comparison and print the result."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--example", type=Path)
    parser.add_argument("--k8s", type=Path, action="append")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    settings = args.settings or find_settings(root)
    if settings is None or not settings.exists():
        print("check-env: no Settings class found (src/<package>/settings.py); skipped")
        return 0
    example = args.example or root / ".env.example"
    if not example.exists():
        print(f"check-env: {example} is missing; every setting must be listed there", file=sys.stderr)
        return 1
    try:
        prefix, fields = read_settings(settings)
    except (ValueError, SyntaxError) as exc:
        print(f"check-env: {exc}", file=sys.stderr)
        return 1
    folders = args.k8s or [root / name for name in CLUSTER_DIRS if (root / name).is_dir()]
    cluster = read_cluster(folders)
    problems = compare(prefix, fields, read_env_keys(example), cluster)
    if cluster is not None:
        for path in cluster.plain_secret_manifests:
            print(f"warning: {path} has a plain Secret manifest; keep real values out of git")
    for problem in problems:
        print(f"FAIL {problem}")
    if problems:
        return 1
    where = "settings, .env.example" + (" and the cluster manifests" if cluster else "")
    print(f"check-env: {len(fields)} settings agree across {where}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
