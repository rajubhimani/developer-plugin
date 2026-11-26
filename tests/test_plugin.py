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
from unittest import mock

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


class SkillReferenceTests(unittest.TestCase):
    """A skill may point at files in its own references folder; they must exist."""

    def test_reference_links_resolve(self) -> None:
        missing = []
        for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
            text = skill.read_text(encoding="utf-8")
            for ref in set(re.findall(r"references/[A-Za-z0-9_.\-]+", text)):
                if not (skill.parent / ref).is_file():
                    missing.append(f"{skill.parent.name}: {ref}")
        self.assertEqual(missing, [])

    def test_every_language_has_an_idioms_guide(self) -> None:
        for skill in sorted((ROOT / "skills").glob("lang-*")):
            self.assertTrue((skill / "references" / "idioms.md").is_file(), skill.name)

    def test_python_container_templates_exist(self) -> None:
        refs = ROOT / "skills" / "lang-python" / "references"
        for name in ("Dockerfile.python", "compose.python.yaml", "env.example", "dockerignore.python", "containers.md"):
            self.assertTrue((refs / name).is_file(), name)

    def test_python_dockerfile_follows_its_own_rules(self) -> None:
        text = (ROOT / "skills" / "lang-python" / "references" / "Dockerfile.python").read_text(encoding="utf-8")
        self.assertIn("--no-install-project", text)  # dependency layer apart from source
        self.assertIn("--mount=type=cache", text)
        self.assertIn("USER 10001", text)  # numeric non-root user
        cmd = [line for line in text.splitlines() if line.startswith("CMD")]
        self.assertTrue(cmd and all(line.startswith("CMD [") for line in cmd), "CMD must be exec form")

    def test_compose_templates_have_no_version_key(self) -> None:
        text = (ROOT / "skills" / "lang-python" / "references" / "compose.python.yaml").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?m)^version:")

    def test_kubernetes_example_keeps_secrets_out(self) -> None:
        text = (ROOT / "skills" / "kubernetes" / "references" / "app.yaml").read_text(encoding="utf-8")
        self.assertNotIn("kind: Secret", text)
        self.assertNotRegex(text, r"secretRef")  # no envFrom on a Secret
        self.assertIn("secretKeyRef", text)
        self.assertNotRegex(text, r":latest\b")


