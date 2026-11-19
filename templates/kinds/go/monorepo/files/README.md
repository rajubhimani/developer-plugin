# {{title}}

<one line: what this repository holds>

```text
apps/       services and commands (each its own module); nothing imports them
packages/   libraries shared by apps and by each other (each its own module)
go.work     the workspace: lists the modules developed together
docs/       architecture and decisions
```

```bash
make check        # vet, lint, test every module
make test         # go test -race in each module
```

Members and the dependency rules are in [docs/architecture.md](docs/architecture.md);
`make structure-check` enforces the rules.
