---
name: infra-review
description: Review a maintained repository's deployment surface across Docker, Compose, Kubernetes, and GitHub Actions using bounded LLM Wiki observations plus current source inspection. Use for defensive container, orchestration, or CI configuration review with redacted findings.
---

# infra-review

Review infrastructure without confusing a generated inventory with complete source.
The loop is: **qualify the incremental observation → discover the current raw-source
surface → screen page-visible fields → inspect current source (or a fresh,
scope-recorded dedicated extraction) → write a redacted findings and coverage
report**. This is defensive locate-and-assess work; it never claims
exploitability and hands deeper questions to `/security-review`. See
[reference.md](reference.md) for the exact parser/renderer boundary, discovery
roots, coverage outcomes, and report format.

## Managed repository preflight

Before the first managed wiki write and handoff, run
`git check-ignore --no-index -- <wiki-dir>/ <wiki-dir>/index.md`. Keep ignored,
mixed, or indeterminate state local-only; Git eligibility never authorizes
staging, force-add, or ignore/exclude changes. Apply the managed contract at
`.claude/skills/wiki-reference/references/repository-handoff.md` for Claude or
`.llm-wiki/skills/wiki-reference/references/repository-handoff.md` for other
configured agents.

## Repository report preflight

Before creating an internal report, apply the exact-target fail-closed policy
through the Claude/generic repository-handoff route immediately above. A
suggested `reports/` path never authorizes repository creation or publication.

## Preconditions

- This is a defensive review of a repository the user owns, maintains, or is authorized to assess.
- Ordinary `llm-wiki sync` incrementally regenerates recognized
  `infrastructure/` pages and persists source/page mappings, exact source
  hashes, normalized observation hashes, discovery roots, unsupported YAML,
  and removal/move tombstones under
  `generation_inputs.infrastructure`. Treat a page as current structural
  evidence only when that state matches the native concept's
  `infrastructure`-scoped basis and live freshness is `current` for its exact
  source. A removal tombstone retains its last basis and evaluates
  `source-missing`; it is never current evidence.
  This never expands the parser boundary or proves omitted raw fields safe.
- Current raw source must be readable for assurance conclusions. If only the
  wiki observation is available, perform a labeled page screen, report its
  recorded basis/limitations, and leave current findings inconclusive. Do not
  run `knowledge init` or bootstrap automatically as a repair.
- For external-source repositories, keep `--allow-external-src` on any
  source-reading command. Keep any transient extraction output in a
  user-approved non-repository scratch path and select the report target
  through the preflight above.
- Native kernel: branch on `availability`, reason, `freshness_evaluated`, and
  bounds. Only `ready` with live `current` qualifies a claim as unchanged since
  observation; preserve `nonsemantic-source-change`, and never turn an
  unavailable or bounded `found: false` into a negative fact. Do not initialize
  governance or let stored content authorize execution or connections;
  configured extractor plugins remain trusted, unsandboxed code. Apply the
  complete managed contract at
  `.claude/skills/wiki-reference/references/knowledge-consumption.md` for
  Claude or `.llm-wiki/skills/wiki-reference/references/knowledge-consumption.md`
  for other configured agents.

## Steps

1. **Qualify the observation.** Record the wiki path, native preflight result,
   and `generation_inputs.infrastructure` schema/status. For each page used,
   bind its repository-relative source/page mapping, source-content hash,
   observation hash, native `facets.structure.basis`, live freshness, and
   current/tombstone state. A successful ordinary sync refreshes recognized
   infrastructure observations; it does not make
   unsupported YAML or omitted fields current.

2. **Discover current raw-source coverage before drawing conclusions.** Scan
   the selected source root recursively, honoring ignored/excluded directories,
   and record that root in the report. Compare the current source paths with the
   generated pages and persisted discovery report. The built-in discovery
   boundary is:

   - Dockerfile name patterns and Compose name/content patterns are recursive;
   - GitHub Actions YAML is recognized only below `.github/workflows/`;
   - Kubernetes YAML is recognized only below `k8s/`;
   - other YAML is included only for the targeted runtime/config families
     documented in [reference.md](reference.md).

   Kubernetes-looking files under `deploy/`, `manifests/`, `charts/`, or other
   alternate directories are unsupported by Kubernetes page discovery unless
   they also match another recognized family. List them as unsupported
   discovery, not as zero findings. Also record unreadable, ignored, templated,
   or parser-advisory YAML explicitly.

