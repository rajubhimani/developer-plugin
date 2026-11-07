"""Check that this project follows the developer plugin's guidelines and stays aligned
with its requirements and docs.

Copied into every project by `make init-project` as tests/alignment/. Run with
`make align` (or `python3 -m unittest discover -s tests/alignment`). It uses only
the standard library, so it works in any language's project. Checks that need a
file the project does not have are skipped, not failed, so the test grows with
the project. Git-based checks run only inside a git repository.
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STANDARD_TARGETS = ("help", "install", "lint", "test", "check", "build", "clean")
# Which lock file each project marker needs (any one of the listed files).
LOCK_RULES = {
    "pyproject.toml": ("uv.lock", "poetry.lock"),
    "go.mod": ("go.sum",),
    "Cargo.toml": ("Cargo.lock",),
    "package.json": ("package-lock.json", "pnpm-lock.yaml", "yarn.lock"),
    "build.gradle": ("gradle.lockfile", "gradle/wrapper/gradle-wrapper.properties"),
    "build.gradle.kts": ("gradle.lockfile", "gradle/wrapper/gradle-wrapper.properties"),
}
PRIVATE_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
SHA_PIN = re.compile(r"uses:\s*\S+@[0-9a-f]{40}\b")
USES_LINE = re.compile(r"^\s*-?\s*uses:\s*(\S+)", re.M)


def tracked_files() -> list[Path] | None:
    """Return files git tracks, or None when the project is not a git repository."""
    if not (ROOT / ".git").exists():
        return None
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                         text=True, check=False).stdout
    return [ROOT / line for line in out.splitlines() if line]


def text(path: Path) -> str:
    """Read a text file, tolerating odd encodings."""
    return path.read_text(encoding="utf-8", errors="replace")


class BasicsTests(unittest.TestCase):
    """README, make targets and ignore rules."""

    def test_readme_has_a_title(self) -> None:
        readme = ROOT / "README.md"
        self.assertTrue(readme.exists(), "add a README.md")
        self.assertRegex(text(readme), r"(?m)^# \S", "README needs a top-level title")

    def test_makefile_has_standard_targets(self) -> None:
        makefile = ROOT / "Makefile"
        self.assertTrue(makefile.exists(), "add a Makefile (see make init-project)")
        for target in STANDARD_TARGETS:
            with self.subTest(target=target):
                self.assertRegex(text(makefile), rf"(?m)^{target}:", "missing standard target")

    def test_gitignore_ignores_env_files(self) -> None:
        gitignore = ROOT / ".gitignore"
        self.assertTrue(gitignore.exists(), "add a .gitignore")
        self.assertRegex(text(gitignore), r"(?m)^\.env", ".gitignore must ignore .env files")

    def test_project_is_a_git_repository(self) -> None:
        self.assertTrue((ROOT / ".git").exists(),
                        "run `git init` (make init-project does it); install git first if missing")

    def test_editorconfig_exists(self) -> None:
        if not (ROOT / ".editorconfig").exists():
            self.skipTest("no .editorconfig")


class SecretTests(unittest.TestCase):
    """Nothing secret is committed."""

    def test_no_env_file_is_tracked(self) -> None:
        files = tracked_files()
        if files is None:
            self.skipTest("not a git repository")
        tracked = [f.name for f in files if f.name == ".env" or f.name.startswith(".env.")
                   and f.name != ".env.example"]
        self.assertEqual(tracked, [], "remove .env files from git and rotate their secrets")

    def test_no_private_keys_are_tracked(self) -> None:
        files = tracked_files()
        if files is None:
            self.skipTest("not a git repository")
        for path in files:
            if not path.is_file() or path.stat().st_size > 1_000_000:
                continue
            with self.subTest(file=path.name):
                self.assertIsNone(PRIVATE_KEY.search(text(path)), "private key committed")


class LockfileTests(unittest.TestCase):
    """Dependencies are pinned by a lock file."""

    def test_each_language_has_a_lock_file(self) -> None:
        checked = False
        for marker, locks in LOCK_RULES.items():
            if (ROOT / marker).exists():
                checked = True
                with self.subTest(marker=marker):
                    self.assertTrue(any((ROOT / lock).exists() for lock in locks),
                                    f"{marker} needs one of: {', '.join(locks)}")
        if not checked:
            self.skipTest("no known project marker found")


class ContainerTests(unittest.TestCase):
    """Dockerfile and Compose follow the docker and compose skills."""

    def test_dockerfile_runs_as_non_root(self) -> None:
        dockerfile = ROOT / "Dockerfile"
        if not dockerfile.exists():
            self.skipTest("no Dockerfile")
        self.assertRegex(text(dockerfile), r"(?m)^USER\s+(?!root\b|0\b)\S+",
                         "set USER to a non-root user")

    def test_dockerfile_has_no_latest_tag(self) -> None:
        dockerfile = ROOT / "Dockerfile"
        if not dockerfile.exists():
            self.skipTest("no Dockerfile")
        for line in text(dockerfile).splitlines():
            if line.strip().upper().startswith("FROM "):
                with self.subTest(line=line):
                    self.assertNotRegex(line, r":latest\b", "pin the base image, not :latest")

    def test_compose_has_no_version_key(self) -> None:
        compose = ROOT / "compose.yaml"
        if not compose.exists():
            self.skipTest("no compose.yaml")
        self.assertNotRegex(text(compose), r"(?m)^version:", "drop the obsolete version key")


class CiTests(unittest.TestCase):
    """Pipelines pin actions and limit token permissions."""

    def workflows(self) -> list[Path]:
        folder = ROOT / ".github" / "workflows"
        return sorted(folder.glob("*.yml")) + sorted(folder.glob("*.yaml")) if folder.exists() else []

    def test_actions_are_pinned_to_commit_sha(self) -> None:
        flows = self.workflows()
        if not flows:
            self.skipTest("no workflows")
        for flow in flows:
            for match in USES_LINE.finditer(text(flow)):
                ref = match.group(1)
                if ref.startswith("./") or ref.startswith("docker://"):
                    continue
                with self.subTest(workflow=flow.name, uses=ref):
                    self.assertRegex(ref, r"@[0-9a-f]{40}$", "pin third-party actions to a full SHA")

    def test_workflows_set_top_level_permissions(self) -> None:
        flows = self.workflows()
        if not flows:
            self.skipTest("no workflows")
        for flow in flows:
            with self.subTest(workflow=flow.name):
                self.assertRegex(text(flow), r"(?m)^permissions:", "set a top-level permissions block")


class TestsExistTests(unittest.TestCase):
    """The project has tests and a docs entry point."""

    def test_project_has_tests(self) -> None:
        patterns = ["tests/**/*.py", "test/**/*.py", "**/*_test.go", "**/test_*.py",
                    "**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts", "**/tests/**/*.rs",
                    "src/test/**/*.java", "**/*_test.cpp", "**/*_test.c", "**/tests/*.c",
                    "**/tests/*.cpp"]
        found = any(True for pattern in patterns for path in ROOT.glob(pattern)
                    if "node_modules" not in path.parts and ".venv" not in path.parts
                    and "alignment" not in path.parts)
        self.assertTrue(found, "add tests; the guidelines require them for new behaviour")

    def test_docs_have_an_index_when_present(self) -> None:
        docs = ROOT / "docs"
        if not docs.is_dir():
            self.skipTest("no docs folder")
        self.assertTrue((docs / "INDEX.md").exists() or (docs / "README.md").exists(),
                        "docs/ needs an INDEX.md or README.md entry point")


REQ_LINE = re.compile(r"(?m)^- (REQ-\d+):")
REQ_REF = re.compile(r"\bREQ-\d+\b")
DOC_LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)\s]*)?\)")
TEST_PATTERNS = ["tests/**/*", "test/**/*", "**/*_test.go", "**/test_*.py", "**/*.test.*",
                 "**/*.spec.*", "**/*_test.cpp", "**/*_test.c", "src/test/**/*.java"]


def requirement_ids() -> list[str]:
    """Return the requirement IDs listed in docs/requirements.md, in order."""
    path = ROOT / "docs" / "requirements.md"
    return REQ_LINE.findall(text(path)) if path.exists() else []


def test_files() -> list[Path]:
    """Return the project's test files, excluding this alignment folder and build output."""
    found: set[Path] = set()
    for pattern in TEST_PATTERNS:
        for path in ROOT.glob(pattern):
            parts = set(path.parts)
            if path.is_file() and not parts & {"alignment", "node_modules", ".venv", ".git", "build", "dist", "target"}:
                found.add(path)
    return sorted(found)


