# Layouts by kind

The trees below are what `make init-project` creates (placeholders in angle brackets are
filled in). Sources for the reasoning: the packaging guides of each language, the
framework guides for larger applications, and monorepo practice from workspace tooling.

## Python

### library

```text
pyproject.toml            metadata, build system, tool settings (the only config file)
src/<package>/__init__.py public API: __all__ lists what is public
src/<package>/_*.py       private modules (leading underscore)
src/<package>/py.typed    tells type checkers the package ships its hints
tests/                    test through the public API
docs/api.md               the public API table and the rules for changing it
.github/workflows/publish.yml   publish on a version tag with trusted publishing
```

Why: the `src` layout stops tests from importing the working copy instead of the
installed package. `__all__` and the underscore rule make the public API a decision.
Trusted publishing (an identity token the publisher exchanges) means no long-lived
secret is stored.

### webapp (service)

```text
src/<package>/main.py        composition root: create_app() wires the layers
src/<package>/settings.py    typed settings, read once (see lang-python)
src/<package>/api/           routes, request and response models, error format, health
src/<package>/services/      use cases and the ports (Protocols) they need
src/<package>/domain/        business rules, plain Python, no framework
src/<package>/adapters/      databases, queues, clients: implement the ports
tests/unit, tests/api        rules and use cases without HTTP; routes through the app
Dockerfile, compose.yaml, .env.example, .dockerignore
```

Imports point one way: main, then api, then services, then domain; adapters implement
ports and depend on domain. `adapters/sql.py` is the only code that knows the table layout;
migrations ship inside the package and run with `python -m <package>.migrate`, as a one-shot
service in Compose or a Job in a cluster that gets the database URL and no other secret.
Readiness pings the database; liveness checks nothing else. Routes are thin, rules are not in routes, API models are
separate from domain types. Group by feature (a module per feature in each layer) and
split into feature folders when a feature grows. `make structure-check` fails when the
domain imports a framework, a service imports the web layer, or a route imports an adapter.

### cli

```text
src/<package>/cli.py        parse arguments, call plain functions, return an exit code
src/<package>/__main__.py   `python -m <package>` runs the same function
[project.scripts]           the installed command
```

Results to standard output, messages to standard error, documented exit codes, tests call
`main(argv)`. Use a CLI framework when there are many subcommands; the shape stays.

### monorepo (uv workspace)

```text
pyproject.toml     workspace root: not a package; members, shared ruff, pyright, pytest
uv.lock            the only lock file
apps/<member>/     deployable (webapp, cli): nothing imports an app
packages/<member>/ libraries shared by apps and by each other
docs/architecture.md, .github/CODEOWNERS
```

Members are named `<repo>-<member>` and imported as `<repo>_<member>`, so they never
clash with a public package. Rules: apps may use packages; packages never use apps; an
app never imports another app; import a sibling only through its public package; declare
siblings with `{ workspace = true }`; tool settings only in the root; pytest runs in
importlib mode so every member can have its own tests folder. A service image builds from
the repository root as context.

## TypeScript (node)

### webapp

`index.html`, `src/main.tsx`, `src/App.tsx`, a Vite config with the test environment, a
strict `tsconfig.json`. A browser bundle is public: no secrets, and build-time values are
fixed in the build (inject a runtime config file to run one build everywhere).

### library

`src/index.ts` is the only public entry; the `exports` map allows no other import path;
`files` limits what is published; ES modules; declarations emitted.

### ui

A library of React components with `react` as a peer dependency. Export components and
prop types from the entry file only; native elements; no app logic.

### monorepo (pnpm workspace)

```text
pnpm-workspace.yaml   apps/* and packages/*
apps/web              the application
packages/ui           shared components
packages/utils        shared helpers
packages/config       shared tsconfig files every member extends
```

Rules: one lock file; sibling dependencies use the workspace protocol; no package depends
on an app and no app on another app; internal packages export their TypeScript source (no
build step to keep in sync) while published packages get their own build; shared external
versions live in one place (the workspace catalog); owners file. Add a task runner with
caching (such as Turborepo) when CI time hurts, not before; it does not change the layout.

