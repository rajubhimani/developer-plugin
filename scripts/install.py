"""Install developer-plugin into each client. Works on Linux, macOS and Windows.

    python3 scripts/install.py claude [--ref vX.Y.Z]
    python3 scripts/install.py codex [--ref vX.Y.Z]
    python3 scripts/install.py antigravity [--ref vX.Y.Z]
    python3 scripts/install.py copilot
    python3 scripts/install.py all [--ref vX.Y.Z]
    python3 scripts/install.py <client> --dry-run      show what would change, write nothing
    python3 scripts/install.py <client> --confirm-update  allow a downgrade or major step
    python3 scripts/install.py check-install [claude|codex|antigravity]
    python3 scripts/install.py uninstall claude|codex|antigravity
    python3 scripts/install.py update-clis

Each client keeps its own copy of the plugin, so deleting this folder does not
break an install. Without --ref the working tree is copied; with --ref, that
committed version is copied from git. A client that is not installed is skipped.

Each copy carries a manifest (version, source, a hash per file) in its marker
file. It lets a re-install report "N added, M updated, K unchanged, J removed",
lets --dry-run preview that, lets check-install report drift without writing,
and makes the install stop before a downgrade or a major version step unless
--confirm-update is given. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
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


def tracked_files() -> list[Path] | None:
    """Return the files git would keep (tracked, plus untracked but not ignored), or None outside git."""
    git = tool("git")
    if git is None:
        return None
    done = subprocess.run([git, "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                          capture_output=True, check=False)
    if done.returncode != 0:
        return None
    return [Path(name) for name in done.stdout.decode("utf-8").split("\0") if name]


def safe_members(tar: tarfile.TarFile) -> list[tarfile.TarInfo]:
    """Return the archive members to extract, refusing links and paths that leave the folder."""
    members = tar.getmembers()
    for member in members:
        parts = Path(member.name).parts
        if member.issym() or member.islnk() or Path(member.name).is_absolute() or ".." in parts:
            raise SystemExit(f"refusing archive member {member.name!r}: links and outside paths are not copied")
    return members


def fill(stage: Path, ref: str | None) -> None:
    """Fill an empty folder with the plugin: the working tree, or a committed ref.

    A working-tree copy takes only the files git tracks or would not ignore, and
    never a symlink, so untracked secrets and outside files are not copied.
    """
    if ref:
        git = tool("git")
        if git is None:
            raise SystemExit("git is needed for --ref; install git first")
        if ref.startswith("-"):
            raise SystemExit(f"not a version or ref: {ref!r}")
        known = subprocess.run([git, "-C", str(ROOT), "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
                               capture_output=True, text=True, check=False)
        if known.returncode != 0:
            raise SystemExit(f"unknown version or ref: {ref}")
        archive = subprocess.run([git, "-C", str(ROOT), "archive", "--format=tar", known.stdout.strip()],
                                 capture_output=True, check=True).stdout
        try:
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                if hasattr(tarfile, "data_filter"):
                    tar.extractall(stage, filter="data")
                else:
                    tar.extractall(stage, members=safe_members(tar))
        except tarfile.TarError as exc:
            raise SystemExit(f"could not extract {ref}: {exc}")
        return
    names = tracked_files()
    if names is None:
        shutil.copytree(ROOT, stage, ignore=COPY_IGNORE, symlinks=True, dirs_exist_ok=True)
        return
    for name in names:
        source = ROOT / name
        if source.is_symlink() or not source.is_file() or COPY_IGNORE(str(source.parent), [source.name]):
            continue
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def hash_tree(folder: Path) -> dict[str, str]:
    """Return a sha256 per file under folder, keyed by POSIX path, leaving out the marker."""
    hashes = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and not path.is_symlink() and path.name != MARKER:
            hashes[path.relative_to(folder).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def read_manifest(dest: Path) -> dict | None:
    """Return the manifest in a copy, None if there is no usable one (legacy marker or none)."""
    try:
        data = json.loads((dest / MARKER).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and isinstance(data.get("hashes"), dict) else None


def plugin_version(folder: Path) -> str:
    """Return the version a plugin folder declares, or 'unknown'."""
    try:
        return str(json.loads((folder / "plugin.json").read_text(encoding="utf-8"))["version"])
    except (OSError, ValueError, KeyError):
        return "unknown"


def version_parts(version: str) -> tuple[int, int, int] | None:
    """Parse MAJOR.MINOR.PATCH, or None."""
    match = re.fullmatch(r"([0-9]+)\.([0-9]+)\.([0-9]+)", version, re.ASCII)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def needs_confirmation(recorded: str, incoming: str) -> str | None:
    """Return why a step from the recorded to the incoming version must be confirmed, else None.

    A patch or minor step, or no step, goes ahead. A downgrade, a major step, or
    a version that cannot be read stops.
    """
    old, new = version_parts(recorded), version_parts(incoming)
    if old is None or new is None:
        return f"cannot compare versions {recorded} and {incoming}"
    if new < old:
        return f"downgrade from {recorded} to {incoming}"
    if new[0] > old[0]:
        return f"major step from {recorded} to {incoming}"
    return None


def confirm(reason: str, bypass: bool) -> bool:
    """Ask for a typed yes. With no terminal, fail closed and name the flag."""
    print(f"stop: {reason}")
    if bypass:
        print("--confirm-update given; continuing")
        return True
    if not sys.stdin.isatty():
        print("nothing written. Re-run with --confirm-update to continue without being asked.")
        return False
    return input("type yes to continue: ").strip().lower() == "yes"


def shown(text: object) -> str:
    """Return text safe to print: control characters escaped, long text cut."""
    return repr(str(text))[:200]


def compare(old: dict[str, str], new: dict[str, str]) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return the added, updated, unchanged and removed paths between two hash maps."""
    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    updated = sorted(path for path in new.keys() & old.keys() if new[path] != old[path])
    unchanged = sorted(path for path in new.keys() & old.keys() if new[path] == old[path])
    return added, updated, unchanged, removed


