# infra-review reference

Supporting detail for [SKILL.md](SKILL.md).

## Generated page fields by artifact type

All artifact types live under the single `infrastructure/` wiki surface; type is distinguished by page shape, not directory.

### Dockerfile

```markdown
# rlm-gateway/Dockerfile
**Path:** `rlm-gateway/Dockerfile`
**Base Image(s):** `python:3.11-slim`
## Exposed Ports
- `8081`
## Build Arguments
| Argument | Default |
## Environment Variables
| Variable | Default |
```

Captured: path, base image(s), exposed ports, build args with defaults, env vars with defaults. Not captured: `USER`/`RUN` instruction bodies (so privilege drop, i.e. running as non-root, is not visible on the page — check the Dockerfile source directly if that matters to the review), and whether the base image tag is pinned to a digest (the page shows whatever tag string is written, e.g. `python:3.11-slim`, which is a mutable tag not a digest).

### Docker Compose

```markdown
# docker-compose.yml
## Services
| Service | Image / Build | Ports | Depends On |
### <service-name>
- **Build context:** ...
- **Ports:** ...
- **Volumes:** ...
- **Environment:** ...
- **Depends on:** ...
- **Command:** ...
```

Captured: per-service build/image, ports, volumes, environment (as written — literal values and `${VAR}` references both appear verbatim), depends_on, command. This is a real, confirmed example from a live dogfood run showing exactly the kind of finding this surface reveals directly on the page:

```
rlm-gateway:
  Volumes: /var/run/docker.sock:/var/run/docker.sock, ...
```

A service mounting the Docker socket has host-level container-escape potential — this is visible on the generated page with no raw-source read needed, which is why Compose review is the highest-yield, lowest-cost part of this skill.

### Kubernetes

```json
{
  "kind": "...", "name": "...", "namespace": "...", "replicas": "...",
  "containers": [...], "service_type": "...", "service_ports": [...],
  "selector": {...}
}
```

Captured: kind, name, namespace, replicas, containers list, Service type/ports, selector. **Not captured** (confirmed by reading `services/infrastructure_inventory.py::_fill_kubernetes_spec`): `securityContext`, `privileged`, `hostPath`, `hostNetwork`, resource `limits`/`requests`. Every one of these is a real, common infra-review concern (privileged pods, host networking, missing resource limits causing noisy-neighbor risk) that the wiki page cannot show — always read the raw manifest for workload resources.

### GitHub Actions

```json
{
  "type": "github_actions", "name": "...", "triggers": [...],
  "jobs": [{"id": "...", "name": "...", "runs_on": "...", "needs": [...], "steps": [...]}]
}
```

Captured: workflow name, triggers, per-job id/name/runs_on/needs/steps.
**Not captured** (confirmed by reading `services/infrastructure_inventory.py::parse_github_actions_workflow`): the `permissions:` block, at either workflow or job level. A workflow with no `permissions:` block gets the repository's default token scope, which is often broader than the workflow needs — this can only be assessed by reading the raw YAML.

## Checklist by artifact type

| Artifact | Check | Source of evidence |
|---|---|---|
| Dockerfile | Base image pinned to digest, not mutable tag | Generated page (tag string) + raw source if digest pinning matters |
| Dockerfile | Secret-shaped env var with a literal default | Generated page |
| Dockerfile | Runs as non-root | Raw source (`USER` instruction) |
| Compose | Host-path or Docker-socket volume mounts | Generated page |
| Compose | Literal secret values vs `${VAR}` references | Generated page |
| Compose | Unnecessarily host-exposed ports | Generated page |
| Kubernetes | `securityContext`/`privileged`/`hostPath`/`hostNetwork` | Raw source only |
| Kubernetes | Missing resource `limits`/`requests` | Raw source only |
| GitHub Actions | Missing or over-broad `permissions:` | Raw source only |
| GitHub Actions | Third-party actions pinned to tag/branch, not commit SHA | Raw source (`uses: owner/action@ref`) |

## Report format

`reports/infra_review_<YYYY-MM-DD>.md`:

```markdown
| ID | Artifact | Issue | Evidence | Severity | Recommendation |
|---|---|---|---|---|---|
| IR-001 | docker-compose.yml (rlm-gateway) | Docker socket mounted into container | Volumes: `/var/run/docker.sock:/var/run/docker.sock` | high | Use a sidecar/remote Docker API with scoped auth instead of the host socket, or document why host-level trust is accepted here |
| IR-002 | .github/workflows/ci.yml | No `permissions:` block | Raw source, workflow-level | medium | Add an explicit minimal `permissions:` block |
```

Include a coverage row for every artifact type actually present in the repo, even when it produced zero findings — "reviewed, clean" is a different, necessary statement from "not reviewed."

## Failure modes

| Symptom | Cause | Response |
|---|---|---|
| No `infrastructure/` pages at all | No Docker/Compose/K8s/Actions files detected, or wiki not synced | Confirm via `ls .github/workflows k8s` etc. whether the repo genuinely has none, versus the wiki being stale. |
| K8s/Actions findings feel thin | Generated page genuinely doesn't carry security-context/permissions fields | This is expected — step 4/5 require the raw-source read; don't treat page silence as "nothing to find." |
| Compose page shows a literal secret | Environment written as a hardcoded value, not `${VAR}` | Flag as a real finding — recommend moving to environment injection, not just noting it. |