class EnvCheckTests(unittest.TestCase):
    """Settings, .env.example and the cluster manifests must name the same variables."""

    def project(self, tmp: str) -> Path:
        """A fresh Python project from init-project."""
        repo = Path(tmp)
        result = run([sys.executable, str(SCRIPTS / "init_project.py"), str(repo), "python"])
        self.assertEqual(result.returncode, 0, result.stderr)
        return repo

    def check(self, repo: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return run([sys.executable, str(SCRIPTS / "check_env.py"), "--root", str(repo), *extra])

    def test_init_project_gives_python_the_container_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp)
            self.assertIn("--no-install-project", (repo / "Dockerfile").read_text(encoding="utf-8"))
            self.assertIn("migrate:", (repo / "compose.yaml").read_text(encoding="utf-8"))
            self.assertIn("!.env.example", (repo / ".dockerignore").read_text(encoding="utf-8"))
            for name in (".env.example", "src/app/settings.py", "scripts/check_env.py"):
                self.assertTrue((repo / name).is_file(), name)
            self.assertIn("check-env", (repo / "Makefile").read_text(encoding="utf-8"))

    def test_other_languages_keep_the_generic_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "go"])
            self.assertFalse((Path(tmp) / "src" / "app" / "settings.py").exists())
            self.assertNotIn("--no-install-project", (Path(tmp) / "Dockerfile").read_text(encoding="utf-8"))

    def test_existing_settings_are_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "src" / "app" / "settings.py"
            target.parent.mkdir(parents=True)
            target.write_text("mine\n", encoding="utf-8")
            result = run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python"])
            self.assertIn("kept    src/app/settings.py", result.stdout)
            self.assertEqual(target.read_text(encoding="utf-8"), "mine\n")

    def test_the_shipped_templates_agree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.check(self.project(tmp))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("6 settings agree", result.stdout)

    def test_the_example_manifests_agree_with_the_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp)
            cluster = str(ROOT / "skills" / "kubernetes" / "references")
            result = self.check(repo, "--k8s", cluster)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("cluster manifests", result.stdout)

    def test_a_field_missing_from_the_example_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp)
            example = repo / ".env.example"
            lines = [x for x in example.read_text(encoding="utf-8").splitlines() if not x.startswith("APP_API_KEY")]
            example.write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = self.check(repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing APP_API_KEY", result.stdout)

    def test_an_unknown_key_in_the_example_fails_but_compose_keys_do_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp)
            example = repo / ".env.example"
            example.write_text(example.read_text(encoding="utf-8") + "APP_STALE=1\n", encoding="utf-8")
            result = self.check(repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn("APP_STALE", result.stdout)
            self.assertNotIn("DB_PASSWORD", result.stdout)  # not prefixed, so Compose-only

    def test_a_required_field_the_cluster_never_supplies_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp)
            k8s = repo / "k8s"
            k8s.mkdir()
            (k8s / "config.yaml").write_text(
                "kind: ConfigMap\ndata:\n  APP_LOG_LEVEL: info\n", encoding="utf-8")
            result = self.check(repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn("never supply required APP_DATABASE_URL", result.stdout)

    def test_a_credential_in_a_configmap_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp)
            k8s = repo / "k8s"
            k8s.mkdir()
            (k8s / "config.yaml").write_text(
                "kind: ConfigMap\ndata:\n  APP_DATABASE_URL: postgres://x\n  APP_API_KEY: k\n",
                encoding="utf-8")
            result = self.check(repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn("APP_DATABASE_URL is a credential but is given as plain config", result.stdout)

    def test_a_stale_cluster_key_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp)
            result = self.check(repo, "--k8s", str(self.cluster_with(repo, "APP_OLD_NAME: x")))
            self.assertEqual(result.returncode, 1)
            self.assertIn("APP_OLD_NAME", result.stdout)

    def cluster_with(self, repo: Path, extra_key: str) -> Path:
        """A cluster folder that supplies every required field plus one extra key."""
        k8s = repo / "k8s"
        k8s.mkdir()
        (k8s / "app.yaml").write_text(
            "kind: ConfigMap\ndata:\n  " + extra_key + "\n---\nkind: Deployment\nenv:\n"
            "  - name: APP_DATABASE_URL\n    valueFrom:\n      secretKeyRef:\n        name: s\n"
            "        key: APP_DATABASE_URL\n  - name: APP_API_KEY\n    valueFrom:\n"
            "      secretKeyRef:\n        name: s\n        key: APP_API_KEY\n", encoding="utf-8")
        return k8s

    def test_no_settings_class_is_skipped_not_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.check(Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertIn("skipped", result.stdout)

    def test_a_field_alias_is_rejected_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp)
            settings = repo / "src" / "app" / "settings.py"
            text = settings.read_text(encoding="utf-8").replace(
                "api_key: SecretStr", 'api_key: SecretStr = Field(alias="KEY")')
            settings.write_text(text, encoding="utf-8")
            result = self.check(repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn("aliases are not supported", result.stderr)

    def test_a_plain_secret_manifest_is_warned_about(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp)
            k8s = self.cluster_with(repo, "APP_LOG_LEVEL: info")
            (k8s / "secret.yaml").write_text("kind: Secret\nstringData:\n  X: y\n", encoding="utf-8")
            result = self.check(repo)
            self.assertIn("plain Secret manifest", result.stdout)

    def test_the_settings_template_really_validates(self) -> None:
        """Run the template with the real library, when it is installed."""
        try:
            import pydantic_settings  # noqa: F401
        except ImportError:
            self.skipTest("pydantic-settings is not installed here")
        code = (
            "import os, sys, tempfile, pathlib\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import settings as s\n"
            "d = tempfile.mkdtemp(); os.chdir(d)\n"
            "pathlib.Path('.env').write_text('APP_LOG_LEVEL=debug\\nAPP_DATABASE_URL=file-value\\n"
            "APP_API_KEY=k\\nDB_PASSWORD=compose-only\\n')\n"
            "os.environ['APP_DATABASE_URL'] = 'env-value'\n"
            "x = s.Settings()\n"
            "assert x.database_url.get_secret_value() == 'env-value', 'environment must win'\n"
            "assert x.log_level == 'debug'\n"
            "assert 'env-value' not in repr(x), 'secret must not print'\n"
            "del os.environ['APP_DATABASE_URL']; pathlib.Path('.env').unlink()\n"
            "try:\n    s.Settings(); raise SystemExit('a missing credential must fail')\n"
            "except Exception as e:\n    assert 'database_url' in str(e)\n"
            "print('ok')\n"
        )
        result = run([sys.executable, "-c", code, str(ROOT / "skills" / "lang-python" / "references")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok", result.stdout)


def all_kinds() -> list[tuple[str, str]]:
    """Every (language, kind) pair that has a kind.json."""
    return sorted((p.parent.parent.name, p.parent.name) for p in (ROOT / "templates" / "kinds").glob("*/*/kind.json"))


STANDALONE = [(lang, kind) for lang, kind in all_kinds()
              if json.loads((ROOT / "templates" / "kinds" / lang / kind / "kind.json").read_text()).get("standalone", True)]


class ProjectKindTests(unittest.TestCase):
    """init-project makes the layout that fits what the project is, and records the choice."""

    def init(self, repo: Path, language: str, *flags: str) -> subprocess.CompletedProcess[str]:
        return run([sys.executable, str(SCRIPTS / "init_project.py"), str(repo), language, *flags])

    def structure(self, repo: Path, *flags: str) -> subprocess.CompletedProcess[str]:
        return run([sys.executable, str(SCRIPTS / "check_structure.py"), str(repo), *flags])

    def test_every_kind_generates_and_passes_its_own_check(self) -> None:
        for language, kind in STANDALONE:
            with self.subTest(language=language, kind=kind), tempfile.TemporaryDirectory() as tmp:
                made = self.init(Path(tmp), language, "--kind", kind, "--name", "demo-app")
                self.assertEqual(made.returncode, 0, made.stderr)
                profile = json.loads((Path(tmp) / ".developer-plugin" / "project.json").read_text())
                self.assertEqual((profile["language"], profile["kind"]), (language, kind))
                for required in profile["required"]:
                    self.assertTrue((Path(tmp) / required).exists(), f"{language} {kind}: {required} missing")
                checked = self.structure(Path(tmp))
                self.assertEqual(checked.returncode, 0, checked.stdout)
                self.assertNotIn("FAIL", checked.stdout)

    def test_rust_kinds_ship_a_cargo_deny_policy(self) -> None:
        # Without deny.toml, `cargo deny check` (part of make lint) rejects every license.
        for kind in ("library", "binary", "workspace"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(self.init(Path(tmp), "rust", "--kind", kind, "--name", "demo").returncode, 0)
                self.assertIn("[licenses]", (Path(tmp) / "deny.toml").read_text())

    def test_inline_rust_tests_count_as_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.init(Path(tmp), "rust", "--kind", "library", "--name", "demo").returncode, 0)
            result = run([sys.executable, "-m", "unittest", "tests.alignment.test_alignment.TestsExistTests",
                          "-k", "test_project_has_tests"], cwd=Path(tmp))
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_template_leaves_a_placeholder_token_or_bad_syntax(self) -> None:
        try:
            import tomllib
        except ImportError:
            self.skipTest("tomllib needs a newer Python")
        for language, kind in STANDALONE:
            with self.subTest(language=language, kind=kind), tempfile.TemporaryDirectory() as tmp:
                self.init(Path(tmp), language, "--kind", kind, "--name", "demo-app")
                for file in Path(tmp).rglob("*"):
                    if not file.is_file() or ".git" in file.parts or file.suffix in (".png", ".ico"):
                        continue
                    text = file.read_text(encoding="utf-8")
                    left = re.findall(r"\{\{(?:name|package|title|scope|module|member|member_rows|gopkg|source_dirs|workspace_dependencies|go_use|package_upper|javagroup|javapkg|javapath)\}\}", text)
                    self.assertEqual(left, [], f"{file.relative_to(tmp)} has an unfilled token")
                    if file.suffix == ".json":
                        json.loads(text)
                    if file.suffix == ".toml":
                        tomllib.loads(text)

    def test_every_kind_json_points_at_real_files(self) -> None:
        for language, kind in all_kinds():
            spec = json.loads((ROOT / "templates" / "kinds" / language / kind / "kind.json").read_text())
            with self.subTest(language=language, kind=kind):
                for field in ("title", "summary", "use_when", "required"):
                    self.assertTrue(spec.get(field), field)
                for entry in spec.get("shared", []):
                    self.assertTrue((ROOT / entry["from"]).is_file(), entry["from"])
                if spec.get("makefile"):
                    self.assertTrue((ROOT / "templates" / "makefiles" / spec["makefile"]).is_file())
                self.assertTrue((ROOT / "templates" / "kinds" / language / kind / "files").is_dir())

    def test_the_workspace_makefiles_have_the_standard_targets(self) -> None:
        for name in ("python-monorepo.mk", "node-monorepo.mk"):
            text = (ROOT / "templates" / "makefiles" / name).read_text(encoding="utf-8")
            for target in STANDARD_TARGETS:
                with self.subTest(file=name, target=target):
                    self.assertRegex(text, rf"(?m)^{re.escape(target)}:")

    def test_the_generated_makefile_runs_the_structure_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.init(Path(tmp), "python", "--kind", "library", "--name", "demo-lib")
            makefile = (Path(tmp) / "Makefile").read_text(encoding="utf-8")
            self.assertRegex(makefile, r"(?m)^check:.*structure-check")
            self.assertRegex(makefile, r"(?m)^structure-check:")
            copy = (Path(tmp) / "scripts" / "check_structure.py").read_text(encoding="utf-8")
            self.assertEqual(copy, (SCRIPTS / "check_structure.py").read_text(encoding="utf-8"))

    def test_without_a_terminal_and_without_a_kind_the_generic_layout_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.init(Path(tmp), "python")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No project kind was chosen", result.stdout)
            self.assertIn("library", result.stdout)
            self.assertFalse((Path(tmp) / ".developer-plugin").exists())
            self.assertTrue((Path(tmp) / "Makefile").exists())

    def test_every_language_has_at_least_one_kind(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        try:
            import project_kinds as pk
        finally:
            sys.path.pop(0)
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.assertTrue([k for k in pk.load_kinds(language).values() if k.standalone])
        self.assertEqual(pk.load_kinds("cobol"), {})  # a language with no kinds falls back to the generic layout

    def test_the_choice_is_recorded_and_not_asked_again(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.init(Path(tmp), "python", "--kind", "cli", "--name", "tool")
            again = self.init(Path(tmp), "python")
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertIn("Project kind: Command line tool", again.stdout)
            self.assertNotIn("No project kind was chosen", again.stdout)

    def test_a_different_kind_for_a_recorded_project_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.init(Path(tmp), "python", "--kind", "cli", "--name", "tool")
            other = self.init(Path(tmp), "python", "--kind", "webapp")
            self.assertEqual(other.returncode, 1)
            self.assertIn("recorded as a python cli", other.stderr)
            self.assertFalse((Path(tmp) / "src" / "tool" / "main.py").exists())

    def test_bad_input_is_an_error_not_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for flags, message in ((("--kind", "nope"), "unknown kind"), (("--kind", "library", "--name", "Bad Name"), "lower-case"),
                                   (("--kind", "monorepo", "--members", "x"), "name:kind"),
                                   (("--kind", "monorepo", "--members", "a:cli,b:monorepo"), "not allowed")):
                with self.subTest(flags=flags):
                    result = self.init(Path(tmp) / "x", "python", *flags) if False else self.init(Path(tmp), "python", *flags)
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn(message, result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_the_questions_accept_numbers_and_names_and_retry(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        try:
            import project_kinds as pk
        finally:
            sys.path.pop(0)
        answers = iter(["9", "what", "4", "Bad Name", "shop", ""])
        said: list[str] = []
        result = pk.intake("python", "ignored", lambda _: next(answers), said.append)
        assert result is not None
        self.assertEqual(result["kind"], "monorepo")
        self.assertEqual(result["name"], "shop")
        self.assertEqual([m["name"] for m in result["members"]], ["api", "core", "utils"])  # type: ignore[union-attr]
        self.assertTrue(any("not a choice" in line for line in said))
        self.assertIsNone(pk.intake("cobol", "x", input, print))

    def test_member_lists_are_validated(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        try:
            import project_kinds as pk
        finally:
            sys.path.pop(0)
        self.assertEqual(pk.parse_members("web:webapp, ui:ui"), [{"name": "web", "kind": "webapp"}, {"name": "ui", "kind": "ui"}])
        for bad in ("", "web", "Web:webapp", "a:x,a:y"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                pk.parse_members(bad)

    def test_node_monorepo_always_has_the_config_member(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.init(Path(tmp), "node", "--kind", "monorepo", "--name", "shop", "--members", "web:webapp")
            self.assertTrue((Path(tmp) / "packages" / "config" / "tsconfig.app.json").is_file())
            tsconfig = json.loads((Path(tmp) / "apps" / "web" / "tsconfig.json").read_text())
            self.assertEqual(tsconfig["extends"], "../../packages/config/tsconfig.app.json")

    def test_workspace_members_get_no_workflows_and_no_tool_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.init(Path(tmp), "python", "--kind", "monorepo", "--name", "acme")
            self.assertEqual(list((Path(tmp) / "packages").rglob("workflows")), [])
            member = (Path(tmp) / "packages" / "core" / "pyproject.toml").read_text(encoding="utf-8")
            self.assertNotIn("[tool.ruff", member)
            self.assertNotIn("[dependency-groups]", member)
            root = (Path(tmp) / "pyproject.toml").read_text(encoding="utf-8")
            self.assertIn('src = ["apps/api/src", "packages/core/src", "packages/utils/src"]', root)

    def test_rust_workspace_lists_library_members_as_shared_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.init(Path(tmp), "rust", "--kind", "workspace", "--name", "acme")
            root = (Path(tmp) / "Cargo.toml").read_text(encoding="utf-8")
            self.assertIn('acme-core = { path = "crates/core" }', root)
            self.assertNotIn("acme-cli = {", root)  # a binary is not a dependency

    # ---- the generated Python projects really run -------------------------------------

    def pytest(self, repo: Path, *paths: str, src: str = "src") -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(str(repo / s) for s in src.split(","))}
        return run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *paths], cwd=repo, env=env)

    def test_the_python_library_and_cli_pass_their_own_tests(self) -> None:
        try:
            import pytest  # noqa: F401
        except ImportError:
            self.skipTest("pytest is not installed here")
        for kind, test_file in (("library", "tests/test_public_api.py"), ("cli", "tests/test_cli.py")):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                self.init(Path(tmp), "python", "--kind", kind, "--name", "demo-app")
                result = self.pytest(Path(tmp), test_file)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_python_webapp_passes_its_own_tests(self) -> None:
        try:
            import alembic, fastapi, pydantic_settings, pytest, sqlalchemy  # noqa: E401, F401
            try:
                import httpx2  # noqa: F401
            except ImportError:
                import httpx  # noqa: F401
        except ImportError:
            self.skipTest("fastapi, sqlalchemy, alembic, pydantic-settings, pytest and an HTTP client are needed")
        with tempfile.TemporaryDirectory() as tmp:
            self.init(Path(tmp), "python", "--kind", "webapp", "--name", "demo-app")
            result = self.pytest(Path(tmp), "tests/unit", "tests/api")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(self.structure(Path(tmp)).returncode, 0)

    def test_the_python_monorepo_members_pass_together(self) -> None:
        try:
            import alembic, fastapi, pydantic_settings, pytest, sqlalchemy  # noqa: E401, F401
            try:
                import httpx2  # noqa: F401
            except ImportError:
                import httpx  # noqa: F401
        except ImportError:
            self.skipTest("fastapi, sqlalchemy, alembic, pydantic-settings, pytest and an HTTP client are needed")
        with tempfile.TemporaryDirectory() as tmp:
            self.init(Path(tmp), "python", "--kind", "monorepo", "--name", "acme")
            result = self.pytest(Path(tmp), src="apps/api/src,packages/core/src,packages/utils/src")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            passed = int(re.search(r"(\d+) passed", result.stdout).group(1))  # type: ignore[union-attr]
            self.assertGreaterEqual(passed, 19)
            self.assertNotIn("failed", result.stdout)

    # ---- the structure check catches each broken rule ---------------------------------

    def project(self, tmp: str, language: str, kind: str, *flags: str) -> Path:
        repo = Path(tmp)
        self.init(repo, language, "--kind", kind, "--name", "demo-app", *flags)
        return repo

    def append(self, path: Path, text: str) -> None:
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    def expect_fail(self, repo: Path, fragment: str) -> None:
        result = self.structure(repo)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(fragment, result.stdout)

    def test_a_domain_that_imports_a_framework_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "webapp")
            self.append(repo / "src" / "demo_app" / "domain" / "items.py", "\nimport fastapi\n")
            self.expect_fail(repo, "domain/items.py imports fastapi")

    def test_a_domain_that_imports_another_layer_by_relative_import_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "webapp")
            self.append(repo / "src" / "demo_app" / "domain" / "items.py", "\nfrom ..adapters import memory\n")
            self.expect_fail(repo, "imports demo_app.adapters")

    def test_a_service_that_imports_the_web_layer_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "webapp")
            self.append(repo / "src" / "demo_app" / "services" / "items.py", "\nfrom demo_app.api import errors\n")
            self.expect_fail(repo, "services/items.py imports demo_app.api")

    def test_a_route_that_imports_an_adapter_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "webapp")
            self.append(repo / "src" / "demo_app" / "api" / "items.py", "\nfrom demo_app.adapters.memory import InMemoryItemRepository\n")
            self.expect_fail(repo, "api/items.py imports demo_app.adapters")

    def test_a_library_without_the_typed_marker_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "library")
            (repo / "src" / "demo_app" / "py.typed").unlink()
            self.expect_fail(repo, "py.typed")

    def test_a_package_that_imports_an_app_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "monorepo")
            self.append(repo / "packages" / "core" / "src" / "demo_app_core" / "_greeting.py", "") if False else None
            self.append(repo / "packages" / "core" / "src" / "demo_app_core" / "__init__.py", "\nimport demo_app_api\n")
            self.expect_fail(repo, "a package must not import an app")

    def test_an_app_that_imports_another_app_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "monorepo", "--members", "api:webapp,admin:webapp")
            self.append(repo / "apps" / "admin" / "src" / "demo_app_admin" / "main.py", "\nimport demo_app_api\n")
            self.expect_fail(repo, "an app must not import an app")

    def test_importing_a_private_module_of_a_sibling_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "monorepo")
            self.append(repo / "apps" / "api" / "src" / "demo_app_api" / "main.py", "\nfrom demo_app_core import _greeting\n")
            self.expect_fail(repo, "public API")

    def test_a_member_with_its_own_lock_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "monorepo")
            (repo / "packages" / "core" / "uv.lock").write_text("", encoding="utf-8")
            self.expect_fail(repo, "must not have its own lock file")

    def test_a_node_package_that_depends_on_an_app_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "node", "monorepo")
            path = repo / "packages" / "utils" / "package.json"
            data = json.loads(path.read_text())
            data["dependencies"] = {"@demo-app/web": "workspace:*"}
            path.write_text(json.dumps(data))
            self.expect_fail(repo, "Nothing may depend on an app")

    def test_a_sibling_not_linked_through_the_workspace_is_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "node", "monorepo")
            path = repo / "apps" / "web" / "package.json"
            data = json.loads(path.read_text())
            data["dependencies"] = {"@demo-app/ui": "^1.0.0"}
            path.write_text(json.dumps(data))
            result = self.structure(repo)
            self.assertIn('WARN apps/web/package.json: @demo-app/ui is a sibling', result.stdout)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(self.structure(repo, "--strict").returncode, 1)

    def test_a_go_library_with_a_main_package_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "go", "library")
            (repo / "tool.go").write_text("package main\n", encoding="utf-8")
            self.expect_fail(repo, "must not contain package main")

    def test_a_rust_workspace_without_a_resolver_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "rust", "workspace")
            manifest = repo / "Cargo.toml"
            manifest.write_text(manifest.read_text(encoding="utf-8").replace('resolver = "<resolver>"\n', ""), encoding="utf-8")
            self.expect_fail(repo, "set the resolver explicitly")

    def test_a_missing_required_file_fails_and_placeholders_only_warn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "python", "cli")
            fresh = self.structure(repo)
            self.assertEqual(fresh.returncode, 0)
            self.assertIn("TODO pyproject.toml: replace <oldest-supported-python>", fresh.stdout)
            (repo / "README.md").unlink()
            self.expect_fail(repo, "README.md is missing")

    def test_a_folder_without_a_record_is_described_not_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "pyproject.toml").write_text("[project]\nname = 'x'\ndependencies = ['fastapi']\n", encoding="utf-8")
            result = self.structure(Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertIn("python webapp", result.stdout)

    def test_a_go_package_that_imports_an_app_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "go", "monorepo", "--module", "github.com/me/acme")
            self.assertEqual(self.structure(repo).returncode, 0)
            (repo / "packages" / "core" / "bad.go").write_text(
                'package demoappcore\n\nimport _ "github.com/me/acme/apps/api/internal/config"\n', encoding="utf-8")
            self.expect_fail(repo, "a package must not import an app")
            self.assertIn("./apps/api", (repo / "go.work").read_text(encoding="utf-8"))

    def test_java_layers_are_enforced_and_a_spring_web_client_in_an_adapter_is_fine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "java", "service")
            base = repo / "src" / "main" / "java" / "com" / "example" / "demoapp"
            adapter = base / "adapter" / "InMemoryItemRepository.java"
            adapter.write_text(adapter.read_text(encoding="utf-8").replace(
                "import java.util.List;", "import java.util.List;\nimport org.springframework.web.client.RestClient;"), encoding="utf-8")
            self.assertEqual(self.structure(repo).returncode, 0, "an adapter may use a web client library")
            domain = base / "domain" / "Item.java"
            domain.write_text(domain.read_text(encoding="utf-8").replace(
                "package com.example.demoapp.domain;", "package com.example.demoapp.domain;\n\nimport org.springframework.stereotype.Component;"), encoding="utf-8")
            self.expect_fail(repo, "domain/Item.java imports org.springframework.stereotype.Component")

    def test_cmake_projects_warn_when_warnings_are_not_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "c", "library")
            self.assertNotIn("WARN", self.structure(repo).stdout)
            cmake = repo / "CMakeLists.txt"
            cmake.write_text(cmake.read_text(encoding="utf-8").replace("-Werror", "").replace("/WX", ""), encoding="utf-8")
            self.assertIn("warnings are not errors", self.structure(repo).stdout)

    def test_a_c_library_with_a_main_function_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.project(tmp, "c", "library")
            (repo / "src" / "extra.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
            self.expect_fail(repo, "defines main in a library")

    def test_java_and_cpp_names_come_from_the_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.init(Path(tmp), "java", "--kind", "library", "--name", "demo-app", "--module", "org.acme")
            self.assertTrue((Path(tmp) / "src" / "main" / "java" / "org" / "acme" / "demoapp" / "Greeter.java").is_file())
            self.assertIn('group = "org.acme"', (Path(tmp) / "build.gradle.kts").read_text(encoding="utf-8"))

    # ---- an existing project is adopted without touching its code ---------------------

    def existing_flat_library(self, tmp: str) -> Path:
        repo = Path(tmp)
        (repo / "mylib").mkdir()
        (repo / "mylib" / "__init__.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        (repo / "pyproject.toml").write_text('[project]\nname = "mylib"\nversion = "1.2.0"\n', encoding="utf-8")
        (repo / "requirements.txt").write_text("requests\n", encoding="utf-8")
        return repo

    def test_adopting_an_existing_project_adds_no_source_and_changes_no_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.existing_flat_library(tmp)
            before = {p: p.read_text() for p in (repo / "mylib" / "__init__.py", repo / "pyproject.toml", repo / "requirements.txt")}
            result = self.init(repo, "python", "--kind", "library", "--name", "mylib")
            self.assertIn("existing project, adding safe files only", result.stdout)
            self.assertFalse((repo / "src").exists(), "must not create a src folder beside real code")
            self.assertEqual({p: p.read_text() for p in before}, before)
            self.assertTrue(json.loads((repo / ".developer-plugin" / "project.json").read_text())["adopted"])

    def test_the_check_reports_what_an_adopted_project_needs_by_hand(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.existing_flat_library(tmp)
            self.init(repo, "python", "--kind", "library", "--name", "mylib", "--structure", "best-practice")
            result = self.structure(repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn("flat layout (package 'mylib' sits beside pyproject.toml)", result.stdout)
            self.assertIn("no [build-system]", result.stdout)
            self.assertIn("requirements.txt: legacy packaging file", result.stdout)
            self.assertIn("init never creates source files in an existing project", result.stdout)
            self.assertNotIn(str(repo), result.stdout, "messages use project-relative paths")

    # ---- the owner decides: best practice, or keep the project's own structure ---------

    def test_an_existing_project_keeps_its_own_structure_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.existing_flat_library(tmp)
            before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
            made = self.init(repo, "python", "--kind", "library", "--name", "mylib")
            self.assertEqual(made.returncode, 0, made.stderr)
            self.assertIn("run again with --structure best-practice", made.stdout)
            profile = json.loads((repo / ".developer-plugin" / "project.json").read_text())
            self.assertEqual((profile["structure"], profile["required"]), ("own", ["docs/project-structure.md"]))
            self.assertFalse((repo / "src").exists(), "no folder is created beside the owner's layout")
            for name, content in before.items():
                self.assertEqual((repo / name).read_bytes(), content, f"{name} must be left as it was")
            note = (repo / "docs" / "project-structure.md").read_text()
            self.assertIn("flat layout, package `mylib`", note)
            self.assertIn("do not move, rename or reorganise", note.lower())
            self.assertIn("docs/project-structure.md", (repo / "AGENTS.md").read_text())
            self.assertFalse((repo / "docs" / "structure-plan.md").exists())

    def test_the_check_does_not_enforce_a_layout_on_an_owners_own_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.existing_flat_library(tmp)
            self.init(repo, "python", "--kind", "library", "--name", "mylib")
            result = self.structure(repo)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertNotIn("FAIL", result.stdout)
            self.assertIn("own structure", result.stdout)
            (repo / "docs" / "project-structure.md").unlink()
            self.assertEqual(self.structure(repo).returncode, 1, "the note is the one required file")

    def test_choosing_best_practice_writes_a_plan_and_moves_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.existing_flat_library(tmp)
            before = (repo / "mylib" / "__init__.py").read_bytes()
            made = self.init(repo, "python", "--kind", "library", "--name", "mylib", "--structure", "best-practice")
            self.assertEqual(made.returncode, 0, made.stderr)
            profile = json.loads((repo / ".developer-plugin" / "project.json").read_text())
            self.assertEqual(profile["structure"], "best-practice")
            plan = (repo / "docs" / "structure-plan.md").read_text()
            self.assertIn("- [ ]", plan)
            self.assertIn("flat layout", plan)
            self.assertEqual((repo / "mylib" / "__init__.py").read_bytes(), before)
            self.assertFalse((repo / "src").exists())
            self.assertFalse((repo / "docs" / "project-structure.md").exists())

    def test_the_choice_can_be_switched_later(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.existing_flat_library(tmp)
            self.init(repo, "python", "--kind", "library", "--name", "mylib")
            switched = self.init(repo, "python", "--structure", "best-practice")
            self.assertEqual(switched.returncode, 0, switched.stderr)
            self.assertIn("structure changed to best-practice", switched.stdout)
            profile = json.loads((repo / ".developer-plugin" / "project.json").read_text())
            self.assertEqual(profile["structure"], "best-practice")
            self.assertTrue((repo / "docs" / "structure-plan.md").exists())
            self.assertEqual(self.structure(repo).returncode, 1, "the recommended layout is enforced again")

    def test_a_project_recorded_before_the_choice_existed_is_not_switched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.existing_flat_library(tmp)
            self.init(repo, "python", "--kind", "library", "--name", "mylib", "--structure", "best-practice")
            path = repo / ".developer-plugin" / "project.json"
            legacy = json.loads(path.read_text())
            del legacy["structure"]
            path.write_text(json.dumps(legacy))
            again = self.init(repo, "python")
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertNotIn("structure changed", again.stdout)
            self.assertNotIn("structure", json.loads(path.read_text()))
            self.assertEqual(self.structure(repo).returncode, 1, "still checked as best practice")

    def test_a_new_empty_project_gets_the_recommended_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            made = self.init(Path(tmp), "python", "--kind", "library", "--name", "fresh")
            self.assertEqual(made.returncode, 0, made.stderr)
            profile = json.loads((Path(tmp) / ".developer-plugin" / "project.json").read_text())
            self.assertEqual(profile["structure"], "best-practice")
            self.assertTrue((Path(tmp) / "src" / "fresh" / "__init__.py").exists())

    def test_projects_get_a_safe_starter_permissions_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self.init(Path(tmp), "python", "--kind", "library", "--name", "fresh").returncode, 0)
            data = json.loads((Path(tmp) / ".claude" / "settings.example.json").read_text())
            allow = data["permissions"]["allow"]
            self.assertIn("Bash(make check)", allow)
            for entry in allow:
                for risky in ("python -", "python3 -", "bash -c", "sh -c", "docker run", "docker exec", "node -e", "curl", "Bash(*)"):
                    self.assertNotIn(risky, entry, f"{entry} could run text an attacker planted")
                self.assertFalse(entry.endswith("(*)"), "no blanket wildcard")
            self.assertIn("Bash(git push --force *)", data["permissions"]["deny"])

    def test_an_unknown_structure_value_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            refused = self.init(Path(tmp), "python", "--kind", "library", "--structure", "whatever")
            self.assertNotEqual(refused.returncode, 0)
            self.assertFalse((Path(tmp) / ".developer-plugin").exists())

    def test_the_question_defaults_to_keeping_the_structure(self) -> None:
        import project_kinds as pk
        said: list[str] = []
        for answers, expected in ((["", ], "own"), (["2"], "own"), (["1"], "best-practice"),
                                  (["best-practice"], "best-practice"), (["nonsense", "1"], "best-practice")):
            replies = iter(answers)
            self.assertEqual(pk.ask_structure(lambda _: next(replies), said.append, "python", "Library",
                                              ["layout: flat"]), expected)
        self.assertTrue(any("found: layout: flat" in line for line in said), "the answer is informed by what was found")

    def test_adopting_a_src_layout_project_may_add_the_typed_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src" / "mylib").mkdir(parents=True)
            (repo / "src" / "mylib" / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
            (repo / "pyproject.toml").write_text('[build-system]\nrequires = ["x"]\n[project]\nname = "mylib"\nrequires-python = ">=3"\n', encoding="utf-8")
            self.init(repo, "python", "--kind", "library", "--name", "mylib")
            self.assertTrue((repo / "src" / "mylib" / "py.typed").is_file())
            self.assertEqual((repo / "src" / "mylib" / "__init__.py").read_text(encoding="utf-8"), "__all__ = []\n")
            self.assertEqual([x for x in (repo / "src").iterdir()], [repo / "src" / "mylib"])

    def test_the_skill_and_docs_name_every_kind(self) -> None:
        layouts = (ROOT / "skills" / "project-structure" / "references" / "layouts.md").read_text(encoding="utf-8").lower()
        skill = (ROOT / "skills" / "project-structure" / "SKILL.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for language, kind in STANDALONE:
            with self.subTest(language=language, kind=kind):
                self.assertIn(kind, layouts)
                self.assertIn(kind, skill)
                self.assertIn(kind, readme)
        self.assertIn(".developer-plugin/project.json", skill)
        self.assertIn("Ask first", skill)


class MaintainedCodeTests(unittest.TestCase):
    """Maintained libraries only; deprecated code is replaced; the generated projects make it loud."""

    def read(self, *parts: str) -> str:
        return ROOT.joinpath(*parts).read_text(encoding="utf-8")

    def test_the_core_standards_say_both_rules(self) -> None:
        rules = self.read("rules", "coding-standards.md")
        self.assertIn("Choose maintained libraries", rules)
        self.assertIn("Update deprecated code when you find it", rules)
        self.assertIn("separate commit", rules)
        for generated in (self.read("skills", "coding-standards", "SKILL.md"), self.read("rules", "AGENTS.md")):
            self.assertIn("Update deprecated code when you find it", generated)  # the copies are in sync

    def test_the_skills_and_agents_carry_the_rules(self) -> None:
        self.assertIn("Is it maintained?", self.read("skills", "dependency-management", "SKILL.md"))
        self.assertIn("Unmaintained and deprecated", self.read("skills", "dependency-management", "SKILL.md"))
        self.assertIn("Deprecations and dependencies", self.read("skills", "code-review-checklist", "SKILL.md"))
        builder = self.read("agents", "builder.md")
        self.assertIn("Deprecations replaced", builder)
        self.assertIn("own commit", builder)
        self.assertIn("deprecat", self.read("agents", "code-reviewer.md").lower())

    def test_generated_python_projects_fail_on_deprecated_calls(self) -> None:
        for kind in ("library", "cli", "webapp", "monorepo"):
            text = self.read("templates", "kinds", "python", kind, "files", "pyproject.toml.tmpl")
            with self.subTest(kind=kind):
                self.assertIn('reportDeprecated = "error"', text)
                self.assertIn("error::DeprecationWarning", text)

    def test_generated_node_projects_lint_for_deprecated_apis_with_the_current_helper(self) -> None:
        for kind in ("webapp", "library", "ui"):
            text = self.read("templates", "kinds", "node", kind, "files", "eslint.config.js")
            with self.subTest(kind=kind):
                self.assertIn("@typescript-eslint/no-deprecated", text)
                self.assertIn('from "eslint/config"', text)
                self.assertNotIn("tseslint.config(", text)  # that helper is itself deprecated

    def test_compiled_languages_make_warnings_errors(self) -> None:
        self.assertIn("-Xlint:all", self.read("templates", "kinds", "java", "library", "files", "build.gradle.kts"))
        self.assertIn("-Werror", self.read("templates", "kinds", "java", "service", "files", "build.gradle.kts"))
        self.assertIn("-Werror", self.read("templates", "kinds", "c", "library", "files", "CMakeLists.txt"))
        self.assertIn("-Werror", self.read("templates", "kinds", "cpp", "executable", "files", "CMakeLists.txt"))
        self.assertIn("-D warnings", self.read("templates", "makefiles", "rust.mk"))  # makes the deprecated lint an error
        self.assertIn("golangci-lint", self.read("templates", "makefiles", "go.mk"))  # runs staticcheck, which flags deprecated use

    def test_templates_use_the_non_deprecated_names(self) -> None:
        service = self.read("templates", "kinds", "java", "service", "files", "gradle", "libs.versions.toml")
        self.assertIn("spring-boot-starter-webmvc", service)
        self.assertNotIn("spring-boot-starter-web\"", service)  # deprecated in favour of webmvc
        python_dev = self.read("templates", "kinds", "python", "webapp", "files", "pyproject.toml.tmpl")
        self.assertNotIn("dev-dependencies", python_dev)  # [dependency-groups] replaced it


class GitGuardTests(unittest.TestCase):
    """The git guard blocks commands that destroy work and lets everything else through."""

    BLOCKED = ["git push --force", "git push -f origin x", "git push --force-with-lease", "git push origin +main",
               "git push origin :old", "git push --delete origin x", "git -C repo push --force",
               "make test && git reset --hard HEAD~1", "git reset --hard", "git clean -fd", "git branch -D old",
               "git checkout .", "git checkout -f main", "git restore .", "git stash drop", "git stash clear",
               "/usr/bin/git reset --hard", "sudo git push -f", "FOO=1 git push -f", "cd x; git push --force",
               "git push -f 'unbalanced"]
    ALLOWED = ["git push", "git push origin feature", "git push -u origin feature", "git reset --soft HEAD~1",
               "git clean -n", "git clean -fdn", "git branch -d old", "git branch --show-current", "git checkout main",
               "git checkout -b new", "git restore --staged .", "git restore file.txt", "git stash", "git stash pop",
               "git status", "git commit --amend -m x", 'echo "git push -f"', "grep -r 'git clean -f' docs",
               "git log --oneline | head", "git push 'unbalanced"]

    def guard(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("guard", SCRIPTS / "block_dangerous_git.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_dangerous_commands_are_blocked(self) -> None:
        guard = self.guard()
        for command in self.BLOCKED:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.check(command))

    def test_ordinary_commands_pass(self) -> None:
        guard = self.guard()
        for command in self.ALLOWED:
            with self.subTest(command=command):
                self.assertIsNone(guard.check(command))

    def test_the_hook_protocol_uses_exit_code_two(self) -> None:
        def call(command: str) -> subprocess.CompletedProcess:
            return subprocess.run([sys.executable, str(SCRIPTS / "block_dangerous_git.py")], capture_output=True, text=True,
                                  input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}), check=False)
        blocked, fine = call("git push --force"), call("git push")
        self.assertEqual((blocked.returncode, fine.returncode), (2, 0))
        self.assertIn("BLOCKED", blocked.stderr)
        for odd in ("", "not json", "{}"):
            done = subprocess.run([sys.executable, str(SCRIPTS / "block_dangerous_git.py")], capture_output=True, text=True,
                                  input=odd, check=False)
            self.assertEqual(done.returncode, 0, f"bad input must not block: {odd!r}")

    def test_new_projects_get_the_guard_and_the_hook_that_runs_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python", "--kind", "library",
                                  "--name", "fresh"]).returncode, 0)
            self.assertTrue((Path(tmp) / "scripts" / "block_dangerous_git.py").is_file())
            data = json.loads((Path(tmp) / ".claude" / "settings.example.json").read_text())
            hook = data["hooks"]["PreToolUse"][0]
            self.assertEqual(hook["matcher"], "Bash")
            self.assertIn("block_dangerous_git.py", hook["hooks"][0]["command"])


class ManualSkillTests(unittest.TestCase):
    """A skill only the person starts must stay out of the model's context."""

    def test_handoff_is_manual_only(self) -> None:
        text = (ROOT / "skills" / "handoff" / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(text.split("\n---\n")[0], r"(?m)^disable-model-invocation: true$")

    def test_no_skill_is_close_to_the_compaction_cut(self) -> None:
        for path in (ROOT / "skills").glob("*/SKILL.md"):
            with self.subTest(skill=path.parent.name):
                self.assertLess(len(path.read_bytes()), 16000, "leave room before the 20,000 character cut")


class LeanAgentTests(unittest.TestCase):
    """Agents start small and load other skills on demand."""

    def test_every_agent_can_load_the_skills_it_does_not_preload(self) -> None:
        for path in sorted((ROOT / "agents").glob("*.md")):
            with self.subTest(agent=path.stem):
                text = path.read_text(encoding="utf-8")
                self.assertIn("## Load on demand", text)
                self.assertRegex(text.split("\n---\n")[0], r"(?m)^tools:.*\bSkill\b")

    def test_no_agent_preloads_more_than_the_budget(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate", SCRIPTS / "validate.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for path in sorted((ROOT / "agents").glob("*.md")):
            preload, _ = module.agent_skills(path)
            weight = sum(len((ROOT / "skills" / n / "SKILL.md").read_text(encoding="utf-8")) // 4 for n in preload)
            self.assertLessEqual(weight, module.MAX_PRELOAD_TOKENS, path.stem)

    def test_validation_rejects_a_preload_over_the_budget(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("validate", SCRIPTS / "validate.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            agent = Path(tmp) / "x.md"
            agent.write_text("---\nname: x\nskills:\n  - kubernetes\n  - lang-python\n---\n## Load on demand\n\n- `docker`: when needed.\n")
            self.assertEqual(module.agent_skills(agent), (["kubernetes", "lang-python"], ["docker"]))


class AgentTests(unittest.TestCase):
    """Agents are valid, use only skills that exist, and reviewers cannot edit."""

    AGENTS = sorted((ROOT / "agents").glob("*.md"))
    READ_ONLY = ("code-reviewer", "security-reviewer", "deploy-reviewer", "debugger")
    ROLES = {"researcher", "requirements-analyst", "architect", "test-designer", "planner",
             "test-writer", "builder", "docs-writer", "code-reviewer", "security-reviewer",
             "deploy-reviewer", "debugger"}

    @staticmethod
    def fields(path: Path) -> dict:
        match = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
        assert match, f"{path.name}: missing frontmatter"
        out: dict = {}
        key = ""
        for line in match.group(1).splitlines():
            if line.startswith("  - ") and key:
                out.setdefault(key, []).append(line[4:].strip())
            else:
                key, _, value = line.partition(":")
                key = key.strip()
                out[key] = value.strip() or []
        return out

    def test_agents_exist(self) -> None:
        self.assertGreaterEqual(len(self.AGENTS), 12)

    def test_each_agent_is_named_and_described(self) -> None:
        for path in self.AGENTS:
            with self.subTest(agent=path.stem):
                fields = self.fields(path)
                self.assertEqual(fields["name"], path.stem)
                self.assertTrue(fields["description"])
                self.assertTrue(fields["tools"])

    def test_agents_name_skills_that_exist(self) -> None:
        for path in self.AGENTS:
            for skill in self.fields(path).get("skills", []):
                with self.subTest(agent=path.stem, skill=skill):
                    self.assertIn(skill, SKILL_FOLDERS)

    def test_reviewers_and_the_debugger_are_read_only(self) -> None:
        for name in self.READ_ONLY:
            tools = {t.strip() for t in self.fields(ROOT / "agents" / f"{name}.md")["tools"].split(",")}
            with self.subTest(agent=name):
                self.assertFalse(tools & {"Edit", "Write"}, "reviewers and the debugger cannot edit")

    def test_every_role_has_an_agent_and_the_handoff_skill(self) -> None:
        names = {path.stem for path in self.AGENTS}
        self.assertEqual(names, self.ROLES)
        for path in self.AGENTS:
            with self.subTest(agent=path.stem):
                # Preloaded or loadable on demand: either way the agent can reach the report shape.
                text = path.read_text(encoding="utf-8")
                self.assertTrue("agent-handoff" in self.fields(path).get("skills", [])
                                or "- `agent-handoff`:" in text, "the agent must be able to reach agent-handoff")


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
        make_repo(path=self.umbrella / "alpha", name="alpha")
        make_repo(path=self.umbrella / "beta", name="beta",
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


class FakeClaude:
    """A stand-in for the claude command that behaves like the real one where it matters.

    It fails to add a marketplace whose folder is missing, and it deletes the folder of a
    marketplace it removes when that folder is under its own managed directory.
    """

    def __init__(self, managed: Path) -> None:
        self.managed = managed
        self.marketplaces: dict[str, dict] = {}
        self.plugins: dict[str, dict] = {}
        self.calls: list[tuple[str, ...]] = []

    def run(self, args: list[str], check: bool = True) -> None:
        command = tuple(args[1:])
        self.calls.append(command)
        try:
            self.handle(command)
        except subprocess.CalledProcessError:
            if check:
                raise

    def fail(self) -> None:
        raise subprocess.CalledProcessError(1, "claude")

    def handle(self, command: tuple[str, ...]) -> None:
        match command:
            case ("plugin", "marketplace", "add", path):
                manifest = Path(path) / ".claude-plugin" / "marketplace.json"
                if not manifest.exists():
                    self.fail()
                name = json.loads(manifest.read_text(encoding="utf-8"))["name"]
                self.marketplaces[name] = {"name": name, "source": "directory", "path": path}
            case ("plugin", "marketplace", "remove", name):
                if name not in self.marketplaces:
                    self.fail()
                entry = self.marketplaces.pop(name)
                folder = Path(entry.get("path", "")) if entry["source"] == "directory" else None
                if folder is not None and self.managed in folder.parents and folder.exists():
                    shutil.rmtree(folder)
                self.plugins = {k: v for k, v in self.plugins.items() if not k.endswith(f"@{name}")}
            case ("plugin", "marketplace", "update", name):
                if name not in self.marketplaces:
                    self.fail()
            case ("plugin", "install", plugin_id):
                _, _, market = plugin_id.partition("@")
                entry = self.marketplaces.get(market)
                if entry is None or entry["source"] != "directory" or not Path(entry["path"]).is_dir():
                    self.fail()
                version = json.loads((Path(entry["path"]) / "plugin.json").read_text(encoding="utf-8"))["version"]
                self.plugins[plugin_id] = {"id": plugin_id, "version": version, "enabled": True}
            case ("plugin", "uninstall", plugin_id):
                if plugin_id not in self.plugins:
                    self.fail()
                del self.plugins[plugin_id]
            case _:
                raise AssertionError(f"unexpected claude command {command}")

    def json(self, claude: str, *args: str) -> list[dict] | None:
        if args == ("plugin", "list", "--json"):
            return list(self.plugins.values())
        if args == ("plugin", "marketplace", "list", "--json"):
            return list(self.marketplaces.values())
        raise AssertionError(f"unexpected claude query {args}")


class ClaudeInstallTests(unittest.TestCase):
    """The Claude installer can be run at any time, in any starting state, and ends installed."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.module = load_installer()
        self.copy = root / "own" / "claude"
        self.legacy = root / "claude" / "marketplaces" / "developer-plugin-local"
        self.fake = FakeClaude(managed=root / "claude" / "marketplaces")
        # Only the claude command is faked. git and the rest stay real, and the test must not need
        # a claude binary: CI machines have none.
        real_tool = self.module.tool
        for name, value in (("tool", lambda name: "claude" if name == "claude" else real_tool(name)),
                            ("run", self.fake.run),
                            ("claude_json", self.fake.json), ("claude_copy", lambda: self.copy),
                            ("legacy_claude_copy", lambda: self.legacy)):
            patcher = mock.patch.object(self.module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.plugin_id = "developer-plugin@developer-plugin"

    def installed(self) -> dict:
        return self.fake.plugins.get(self.plugin_id, {})

    def test_installs_from_nothing(self) -> None:
        self.module.install_claude(ref=None)
        self.assertTrue(self.installed()["enabled"])
        self.assertEqual(self.fake.marketplaces["developer-plugin"]["path"], str(self.copy))

    def test_running_again_never_removes_the_marketplace(self) -> None:
        self.module.install_claude(ref=None)
        self.fake.calls.clear()
        self.module.install_claude(ref=None)
        self.assertTrue(self.installed()["enabled"])
        self.assertNotIn(("plugin", "marketplace", "remove", "developer-plugin"), self.fake.calls)
        self.assertTrue(self.copy.is_dir())

    def test_an_earlier_install_is_migrated(self) -> None:
        self.legacy.mkdir(parents=True)
        (self.legacy / ".claude-plugin").mkdir()
        (self.legacy / ".claude-plugin" / "marketplace.json").write_text('{"name": "developer-plugin-local"}')
        (self.legacy / self.module.MARKER).write_text("{}")
        self.fake.marketplaces["developer-plugin-local"] = {
            "name": "developer-plugin-local", "source": "directory", "path": str(self.legacy)}
        self.fake.plugins["developer-plugin@developer-plugin-local"] = {
            "id": "developer-plugin@developer-plugin-local", "version": "0.0.1", "enabled": True}
        self.module.install_claude(ref=None)
        self.assertNotIn("developer-plugin-local", self.fake.marketplaces)
        self.assertNotIn("developer-plugin@developer-plugin-local", self.fake.plugins)
        self.assertFalse(self.legacy.exists())
        self.assertTrue(self.installed()["enabled"])

    def test_a_github_marketplace_is_switched_to_the_local_copy(self) -> None:
        self.fake.marketplaces["developer-plugin"] = {
            "name": "developer-plugin", "source": "github", "repo": "rajubhimani/developer-plugin"}
        self.module.install_claude(ref=None)
        self.assertEqual(self.fake.marketplaces["developer-plugin"]["source"], "directory")
        self.assertTrue(self.installed()["enabled"])

    def test_a_wrong_end_state_is_reported(self) -> None:
        original = self.fake.handle

        def refuse(command: tuple[str, ...]) -> None:
            original(command)
            if command[:2] == ("plugin", "install"):
                self.fake.plugins[command[2]]["enabled"] = False

        with mock.patch.object(self.fake, "handle", refuse), self.assertRaises(SystemExit) as raised:
            self.module.install_claude(ref=None)
        self.assertIn("did not finish", str(raised.exception))

    def test_uninstall_removes_ours_and_leaves_a_github_marketplace(self) -> None:
        self.module.install_claude(ref=None)
        self.module.uninstall_claude()
        self.assertEqual((self.fake.plugins, self.fake.marketplaces, self.copy.exists()), ({}, {}, False))
        self.fake.marketplaces["developer-plugin"] = {
            "name": "developer-plugin", "source": "github", "repo": "rajubhimani/developer-plugin"}
        self.module.uninstall_claude()
        self.assertIn("developer-plugin", self.fake.marketplaces)

    def test_the_installer_and_the_published_marketplace_agree(self) -> None:
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(market["name"], self.module.CLAUDE_MARKETPLACE)
        self.assertEqual(market["plugins"][0]["name"], self.module.PLUGIN)


class InstallManifestTests(unittest.TestCase):
    """Installs record a manifest, preview with --dry-run, report drift, and stop on risky steps."""

    def setUp(self) -> None:
        self.installer = load_installer()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name) / "copy"

    def test_install_writes_a_manifest_with_a_hash_per_file(self) -> None:
        self.assertTrue(self.installer.export(dest=self.dest, ref=None))
        manifest = self.installer.read_manifest(self.dest)
        self.assertEqual(manifest["version"], self.installer.plugin_version(ROOT))
        self.assertIn("plugin.json", manifest["hashes"])
        self.assertNotIn(self.installer.MARKER, manifest["hashes"])

    def test_dry_run_writes_nothing(self) -> None:
        self.assertTrue(self.installer.export(dest=self.dest, ref=None, dry_run=True))
        self.assertFalse(self.dest.exists())
        self.assertEqual([p.name for p in Path(self.tmp.name).iterdir()], [])

    def test_second_install_reports_everything_unchanged(self) -> None:
        import contextlib
        import io
        self.installer.export(dest=self.dest, ref=None)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.installer.export(dest=self.dest, ref=None)
        self.assertRegex(out.getvalue(), r"0 added, 0 updated, [1-9]\d* unchanged, 0 removed")

    def test_reinstall_removes_a_file_the_plugin_no_longer_ships(self) -> None:
        self.installer.export(dest=self.dest, ref=None)
        manifest = self.installer.read_manifest(self.dest)
        manifest["hashes"]["skills/retired/SKILL.md"] = "0" * 64
        (self.dest / self.installer.MARKER).write_text(json.dumps(manifest), encoding="utf-8")
        (self.dest / "skills" / "retired").mkdir(parents=True)
        (self.dest / "skills" / "retired" / "SKILL.md").write_text("old", encoding="utf-8")
        self.installer.export(dest=self.dest, ref=None)
        self.assertFalse((self.dest / "skills" / "retired").exists())

    def test_downgrade_and_major_steps_need_confirmation(self) -> None:
        needs = self.installer.needs_confirmation
        self.assertIsNotNone(needs(recorded="1.2.0", incoming="1.1.9"))
        self.assertIsNotNone(needs(recorded="1.2.0", incoming="2.0.0"))
        self.assertIsNotNone(needs(recorded="junk", incoming="1.0.0"))
        self.assertIsNone(needs(recorded="1.2.0", incoming="1.2.1"))
        self.assertIsNone(needs(recorded="1.2.0", incoming="1.3.0"))
        self.assertIsNone(needs(recorded="1.2.0", incoming="1.2.0"))

    def test_a_stopped_install_leaves_the_old_copy(self) -> None:
        self.installer.export(dest=self.dest, ref=None)
        manifest = self.installer.read_manifest(self.dest)
        manifest["version"] = "99.0.0"
        (self.dest / self.installer.MARKER).write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.installer.export(dest=self.dest, ref=None)
        self.assertEqual(self.installer.read_manifest(self.dest)["version"], "99.0.0")
        self.assertTrue(self.installer.export(dest=self.dest, ref=None, confirm_update=True))

    def test_unicode_digits_in_a_version_do_not_crash(self) -> None:
        self.assertIsNone(self.installer.version_parts("1.2.\u00b2"))
        self.assertIsNotNone(self.installer.needs_confirmation(recorded="1.2.\u00b2", incoming="1.2.3"))

    def test_working_tree_copy_skips_untracked_secrets_and_symlinks(self) -> None:
        names = {path.as_posix() for path in self.installer.tracked_files() or []}
        self.assertIn("plugin.json", names)
        self.assertNotIn(".git/config", names)
        with tempfile.TemporaryDirectory() as tmp:
            self.installer.fill(stage=Path(tmp), ref=None)
            self.assertFalse(any(p.is_symlink() for p in Path(tmp).rglob("*")))
            self.assertFalse((Path(tmp) / ".env").exists())

    def test_a_folder_the_installer_did_not_make_is_not_replaced(self) -> None:
        self.dest.mkdir()
        (self.dest / "mywork.txt").write_text("mine", encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.installer.export(dest=self.dest, ref=None)
        self.assertTrue((self.dest / "mywork.txt").exists())

    def test_a_ref_that_looks_like_an_option_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                self.installer.fill(stage=Path(tmp), ref="--output=/tmp/x")

    def test_dry_run_creates_nothing_even_for_a_new_folder(self) -> None:
        deep = Path(self.tmp.name) / "a" / "b" / "copy"
        self.installer.export(dest=deep, ref=None, dry_run=True)
        self.assertFalse((Path(self.tmp.name) / "a").exists())

    def test_a_ref_copy_is_readable_by_the_clients(self) -> None:
        if sys.platform == "win32":
            self.skipTest("POSIX modes only")
        self.installer.export(dest=self.dest, ref="HEAD")
        self.assertEqual(self.dest.stat().st_mode & 0o777, 0o755)

    def test_without_a_terminal_a_risky_step_is_refused(self) -> None:
        import unittest.mock
        class NoTerminal:
            def isatty(self) -> bool:
                return False
        with unittest.mock.patch.object(sys, "stdin", NoTerminal()):
            self.assertFalse(self.installer.confirm(reason="test", bypass=False))
            self.assertTrue(self.installer.confirm(reason="test", bypass=True))

    def test_a_legacy_marker_still_gets_the_downgrade_check(self) -> None:
        self.dest.mkdir()
        (self.dest / "plugin.json").write_text(json.dumps({"version": "99.0.0"}), encoding="utf-8")
        (self.dest / self.installer.MARKER).write_text("created by an older installer\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.installer.export(dest=self.dest, ref=None)
        self.assertTrue(self.installer.export(dest=self.dest, ref=None, confirm_update=True))

    def test_an_interrupted_swap_is_recovered_on_the_next_install(self) -> None:
        self.installer.export(dest=self.dest, ref=None)
        self.dest.rename(self.dest.with_name(f".{self.dest.name}.old"))
        self.assertTrue(self.installer.export(dest=self.dest, ref=None, dry_run=False))
        self.assertTrue((self.dest / "plugin.json").exists())
        self.assertFalse(self.dest.with_name(f".{self.dest.name}.old").exists())

    def test_a_failed_swap_keeps_the_previous_copy(self) -> None:
        import unittest.mock
        self.installer.export(dest=self.dest, ref=None)
        with unittest.mock.patch.object(self.installer.shutil, "move", side_effect=PermissionError("in use")):
            with self.assertRaises(SystemExit):
                self.installer.export(dest=self.dest, ref=None)
        self.assertTrue((self.dest / "plugin.json").exists())

    def test_check_install_reports_drift_and_exit_codes(self) -> None:
        env = dict(os.environ, HOME=self.tmp.name, USERPROFILE=self.tmp.name)
        copy = Path(self.tmp.name) / ".gemini" / "config" / "plugins" / "developer-plugin"
        none = run([sys.executable, str(SCRIPTS / "install.py"), "check-install", "antigravity"], env=env)
        self.assertEqual(none.returncode, 0, none.stdout)
        self.assertIn("not installed", none.stdout)
        self.installer.export(dest=copy, ref=None)
        ok = run([sys.executable, str(SCRIPTS / "install.py"), "check-install", "antigravity"], env=env)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        (copy / "README.md").write_text("edited", encoding="utf-8")
        drift = run([sys.executable, str(SCRIPTS / "install.py"), "check-install", "antigravity"], env=env)
        self.assertEqual(drift.returncode, 1)
        self.assertIn("modified since install", drift.stdout)
        (copy / self.installer.MARKER).write_text("legacy", encoding="utf-8")
        legacy = run([sys.executable, str(SCRIPTS / "install.py"), "check-install", "antigravity"], env=env)
        self.assertEqual(legacy.returncode, 2)


class ScaffoldUpdateTests(unittest.TestCase):
    """--update brings a project to this plugin version without touching anything the owner edited."""

    def made(self, *flags: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        done = run([sys.executable, str(SCRIPTS / "init_project.py"), str(root), "python", *flags])
        self.assertEqual(done.returncode, 0, done.stderr)
        return root

    def commit(self, root: Path) -> None:
        for args in (["add", "-A"], ["commit", "-q", "-m", "state"]):
            done = run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", *args])
            self.assertEqual(done.returncode, 0, done.stderr)

    def update(self, root: Path, *flags: str) -> subprocess.CompletedProcess:
        return run([sys.executable, str(SCRIPTS / "init_project.py"), str(root), "python", "--update", *flags])

    def record(self, root: Path) -> dict:
        return json.loads((root / ".developer-plugin" / "scaffold.json").read_text(encoding="utf-8"))

    def test_init_records_a_hash_for_each_file_it_wrote(self) -> None:
        root = self.made("--kind", "library", "--name", "demo")
        files = self.record(root)["files"]
        for name in ("Makefile", ".editorconfig", "scripts/tasks.py", "tests/alignment/test_alignment.py"):
            self.assertIn(name, files)
        self.assertEqual(self.record(root)["version"], json.loads((ROOT / "plugin.json").read_text())["version"])

    def test_an_untouched_project_is_unchanged_by_an_update(self) -> None:
        root = self.made("--kind", "library", "--name", "demo")
        self.commit(root)
        result = self.update(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("0 to create, 0 to refresh", result.stdout)
        self.assertEqual(run(["git", "-C", str(root), "status", "--porcelain"]).stdout.strip(), "")

    def test_update_never_overwrites_an_edit_and_never_deletes(self) -> None:
        root = self.made("--kind", "library", "--name", "demo")
        (root / ".editorconfig").write_text((root / ".editorconfig").read_text() + "# mine\n", encoding="utf-8")
        (root / "CHANGELOG.md").unlink()
        old = "an older plugin wrote this\n"
        (root / ".gitmessage").write_text(old, encoding="utf-8")
        import hashlib
        record = self.record(root)
        record["files"][".gitmessage"] = hashlib.sha256(old.encode()).hexdigest()
        record["files"]["scripts/retired.py"] = "x"
        (root / "scripts" / "retired.py").write_text("retired\n", encoding="utf-8")
        (root / ".developer-plugin" / "scaffold.json").write_text(json.dumps(record), encoding="utf-8")
        self.commit(root)
        result = self.update(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# mine", (root / ".editorconfig").read_text(), "an edit is never overwritten")
        self.assertIn("kept    .editorconfig (you edited it", result.stdout)
        self.assertIn("-# mine", result.stdout, "the diff is shown")
        self.assertTrue((root / "CHANGELOG.md").is_file(), "a missing file is created")
        self.assertNotEqual((root / ".gitmessage").read_text(), old, "an untouched older file is refreshed")
        self.assertTrue((root / "scripts" / "retired.py").is_file(), "nothing is deleted")
        self.assertIn("orphan  scripts/retired.py", result.stdout)
        self.commit(root)
        again = self.update(root)
        self.assertIn("0 to create, 0 to refresh", again.stdout, "a second update has nothing left to do")

    def test_a_dry_run_writes_nothing_and_a_dirty_tree_is_refused(self) -> None:
        root = self.made("--kind", "library", "--name", "demo")
        (root / "CHANGELOG.md").unlink()
        refused = self.update(root)
        self.assertEqual(refused.returncode, 1)
        self.assertIn("uncommitted changes", refused.stderr)
        looked = self.update(root, "--dry-run")
        self.assertEqual(looked.returncode, 0)
        self.assertIn("create  CHANGELOG.md", looked.stdout)
        self.assertFalse((root / "CHANGELOG.md").exists())

    def test_update_needs_a_project_the_plugin_set_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.update(Path(tmp))
            self.assertEqual(result.returncode, 1)
            self.assertIn("--update is for a project the plugin already set up", result.stderr)

    def test_moving_a_project_backwards_needs_confirmation(self) -> None:
        root = self.made("--kind", "library", "--name", "demo")
        record = self.record(root)
        record["version"] = "99.0.0"
        (root / ".developer-plugin" / "scaffold.json").write_text(json.dumps(record), encoding="utf-8")
        self.commit(root)
        refused = self.update(root)
        self.assertEqual(refused.returncode, 1)
        self.assertIn("backwards", refused.stderr)
        self.assertEqual(self.update(root, "--confirm-update").returncode, 0)

    def test_an_owners_own_structure_note_is_never_touched_or_recorded(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "pyproject.toml").write_text('[project]\nname="m"\nversion="0.1"\n', encoding="utf-8")
        (root / "m").mkdir()
        (root / "m" / "__init__.py").write_text("", encoding="utf-8")
        self.assertEqual(run([sys.executable, str(SCRIPTS / "init_project.py"), str(root), "python", "--kind", "library",
                              "--name", "m", "--no-input"]).returncode, 0)
        note = root / "docs" / "project-structure.md"
        note.write_text(note.read_text() + "\n- our team rule\n", encoding="utf-8")
        self.assertNotIn("docs/project-structure.md", self.record(root)["files"])
        self.commit(root)
        result = self.update(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("- our team rule", note.read_text())
        self.assertFalse((root / "src").exists(), "an update never creates a layout the owner declined")

    def test_a_dry_run_without_update_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python", "--dry-run"])
            self.assertEqual(result.returncode, 1)


class TestHonestyTests(unittest.TestCase):
    """The check sees what a machine can: skips added, assertions removed, test files deleted."""

    BASE = "def test_a():\n    assert 1 == 1\n    assert 2 == 2\n"

    def repo(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "tests").mkdir()
        (root / "tests" / "test_a.py").write_text(self.BASE, encoding="utf-8")
        (root / "src.py").write_text("x = 1\n", encoding="utf-8")
        self.git(root, "init", "-q")
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "base")
        return root

    def git(self, root: Path, *args: str) -> None:
        done = run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", *args])
        self.assertEqual(done.returncode, 0, done.stderr)

    def verdict(self, root: Path) -> subprocess.CompletedProcess:
        self.git(root, "add", "-A")
        self.git(root, "commit", "-q", "-m", "change")
        return run([sys.executable, str(SCRIPTS / "check_tests_honest.py"), "--base", "HEAD~1"], cwd=root)

    def test_a_clean_change_passes(self) -> None:
        root = self.repo()
        (root / "tests" / "test_a.py").write_text(self.BASE + "def test_b():\n    assert 3 == 3\n", encoding="utf-8")
        (root / "src.py").write_text("x = 2  # skip this\n", encoding="utf-8")
        self.assertEqual(self.verdict(root).returncode, 0)

    def test_an_added_skip_marker_fails(self) -> None:
        for marker in ("@pytest.mark.skip\n", "@pytest.mark.xfail\n", "@unittest.skip('later')\n"):
            root = self.repo()
            (root / "tests" / "test_a.py").write_text(marker + self.BASE, encoding="utf-8")
            result = self.verdict(root)
            self.assertEqual(result.returncode, 1, marker)
            self.assertIn("adds a skip or focus marker", result.stdout)

    def test_other_languages_markers_fail(self) -> None:
        for name, text in (("a.test.ts", "it.only('x', () => {})\n"), ("a_test.go", "t.Skip(\"no\")\n"),
                           ("tests/a.rs", "#[ignore]\n"), ("tests/ATest.java", "@Disabled\n")):
            root = self.repo()
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            self.assertEqual(self.verdict(root).returncode, 1, name)

    def test_a_removed_assertion_fails_and_a_replaced_one_does_not(self) -> None:
        root = self.repo()
        (root / "tests" / "test_a.py").write_text("def test_a():\n    assert 1 == 1\n", encoding="utf-8")
        result = self.verdict(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("1 assertion(s) removed", result.stdout)
        root = self.repo()
        (root / "tests" / "test_a.py").write_text("def test_a():\n    assert 1 == 1\n    assert 3 == 3\n", encoding="utf-8")
        self.assertEqual(self.verdict(root).returncode, 0)

    def test_a_deleted_test_file_fails(self) -> None:
        root = self.repo()
        (root / "tests" / "test_a.py").unlink()
        result = self.verdict(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("test file deleted", result.stdout)

    def test_a_deliberate_skip_with_a_reason_is_allowed(self) -> None:
        root = self.repo()
        (root / "tests" / "test_a.py").write_text("# honest-ok: needs docker\n@pytest.mark.skip  # honest-ok: needs docker\n" + self.BASE, encoding="utf-8")
        self.assertEqual(self.verdict(root).returncode, 0)
        root = self.repo()
        (root / "tests" / "test_a.py").write_text("@pytest.mark.skip  # honest-ok:\n" + self.BASE, encoding="utf-8")
        self.assertEqual(self.verdict(root).returncode, 1, "a reason is required")

    def test_new_projects_get_the_check_and_a_make_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            made = run([sys.executable, str(SCRIPTS / "init_project.py"), tmp, "python", "--kind", "library", "--name", "fresh"])
            self.assertEqual(made.returncode, 0, made.stderr)
            self.assertTrue((Path(tmp) / "scripts" / "check_tests_honest.py").is_file())
            self.assertIn("honest-tests:", (Path(tmp) / "Makefile").read_text(encoding="utf-8"))


class SurfaceTests(unittest.TestCase):
    """The public surface decides the lowest version level, and removals need a warning first."""

    def repo(self, version: str = "0.1.0") -> Path:
        """Make a small tagged git repository holding a skill, an agent, a kind and a command."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "scripts").mkdir()
        for name in ("release.py", "surface.py"):
            shutil.copy(SCRIPTS / name, root / "scripts" / name)
        (root / "skills" / "alpha").mkdir(parents=True)
        (root / "skills" / "alpha" / "SKILL.md").write_text("---\nname: alpha\n---\n", encoding="utf-8")
        (root / "agents").mkdir()
        (root / "agents" / "worker.md").write_text("---\nname: worker\n---\n", encoding="utf-8")
        (root / "templates" / "kinds" / "python" / "library").mkdir(parents=True)
        (root / "templates" / "kinds" / "python" / "library" / "kind.json").write_text("{}", encoding="utf-8")
        (root / "Makefile").write_text("check: ## Gate\n\ttrue\n", encoding="utf-8")
        (root / "plugin.json").write_text(json.dumps({"name": "p", "version": version}), encoding="utf-8")
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "p", "version": version}), encoding="utf-8")
        (root / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n\n- Something.\n", encoding="utf-8")
        for args in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "x"],
                     ["tag", f"v{version}"]):
            self.assertEqual(run(["git", "-C", str(root), *args]).returncode, 0)
        return root

    def surface(self, root: Path) -> subprocess.CompletedProcess:
        return run([sys.executable, str(root / "scripts" / "surface.py")], cwd=root)

    def level(self, root: Path) -> str:
        import importlib.util
        spec = importlib.util.spec_from_file_location("surface_under_test", root / "scripts" / "surface.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return str(module.compare(root)["floor"])

    def test_nothing_new_allows_a_patch(self) -> None:
        root = self.repo()
        self.assertEqual(self.level(root), "patch")

    def test_adding_a_skill_an_agent_a_kind_or_a_command_needs_a_minor(self) -> None:
        for make in (lambda r: (r / "skills" / "beta").mkdir() or (r / "skills" / "beta" / "SKILL.md").write_text("x"),
                     lambda r: (r / "agents" / "other.md").write_text("x"),
                     lambda r: (r / "templates" / "kinds" / "go").mkdir() or (r / "templates" / "kinds" / "go" / "cli").mkdir()
                     or (r / "templates" / "kinds" / "go" / "cli" / "kind.json").write_text("{}"),
                     lambda r: (r / "Makefile").write_text("check: ## Gate\n\ttrue\nship: ## Ship\n\ttrue\n")):
            root = self.repo()
            make(root)
            self.assertEqual(self.level(root), "minor")

    def test_a_release_below_the_floor_is_refused_and_auto_picks_the_floor(self) -> None:
        root = self.repo()
        (root / "skills" / "beta").mkdir()
        (root / "skills" / "beta" / "SKILL.md").write_text("x")
        refused = run([sys.executable, str(root / "scripts" / "release.py"), "bump", "patch"], cwd=root)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("below the lowest level", refused.stderr)
        self.assertEqual(json.loads((root / "plugin.json").read_text())["version"], "0.1.0", "nothing was written")
        done = run([sys.executable, str(root / "scripts" / "release.py"), "bump", "auto", "--date", "2026-11-26"], cwd=root)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads((root / "plugin.json").read_text())["version"], "0.2.0")

    def test_a_removal_fails_the_check_until_the_version_allows_it(self) -> None:
        root = self.repo()
        shutil.rmtree(root / "skills" / "alpha")
        self.assertEqual(self.level(root), "minor", "before 1.0 a minor release may break things")
        failed = run([sys.executable, str(root / "scripts" / "surface.py"), "--check"], cwd=root)
        self.assertEqual(failed.returncode, 1)
        self.assertIn("skill alpha removed since v0.1.0", failed.stdout)
        for name in ("plugin.json", ".claude-plugin/plugin.json"):
            (root / name).write_text(json.dumps({"name": "p", "version": "0.2.0"}))
        self.assertEqual(run([sys.executable, str(root / "scripts" / "surface.py"), "--check"], cwd=root).returncode, 0)

    def test_after_1_0_a_removal_needs_a_major(self) -> None:
        root = self.repo(version="1.0.0")
        (root / "agents" / "worker.md").unlink()
        self.assertEqual(self.level(root), "major")
        for name in ("plugin.json", ".claude-plugin/plugin.json"):
            (root / name).write_text(json.dumps({"name": "p", "version": "1.1.0"}))
        self.assertEqual(run([sys.executable, str(root / "scripts" / "surface.py"), "--check"], cwd=root).returncode, 1)
        for name in ("plugin.json", ".claude-plugin/plugin.json"):
            (root / name).write_text(json.dumps({"name": "p", "version": "2.0.0"}))
        self.assertEqual(run([sys.executable, str(root / "scripts" / "surface.py"), "--check"], cwd=root).returncode, 0)

    def test_with_no_release_tag_there_is_nothing_to_compare(self) -> None:
        root = self.repo()
        run(["git", "-C", str(root), "tag", "-d", "v0.1.0"])
        result = self.surface(root)
        self.assertEqual(result.returncode, 0)
        self.assertIn("no release tag yet", result.stdout)
        auto = run([sys.executable, str(root / "scripts" / "release.py"), "bump", "auto"], cwd=root)
        self.assertNotEqual(auto.returncode, 0)
        self.assertIn("no release tag yet", auto.stderr)

    def test_the_real_plugin_passes_its_own_surface_check(self) -> None:
        self.assertEqual(run([sys.executable, str(SCRIPTS / "surface.py"), "--check"]).returncode, 0)


class VersioningTests(unittest.TestCase):
    """Versions, changelog sections, pinned CI actions and version-specific installs."""

    def fake_project(self, root: Path, changelog: str) -> None:
        (root / "scripts").mkdir()
        shutil.copy(SCRIPTS / "release.py", root / "scripts" / "release.py")
        shutil.copy(SCRIPTS / "surface.py", root / "scripts" / "surface.py")
        (root / "plugin.json").write_text(json.dumps({"name": "developer-plugin", "version": "0.1.0"}), encoding="utf-8")
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "developer-plugin", "version": "0.1.0"}), encoding="utf-8")
        (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")

    def release(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return run([sys.executable, str(root / "scripts" / "release.py"), *args], cwd=root)

    def test_minor_bump_updates_manifests_and_closes_unreleased(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fake_project(root=root, changelog="# Changelog\n\n## [Unreleased]\n\n- Added a thing.\n")
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
                self.fake_project(root=root, changelog="# Changelog\n\n## [Unreleased]\n\n- Change.\n")
                self.assertEqual(self.release(root, "bump", level).returncode, 0)
                self.assertEqual(json.loads((root / "plugin.json").read_text(encoding="utf-8"))["version"], expected)

    def test_empty_unreleased_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fake_project(root=root, changelog="# Changelog\n\n## [Unreleased]\n\n")
            result = self.release(root, "bump", "minor")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nothing to release", result.stderr)

    def test_verify_and_notes_for_a_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fake_project(root=root, changelog="# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 2026-11-07\n\n- First release.\n")
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
            installer.export(dest=working, ref=None)
            self.assertTrue((working / "plugin.json").exists())
            self.assertFalse((working / ".git").exists())
            self.assertTrue((working / ".installed-by-developer-plugin").exists())

    def test_export_copies_a_committed_version(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        installer = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "by-ref"
            installer.export(dest=dest, ref="HEAD")
            self.assertTrue((dest / "plugin.json").exists())

    def test_export_refuses_an_unknown_version(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        installer = load_installer()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                installer.export(dest=Path(tmp) / "x", ref="v99.0.0")


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
