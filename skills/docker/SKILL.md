---
name: docker
description: Container images: multi-stage Dockerfiles, digest-pinned bases, non-root users, secret-safe builds, healthchecks, scanning. Use when writing or reviewing a Dockerfile or building images.
verified: 2026-11-07
---

# Docker images

## Current tools

Look these up when you start: the Docker Engine and Buildx release notes, and
the current base images you plan to use. Get a base image digest with
`docker buildx imagetools inspect <image:tag>`. Check the Dockerfile reference
for current instruction syntax before relying on a flag.

## Principles

- **Reproducible base:** pin the base image by digest in production builds, and
  record the tag beside it in a comment so a human can read it. Update the digest
  on purpose, through review.
- **Small runtime:** build in one stage, run in a minimal stage that has only what
  the program needs. Use a slim or distroless base where the language allows it.
- **Least privilege:** run as a non-root user (`USER` with a numeric UID). Do not
  write to the image filesystem at run time except in declared volumes.
- **Cache-friendly order:** copy dependency manifests and install before copying
  the source, so code changes do not reinstall dependencies.
- **No secrets in layers:** never put tokens in `ARG`, `ENV` or `COPY`. Use BuildKit
  secret mounts (`RUN --mount=type=secret`) for build-time credentials.
- **One process per container,** started in exec form (`CMD ["app"]`), so signals
  reach it and it stops cleanly.
- **Healthcheck:** declare a `HEALTHCHECK` that tests the real service, or let the
  orchestrator probe it.
- **Labels:** set standard OCI labels (source, revision, created) so an image
  can be traced back to its commit.

## Layers and caching

- Order instructions from least to most often changing: base, tooling, dependency
  manifests and install, then source. A changed layer rebuilds every layer after it.
- Install dependencies from manifest and lock files only (bind-mount or copy just
  those), so a source edit never reinstalls them.
- Use BuildKit cache mounts for package caches (`RUN --mount=type=cache,...`); they
  speed up rebuilds and never enter the image.
- `.dockerignore` keeps the context small and stops unrelated files from
  invalidating the cache.
- In CI the builder is usually fresh: export and import the cache (registry or the
  CI backend) with all stages included. Look up the current cache options.
- Use multi-stage builds: compilers and dev tools stay in the build stage; the final
  stage holds only the runtime and the output. Add named `dev` and `test` stages for
  Compose and CI, and ship only the `runtime` stage.
- Build for the platform you run; test the stop time (`docker stop` should return
  quickly if signals reach the app).
- Check: build twice (second is cached), change one source line (only late layers
  rebuild), `docker history` (no secrets), `docker run --rm <image> id` (not root).

## Per language

The recipe differs by language: dependency layer, runtime base, signal handling and
memory settings. See the idioms guide inside each `lang-*` skill; the Python
templates and guide are in the `lang-python` skill's references folder. For running images in a
cluster see `kubernetes`.

## Build gates

1. `.dockerignore` excludes `.git`, local env files, build output and caches.
2. Build with provenance and an SBOM attached (Buildx options; confirm the flag
   names in the Buildx docs).
3. Scan the image for known vulnerabilities in CI with a scanner the team
   chooses (for example Trivy or Grype; confirm the current action or command).
4. Run the image's healthcheck or a smoke test before promoting it.

## Common mistakes

- `latest` tags in production.
- Running as root because it was the default.
- Copying the whole repository, including secrets and test data, into the image.
- Installing build tools in the runtime stage.

Use `templates/Dockerfile` as a starting point.
