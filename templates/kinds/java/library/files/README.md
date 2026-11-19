# {{title}}

<one line: what this library does>

```kotlin
dependencies { implementation("{{javagroup}}:{{name}}:0.1.0") }
```

## Develop

The Gradle wrapper is not shipped (it carries a version); create it once with
`gradle wrapper`, commit it, then:

```bash
make install   # resolve dependencies
make check     # format check, compile with all warnings as errors, javadoc, tests
make build     # jar, sources jar and javadoc jar
```

Replace the `<...>` placeholders in `build.gradle.kts` and `gradle/libs.versions.toml` with
current values (all dependency versions live in the catalog). The compiler runs with
`-Xlint:all -Werror`, so a deprecated call fails the build. Publish with the
`maven-publish` plugin and signed artifacts when you are ready.

## Public API and versions

The public API is the public types in `{{javapkg}}`; see [docs/api.md](docs/api.md).
Versions follow semantic versioning; every release is in [CHANGELOG.md](CHANGELOG.md).
