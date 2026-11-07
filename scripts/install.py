"""Install developer-plugin into each client. Works on Linux, macOS and Windows.

    python3 scripts/install.py claude [--ref vX.Y.Z]
    python3 scripts/install.py codex [--ref vX.Y.Z]
    python3 scripts/install.py antigravity [--ref vX.Y.Z]
    python3 scripts/install.py copilot
    python3 scripts/install.py all [--ref vX.Y.Z]
    python3 scripts/install.py uninstall claude|codex|antigravity
    python3 scripts/install.py update-clis

Each client keeps its own copy of the plugin, so deleting this folder does not
break an install. Without --ref the working tree is copied; with --ref, that
committed version is copied from git. A client that is not installed is skipped.
Standard library only.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = "developer-plugin"
MARKETPLACE = "developer-plugin-local"
MARKER = ".installed-by-developer-plugin"
COPY_IGNORE = shutil.ignore_patterns(".git", "build", ".DS_Store", "__pycache__", ".pytest_cache")


def claude_copy() -> Path:
    """Where Claude Code keeps this plugin's marketplace copy."""
    return Path.home() / ".claude" / "plugins" / "marketplaces" / MARKETPLACE


def codex_copy() -> Path:
    """Where Codex keeps this plugin's marketplace copy."""
    return Path.home() / ".codex" / "marketplaces" / MARKETPLACE


def antigravity_copy() -> Path:
    """Where Antigravity loads plugins from."""
    return Path.home() / ".gemini" / "config" / "plugins" / PLUGIN


def tool(name: str) -> str | None:
    """Return the full path of a command, or None. Finds .cmd and .exe shims on Windows."""
    return shutil.which(name)


def run(args: list[str], check: bool = True) -> None:
    """Run a command, showing its output."""
    print("+", " ".join(args), flush=True)
    subprocess.run(args, check=check)


