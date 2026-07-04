---
name: infra-review
description: Review a repository's deployment surface — Dockerfiles, Compose services, Kubernetes manifests, and GitHub Actions workflows — using LLM Wiki's generated infrastructure pages as the enumeration, then apply a checklist for privileged containers, host mounts, exposed ports, plaintext secrets in env blocks, over-broad Actions permissions, and missing resource limits. Use for a defensive review of a repository's containers/orchestration/CI config; the generated pages are a normalized inventory, not a security review — several checklist items require reading raw source because the generated page doesn't capture them.
---

# infra-review

Turn the deterministic infrastructure inventory into an actual security and operability review. The loop is: **enumerate `infrastructure/` pages → checklist-driven review per artifact type → for gaps the generated page doesn't capture, read the raw source file → findings report → persistent semantic notes on the pages themselves**. This is defensive, locate-and- assess scope — like `attack-surface`, it never claims exploitation and hands deep questions to `/security-review`. See [reference.md](reference.md) for the exact generated-page fields per artifact type, what each type's page does *not* capture (and therefore requires a raw-source read for), and the report format.

## Preconditions

- This is a defensive review of a repository the user owns, maintains, or is authorized to assess.
- A wiki with `infrastructure/` pages already exists (run `wiki-sync` or `wiki-bootstrap` first if not — this skill reads the generated inventory, it does not parse Dockerfiles/Compose/K8s/Actions itself).
- For external-source repositories, keep `--allow-external-src` on any source-reading command and report/output paths under the current project.

## Steps

1. **Enumerate the infrastructure surface.** List every page under `infrastructure/` from the wiki (or `index.md`'s Infrastructure section).
   Group by artifact type from each page's own heading shape: Dockerfile pages have `**Base Image(s):**`; Compose pages have a `## Services` table; Kubernetes/GitHub Actions pages exist when the repo has `k8s/`/`.github/workflows/` content — the current registry stores all of these under the single `infrastructure/` surface.

2. **Review Dockerfile pages** against the generated fields (base image, exposed ports, build arguments, environment variables): flag base images without a pinned tag or digest, any environment variable whose name suggests a secret (`_KEY`, `_TOKEN`, `_SECRET`, `_PASSWORD`) with a literal (non-`${...}`) default value baked into the page, and exposed ports that don't match a documented service purpose.

3. **Review Compose pages** against the generated services table (image/build, ports, depends-on) and per-service detail (volumes, environment, command): flag host-path volume mounts (especially `/var/run/docker.sock` or other host-privileged paths), environment values that are literal secrets rather than `${VAR}` references, and services with host-exposed ports that don't need to be public.

4. **Review Kubernetes pages, reading raw source for what the page omits.**
   The generated page captures `kind`, `name`, `namespace`, `replicas`, `containers`, `service_type`/`service_ports`, and `selector` — it does **not** capture `securityContext`, `privileged`, `hostPath`, `hostNetwork`, or resource `limits`/`requests`. Read the raw manifest source directly for every workload resource (`Deployment`, `Pod`, `DaemonSet`, etc.) to check those fields; do not assume their absence from the generated page means they're absent from the manifest.

5. **Review GitHub Actions pages, reading raw source for what the page omits.** The generated page captures workflow `name`, `triggers`, and per-job `id`/`name`/`runs_on`/`needs`/`steps` — it does **not** capture the workflow- or job-level `permissions:` block. Read the raw workflow YAML directly to check for missing `permissions:` (defaults to broad token scope) or `permissions: write-all`-equivalent over-broad grants, and for third-party actions pinned to a mutable tag/branch instead of a commit SHA.

6. **Write the findings report and persistent semantic notes.** Create `reports/infra_review_<YYYY-MM-DD>.md` with one `IR-NNN` row per finding (artifact, issue, evidence, severity, recommendation) using the format in [reference.md](reference.md). For confirmed findings the maintainer wants tracked long-term, also add a short `## Notes` entry directly on the relevant `infrastructure/*.md` page — this is a legitimate agent-editable semantic surface, and it makes the finding visible the next time anyone reads that page, not just in a point-in-time report.

7. **Hand off.** State plainly which checklist items were answered from the generated page alone versus required a raw-source read (K8s security-context/limits, Actions permissions), and which artifact types had zero findings versus zero *coverage* (no such files exist in this repo) — these are different and must not be conflated. Route anything needing deeper exploitability analysis to `/security-review`.

## Context budget

Read the generated `infrastructure/*.md` pages first — for Dockerfile and Compose artifacts they are usually sufficient on their own. Reserve raw source reads specifically for Kubernetes workload manifests (security context, resource limits) and GitHub Actions workflows (permissions, action pinning), since those are the two documented gaps in the generated model. Do not re-run `extract --deep` for this workflow; the wiki's infrastructure pages are already current if `wiki-sync` ran recently.
