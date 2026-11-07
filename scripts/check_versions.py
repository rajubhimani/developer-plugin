"""Print the current stable release of common tools, from their public sources.

Nothing is stored here: each run asks the registry, release feed or GitHub API
live, so the answer stays current without editing any skill. Failures are shown
per tool and never stop the others. Standard library only.

Usage: python3 scripts/check_versions.py [--json]
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import urllib.error
import urllib.request

TIMEOUT = 10
# (display name, source kind, argument). Add a row to track another tool.
TOOLS = [
    ("Python", "endoflife", "python"),
    ("Go", "endoflife", "go"),
    ("Node.js", "endoflife", "nodejs"),
    ("Rust", "endoflife", "rust"),
    ("Java (latest LTS)", "endoflife-lts", "oracle-jdk"),
    ("CMake", "github", "Kitware/CMake"),
    ("golangci-lint", "github", "golangci/golangci-lint"),
    ("Gradle", "github", "gradle/gradle"),
    ("uv", "pypi", "uv"),
    ("ruff", "pypi", "ruff"),
    ("pyright", "pypi", "pyright"),
    ("React", "npm", "react"),
    ("TypeScript", "npm", "typescript"),
    ("Vite", "npm", "vite"),
    ("Vitest", "npm", "vitest"),
    ("ESLint", "npm", "eslint"),
    ("Playwright", "npm", "@playwright/test"),
]


def fetch_json(url: str) -> object:
    """Fetch and decode a JSON document, raising on any network or format error."""
    request = urllib.request.Request(url, headers={"User-Agent": "developer-plugin-check"})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def latest(kind: str, arg: str) -> str:
    """Return the latest stable version string for one tool."""
    if kind == "npm":
        return str(fetch_json(f"https://registry.npmjs.org/{arg}/latest")["version"])  # type: ignore[index]
    if kind == "pypi":
        return str(fetch_json(f"https://pypi.org/pypi/{arg}/json")["info"]["version"])  # type: ignore[index]
    if kind == "github":
        return str(fetch_json(f"https://api.github.com/repos/{arg}/releases/latest")["tag_name"])  # type: ignore[index]
    if kind in ("endoflife", "endoflife-lts"):
        cycles = fetch_json(f"https://endoflife.date/api/{arg}.json")
        for cycle in cycles:  # type: ignore[attr-defined]
            if kind == "endoflife" or cycle.get("lts"):
                return str(cycle.get("latest") or cycle["cycle"])
        raise ValueError(f"no LTS cycle for {arg}")
    raise ValueError(f"unknown source kind: {kind}")


def run(as_json: bool) -> int:
    """Look up every tool and print a table or JSON."""
    checked = dt.date.today().isoformat()
    rows = []
    for name, kind, arg in TOOLS:
        try:
            rows.append({"tool": name, "latest": latest(kind, arg), "source": f"{kind}:{arg}"})
        except (urllib.error.URLError, OSError, KeyError, IndexError, ValueError) as exc:
            rows.append({"tool": name, "latest": "unavailable", "source": f"{kind}:{arg}",
                         "error": type(exc).__name__})
    if as_json:
        print(json.dumps({"checked": checked, "tools": rows}, indent=2))
    else:
        print(f"Current stable releases, looked up {checked}:\n")
        print("| Tool | Latest | Source |\n|---|---|---|")
        for row in rows:
            print(f"| {row['tool']} | {row['latest']} | {row['source']} |")
    return 0


if __name__ == "__main__":
    sys.exit(run("--json" in sys.argv[1:]))
