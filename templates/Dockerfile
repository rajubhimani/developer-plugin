# Multi-stage container image. Replace the placeholders, then build with:
#   docker build -t app:local .
# Pin BASE_IMAGE by digest for release builds (see the docker skill).
ARG BASE_IMAGE=<builder-image:tag@sha256:digest>
ARG RUNTIME_IMAGE=<runtime-image:tag@sha256:digest>

FROM ${BASE_IMAGE} AS build
WORKDIR /src
# Dependency manifests first, so code edits reuse the cached install layer.
COPY <dependency-manifest-files> ./
RUN <install dependencies>
COPY . .
RUN <build command> --output /out/app

FROM ${RUNTIME_IMAGE}
ARG REVISION=unknown
LABEL org.opencontainers.image.revision=$REVISION
RUN useradd --system --uid 10001 app 2>/dev/null || adduser -S -u 10001 app
COPY --from=build /out/app /usr/local/bin/app
USER 10001
EXPOSE 8080
# HEALTHCHECK CMD <command that exits 0 when the service is ready>
ENTRYPOINT ["/usr/local/bin/app"]
