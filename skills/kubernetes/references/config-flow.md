# From `.env` on a laptop to a cluster

One set of setting names. Only the source of the values changes.

```text
.env.example      names + safe dummy values (committed; the contract)
.env              your local values (git-ignored, docker-ignored)
Settings class    typed fields for the same names (one place reads the environment)
compose.yaml      env_file passes .env into the container; ${VAR} fills the file
ConfigMap         plain values for the cluster (committed, per environment overlay)
Secret            credentials; created from a secrets manager, never committed in plain text
```

## Precedence you can rely on

1. **In the app:** real environment variable, then `.env` file, then mounted secret
   files, then the default in code (look up the exact order in the settings
   library you use and test it).
2. **In Compose:** values given on the command line and the shell, then
   `environment:`, then `env_file:`, then the image's own defaults. A plain `.env`
   in the project folder also fills `${VAR}` in the compose file itself. Run
   `docker compose config` to see the final result instead of guessing.
3. **In Kubernetes:** what the pod spec says (`env`, `envFrom`, mounted files). An
   explicit `env` entry beats `envFrom` for the same name. There is no `.env`.

## Which values go where

| Kind | Local | Compose | Cluster |
|---|---|---|---|
| Plain setting (log level, timeouts, feature flag) | `.env` | `.env` via `env_file` | ConfigMap |
| Address of another container or service | `.env` (localhost) | `environment:` (service name) | ConfigMap (service DNS name) |
| Credential (password, token, key) | `.env` dummy | `.env` dummy | Secret from a secrets manager |
| Image tag or digest | not needed | `.env` | the Deployment or an overlay |

## Keeping them in step

- `make check-env` (the script `scripts/check_env.py`, copied into new Python
  projects) compares the `Settings` fields, `.env.example` and the manifests under
  `k8s`, `deploy`, `helm` or `kustomize`, and `make check` runs it. It fails when a
  field is missing from `.env.example`, when `.env.example` or the cluster sets a
  name that is not a field, when a required field is never supplied to the cluster,
  and when a credential (`SecretStr`) is given as plain config. It warns about a
  plain `Secret` manifest in git. It reads names only, so it cannot say a value is
  right; start-up validation does that.
- Adding a setting means four edits in one change: the `Settings` class,
  `.env.example`, the ConfigMap or Secret, and the docs line. Review looks for all
  four.

## Getting secrets into the cluster

Pick one and write it in the decision record:

- **Operator sync:** the secrets manager is the source of truth and an operator
  creates the Kubernetes Secret and refreshes it. Rotation happens in the manager.
- **Encrypted in git:** sealed or encrypted secret files are committed and only the
  cluster or the pipeline can decrypt them.
- **CSI mount:** secrets are mounted as files straight from the manager.

Whichever you choose: encryption at rest on, RBAC limiting who can read secrets,
least-privilege access per app, rotation tested (see `secrets-and-config`).

## When a value changes

| Change | What must happen |
|---|---|
| ConfigMap value used as an env var | Roll the pods (hashed name or checksum annotation) |
| Secret value used as an env var | Roll the pods |
| Secret mounted as a file | The file updates; the app must re-read it, or roll |
| Image digest | Normal rollout; promote the same digest between environments |

## Front ends

A browser app cannot read cluster environment variables. Either inject a small
runtime config file when the container starts (from the same ConfigMap), or serve it
from the API. Values compiled in at build time are fixed in the image, so they
break the "one image for every environment" rule. Never put a secret in a front-end
bundle.
