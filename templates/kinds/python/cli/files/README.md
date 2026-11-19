# {{title}}

<one line: what this command does and who it is for>

## Install and run

```bash
uv tool install {{name}}     # or: pipx install {{name}}
{{name}} world
python -m {{package}} world  # same function, no install needed on PATH
```

## Develop

```bash
make install
make check
make run     # runs the command from the source tree
```

## Behaviour that scripts can rely on

- Results go to standard output; messages for people and errors go to standard error.
- Exit code 0 on success, 2 for bad usage, 1 for any other failure.
- `--version` prints the installed version.
- Options and exit codes are part of the public interface and follow semantic
  versioning; see [CHANGELOG.md](CHANGELOG.md).
