---
name: kubernetes
description: "Kubernetes: probes, resources, shutdown, security, rollout. Use for manifests, moving from Compose, or a pod that restarts or is never ready."
metadata:
  verified: "2026-11-19"
---

# Kubernetes

The app is built once as an image. The cluster supplies configuration, secrets,
scale and restarts. Keep the manifests small, explicit and the same in every
environment except for values.

Examples are in `references/`: `app.yaml` (a full annotated set), `config-flow.md`
(from `.env` to the cluster) and `kustomize-layout.md`.

## Configuration

1. **Same variable names as local.** The settings the app reads from `.env` and
   Compose are the keys of the ConfigMap and Secret. One list, three places (see
   `secrets-and-config`, `lang-python`).
2. **ConfigMap for plain values, Secret for credentials.** Never put a credential
   in a ConfigMap, an image or a committed manifest.
3. **Pull in a ConfigMap with `envFrom`,** and secrets key by key with
   `secretKeyRef` so one extra key cannot slip into the process environment.
   Alternatively mount a Secret as files (read-only, restrictive mode) and read the
   directory; files also update without a restart.
4. **Environment variables are fixed when the pod starts.** A changed ConfigMap
   does nothing until pods roll. Use generated names with a content hash (Kustomize
   does this) or a checksum annotation so a config change triggers a rollout.
5. **A Secret is encoded, not encrypted.** Turn on encryption at rest, restrict
   who can read secrets with RBAC, and keep the source of truth in a secrets
   manager synced by an operator, or commit only encrypted secrets. Never commit a
   plain Secret with real values.
6. **Mark config immutable** when it should not change under a running version.
7. **Validate on start.** The app fails fast on a missing setting; the pod then
   shows a clear restart reason instead of misbehaving.

## Workload

1. **Image:** pinned by digest or an immutable tag, never `latest`; the same image
   in every environment; pull policy matches.
2. **Resources:** set requests on every container (scheduling depends on them) and
   a memory limit to contain leaks. Be careful with CPU limits; they throttle. Size
   from measured use, review often.
3. **Probes** (three different questions):
   - *Startup:* has it finished booting? Protects slow starts from the others.
   - *Readiness:* can it take traffic now? Checks the app and its needed
     dependencies. Failing removes it from the service; no restart.
   - *Liveness:* is the process stuck? Checks only the process itself, never a
     database or another service; otherwise an outage elsewhere restarts healthy
     pods.
4. **Graceful shutdown:** the app handles SIGTERM, fails readiness, finishes
   in-flight work and exits. Set the termination grace period longer than the
   longest request. A short `preStop` pause lets routing catch up. Process 1 must
   receive the signal (exec-form command; see `docker`).
5. **Availability:** at least two replicas for anything that matters, a rolling
   update that never drops below desired capacity (zero unavailable, one surge), a
   disruption budget so node drains cannot take the service down (not so strict that
   maintenance stalls), and spread across nodes or zones.
6. **Scaling:** a horizontal autoscaler with a sensible minimum and maximum on a
   metric that tracks load; the app must be stateless and start fast.
7. **State:** keep it out of the pod. Use managed databases and queues, or a
   StatefulSet with a storage class and a backup plan when you must.

## Security

1. **Pod and container security context:** run as non-root with a numeric user, no
   privilege escalation, all capabilities dropped, the runtime's default seccomp
   profile, and a read-only root filesystem with a small writable temp volume.
2. **A service account per app,** with no extra permissions. Do not mount the token
   if the app never calls the cluster API.
3. **Least-privilege RBAC;** no cluster-admin for apps or pipelines.
4. **Network policy:** deny by default, then allow only the needed traffic.
5. **Enforce a restricted pod security level** on the namespace.
6. **Only trusted registries;** scan images and verify provenance (see `docker`,
   `dependency-management`).
7. **Do not expose** the dashboard, debug ports or the metrics endpoint publicly.

## Jobs and migrations

- Run schema migrations as a separate Job (or a hook in your deploy tool) before
  the new version, not inside every pod start. Give the Job the database credential
  only, not the application's other secrets. Make them backward compatible so old
  and new pods can run together (see `database-migrations`).
- Jobs set a retry limit, a deadline and clean-up of finished pods. Scheduled jobs
  set a concurrency policy and are idempotent (see `resilience`).

## Packaging and delivery

- **Kustomize** (a base plus a small overlay per environment) for plain manifests,
  or **Helm** when you ship a configurable package. Pick one per project.
- Overlays change values (replicas, resources, hostnames, config), not structure.
  Secrets are never patched in as plain text.
- Label everything with the standard app labels so tools and people can find it.
- **Validate before apply:** render, check against the schema, lint with a policy
  tool, and run a server-side dry run. Fail the pipeline on findings.
- **GitOps:** the cluster pulls from the repo; a change is a pull request, and
  rollback is a revert. Promote the same image digest from environment to
  environment (see `ci-cd`).
- Resources set their namespace explicitly; no application in the default
  namespace.

## Observability

Logs to standard output as structured lines; metrics on a cluster-internal port;
trace context passed on (see `observability`). Alert on restarts, unready pods,
saturation and error rate. Know the first three commands you run when a pod fails:
describe the pod, read the previous container's logs, list recent events.

## Rollback

Keep revision history, know the undo command and the GitOps revert, and make the
previous version work with the current schema. Roll out gradually for risky
changes (see `delivery-practices`).

## Local clusters

Use Compose first. Use a local cluster (kind, k3d, minikube) only to test the
manifests or cluster behaviour, with a dev-loop tool if you iterate often. Look up
the current tool set.

## Checklist for a new service

| Check | Done when |
|---|---|
| Config | ConfigMap and Secret keys match `.env.example` and the settings class |
| Secrets | None in git or the image; synced from a manager |
| Resources | Requests set; memory limit set |
| Probes | Startup, readiness, liveness with the right scope |
| Shutdown | SIGTERM handled; grace period fits; exec-form command |
| Availability | Replicas two or more; disruption budget; rolling update settings |
| Security | Non-root, read-only root, dropped capabilities, own service account |
| Network | Default deny plus the needed rules |
| Delivery | Digest-pinned image; validated manifests; rollback known |

## Current tools

Look up the current API versions of each resource, the validator and policy tools,
and the Kustomize or Helm syntax before writing manifests. Field names and
defaults change between releases.

## Related

`docker`, `compose`, `secrets-and-config`, `resilience`, `observability`,
`ci-cd`, `database-migrations`, and the language skills for the image recipe.
