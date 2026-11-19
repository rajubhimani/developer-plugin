# Kustomize layout: one base, a small overlay per environment

```text
k8s/
  base/
    kustomization.yaml       lists the resources and the config generator
    app.yaml                 Deployment, Service, PDB, HPA, NetworkPolicy
    migrate-job.yaml
  overlays/
    dev/
      kustomization.yaml     namespace, image digest, replicas, small resources
      config.env             plain values for dev
    staging/
      kustomization.yaml
      config.env
    prod/
      kustomization.yaml     namespace, image digest, replicas, real resources
      config.env
```

## Rules

1. **Base holds structure; overlays hold values.** If an overlay rewrites a lot of
   the base, the base is wrong.
2. **Generate the ConfigMap from an env file** in each overlay. The generator adds
   a hash to the name, so a changed value renames the ConfigMap and rolls the
   pods (see `config-flow.md`).
3. **Secrets are not generated from plain files in git.** Reference an existing
   Secret created by an operator, or commit only encrypted material.
4. **One namespace per environment,** set in the overlay.
5. **The image digest is set in the overlay,** written by the release pipeline.
   The same digest moves dev, then staging, then prod.
6. **Keep patches small and named** for what they change (`replicas`, `resources`).
7. **Render and validate in CI:** build each overlay, check it against the schema,
   run the policy linter and a server-side dry run against a test cluster.

## Sketch of a prod overlay (look up current field names before use)

```yaml
# overlays/prod/kustomization.yaml
resources:
  - ../../base
namespace: <app>-prod
configMapGenerator:
  - name: app-config
    envs:
      - config.env
images:
  - name: <registry>/<app>
    digest: sha256:<digest>
replicas:
  - name: app
    count: 4
patches:
  - path: resources.patch.yaml
```

## Helm instead

Use Helm when the package is configurable by many consumers. Keep the chart values
the same names as the settings. Lint the chart, render it with each values file, and
validate the output exactly as you would Kustomize output. Do not mix both tools on
the same resources.
