# {{title}}

<one line: what this repository holds>

```text
apps/       deployable things (services, command line tools); nothing imports them
packages/   libraries shared by apps and by each other
docs/       architecture and decisions
```

## Work in it

```bash
make install            # uv sync --all-packages: one environment, one lock file
make check              # format, lint, type-check, test every member
uv run --package <member> pytest      # one member
uv add --package <member> <dependency>   # add a dependency to one member
```

Members and what each one is are listed in [docs/architecture.md](docs/architecture.md).
The dependency rules are enforced by `make structure-check`.
