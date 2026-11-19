# {{title}}

<one line: what this library does and who it is for>

```bash
go get {{module}}
```

```go
greeting, err := {{gopkg}}.Greet("world")
```

## Public API

Every exported identifier is public and follows semantic versioning; put private code
under `internal/`. Add a runnable `Example` for each public function: it is both
documentation and a test. Release by tagging `vX.Y.Z`; a new major version changes the
module path (`/v2`). Record changes in [CHANGELOG.md](CHANGELOG.md).
