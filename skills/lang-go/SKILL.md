---
name: lang-go
description: Go project setup and quality gates (go modules, cmd and internal layout, gofmt, go vet, golangci-lint v2, race detector, govulncheck). Use when creating, changing, reviewing or testing Go code.
verified: 2026-11-07
---

# Go

## Current versions

Look these up when you start: the Go release feed `https://go.dev/dl/?mode=json`
(first stable entry), and for golangci-lint the GitHub releases API
`https://api.github.com/repos/golangci/golangci-lint/releases/latest`.

## Setup

- Set the Go version in `go.mod` to the current release you looked up. Use the `toolchain`
  line only if the team needs a specific patch release.
- One module per repo for most projects. Use `go.work` only for several modules
  developed together.
- Layout: `cmd/<app>/main.go` stays thin; logic lives in `internal/` packages
  (not importable from outside the module). Keep the tree shallow.
- Commit `go.sum`. Run `go mod tidy` before committing.

## Quality gates

1. `gofmt -l .` must print nothing.
2. `go vet ./...`
3. `golangci-lint run` using a v2 config file (`version: "2"`). Enable the
   linters the team agrees on and suppress individual findings with a reason.
4. `go test -race ./...`
5. `govulncheck ./...` in CI for known vulnerabilities in dependencies.

## Common mistakes

- Ignoring returned errors (`_ = f()`) without a comment saying why.
- Goroutines without a way to stop them or wait for them.
- Global mutable state that tests cannot reset.
- Packages named `util` or `common` that collect unrelated helpers.

Source to check before relying on details: the Go command documentation and
golangci-lint and govulncheck docs.
