# infra-review reference

Supporting detail for [SKILL.md](SKILL.md).

## Bootstrap snapshot and discovery boundary

All generated artifact types live under the single `infrastructure/` wiki
surface; type is distinguished by page shape, not directory. These are
bootstrap-time pages. Ordinary sync does not regenerate them, and lint does not
compare their complete rendered content with current source.

The coverage table below is bounded to the current
`services/infrastructure_inventory.py` YAML parsers,
`commands/extract_cmd.py` Docker/Compose parsers, and
`commands/bootstrap_cmd.py` renderers. Recheck those seams when implementation
changes.

Built-in discovery starts at the selected source root, walks recursively, and
honors ignored/excluded directories:

| Family | Built-in discovery |
|---|---|
| Dockerfile | `Dockerfile`, `Dockerfile.*`, and `*.dockerfile` anywhere below the source root |
| Compose | `docker-compose*.yml`/`.yaml`, `compose*.yml`/`.yaml`, plus any scanned YAML whose content has a recognizable top-level Compose `services` shape |
| GitHub Actions | `.github/workflows/**/*.yml` and `.github/workflows/**/*.yaml` only |
| Kubernetes | `k8s/**/*.yml` and `k8s/**/*.yaml` only |
| Targeted runtime/config YAML | Recognized Prometheus, Prometheus rules, Grafana provisioning, Promtail, Loki, Envoy, Buf, and service-local model config shapes |

Generic YAML and Kubernetes-looking YAML in alternate roots such as `deploy/`,
`manifests/`, or `charts/` do not become Kubernetes pages. Helm templates,
anchors/merge keys, custom tags, and other complex YAML may exceed the
line-oriented parsers even inside a supported root. Disclose those paths as
unsupported or bounded coverage.

## Page-visible fields versus raw-source checks

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

Page-visible: path; base image and multi-stage aliases; exposed ports; build
arguments and environment defaults; volumes; working directory; entrypoint and
command; `COPY`/`ADD`; labels; and healthcheck. The written `FROM` value lets a
reviewer screen a mutable tag versus a digest.

Raw-source-only or incomplete: `USER`, `RUN`, `SHELL`, `ONBUILD`, instruction
semantics, and parser edge cases. Inspect source before concluding that the
container drops privilege or that no unsafe build/runtime instruction exists.

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

Page-visible: service image/build context, ports, volumes, environment as
written, `depends_on`, command, and top-level network/named-volume names.
This supports initial screening for host mounts, literal settings, and exposed
ports:

```
rlm-gateway:
  Volumes: /var/run/docker.sock:/var/run/docker.sock, ...
```

Raw-source-only or incomplete: `privileged`, `user`, capabilities,
`security_opt`, `network_mode`, secrets/configs, healthcheck/restart/deploy
semantics, and complex YAML anchors/merges. Page evidence may identify a
candidate finding, but current raw source is required for an assurance
conclusion.

### Kubernetes

```markdown
| Name | Image | Ports | Requests | Limits |
|---|---|---|---|---|
| `api` | `example/api:latest` | `8000` | `cpu=500m`, `memory=512Mi` | `cpu=1`, `memory=1Gi` |
```

Page-visible: API version, kind, name, namespace, replicas; container
name/image/ports; container resource `requests` and `limits`; Service
type/ports; and selector.

Raw-source-only or incomplete: `securityContext`, `privileged`, `hostPath`,
`hostNetwork`, volumes, environment/secret references, probes, service-account
and RBAC semantics, and arbitrary workload fields. A dash in Requests/Limits is
useful screening evidence, but must be confirmed in current raw source because
templates or unsupported YAML can be omitted.

### GitHub Actions

```json
{
  "type": "github_actions", "name": "...", "triggers": [...],
  "jobs": [{"id": "...", "name": "...", "runs_on": "...", "needs": [...], "steps": [...]}]
}
```

Page-visible: workflow name/triggers; job id, display name, `runs-on`, `needs`,
and step count; and each step's name, `uses`, or `run`. Because `uses` is
rendered, a mutable third-party ref can be screened from the page.