def export(dest: Path, ref: str | None) -> None:
    """Replace dest with a copy of the plugin: the working tree, or a committed ref."""
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    elif dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    if ref:
        git = tool("git")
        if git is None:
            raise SystemExit("git is needed for --ref; install git first")
        known = subprocess.run([git, "-C", str(ROOT), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                               capture_output=True, check=False)
        if known.returncode != 0:
            raise SystemExit(f"unknown version or ref: {ref}")
        archive = subprocess.run([git, "-C", str(ROOT), "archive", "--format=tar", ref],
                                 capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            if hasattr(tarfile, "data_filter"):
                tar.extractall(dest, filter="data")
            else:
                tar.extractall(dest)  # older Python: archive is from this repository
    else:
        shutil.copytree(ROOT, dest, ignore=COPY_IGNORE, dirs_exist_ok=True)
    (dest / MARKER).write_text("created by developer-plugin install; safe to delete\n", encoding="utf-8")
    print(f"copied {ref or 'working tree'} to {dest}")


def skip(client: str, reason: str) -> None:
    """Report a client that was not installed."""
    print(f"{client}: {reason}, skipping")


def install_claude(ref: str | None) -> None:
    """Install into Claude Code from its own copy."""
    claude = tool("claude")
    if claude is None:
        return skip("claude", "not installed")
    dest = claude_copy()
    export(dest, ref)
    run([claude, "plugin", "uninstall", f"{PLUGIN}@{MARKETPLACE}"], check=False)
    run([claude, "plugin", "marketplace", "remove", MARKETPLACE], check=False)
    run([claude, "plugin", "marketplace", "add", str(dest)])
    run([claude, "plugin", "install", f"{PLUGIN}@{MARKETPLACE}"])
    print("claude: installed. Start a new session and run /plugin to confirm.")


def install_codex(ref: str | None) -> None:
    """Install into Codex from its own marketplace copy."""
    codex = tool("codex")
    if codex is None:
        return skip("codex", "not installed")
    stage = codex_copy()
    export(stage / "plugins" / PLUGIN, ref)
    (stage / ".agents" / "plugins").mkdir(parents=True, exist_ok=True)
    marketplace = {
        "name": MARKETPLACE,
        "plugins": [{
            "name": PLUGIN,
            "source": {"source": "local", "path": f"./plugins/{PLUGIN}"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Developer",
        }],
    }
    (stage / ".agents" / "plugins" / "marketplace.json").write_text(
        json.dumps(marketplace, indent=2) + "\n", encoding="utf-8")
    run([codex, "plugin", "remove", f"{PLUGIN}@{MARKETPLACE}"], check=False)
    run([codex, "plugin", "marketplace", "remove", MARKETPLACE], check=False)
    run([codex, "plugin", "marketplace", "add", str(stage)])
    run([codex, "plugin", "add", f"{PLUGIN}@{MARKETPLACE}"])
    print(f"codex: {PLUGIN} installed and enabled from {MARKETPLACE}")


def install_antigravity(ref: str | None) -> None:
    """Copy into Antigravity's plugin folder (macOS checks the app is installed)."""
    if sys.platform == "darwin" and not Path("/Applications/Antigravity.app").exists():
        return skip("antigravity", "app not installed")
    dest = antigravity_copy()
    export(dest, ref)
    print(f"antigravity: copied to {dest}. Restart Antigravity to load it.")


def install_copilot(ref: str | None) -> None:
    """Install into the Copilot CLI from the git remote (pushed commits only)."""
    if ref:
        print("copilot: --ref is not supported; Copilot installs from the git remote")
    copilot = tool("copilot")
    if copilot is None:
        return skip("copilot", "CLI not installed")
    source = os.environ.get("COPILOT_SOURCE") or git_remote()
    if not source:
        raise SystemExit("copilot: no git remote; set COPILOT_SOURCE=<git url>")
    print(f"copilot: installing from {source} (pushed commits only)")
    run([copilot, "plugin", "install", source])
    print("copilot: installed. Run 'copilot plugin list' to confirm.")
    print(f"VS Code Copilot: enable chat.plugins.enabled, then 'Chat: Install Plugin from Source' -> {ROOT}")


def git_remote() -> str:
    """Return the origin URL of this repository, or ''."""
    git = tool("git")
    if git is None:
        return ""
    done = subprocess.run([git, "-C", str(ROOT), "remote", "get-url", "origin"],
                          capture_output=True, text=True, check=False)
    return done.stdout.strip() if done.returncode == 0 else ""


def uninstall_claude() -> None:
    """Remove the Claude Code install and its copy, if this installer made it."""
    claude = tool("claude")
    if claude is not None:
        run([claude, "plugin", "uninstall", f"{PLUGIN}@{MARKETPLACE}"], check=False)
        run([claude, "plugin", "marketplace", "remove", MARKETPLACE], check=False)
    copy = claude_copy()
    if (copy / MARKER).exists():
        shutil.rmtree(copy)
        print("claude: copy removed")


def uninstall_codex() -> None:
    """Remove the Codex install and its marketplace copy, if this installer made it."""
    codex = tool("codex")
    if codex is not None:
        run([codex, "plugin", "remove", f"{PLUGIN}@{MARKETPLACE}"], check=False)
        run([codex, "plugin", "marketplace", "remove", MARKETPLACE], check=False)
    copy = codex_copy()
    if (copy / MARKER).exists() or (copy / "plugins" / PLUGIN / MARKER).exists():
        shutil.rmtree(copy)
        print("codex: copy removed")


def uninstall_antigravity() -> None:
    """Remove the Antigravity copy; only a link or a folder this installer made."""
    copy = antigravity_copy()
    if copy.is_symlink():
        copy.unlink()
        print("antigravity: link removed")
    elif (copy / MARKER).exists():
        shutil.rmtree(copy)
        print("antigravity: copy removed")
    else:
        print("antigravity: nothing to remove")


def update_clis() -> None:
    """Upgrade the npm-installed Codex CLI to the latest release."""
    npm = tool("npm")
    if npm is None:
        raise SystemExit("npm is not installed; install Node.js first")
    run([npm, "install", "-g", "@openai/codex@latest"])


INSTALLERS = {"claude": install_claude, "codex": install_codex,
              "antigravity": install_antigravity, "copilot": install_copilot}
UNINSTALLERS = {"claude": uninstall_claude, "codex": uninstall_codex,
                "antigravity": uninstall_antigravity}


def main(argv: list[str]) -> int:
    """Run one installer, or all of them."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=[*INSTALLERS, "all", "uninstall", "update-clis"])
    parser.add_argument("client", nargs="?", choices=list(UNINSTALLERS), help="for uninstall")
    parser.add_argument("--ref", default=None, help="tag or commit to install, e.g. vX.Y.Z")
    args = parser.parse_args(argv)
    if args.command == "all":
        failed = False
        for name, installer in INSTALLERS.items():
            try:
                installer(args.ref)
            except (subprocess.CalledProcessError, SystemExit) as exc:
                print(f"{name}: failed: {exc}", file=sys.stderr)
                failed = True
        return 1 if failed else 0
    if args.command == "uninstall":
        if args.client is None:
            parser.error("uninstall needs a client: claude, codex or antigravity")
        UNINSTALLERS[args.client]()
        return 0
    if args.command == "update-clis":
        update_clis()
        return 0
    INSTALLERS[args.command](args.ref)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