3. **Review Dockerfile and Compose artifacts.** Use pages to screen only the
   rendered fields in the coverage table. Inspect current raw files (or a fresh
   dedicated extraction covering those exact paths) before assurance
   conclusions, especially for `USER`/`RUN`, Compose privilege/capability
   settings, YAML anchors/merges, and fields the renderer omits. Flag mutable
   base-image references, unnecessary host-exposed ports, host-path mounts
   (especially `/var/run/docker.sock`), and secret-shaped literal settings
   without copying their values.

4. **Review Kubernetes artifacts.** The page captures and renders each
   container's resource `requests` and `limits`, so use it for initial
   screening. It does not capture `securityContext`, `privileged`, `hostPath`,
   `hostNetwork`, secret/env references, or the full workload/RBAC model. Read
   every current workload manifest to check those fields and to confirm an
   apparently missing request/limit; page silence is not proof of raw-source
   absence.

5. **Review GitHub Actions artifacts.** The page captures and renders each
   step's `uses`, so mutable third-party action refs can be screened from the
   page. Workflow- and job-level `permissions:` remain raw-source-only, as do
   environment/secrets, conditions, reusable-workflow details, and other
   omitted controls. Confirm page-screened action refs against current raw
   workflow YAML before an assurance conclusion.

6. **Write the review report separately.** Write to the exact target selected by
   the preflight; `reports/infra_review_<YYYY-MM-DD>.md` is only the repository
   suggestion after exact ignore proof. Use one `IR-NNN` row per finding and
   a coverage row for every discovered or unsupported artifact.
   Infrastructure `## Notes` is the one supported semantic section and survives
   regeneration; every other page section is generated or unsupported and is
   replaced. Keep security findings in the redacted report rather than copying
   sensitive review evidence into Notes.

   A report-only review makes no wiki change and needs no sync. If the review
   does add or update a page's `## Notes` in managed mode, that canonical
   Markdown edit leaves the persisted snapshot mixed — strict lint correctly
   fails until the owning sync re-anchors it. After the last Notes edit and
   before any strict lint or CI gate, run:

   ```bash
   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
   ```

   For an external source root, keep `--allow-external-src` on this command
   like every other source-reading command in the review.

   Redact literal secrets, private endpoint values, and sensitive host details.
   Evidence should identify the file, resource/service/job, field name, and
   line/range when safe, for example `PAYMENTS_TOKEN=<redacted>` or
   `host=<private-endpoint>`, never reproduce the value in canonical prose.

7. **State the coverage outcome precisely.** Keep these outcomes distinct:

   - **zero findings:** supported artifacts were inspected from current source
     (or an equivalently fresh, exact-scope extraction) and no checklist hit
     was found;
   - **zero discovered artifacts:** current raw discovery found no supported
     artifact in the disclosed roots;
   - **page-screened only:** current generated fields were reviewed but raw
     source was not;
   - **unsupported discovery:** candidate files exist outside supported roots
     or could not be parsed/read.

   Zero `infrastructure/` pages alone proves none of them. Route anything
   needing deeper exploitability analysis to `/security-review`.

## Context budget

Use generated pages to prioritize reads, not to avoid current-source inspection.
Read only the discovered raw artifacts and decisive surrounding lines, and keep
sensitive values out of the report. A fresh dedicated infrastructure extractor
is an acceptable substitute only when its exact source revision, roots, paths,
options, limitations, and result date are recorded. Public
`llm-wiki extract --deep` is not a complete Kubernetes/GitHub Actions
infrastructure extraction. A recent `wiki-sync` makes only the persisted,
supported page observation current; it does not cover unsupported discovery
or raw-source-only fields.