Raw-source-only or incomplete: workflow- and job-level `permissions:`, job/step
environment and secrets, `with`, conditions, environments, containers/services,
reusable-workflow semantics, and other controls. Missing or over-broad
permissions can only be assessed from current raw YAML.

## Checklist by artifact type

| Artifact | Check | Source of evidence |
|---|---|---|
| Dockerfile | Base image pinned to digest, not mutable tag | Page screen; current raw source confirms |
| Dockerfile | Secret-shaped env var with a literal default | Page screen; report only the key with `<redacted>` |
| Dockerfile | Runs as non-root | Raw source (`USER` instruction) |
| Compose | Host-path or Docker-socket volume mounts | Page screen; current raw source confirms |
| Compose | Literal secret values vs `${VAR}` references | Page screen; redact value; current raw source confirms |
| Compose | Unnecessarily host-exposed ports | Page screen; current raw source confirms |
| Kubernetes | `securityContext`/`privileged`/`hostPath`/`hostNetwork` | Raw source only |
| Kubernetes | Resource `limits`/`requests` | Page screen (captured and rendered); current raw source confirms absence/presence |
| GitHub Actions | Missing or over-broad `permissions:` | Raw source only |
| GitHub Actions | Third-party actions pinned to tag/branch, not commit SHA | Page screen (`uses` is rendered); current raw source confirms |

## Report format

`reports/infra_review_<YYYY-MM-DD>.md`:

```markdown
| ID | Artifact | Issue | Evidence | Severity | Recommendation |
|---|---|---|---|---|---|
| IR-001 | docker-compose.yml (rlm-gateway) | Docker socket mounted into container | Volumes: `/var/run/docker.sock:/var/run/docker.sock` | high | Use a sidecar/remote Docker API with scoped auth instead of the host socket, or document why host-level trust is accepted here |
| IR-002 | .github/workflows/ci.yml | No `permissions:` block | Raw source, workflow-level | medium | Add an explicit minimal `permissions:` block |
```

Do not reproduce literal secrets, private endpoints, internal hostnames, or
sensitive host paths in evidence. Use the source path plus resource/service/job,
field, safe line/range, and a placeholder such as `<redacted>`,
`<private-endpoint>`, or `<sensitive-host-path>`.

Include a coverage row for every supported or candidate artifact:

| Artifact/path | Discovery | Evidence basis | Outcome | Limitation |
|---|---|---|---|---|
| `k8s/deployment.yaml` | supported `k8s/` root | current raw source | zero findings | line-oriented page parser used only for orientation |
| `deploy/api.yaml` | alternate YAML root | raw candidate only | unsupported discovery | no Kubernetes page expected |
| snapshot pages | page enumeration | bootstrap snapshot only | snapshot-screened only | current source unavailable |

Only the first row can support “zero findings.” “Zero discovered artifacts,”
“snapshot-screened only,” and “unsupported discovery” are separate outcomes.
Zero pages by itself supports none of them.

## Failure modes

| Symptom | Cause | Response |
|---|---|---|
| No `infrastructure/` pages at all | No supported files at bootstrap, stale/missing bootstrap pages, unsupported discovery root, or parser limitation | Inspect current raw discovery roots; choose one explicit outcome instead of “clean.” |
| Kubernetes/Actions findings feel thin | Pages omit security context/permissions and other controls | Read current raw YAML; page silence is not “nothing to find.” |
| Compose page shows a literal secret | A value may have been captured into the bootstrap page | Flag the key, redact the value everywhere, and confirm/remediate in current raw source. |
| Alternate-directory Kubernetes YAML has no page | Only the `k8s/` root is recognized as Kubernetes | Record unsupported discovery and review raw source or use an authorized dedicated extractor. |
| A dedicated extractor disagrees with pages | Pages and extraction have different source basis or coverage | Prefer the fresh exact-scope result, record both bases, and do not merge them into a stronger claim. |