## Go

- **monorepo:** a `go.work` file lists the modules; `apps/<name>` (services and commands) and
  `packages/<name>` (libraries) are each their own module. Apps may import packages, packages
  never import apps, an app never imports another app, and members declare siblings in their
  `go.mod` with no `replace` directive (the workspace resolves them).
- **service:** `cmd/<name>/main.go` (thin), `internal/config` (settings read once),
  `internal/server` (routes, start, graceful stop with every timeout set).
- **library:** root package, `doc.go`, runnable `Example` tests; private code under
  `internal/`; a major version changes the module path.
- **cli:** `cmd/<name>/main.go` calls `internal/cli`, which takes its streams as parameters.

Start flat and add `internal/` packages per concern as the code grows; use the `pkg/`
folder only for code that other modules should import. `go.work` joins several modules
for local development.

## Rust

- **library:** `src/lib.rs`, a typed error enum, doc tests as examples, no `unwrap`.
- **binary:** a thin `src/main.rs` over `src/lib.rs`, so logic is testable.
- **workspace:** a virtual manifest at the root, a flat `crates/` folder, versions and lints
  declared once and inherited, the resolver set explicitly, binaries depend on libraries
  and never the reverse, `Cargo.lock` committed.

## Java (Gradle, Kotlin DSL, version catalog)

- **library:** `java-library`, a public API of public types, javadoc required by the build,
  sources and javadoc jars, JUnit 5, Spotless formatting.
- **cli:** `application` plugin; `Main` is thin and calls `Cli.run`, which takes its streams as
  parameters so tests need no terminal; documented exit codes.
- **service:** Spring Boot with layers `web`, `service`, `domain`, `adapter` (imports point
  one way, domain imports no framework), constructor injection, problem-details errors,
  graceful shutdown, only the health endpoint exposed with liveness and readiness probes.

Every kind compiles with `-Xlint:all -Werror`, so a deprecated call fails the build. The
Gradle wrapper carries a version, so it is created once with `gradle wrapper` and committed.

## C and C++ (CMake presets)

- **library:** a public header under `include/<name>/` (C: a status enum, documented buffer
  ownership; C++: a namespace, `[[nodiscard]]`, documented exceptions), private code in `src/`.
- **executable:** a thin `main` over a library function that takes its streams as
  parameters; documented exit codes.

Presets give `debug`, `asan` (address and undefined-behaviour sanitizers) and `release`. Warnings,
deprecated declarations included, are errors. Tests are plain `ctest` programs with no
framework; move to a maintained framework when the suite grows.

## How well each kind is verified

- **Python (library, cli, webapp, monorepo):** the plugin's tests generate each kind and
  run its own tests when the libraries are installed. When written, the generated projects
  also passed ruff, formatting and strict type checking, and the workspace installed,
  tested and built with `uv`.
- **TypeScript (webapp, library, ui, monorepo):** checked by hand with real installs
  (type-check, tests, lint, build; the workspace with `pnpm`). The plugin's tests check
  structure and that every generated JSON file parses, not the toolchain.
- **Java:** built and tested with a real JDK and Gradle: formatting, `-Xlint:all -Werror`,
  javadoc and the tests, including the Spring Boot application context and its probes.
  A planted deprecated call failed the build. The plugin's tests check structure, the layer
  rules and the generated names, not the toolchain.
- **C and C++:** configured, built and tested with CMake and clang under the address and
  undefined-behaviour sanitizers, and built in release mode; executables were run.
- **Go and Rust:** the plugin's tests check structure, the rules and that every generated
  manifest parses. The sample code was written to be simple and was not compiled by the
  plugin's tests (no Go or Rust toolchain was available); run `make check` in a new project
  and report anything that fails.

## Not covered yet

A Go or Rust database adapter, and Kotlin, .NET and other languages. Add a kind by creating
`templates/kinds/<language>/<kind>/` with a `kind.json` and the files to copy.
