"""A Claude Code PreToolUse hook that blocks git commands which destroy work or history.

Claude Code runs it before every Bash command and passes the call as JSON on standard input.
Exit 2 blocks the command and shows the message to the agent; exit 0 lets it run.

Blocked: force or delete pushes, `reset --hard`, `clean` with force, `branch -D`, `checkout .`
or `checkout --force`, `restore .`, `stash drop` and `stash clear`. A plain push, commit, merge,
rebase, `reset --soft`, a dry-run `clean -n` and `branch -d` are allowed.

The command is split with a real shell tokenizer, so `git -C repo push --force` is caught, a
chain such as `make test && git reset --hard` is caught, and the text of `echo "git push -f"` is
not mistaken for a command. If the command cannot be parsed it falls back to a cautious text
match. Standard library only; works on Windows. Wire it in `.claude/settings.json`:

    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
        "command": "python3 \\"$CLAUDE_PROJECT_DIR/scripts/block_dangerous_git.py\\""}]}]}
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

WRAPPERS = {"sudo", "env", "command", "time", "nohup", "exec", "nice", "xargs"}
OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
FALLBACK = re.compile(
    r"git\b[^\n;&|]*\b(push\b[^\n;&|]*(\s-[a-zA-Z]*[fd]\b|--force|--delete|\s\+\S)|reset\s+--hard|clean\b[^\n;&|]*\s-[a-zA-Z]*f"
    r"|branch\s+-D\b|checkout\s+(-f|--force|\.)|restore\s+\.|stash\s+(drop|clear))")


def segments(command: str) -> list[list[str]]:
    """Split a shell command line into simple commands, each a list of words."""
    lexer = shlex.shlex(command.replace("\r", "").replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    out: list[list[str]] = [[]]
    for token in lexer:
        if all(ch in ";&|()<>" for ch in token):
            if out[-1]:
                out.append([])
        else:
            out[-1].append(token)
    return [s for s in out if s]


def git_call(words: list[str]) -> tuple[str, list[str]] | None:
    """Return (subcommand, args) if this simple command runs git, else None."""
    i = 0
    while i < len(words) and (words[i] in WRAPPERS or "=" in words[i] or words[i].startswith("-")):
        i += 1
    if i >= len(words) or os.path.basename(words[i]).lower() not in ("git", "git.exe"):
        return None
    i += 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in OPTIONS_WITH_VALUE else 1
    return (words[i], words[i + 1:]) if i < len(words) else None


def cluster(args: list[str], letter: str) -> bool:
    """True when a short-option cluster such as -fd contains the letter."""
    return any(re.fullmatch(rf"-[a-zA-Z]*{letter}[a-zA-Z]*", a) for a in args)


def reason(sub: str, args: list[str]) -> str | None:
    """Return why this git command is blocked, or None."""
    if sub == "push":
        refspec_force = any(a.startswith("+") and len(a) > 1 for a in args)
        if cluster(args, "f") or cluster(args, "d") or refspec_force or any(
                a in ("--force", "--delete", "--mirror", "--force-if-includes") or a.startswith("--force-with-lease")
                for a in args) or any(a.startswith(":") and len(a) > 1 for a in args):
            return "a force or delete push rewrites or removes history on the remote"
    if sub == "reset" and "--hard" in args:
        return "reset --hard throws away uncommitted work"
    if sub == "clean" and (cluster(args, "f") or "--force" in args) and not (cluster(args, "n") or "--dry-run" in args):
        return "clean with force deletes untracked files for good"
    if sub == "branch" and (cluster(args, "D") or (("--delete" in args or cluster(args, "d")) and ("--force" in args or cluster(args, "f")))):
        return "branch -D deletes a branch even if it is not merged"
    if sub == "checkout" and ("." in args or "--force" in args or cluster(args, "f")):
        return "this checkout overwrites uncommitted changes"
    if sub == "restore" and "." in args and ("--staged" not in args or "--worktree" in args):
        return "restore . throws away uncommitted changes"
    if sub == "stash" and args[:1] and args[0] in ("drop", "clear"):
        return "stash drop or clear loses saved work"
    return None


def check(command: str) -> str | None:
    """Return a message when the command must be blocked, else None."""
    try:
        parsed = segments(command)
    except ValueError:  # unbalanced quotes and the like: be cautious on the raw text
        return "could not parse it and it looks like a destructive git command" if FALLBACK.search(command) else None
    for words in parsed:
        call = git_call(words)
        if call and (why := reason(*call)):
            return f"`{' '.join(words)[:120]}`: {why}"
    return None


def main() -> int:
    """Read the hook call from stdin; block a dangerous git command."""
    try:
        command = str(json.load(sys.stdin).get("tool_input", {}).get("command", ""))
    except (ValueError, AttributeError):
        return 0
    message = check(command) if command else None
    if message:
        print(f"BLOCKED by the project's git guard: {message}. If the person really wants this, "
              "ask them to run it themselves.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
