# {{title}}

<one line: what this service does>

```bash
go mod edit -go=<current-go-version> && go mod tidy
make check
APP_ADDR=:8080 go run ./cmd/{{name}}
curl localhost:8080/healthz
```

## Layout

```text
cmd/{{name}}/     the entry point: reads config, wires, starts (kept thin)
internal/config/  settings from APP_* environment variables, read once
internal/server/  routes, start and graceful stop
```

Code under `internal/` cannot be imported by other modules. Add a package per
concern (`internal/<feature>`); promote code out of `internal/` only when another
module truly needs it. Settings are environment variables; in a cluster the same
names come from a ConfigMap and a Secret (see the kubernetes skill).
