---
name: lang-java
description: "Java setup and gates: LTS JDK, Gradle or Maven, JUnit, static analysis. Use when writing, reviewing or building Java."
metadata:
  verified: "2026-11-07"
---

# Java

## Current versions

Look these up when you start: the newest long-term-support (LTS) JDK from
`https://endoflife.date/api/oracle-jdk.json` (take the first entry with `lts` set).
Gradle from `https://api.github.com/repos/gradle/gradle/releases/latest`. Maven
from the Apache release page, since Homebrew formulas can lag.

## Setup

- Target the current LTS JDK for new projects.
  Pin it with the Gradle toolchain or Maven `release` setting.
- Gradle: Kotlin DSL, plugins in a `plugins {}` block, and all dependency versions
  in `gradle/libs.versions.toml` (a version catalog). Commit the wrapper.
- Maven: `maven.compiler.release` set once in the parent POM; commit the wrapper.
- Spring Boot: check its own requirements for the JDK minimum before upgrading.

## Quality gates

1. Format and style check, for example Spotless or Checkstyle.
2. Static analysis: SpotBugs and Error Prone (or the compiler's warnings as
   errors). Confirm current plugin versions in their docs.
3. `./gradlew check` or `mvn verify` runs tests and analysis together.
4. JUnit 5 tests; integration tests in a separate task so the fast loop stays
   fast.
5. Dependency vulnerability scan in CI (the OWASP dependency-check plugin or the
   platform's equivalent).

## Common mistakes

- Dependency versions written in several build files instead of the catalog.
- Catching `Exception` and swallowing it.
- Mutable static state shared between tests.
- Using preview language features in production code.

Source to check before relying on details: the Gradle and Maven documentation,
the OpenJDK release notes, and the Spring Boot system requirements.

## Deeper guide

`references/idioms.md` covers how this language handles errors, concurrency,
configuration, logging, testing, security and the container image, and where it
differs from the others. Read it when you design or review more than a small edit.
