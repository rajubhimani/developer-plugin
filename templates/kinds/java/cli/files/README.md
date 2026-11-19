# {{title}}

<one line: what this command does>

The Gradle wrapper is not shipped (it carries a version); create it once with
`gradle wrapper` and commit it. Replace the `<...>` placeholders in `build.gradle.kts` and
`gradle/libs.versions.toml` with current values. Then:

```bash
make check                  # format check, compile with all warnings as errors, tests
./gradlew run --args="world"
./gradlew installDist       # a runnable distribution in build/install
```

Results go to standard output, messages for people to standard error. Exit code 0 is success,
2 is bad usage, 1 is any other failure. `Main` only calls `Cli.run`; the logic and its tests
live there. For many subcommands use a maintained command line library (for example Picocli);
the structure stays the same.
