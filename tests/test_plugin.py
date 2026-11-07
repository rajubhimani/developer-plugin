"""Tests that keep the plugin aligned: manifests, skills, templates, generators.

Run with `make test` (or `python3 -m unittest discover -s tests`). Standard
library only, so no install is needed. Generator tests run in temporary folders
and never touch a real projects folder.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
LANGUAGES = ("python", "go", "rust", "node", "c", "cpp", "java")
STANDARD_TARGETS = ("help", "install", "format", "lint", "test", "check", "align",
                    "build", "run", "docker-build", "clean")
SKILL_FOLDERS = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))


def run(args: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run a command and capture its output."""
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, check=False)


def frontmatter(path: Path) -> dict[str, str]:
    """Return the simple key: value pairs of a SKILL.md front matter block."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


class ManifestTests(unittest.TestCase):
    """The three manifests describe the same plugin."""

    def test_manifests_parse_and_agree(self) -> None:
        paths = [ROOT / "plugin.json", ROOT / ".claude-plugin" / "plugin.json",
                 ]
        docs = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
        self.assertEqual({d["name"] for d in docs}, {"developer-plugin"})
        self.assertEqual(len({d["version"] for d in docs}), 1)

    def test_claude_marketplace_points_at_plugin(self) -> None:
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(market["plugins"][0]["name"], "developer-plugin")

    def test_hook_runs_existing_script(self) -> None:
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        command = hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        self.assertIn("scripts/init_workspace.py", command)
        self.assertTrue((ROOT / "scripts" / "init_workspace.py").exists())


class SkillTests(unittest.TestCase):
    """Every skill is discoverable, dated, and free of hard-coded versions."""

    def test_skills_exist(self) -> None:
        self.assertGreaterEqual(len(SKILL_FOLDERS), 15)

    def test_each_skill_has_name_description_and_date(self) -> None:
        for folder in SKILL_FOLDERS:
            with self.subTest(skill=folder):
                fields = frontmatter(ROOT / "skills" / folder / "SKILL.md")
                self.assertEqual(fields.get("name"), folder)
                self.assertTrue(fields.get("description"))
                self.assertRegex(fields.get("verified", ""), r"^\d{4}-\d{2}-\d{2}$")

    def test_no_hard_coded_versions_in_skill_bodies(self) -> None:
        number = re.compile(r"(?<![\w.])\d+\.\d+(\.\d+)?(?![\w.])")
        for folder in SKILL_FOLDERS:
            body = (ROOT / "skills" / folder / "SKILL.md").read_text(encoding="utf-8")
            body = body.split("\n---\n", 1)[-1]
            for line in body.splitlines():
                with self.subTest(skill=folder, line=line):
                    self.assertIsNone(number.search(line))

    def test_generated_rules_copies_are_current(self) -> None:
        result = run([sys.executable, str(SCRIPTS / "sync_rules.py"), "--check"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class TemplateTests(unittest.TestCase):
    """Every language has a Makefile with the standard targets."""

    def test_each_language_makefile_has_standard_targets(self) -> None:
        for language in LANGUAGES:
            text = (ROOT / "templates" / "makefiles" / f"{language}.mk").read_text(encoding="utf-8")
            for target in STANDARD_TARGETS:
                with self.subTest(language=language, target=target):
                    self.assertRegex(text, rf"(?m)^{re.escape(target)}:", "missing target")

    def test_shared_templates_exist(self) -> None:
        for name in ("Dockerfile", "compose.yaml", ".dockerignore", ".editorconfig", ".gitignore"):
            with self.subTest(template=name):
                self.assertTrue((ROOT / "templates" / name).exists())

    def test_compose_has_no_obsolete_version_key(self) -> None:
        text = (ROOT / "templates" / "compose.yaml").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?m)^version:")


class MakefileTests(unittest.TestCase):
    """The Makefile exposes the targets the docs promise."""

    def test_documented_targets_exist(self) -> None:
        text = (ROOT / "Makefile").read_text(encoding="utf-8")
        for target in ("help", "validate", "test", "check", "versions", "init-project",
                       "navigator", "workspace", "install-claude", "install-codex",
                       "install-copilot", "install-all", "update-clis",
                       "install-antigravity", "uninstall-antigravity"):
            with self.subTest(target=target):
                self.assertRegex(text, rf"(?m)^{re.escape(target)}:")


class InitProjectTests(unittest.TestCase):
    """init-project copies files once and never overwrites."""

    def test_copies_then_keeps_existing_files(self) -> None:
        for language in LANGUAGES:
            with self.subTest(language=language), tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp)
                first = run([sys.executable, str(SCRIPTS / "init_project.py"), str(repo), language])
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertTrue((repo / "Makefile").exists())
                self.assertTrue((repo / ".github" / "workflows" / "ci.yml").exists())
                (repo / "Makefile").write_text("custom\n", encoding="utf-8")
                second = run([sys.executable, str(SCRIPTS / "init_project.py"), str(repo), language])
                self.assertIn("kept    Makefile", second.stdout)
                makefile = (repo / "Makefile").read_text(encoding="utf-8")
                self.assertTrue(makefile.startswith("custom\n"), "existing lines must be kept")
                self.assertEqual(makefile.count("# tasks: start"), 1)


def make_repo(path: Path, name: str, extra: str = "") -> None:
    """Create a small git repo with a README and optional manifest text."""
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    (path / "README.md").write_text(f"# {name}\n\nA test project called {name}.\n", encoding="utf-8")
    (path / "Makefile").write_text("build:\n\techo build\n", encoding="utf-8")
    if extra:
        (path / "package.json").write_text(extra, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                    "commit", "-qm", "init"], cwd=path, check=True)


class UmbrellaTests(unittest.TestCase):
    """The umbrella setup writes docs beside the repos and leaves the repos alone."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.umbrella = self.tmp / "projects"
        self.umbrella.mkdir()
        make_repo(self.umbrella / "alpha", "alpha")
        make_repo(self.umbrella / "beta", "beta",
                  extra='{"name": "beta", "dependencies": {"alpha": "file:../alpha"}}')

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def workspace(self) -> subprocess.CompletedProcess:
        return run([sys.executable, str(SCRIPTS / "init_workspace.py"), str(self.umbrella)])

    def test_writes_index_projects_and_links(self) -> None:
        self.assertEqual(self.workspace().returncode, 0)
        docs = self.umbrella / "docs"
        self.assertTrue((docs / "INDEX.md").exists())
        self.assertTrue((docs / "links.md").exists())
        self.assertTrue((docs / "notes.md").exists())
        for name in ("alpha", "beta"):
            with self.subTest(project=name):
                self.assertTrue((docs / "projects" / name / "INDEX.md").exists())
                self.assertTrue((docs / "projects" / name / "commands.md").exists())
                self.assertTrue((docs / "projects" / name / "notes.md").exists())
        self.assertIn("beta", (docs / "links.md").read_text(encoding="utf-8"))
        self.assertIn("alpha", (docs / "links.md").read_text(encoding="utf-8"))

    def test_repos_stay_untouched(self) -> None:
        self.workspace()
        for name in ("alpha", "beta"):
            status = run(["git", "status", "--porcelain"], cwd=self.umbrella / name).stdout
            self.assertEqual(status.strip(), "", f"{name} has changes: {status}")

    def test_rerun_keeps_user_notes(self) -> None:
        self.workspace()
        notes = self.umbrella / "docs" / "projects" / "alpha" / "notes.md"
        notes.write_text(notes.read_text(encoding="utf-8") + "\nKEEP ME\n", encoding="utf-8")
        self.workspace()
        self.assertIn("KEEP ME", notes.read_text(encoding="utf-8"))

    def test_index_keeps_user_text_outside_markers(self) -> None:
        self.workspace()
        index = self.umbrella / "docs" / "projects" / "alpha" / "INDEX.md"
        index.write_text("My hand-written intro\n" + index.read_text(encoding="utf-8"), encoding="utf-8")
        self.workspace()
        self.assertIn("My hand-written intro", index.read_text(encoding="utf-8"))

    def test_workspace_file_keeps_user_settings(self) -> None:
        self.workspace()
        ws = self.umbrella / f"{self.umbrella.name}.code-workspace"
        data = json.loads(ws.read_text(encoding="utf-8"))
        data["settings"]["editor.tabSize"] = 2
        ws.write_text(json.dumps(data), encoding="utf-8")
        self.workspace()
        self.assertEqual(json.loads(ws.read_text(encoding="utf-8"))["settings"]["editor.tabSize"], 2)
        folders = [f["path"] for f in json.loads(ws.read_text(encoding="utf-8"))["folders"]]
        self.assertEqual(sorted(folders), ["alpha", "beta", "docs"])

    def test_agent_files_created_once(self) -> None:
        self.workspace()
        self.assertEqual((self.umbrella / "CLAUDE.md").read_text(encoding="utf-8").strip(), "@AGENTS.md")
        (self.umbrella / "AGENTS.md").write_text("mine\n", encoding="utf-8")
        self.workspace()
        self.assertEqual((self.umbrella / "AGENTS.md").read_text(encoding="utf-8"), "mine\n")

    def test_project_mode_writes_only_under_umbrella_docs(self) -> None:
        result = run([sys.executable, str(SCRIPTS / "init_workspace.py"),
                      str(self.umbrella / "alpha")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.umbrella / "docs" / "projects" / "alpha" / "INDEX.md").exists())
        self.assertFalse((self.umbrella / "docs" / "INDEX.md").exists())


