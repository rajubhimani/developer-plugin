# {{title}}

<one line: what this service does>

The Gradle wrapper is not shipped (it carries a version); create it once with
`gradle wrapper` and commit it. Replace the `<...>` placeholders in `build.gradle.kts` and
`gradle/libs.versions.toml` with current values (the Spring Boot version, the JDK version you
target). Then:

```bash
make check                                    # format check, compile with all warnings as errors, tests
./gradlew bootRun
curl localhost:8080/actuator/health/readiness
```

Layers and rules: [docs/architecture.md](docs/architecture.md). Settings are environment
variables (`APP_PORT`, `APP_SHUTDOWN_TIMEOUT`); see `src/main/resources/application.yml`. Build
the container image from the layered jar (see the lang-java skill and the docker skill) and run
it as in the kubernetes skill.
