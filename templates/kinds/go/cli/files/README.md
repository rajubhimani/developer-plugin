# {{title}}

<one line: what this command does>

```bash
go mod edit -go=<current-go-version> && go mod tidy
go run ./cmd/{{name}} world
make check
```

Results go to standard output; messages for people go to standard error. Exit code 0 is
success, 2 is bad usage, 1 is any other failure. Options and exit codes are the public
interface and follow semantic versioning. `main` only calls `cli.Run`; the logic is in
`internal/cli` where tests reach it without a terminal.