class ProjectAlignmentTests(unittest.TestCase):
    """The alignment test copied into projects passes good projects and fails bad ones."""

    GOOD_MAKEFILE = "".join(f"{target}:\n\techo {target}\n\n" for target in
                            ("help", "install", "lint", "test", "check", "build", "clean"))

    def project(self, root: Path, *, lock: bool, makefile: str) -> None:
        """Lay out a minimal Python-style project with the alignment test copied in."""
        (root / "tests" / "alignment").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        shutil.copy(ROOT / "templates" / "alignment" / "test_alignment.py",
                    root / "tests" / "alignment" / "test_alignment.py")
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
        (root / "Makefile").write_text(makefile, encoding="utf-8")
        (root / ".gitignore").write_text(".env\n", encoding="utf-8")
        (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
        (root / "docs").mkdir(exist_ok=True)
        (root / "docs" / "requirements.md").write_text("- REQ-001: the demo works\n", encoding="utf-8")
        (root / "docs" / "INDEX.md").write_text("# Index\n", encoding="utf-8")
        (root / "tests" / "test_demo.py").write_text("# REQ-001\ndef test_ok():\n    pass\n", encoding="utf-8")
        if lock:
            (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")

    def check(self, root: Path) -> subprocess.CompletedProcess:
        return run([sys.executable, "-m", "unittest", "discover", "-s",
                    str(root / "tests" / "alignment"), "-p", "test_*.py"], cwd=root)

    def test_good_project_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.project(root, lock=True, makefile=self.GOOD_MAKEFILE)
            result = self.check(root)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_lock_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.project(root, lock=False, makefile=self.GOOD_MAKEFILE)
            result = self.check(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("uv.lock", result.stderr)

    def test_missing_standard_target_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.project(root, lock=True, makefile="help:\n\techo help\n")
            result = self.check(root)
            self.assertNotEqual(result.returncode, 0)

    def test_every_language_makefile_runs_align(self) -> None:
        for language in LANGUAGES:
            with self.subTest(language=language):
                text = (ROOT / "templates" / "makefiles" / f"{language}.mk").read_text(encoding="utf-8")
                self.assertRegex(text, r"(?m)^check: align")
                self.assertIn("tests/alignment", text)

    def test_init_project_copies_the_alignment_test(self) -> None:
        for language in LANGUAGES:
            with self.subTest(language=language), tempfile.TemporaryDirectory() as tmp:
                run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, language])
                self.assertTrue((Path(tmp) / "tests" / "alignment" / "test_alignment.py").exists())


class RequirementAlignmentTests(unittest.TestCase):
    """Requirements, tests and docs stay aligned, as checked inside a project."""

    def build(self, root: Path, *, requirements: str, test: str, docs: dict[str, str] | None = None) -> None:
        """Lay out a project with the alignment test and the given requirement and test text."""
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        shutil.copytree(ROOT / "templates" / "alignment", root / "tests" / "alignment")
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
        (root / "Makefile").write_text("".join(f"{x}:\n\techo {x}\n\n" for x in
                                      ("help", "install", "lint", "test", "check", "build", "clean")),
                                       encoding="utf-8")
        (root / ".gitignore").write_text(".env\n", encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs" / "requirements.md").write_text(requirements, encoding="utf-8")
        for name, body in (docs or {}).items():
            (root / "docs" / name).write_text(body, encoding="utf-8")
        (root / "tests" / "test_demo.py").write_text(test, encoding="utf-8")

    def check(self, root: Path) -> subprocess.CompletedProcess:
        return run([sys.executable, "-m", "unittest", "discover", "-s",
                    str(root / "tests" / "alignment"), "-p", "test_*.py"], cwd=root)

    def test_aligned_project_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build(root, requirements="- REQ-001: users can log in\n",
                       test="# REQ-001: users can log in\ndef test_login():\n    pass\n",
                       docs={"INDEX.md": "[self](INDEX.md)\n"})
            result = self.check(root)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_uncovered_requirement_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build(root, requirements="- REQ-001: users can log in\n- REQ-002: users can log out\n",
                       test="# REQ-001\ndef test_login():\n    pass\n")
            result = self.check(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("REQ-002", result.stderr)

    def test_orphan_test_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build(root, requirements="- REQ-001: users can log in\n",
                       test="# REQ-001 and REQ-009\ndef test_login():\n    pass\n")
            result = self.check(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("REQ-009", result.stderr)

    def test_broken_docs_link_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build(root, requirements="- REQ-001: users can log in\n",
                       test="# REQ-001\ndef test_login():\n    pass\n",
                       docs={"INDEX.md": "See [missing](gone.md)\n"})
            result = self.check(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("broken link", result.stderr)

    def test_init_project_copies_requirements_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python"])
            self.assertTrue((Path(tmp) / "docs" / "requirements.md").exists())


class GitSetupTests(unittest.TestCase):
    """init-project makes a git repository, and says so when git is missing."""

    def test_init_project_creates_git_repository(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as tmp:
            run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python"])
            self.assertTrue((Path(tmp) / ".git").exists())

    def test_init_project_keeps_existing_repository(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
            result = run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python"])
            self.assertIn("already set up", result.stdout)

    def test_init_project_task_targets_added_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python"])
            run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python"])
            text = (Path(tmp) / "Makefile").read_text(encoding="utf-8")
            self.assertEqual(text.count("# tasks: start"), 1)


class StandingDecisionTests(unittest.TestCase):
    """Rejections and decisions are remembered in AGENTS.md, and reopening removes them."""

    def tool(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return run([sys.executable, str(SCRIPTS / "tasks.py"), "--root", str(root), *args])

    def test_rejection_is_listed_and_reopening_removes_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Agents\n\nKeep this text.\n", encoding="utf-8")
            self.assertEqual(self.tool(root, "new", "checkout", "Guest checkout", "--req", "REQ-004").returncode, 0)
            self.assertEqual(self.tool(root, "move", "checkout-01", "rejected", "--reason", "out of scope").returncode, 0)
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("[rejected] checkout-01", agents)
            self.assertIn("Keep this text.", agents)
            self.tool(root, "move", "checkout-01", "backlog")
            self.assertNotIn("checkout-01", (root / "AGENTS.md").read_text(encoding="utf-8"))

    def test_decision_is_logged_and_listed_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.tool(root, "decide", "Use Postgres")
            self.tool(root, "sync")
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(agents.count("[decided] Use Postgres"), 1)
            self.assertIn("Use Postgres", (root / "docs" / "decisions" / "log.md").read_text(encoding="utf-8"))

    def test_rejection_needs_a_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.tool(root, "new", "checkout", "Guest checkout", "--req", "REQ-004")
            result = self.tool(root, "move", "checkout-01", "rejected")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--reason", result.stderr)


class ClientCompatibilityTests(unittest.TestCase):
    """Each supported client has the files its format needs."""

    REQUIRED = {
        "claude": [".claude-plugin/plugin.json", "hooks/hooks.json"],
        "codex": ["plugin.json"],
        "copilot": ["plugin.json"],
        "antigravity": ["plugin.json", "hooks.json", "rules/AGENTS.md"],
    }

    def test_each_client_has_its_files(self) -> None:
        for client, files in self.REQUIRED.items():
            for name in files:
                with self.subTest(client=client, file=name):
                    self.assertTrue((ROOT / name).exists(), f"{client} needs {name}")

    def test_skills_are_shared_by_every_client(self) -> None:
        self.assertGreaterEqual(len(SKILL_FOLDERS), 20)

    def test_client_table_lists_every_client(self) -> None:
        text = (ROOT / "docs" / "CLIENTS.md").read_text(encoding="utf-8")
        for name in ("Claude Code", "Codex", "GitHub Copilot CLI", "Antigravity"):
            with self.subTest(client=name):
                self.assertIn(name, text)

    def test_antigravity_hook_uses_named_format(self) -> None:
        hooks = json.loads((ROOT / "hooks.json").read_text(encoding="utf-8"))
        handlers = next(iter(hooks.values()))["SessionStart"]
        self.assertEqual(handlers[0]["type"], "command")


class InstallLocationTests(unittest.TestCase):
    """Installs copy the plugin into each client's own folder, on any operating system."""

    def installer_text(self) -> str:
        return (SCRIPTS / "install.py").read_text(encoding="utf-8")

    def test_no_symlink_to_the_project(self) -> None:
        for text in (self.installer_text(), (ROOT / "Makefile").read_text(encoding="utf-8")):
            self.assertNotIn("os.symlink", text)
            self.assertNotIn("ln -sfn", text)

    def test_each_client_copies_into_its_own_folder(self) -> None:
        text = self.installer_text()
        for folder in (".claude", ".codex", ".gemini"):
            with self.subTest(folder=folder):
                self.assertIn(folder, text)
        self.assertIn("MARKER", text)

    def test_makefile_only_wraps_the_python_installer(self) -> None:
        text = (ROOT / "Makefile").read_text(encoding="utf-8")
        for target in ("install-claude", "install-codex", "install-antigravity", "install-copilot"):
            with self.subTest(target=target):
                self.assertRegex(text, rf"(?m)^{target}:.*\n\t@\$\(PY\) scripts/install\.py")

    def fake_home(self, tmp: str) -> dict[str, str]:
        """Environment that points the home folder at a temporary directory, on every OS."""
        env = dict(os.environ)
        env["HOME"] = tmp
        env["USERPROFILE"] = tmp
        return env

    def test_uninstall_removes_only_what_the_installer_made(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            made = Path(tmp) / ".gemini" / "config" / "plugins" / "developer-plugin"
            made.mkdir(parents=True)
            (made / ".installed-by-developer-plugin").write_text("x", encoding="utf-8")
            result = run([sys.executable, str(SCRIPTS / "install.py"), "uninstall", "antigravity"],
                         env=self.fake_home(tmp))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(made.exists())

    def test_uninstall_keeps_a_folder_it_did_not_make(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            theirs = Path(tmp) / ".gemini" / "config" / "plugins" / "developer-plugin"
            theirs.mkdir(parents=True)
            (theirs / "notes.txt").write_text("mine", encoding="utf-8")
            run([sys.executable, str(SCRIPTS / "install.py"), "uninstall", "antigravity"],
                env=self.fake_home(tmp))
            self.assertTrue((theirs / "notes.txt").exists())

    def fake_env_run(self, tmp: str, *args: str) -> subprocess.CompletedProcess:
        return run([sys.executable, str(SCRIPTS / "install.py"), *args], env=self.fake_home(tmp))


def load_installer():
    """Import scripts/install.py as a module, for testing its functions directly."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("install", SCRIPTS / "install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VersioningTests(unittest.TestCase):
    """Versions, changelog sections, pinned CI actions and version-specific installs."""

    def fake_project(self, root: Path, changelog: str) -> None:
        (root / "scripts").mkdir()
        shutil.copy(SCRIPTS / "release.py", root / "scripts" / "release.py")
        (root / "plugin.json").write_text(json.dumps({"name": "developer-plugin", "version": "0.1.0"}), encoding="utf-8")
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "developer-plugin", "version": "0.1.0"}), encoding="utf-8")
        (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")

    def release(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return run([sys.executable, str(root / "scripts" / "release.py"), *args], cwd=root)

    def test_minor_bump_updates_manifests_and_closes_unreleased(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fake_project(root, "# Changelog\n\n## [Unreleased]\n\n- Added a thing.\n")
            result = self.release(root, "bump", "minor", "--date", "2026-11-07")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((root / "plugin.json").read_text(encoding="utf-8"))["version"], "0.2.0")
            self.assertEqual(json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"], "0.2.0")
            changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("## [Unreleased]\n\n## [0.2.0] - 2026-11-07", changelog)
            self.assertIn("- Added a thing.", changelog)

    def test_major_and_patch_bumps(self) -> None:
        for level, expected in (("major", "1.0.0"), ("patch", "0.1.1")):
            with self.subTest(level=level), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.fake_project(root, "# Changelog\n\n## [Unreleased]\n\n- Change.\n")
                self.assertEqual(self.release(root, "bump", level).returncode, 0)
                self.assertEqual(json.loads((root / "plugin.json").read_text(encoding="utf-8"))["version"], expected)

    def test_empty_unreleased_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fake_project(root, "# Changelog\n\n## [Unreleased]\n\n")
            result = self.release(root, "bump", "minor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nothing to release", result.stderr)

    def test_verify_and_notes_for_a_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fake_project(root, "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 2026-11-07\n\n- First release.\n")
            self.assertEqual(self.release(root, "verify", "0.1.0").returncode, 0)
            self.assertIn("First release.", self.release(root, "notes", "0.1.0").stdout)
            self.assertNotEqual(self.release(root, "verify", "9.9.9").returncode, 0)

    def test_ci_actions_are_pinned_to_commit_hashes(self) -> None:
        flows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        self.assertTrue(flows, "no workflows")
        for flow in flows:
            for match in re.finditer(r"uses:\s*(\S+)", flow.read_text(encoding="utf-8")):
                with self.subTest(workflow=flow.name, uses=match.group(1)):
                    self.assertRegex(match.group(1), r"@[0-9a-f]{40}$")

    def test_release_workflow_runs_on_version_tags(self) -> None:
        text = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("v[0-9]+.[0-9]+.[0-9]+", text)
        self.assertIn("release.py verify", text)

    def test_export_copies_the_working_tree_without_git(self) -> None:
        installer = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            working = Path(tmp) / "working"
            installer.export(working, None)
            self.assertTrue((working / "plugin.json").exists())
            self.assertFalse((working / ".git").exists())
            self.assertTrue((working / ".installed-by-developer-plugin").exists())

    def test_export_copies_a_committed_version(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        installer = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "by-ref"
            installer.export(dest, "HEAD")
            self.assertTrue((dest / "plugin.json").exists())

    def test_export_refuses_an_unknown_version(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        installer = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                installer.export(Path(tmp) / "x", "v99.0.0")


class GitPracticeTests(unittest.TestCase):
    """Git practice files ship with the plugin and carry no tool attribution."""

    def test_git_templates_exist(self) -> None:
        for name in ("gitattributes", "gitmessage", "github/pull_request_template.md", "CHANGELOG.md"):
            with self.subTest(template=name):
                self.assertTrue((ROOT / "templates" / name).exists())

    def test_commit_template_has_no_attribution(self) -> None:
        text = (ROOT / "templates" / "gitmessage").read_text(encoding="utf-8")
        for banned in ("Co-Authored-By", "Generated with", "Claude", "Anthropic"):
            with self.subTest(banned=banned):
                self.assertNotIn(banned, text)

    def test_git_skills_exist(self) -> None:
        for skill in ("git-workflow", "versioning-release", "code-comments"):
            with self.subTest(skill=skill):
                self.assertTrue((ROOT / "skills" / skill / "SKILL.md").exists())

    def test_init_project_copies_git_files_and_commit_template(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as tmp:
            run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python"])
            for name in (".gitattributes", ".gitmessage", ".github/pull_request_template.md", "CHANGELOG.md"):
                with self.subTest(file=name):
                    self.assertTrue((Path(tmp) / name).exists())
            config = run(["git", "config", "commit.template"], cwd=Path(tmp)).stdout.strip()
            self.assertEqual(config, ".gitmessage")

    def test_gitignore_covers_secrets_and_build_output(self) -> None:
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("build/", ".env", "__pycache__/", ".DS_Store"):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, text)


if __name__ == "__main__":
    unittest.main()