def git_commit() -> str:
    """Return the short commit of this checkout, or ''."""
    git = tool("git")
    if git is None:
        return ""
    done = subprocess.run([git, "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True, check=False)
    return done.stdout.strip() if done.returncode == 0 else ""


def remove_path(path: Path) -> None:
    """Remove a file, a link (never its target) or a folder, if it exists."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def export(dest: Path, ref: str | None, dry_run: bool = False, confirm_update: bool = False) -> bool:
    """Replace dest with a copy of the plugin and say what changed.

    The copy is built beside dest and swapped in; the old copy is kept until the
    new one is in place, so an interrupt leaves a copy or the whole new one (an
    interrupt between the two renames leaves it as a hidden .old folder). A
    refused step raises SystemExit, so callers and `all` see a failure. With
    dry_run nothing is created under dest's folder.
    """
    old_copy = dest.with_name(f".{dest.name}.old")
    if not dry_run and not dest.exists() and not dest.is_symlink() and old_copy.is_dir():
        old_copy.rename(dest)
        print(f"recovered the previous copy from an interrupted install: {dest}")
    previous = read_manifest(dest)
    if previous is None and dest.exists() and not (dest / MARKER).exists() and not dry_run:
        if not confirm(reason=f"{dest} exists and was not made by this installer", bypass=confirm_update):
            raise SystemExit(1)
    stage = Path(tempfile.mkdtemp(prefix=f".{dest.name}.new-", dir=None if dry_run else dest.parent
                                  if dest.parent.exists() else None))
    try:
        os.chmod(stage, 0o755)  # mkdtemp makes it private; clients read the copy
        fill(stage=stage, ref=ref)
        incoming = plugin_version(stage)
        new_hashes = hash_tree(stage)
        recorded = str(previous.get("version")) if previous is not None else (
            plugin_version(dest) if (dest / MARKER).exists() else None)
        if recorded is not None:
            reason = needs_confirmation(recorded=recorded, incoming=incoming)
            if reason and dry_run:
                print(f"note: a real run would stop for confirmation ({shown(reason)})")
            elif reason and not confirm(reason=reason, bypass=confirm_update):
                raise SystemExit(1)
        elif dest.exists() and not dry_run:
            print(f"note: {dest} has no recorded version; replacing it")
        added, updated, unchanged, removed = compare(old=(previous or {}).get("hashes", {}), new=new_hashes)
        summary = f"{len(added)} added, {len(updated)} updated, {len(unchanged)} unchanged, {len(removed)} removed"
        if dry_run:
            for label, paths in (("+", added), ("~", updated), ("-", removed)):
                for path in paths:
                    print(f"  {label} {path}")
            print(f"dry run, nothing written: {summary} (version {incoming})")
            return True
        manifest = {"plugin": PLUGIN, "version": incoming, "source": ref or "working tree",
                    "commit": git_commit(), "root": ROOT.as_posix(), "hashes": new_hashes}
        (stage / MARKER).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        remove_path(old_copy)
        try:
            if dest.is_symlink() or dest.is_file():
                dest.unlink()
            elif dest.exists():
                dest.rename(old_copy)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(stage), str(dest))
        except OSError as exc:
            if old_copy.is_dir() and not dest.exists():
                old_copy.rename(dest)
            raise SystemExit(f"could not replace {dest} ({exc}); the previous copy was kept. "
                             "Close anything using it and run again.")
        remove_path(old_copy)
        print(f"copied {ref or 'working tree'} to {dest}: {summary}")
        return True
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def skip(client: str, reason: str) -> None:
    """Report a client that was not installed."""
    print(f"{client}: {reason}, skipping")


def install_claude(ref: str | None, dry_run: bool = False, confirm_update: bool = False) -> None:
    """Install into Claude Code from its own copy."""
    claude = tool("claude")
    if claude is None:
        return skip(client="claude", reason="not installed")
    dest = claude_copy()
    export(dest=dest, ref=ref, dry_run=dry_run, confirm_update=confirm_update)
    if dry_run:
        return
    run([claude, "plugin", "uninstall", f"{PLUGIN}@{MARKETPLACE}"], check=False)
    run([claude, "plugin", "marketplace", "remove", MARKETPLACE], check=False)
    run([claude, "plugin", "marketplace", "add", str(dest)])
    run([claude, "plugin", "install", f"{PLUGIN}@{MARKETPLACE}"])
    print("claude: installed. Start a new session and run /plugin to confirm.")


def install_codex(ref: str | None, dry_run: bool = False, confirm_update: bool = False) -> None:
    """Install into Codex from its own marketplace copy."""
    codex = tool("codex")
    if codex is None:
        return skip(client="codex", reason="not installed")
    stage = codex_copy()
    export(dest=stage / "plugins" / PLUGIN, ref=ref, dry_run=dry_run, confirm_update=confirm_update)
    if dry_run:
        return
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


def install_antigravity(ref: str | None, dry_run: bool = False, confirm_update: bool = False) -> None:
    """Copy into Antigravity's plugin folder (macOS checks the app is installed)."""
    if sys.platform == "darwin" and not Path("/Applications/Antigravity.app").exists():
        return skip(client="antigravity", reason="app not installed")
    dest = antigravity_copy()
    export(dest=dest, ref=ref, dry_run=dry_run, confirm_update=confirm_update)
    if dry_run:
        return
    print(f"antigravity: copied to {dest}. Restart Antigravity to load it.")


def install_copilot(ref: str | None, dry_run: bool = False, confirm_update: bool = False) -> None:
    """Install into the Copilot CLI from the git remote (pushed commits only)."""
    if ref:
        print("copilot: --ref is not supported; Copilot installs from the git remote")
    copilot = tool("copilot")
    if copilot is None:
        return skip(client="copilot", reason="CLI not installed")
    source = os.environ.get("COPILOT_SOURCE") or git_remote()
    if not source:
        raise SystemExit("copilot: no git remote; set COPILOT_SOURCE=<git url>")
    if source.startswith("-"):
        raise SystemExit(f"copilot: not a source: {source!r}")
    print(f"copilot: installing from {source} (pushed commits only)")
    if dry_run:
        print("dry run, nothing written")
        return
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


COPIES = {"claude": claude_copy,
          "codex": lambda: codex_copy() / "plugins" / PLUGIN,
          "antigravity": antigravity_copy}


def check_copy(client: str, current: dict[str, str], version: str) -> str:
    """Report how one client's copy differs from this checkout. Return ok, drift, none or corrupt."""
    dest = COPIES[client]()
    if not (dest / MARKER).exists():
        print(f"{client}: not installed (no copy at {dest})")
        return "none"
    manifest = read_manifest(dest)
    if manifest is None:
        print(f"{client}: the copy at {dest} has no readable manifest (older install). Reinstall to record one.")
        return "corrupt"
    problems = []
    if manifest.get("version") != version:
        problems.append(f"installed version {shown(manifest.get('version'))} != checkout version {version}")
    if manifest.get("root") != ROOT.as_posix():
        problems.append(f"installed from {shown(manifest.get('root'))}, this checkout is {ROOT.as_posix()}")
    recorded: dict[str, str] = manifest["hashes"]
    on_disk = hash_tree(dest)
    missing = sorted(path for path in recorded if path not in on_disk)
    modified = sorted(path for path in recorded if path in on_disk and on_disk[path] != recorded[path])
    stale = sorted(path for path in recorded
                   if path in on_disk and on_disk[path] == recorded[path] and current.get(path) not in (None, recorded[path]))
    gone = sorted(path for path in recorded if path not in current)
    new = sorted(path for path in current if path not in recorded)
    for label, paths in (("missing", missing), ("modified since install", modified),
                         ("stale (checkout changed since install)", stale),
                         ("no longer shipped by this checkout", gone), ("new in this checkout", new)):
        if paths:
            problems.append(f"{len(paths)} file(s) {label}: {', '.join(shown(p) for p in paths[:20])}"
                            + (" ..." if len(paths) > 20 else ""))
    if not problems:
        print(f"{client}: up to date (version {manifest.get('version')})")
        return "ok"
    print(f"{client}: DRIFTED")
    for problem in problems:
        print(f"  - {problem}")
    print(f"  run: python3 scripts/install.py {client}")
    return "drift"


def check_install(clients: list[str]) -> int:
    """Compare installed copies with this checkout, read-only. Exit 0 ok, 1 drift, 2 unreadable."""
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "source"
        stage.mkdir()
        fill(stage=stage, ref=None)
        current, version = hash_tree(stage), plugin_version(stage)
    results = [check_copy(client=client, current=current, version=version) for client in clients]
    print("copilot installs from the git remote and is not checked here")
    if "corrupt" in results:
        return 2
    return 1 if "drift" in results else 0


INSTALLERS = {"claude": install_claude, "codex": install_codex,
              "antigravity": install_antigravity, "copilot": install_copilot}


UNINSTALLERS = {"claude": uninstall_claude, "codex": uninstall_codex,
                "antigravity": uninstall_antigravity}


def main(argv: list[str]) -> int:
    """Run one installer, or all of them."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=[*INSTALLERS, "all", "uninstall", "update-clis", "check-install"])
    parser.add_argument("client", nargs="?", choices=list(UNINSTALLERS), help="for uninstall and check-install")
    parser.add_argument("--ref", default=None, help="tag or commit to install, e.g. vX.Y.Z")
    parser.add_argument("--dry-run", action="store_true", help="show what would change; write nothing")
    parser.add_argument("--confirm-update", action="store_true",
                        help="continue past a downgrade or major version step without asking")
    args = parser.parse_args(argv)
    options = {"ref": args.ref, "dry_run": args.dry_run, "confirm_update": args.confirm_update}
    if args.command == "check-install":
        return check_install(clients=[args.client] if args.client else list(COPIES))
    if args.command == "all":
        failed = False
        for name, installer in INSTALLERS.items():
            try:
                installer(**options)
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
    INSTALLERS[args.command](**options)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
