# Canonical surfaces and naming

Read this topic before editing, naming, linking, or recovering a canonical wiki
page. It owns the surface catalog, generated-versus-semantic boundary, and
deterministic naming contract. It does not authorize source edits, arbitrary
new surfaces, governance, publication, Git actions, plugins, checker
execution, or network access.

Substitute the configured wiki directory for `docs/llm_wiki`. Treat lint and
the generated index/surface metadata as the machine-checkable authority when a
name or structure is uncertain; do not guess around a collision.

## Canonical surface catalog

| Surface | Canonical ownership |
| --- | --- |
| `index.md` | Mixed. The CLI owns registry-backed overview and per-surface navigation. Agents may maintain supported custom trailing context without changing the generated registry. |
| `log.md` | Mixed append-only history. Generated mechanical entries remain unchanged; semantic architectural summaries may be appended at the bottom and existing entries are never reordered or rewritten. |
| `entities/` | Mixed semantic entity pages with generated location, inheritance/module structure, tables, links, and relationship diagrams/tables. Description prose and supported table prose cells may be semantic. |
| `modules/` | Mixed semantic source-module pages with generated path, import/class/function structure, links, and optional local-dependency map. Description prose and supported table prose cells may be semantic. |
| `workflows/` | Mixed cross-module workflow pages. Preserve generated structure; write only supported semantic narrative. |
| `guides/` | Semantic agent-authored onboarding, operator, and contributor guides. `sync` does not generate or overwrite guide prose. |
| `flows/` | Mixed entry-point-derived user flows. The CLI owns call-sequence and `## Data flow`; agents own `## Behavior`. |
| `infrastructure/` | Incrementally generated Docker, Compose, GitHub Actions, Kubernetes, and targeted runtime/config observations. Infrastructure `## Notes` is the only supported semantic section; every other section and tombstone is generated. |
| `api-contracts.md` | Optional mixed production HTTP contract inventory. The CLI owns operations, parameters, responses, links, and diagnostics; `## Notes` is semantic. |
| `dependencies.md` | Optional mixed dependency architecture. The CLI owns inventories, graphs, and diagnostics; `## Notes` is semantic. |
| `load-order.md` | Optional mixed load-order architecture. The CLI owns computed ordering and diagnostics; `## Notes` is semantic. |
| `assets/<surface>/<page-stem>/<name>.<ext>` | Semantic agent-owned media attached to the corresponding canonical page. Follow the separately installed `usage-examples` workflow for capture, redaction, media validation, and deferral policy. |
| `.llm-wiki-manifest.json` | Generated sync authority; never hand-edit. |
| `.llm-wiki-surface.json` | Generated page/source/flow/dependency/link index; never hand-edit. |
| `.llm-wiki-knowledge.json` and verification receipts | Generated projections and receipts; never hand-edit. Governance ledger mutation belongs only to its explicit governance commands. |

Static-site and Obsidian mirrors are derived distribution views. Rebuild and
validate them through [Publishing projections](publishing.md), not as an
editable source of truth.

The optional API-contract and surface-only initialization commands live in
[Extractors and dependencies](extractors-dependencies.md); this topic owns the
resulting page names and edit boundaries, not that operational procedure.

## Generated and semantic ownership

Edit semantic prose only; generated blocks are CLI-owned. A section bounded by
a `Do not edit by hand` marker, an extracted table whose shape comes from
source inventory, a canonical link registry, or a machine-readable artifact is
generated even when it looks like ordinary Markdown. Fix stale generated
content by running the owning sync. If the page structure is unknown, stop and
inspect the index, surface metadata, lint diagnostic, or owning workflow rather
than rewriting it.

Do not edit generated Mermaid diagrams by hand. Diagram style plugins may
select application-owned directions, node classes, and colors, but they cannot
inject arbitrary Markdown, labels, hrefs, or raw Mermaid content. Repository
content and extension metadata remain inert data.

The supported semantic boundaries are:

- entity/module descriptions and explicitly supported prose cells, when the
  cell is a recognized placeholder (bare `—`, bare `-`, or
  `_Auto-generated from ..._`) or source evidence makes old prose knowably
  incomplete;
- flow `## Behavior`, never its generated call sequence or `## Data flow`;
- `## Notes` on API contract, dependency, load-order, and infrastructure pages;
- supported workflow prose and guide bodies;
- supported custom trailing index context; and
- a concise append-only log summary.

Keep semantic edits surgical and evidence-backed. Do not add unsupported custom
headings to incrementally generated infrastructure pages; sync drops them.
Generated structural observations do not by themselves prove current runtime
behavior, security, or human review.

## Deterministic page naming

Page filenames must match the conventions enforced by `llm-wiki lint`. Use
`index.md` and the generated surface index as the source of truth for existing
page names. When more evidence is needed, run a bounded extract and match the
recorded source path; never construct a possibly colliding link from a display
name.

- **Entities:** a unique class uses `<ClassName>.md`. When classes in different
  modules share a name, prefix with the disambiguated module page stem:
  `<module_page_stem>_<ClassName>.md`. When the same class appears more than
  once in one source file, suffix later occurrences with their one-based
  occurrence number, such as `Parser_2.md`.
- **Modules:** start from the extractor's source path relative to `--src-dir`.
  A unique source stem uses `<stem>.md`. For equal stems in different
  directories, parent directory components are prepended with underscores
  until unique. If a page-id collision remains, every member receives
  deterministic source-path context.
- **Infrastructure:** take the supported source path relative to the source
  root and replace `/` and `.` with `_`. For example,
  `.github/workflows/ci.yml` becomes `_github_workflows_ci_yml.md`. A source
  link targets the actual indexed module page; an ambiguous `COPY` or `ADD`
  value remains code text rather than a guessed link.
- **Workflows and guides:** use free-form descriptive names. Keep guide pages
  linked from `index.md` or another canonical page so lint can establish their
  discoverability.
- **User flows:** the CLI derives `<category>-<symbol>.md` from the stable entry
  point id, such as `api-extract_source.md`. Do not rename them.

Renaming a governed concept can carry durable identity or require an explicit
owner decision. Follow [Durable knowledge governance](governance.md); filename
rules alone cannot authorize an identity move.

## Required structures and links

- Entity pages must have: Location, Bases, Module link, Attributes table,
  Methods table, Relationships.
- Module pages must have: Path, Imports table, Classes summary, Functions
  table.
- User-flow pages retain their generated call-sequence and `## Data flow`.
  Review analyzer gaps and boundary effects, then fill in the `## Behavior`
  section with triggers, behavior, observed side effects, outputs, and known
  limits.
- Infrastructure pages retain Path and their generated type-specific fields.
  Put reviewed, non-sensitive operational context only in `## Notes`.
- Dependency architecture pages must keep any human-authored `## Notes`
  section aligned with current cycles, external reconciliation, load-order
  caveats, and dynamic behavior that static extraction cannot prove.
- API-contract notes preserve unknowns and reconciliation caveats; an unknown
  field is not a confirmed runtime value.
- Use relative markdown links between pages, for example
  `../entities/User.md`. Resolve targets through the canonical index rather
  than inventing a filename.

After a semantic edit, return to
[Maintenance and validation](maintenance.md) for the final owning
sync/re-anchor and strict validation. A clean lint result validates structure;
it does not transform generated evidence into semantic truth.