class RequirementTests(unittest.TestCase):
    """Requirements, tests and docs stay aligned with each other."""

    def test_requirements_file_exists(self) -> None:
        self.assertTrue((ROOT / "docs" / "requirements.md").exists(),
                        "add docs/requirements.md with one line per requirement")

    def test_requirement_ids_are_unique(self) -> None:
        ids = requirement_ids()
        self.assertEqual(len(ids), len(set(ids)), "requirement IDs must be unique")

    def test_every_requirement_has_a_test(self) -> None:
        covered = set()
        for path in test_files():
            covered |= set(REQ_REF.findall(text(path)))
        for req in requirement_ids():
            with self.subTest(requirement=req):
                self.assertIn(req, covered, f"{req} has no test that names it")

    def test_every_test_reference_exists(self) -> None:
        known = set(requirement_ids())
        for path in test_files():
            for ref in set(REQ_REF.findall(text(path))):
                with self.subTest(file=path.name, requirement=ref):
                    self.assertIn(ref, known, "test names a requirement that is not in docs/requirements.md")


class DocsLinkTests(unittest.TestCase):
    """Relative links in the docs point at files that exist."""

    def test_relative_links_resolve(self) -> None:
        docs = ROOT / "docs"
        if not docs.is_dir():
            self.skipTest("no docs folder")
        for path in sorted(docs.rglob("*.md")):
            for link in DOC_LINK.findall(text(path)):
                if link.startswith(("http://", "https://", "mailto:")):
                    continue
                with self.subTest(file=str(path.relative_to(ROOT)), link=link):
                    self.assertTrue((path.parent / link).exists(), "broken link")


if __name__ == "__main__":
    unittest.main()
