# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.7.0] - 2026-08-12

### Added

- Explicit `knowledge_mode=off|auto|required` context requests use
  `llm-wiki-context/v2` and `llm-wiki-qualified-context-packet/v2` for bounded
  native evidence. Omitting the mode retains the v1 CLI, Python, MCP, and raw
  protocol behavior and is not deprecated in this release; any future default
  change will be announced first with a migration window.
- A shared bounded `llm-wiki-documentation-query/v1` dispatcher through Python
  `query_documentation(...)` and MCP `query_documentation`, with exact
  snapshot-backed concept, surface, and relationship queries plus opt-in
  full-inventory symbol, entrypoint, dependency, and supplied-impact queries.
- Versioned `compact` and `expanded_inline` managed-schema profile markers,
  structured managed-reference verification, and live lifecycle reporting for
  current, disabled, unavailable, legacy, and broken combinations.
- A bounded `upgrade --cleanup-source-agent` recovery option for explicitly
  reconciling an interrupted agent switch without guessing which parallel
  schema is authoritative.
- A one-hop managed `wiki-reference` topic tree for maintenance, canonical
  surfaces, repository handoff, qualified knowledge use, context and query
  selection, governance, extraction, publishing, and resource-aware execution.
  Legacy anchors remain available through a compact compatibility index.
- Exact, fork-safe extractor-helper cache reuse in the reusable full-integrity
  action. The cache identity binds the selected helper plan, runner platform,
  locked toolchains, helper sources and dependency locks, helper-cache contract,
  CLI version, and immutable action revision; helper preparation always
  revalidates restored state before integrity checks run.
- A read-only scheduled/manual convergence workflow that performs one real,
  plugin-disabled sync from a clean default-branch checkout and publishes
  complete wiki status, tracked diff, full-worktree status, sync output, and a
  versioned hash receipt.
- A separately named strict doctor dashboard with locked helper preparation,
  explicit healthy/degraded/unhealthy presentation, bounded summary output,
  and a fixed diagnostic evidence artifact.
- `sync --no-plugins` for trusted automation that must never import or execute
  project-local extractor or generation plugins.

### Changed

- Multi-wiki ownership is now explicit without changing the public Site CLI:
  `doc-hub` owns source aggregation, hub export, and the first mirror check;
  `publish-docs` consumes that checked mirror and owns builder detection,
  built-site validation, and deploy handoff. Existing combined workflows move
  only their hub aggregation stage to `doc-hub`.
- Older unversioned managed instruction blocks in the configured agent's
  current schema path now migrate in place to a versioned profile without
  changing surrounding user prose or separately owned plugin blocks. The
  obsolete generic `.agents.md` path is not relocated: initialization and
  upgrade create or refresh `AGENTS.md` while preserving `.agents.md` unchanged
  as user-owned, manually managed content. `upgrade --no-skills` is the
  supported self-contained rollback through at least the next minor
  compatibility cycle, while `upgrade --skills` refreshes and verifies the
  managed reference before returning to compact delivery. Omitting `--wiki-dir`
  continues to select `docs/llm_wiki`; non-default installations must carry the
  same explicit wiki path through upgrade and status lifecycle commands.
- The `compact` managed-schema profile is now a bounded knowledge-first kernel
  that uses a reusable qualified packet with `--knowledge-mode auto`, concise
  evidence and authority rules, and direct verified-topic routes. The
  `expanded_inline` profile remains self-contained for opt-out and recovery,
  while both profiles carry the same durable repository-content safeguards.
- Initialization and upgrade now provision and verify the managed reference
  before choosing a schema profile. Agent switches commit a usable destination
  schema and config before cleaning an old exact managed path; failures keep an
  expanded inline procedure and preserve prior or locally changed content.
- Explicit source-agent cleanup removes only that agent's managed schema block.
  When managed references are enabled and the target verifies current, it may
  also remove an exact current source reference; opt-out, modified, and
  incomplete reference trees remain preserved for review.
- Agent configuration writes are atomic, preserve compatible extension keys,
  and record user intent separately from the last rendered profile and reason.
  Status derives health from live schema/reference state, while uninstall
  removes only exact current managed-reference trees after schema cleanup.
- Generated and bundled skill routes now open the exact managed reference topic
  they need. Reference installation and upgrade validate the complete nested
  tree, repair managed files deliberately, and fail safely around unexpected or
  linked filesystem entries.
- Generated entity References tables now aggregate exact repeated call
  observations into one logical row with a call-site count, keep call and type
  references distinct, apply the 12-row presentation bound after grouping, and
  disclose exact logical coverage when truncated. Raw and versioned
  relationship interfaces retain their line-specific records.
- Selected skill installs and exports now expand a central, portable dependency
  map transitively in deterministic dependency-first order. Knowledge-consuming
  workflows automatically include and verify `wiki-reference`; reports separate
  requested roots from dependency-included skills, cycles or missing bundled
  dependencies fail before writing, and local reference drift stops its
  consumers. `--force` can refresh differing expected regular files, while
  unexpected or conflicting entries remain preserved and keep consumers
  blocked until reviewed and moved aside.
- `ci-check --format json` now emits the versioned
  `llm-wiki-ci-check/v1` envelope. Its nested `llm-wiki-doctor/v1` health
  projection is composed from the same lint evaluation, so the full-integrity
  action can render broad blocking policy and polished health status without a
  second source scan.
- The repository's full-integrity workflow now delegates to the reusable action
  and uses a measured 15-minute timeout while retaining single-worker source
  evaluation.

## [1.6.0] - 2026-08-09

### Added

- Portable CI adoption for initialized managed wikis through
  `llm-wiki install-ci`, which installs a dedicated full-integrity GitHub
  Actions workflow from an immutable action commit without modifying unrelated
  automation.
- A reusable full-integrity GitHub composite action that installs
  checksum-verified toolchains as needed, prepares detected
  TypeScript/JavaScript, Go, Rust, and Haskell extractor helpers, runs the
  strict integrity check with project-local plugins disabled, preserves the
  original command status, verifies a clean worktree, and uploads a fixed,
  allowlisted set of validation and toolchain evidence.
- Source-selected managed wikis with committed selection profiles, curated task
  guides, architecture notes, module and entity references, workflows,
  entry-point flows, and portable provenance.

### Changed

- Wiki bootstrap and sync now maintain deterministic generated surfaces,
  preserve human-owned semantic sections, retire stale generated flows and
  workflows safely, and keep dependency and runtime-basis projections current.
- Source selection and source-plugin trust are independent, with exact selected
  inputs bound into the managed snapshot and integrity artifacts.
- Repository revision evidence is scoped to the selected source so wiki-only
  commits converge without obscuring selected-source changes.

### Fixed

- Make managed wiki generation portable across fresh checkouts, Windows path
  semantics and line-ending configuration, external source roots, and
  host-specific filesystem layouts.
- Keep generated dependency order, workflow metadata, public log provenance,
  hidden artifact hashes, and semantic ownership mutually consistent across
  repeated synchronization.
- Fail closed on malformed or colliding CI evidence while retaining valid
  diagnostics and the original integrity-check failure status.
- Keep optional MCP installs on the compatible `pydantic-settings` 2.14
  release line so server startup remains warning-free in fresh environments.

## [1.5.1] - 2026-08-04

### Fixed

- Correct the PyPI release metadata for version `1.5.1`.

## [1.5.0] - 2026-07-31

### Added

- Opt-in, allowlisted native-knowledge summaries for static-site and Obsidian
  mirrors, including governed identities, lifecycle, scoped review,
  verification, and freshness. Obsidian mirrors can additionally render native
  typed-relationship metadata.
- Native context, graph, knowledge, and MCP search responses now disclose exact
  response-layer totals, returned counts, and truncation through additive
  `bounds` metadata.
- A protected calibration sibling lifecycle through `llm-wiki docs calibration`
  and matching typed Python APIs. It freezes matching evidence from two
  independent documentation controls, admits a fresh cohort only after
  authority and isolation gates, runs three independent intake roles plus a
  source-cited verifier, and stops at a deterministic pre-labeling intake
  without changing the documentation-run contract or default priority policy.
- A provider-neutral OCI broker for the qualifying local profile. It invokes
  digest-pinned Docker or Podman images with fixed argument vectors, a
  sanitized environment, no network, a read-only root filesystem, dropped
  capabilities, bounded resources, a single size-limited result-file bind, and
  live adversarial denial probes that include over-limit and sibling-output
  attempts. External-broker contracts remain credential-free and require
  separately established host authentication; no provider SDK or adapter is
  included.
- Priority-blind standalone documentation calibration evidence: bootstrap and
  surface artifacts now preserve detector/language provenance, routes, bounded
  call/data-flow details, boundary confidence and gaps, and dependency metrics;
  `docs prepare` records a source-cited complete census and an evidence-only
  shadow without changing the v1 priority rule. Fail-closed preflight and
  mechanical verdict helpers support an external isolated calibration runner,
  while missing labels, holdout custody, or isolation cannot be represented as
  a candidate result.
- Agent-driven standalone documentation workspaces through `llm-wiki docs
  prepare|status|packet|record-result|verify|export` and matching typed Python
  APIs. Runs are explicit, resumable, provider-neutral, and isolated from the
  source project; the core creates deterministic evidence and local publication
  handoffs but invokes no model, installs no target instructions, and never
  deploys.
- Two baseline strategies: deterministic source bootstrap and path-safe
  adoption of an existing canonical wiki, including pages previously enriched
  by LLM-backed `llm-wiki` workflows. Adoption preserves legacy index-only
  inputs, pre-native manifest v4/surface pairs, and manifest v5 inputs while
  validating a marked v5 manifest/surface/knowledge trio as one committed
  projection. Runs record a source content-hash baseline and byte-preserving
  input-wiki snapshot provenance, generated ownership, semantic-page
  classifications, and explicit `require-current`, workspace-only
  `refresh-snapshot`, or limited `allow-unverified` freshness decisions.
- Versioned documentation run, worklist/readiness, agent packet/result, review
  ledger, verification, final-report, and model-routing contracts. Result
  reconciliation independently checks reported wiki paths, source/input hashes,
  and generated ownership; review findings are normalized into a stable ledger,
  while publication evidence is checked during export and verification.
- Credential-free host model routing for both `generic-agent` and `handoff`
  modes. Policies accept OpenAI-compatible, Anthropic, Google Gemini,
  local/self-hosted, and other provider families, including caller labels for
  Mistral, DeepSeek, Alibaba/Qwen, gateways, and cloud backends. Policies
  require low-cost defaults and reserve balanced/capability routes for
  configured escalation signals or explicit user overrides. The routing API
  returns serializable host-owned selection metadata and does not invoke a
  provider. Mistral, DeepSeek, Qwen, gateway, and cloud labels currently use the
  v1 `other` family; first-class backend/publisher/transport bindings are not
  included. Provider families and tiers are caller-maintained labels: the core
  includes no native provider adapter, current-price lookup, or proof of the
  concrete model used.
- Bundled `agent-docs` and `wiki-semantic-enhance` skills plus external-mode
  contracts in the user-doc, onboarding, usage, review, and publication skills.
  Standalone runs export hashed run-local copies rather than installing skills
  into the target project.
- A focused [standalone documentation guide](docs/standalone-documentation.md)
  covering source and enriched-wiki setup, trust/isolation, agent handoffs,
  result schemas, low-cost routing, Python APIs, refresh/resume behavior,
  builders, limitations, and troubleshooting.
- Bounded trigger lock waiting through `LLM_WIKI_LOCK_WAIT`, one-hour circuit
  breaker auto-recovery with `LLM_WIKI_BREAKER_TTL_SECONDS` control, and
  configurable helper runtimes through `LLM_WIKI_EXTRACTOR_TIMEOUT`.
- Typed return contracts for the supported Python API, a shared protocol
  version registry with documented migration rules, and stable
  `InvalidRequestError`, `WorkspaceStateError`, and `ArtifactIntegrityError`
  failure categories across every public API function.

### Changed

- Site and Obsidian enrichment now share a validated snapshot projection. The
  default remains disabled and byte-compatible, while portable enrichment uses
  public redaction unless a caller explicitly selects the internal profile.
- Calibration packet validation now uses one 16 MiB ceiling across the CLI,
  controller, and OCI broker. The broker previously retained a separate,
  unused 64 MiB ceiling even though it receives the direct packet bytes.
- Manifest v5 is the current native wiki format. Standalone adoption retains
  manifest v4/surface compatibility, distinguishes markerless v5 surface-only
  inputs from complete marked v5 trios, and exposes unevaluable inputs as
  unverified snapshot-only evidence instead of claiming current knowledge.
- Standalone result reconciliation refreshes the controller-owned native
  projection after accepted semantic Markdown changes and re-anchors generated
  ownership before later validation or dispatch.

### Deprecated

- Documentation calibration lifecycle APIs now use the canonical
  `prepare_calibration_run`, `get_calibration_run_status`,
  `admit_calibration_run`, `build_calibration_agent_packet`,
  `dispatch_calibration_agent`, `record_calibration_agent_result`,
  `verify_calibration_run`, and
  `use_calibration_host_broker_authenticator` names. The corresponding
  `prepare_p0_calibration_run`, `get_p0_calibration_run_status`,
  `admit_p0_calibration_run`, `build_p0_calibration_agent_packet`,
  `dispatch_p0_calibration_agent`, `record_p0_calibration_agent_result`,
  `verify_p0_calibration_run`, and
  `use_p0_calibration_host_broker_authenticator` compatibility aliases now emit
  `DeprecationWarning`.
- The bundled sample plugin is now `documentation-hooks`. The legacy
  `m4-documentation-hooks` sample ID remains a compatibility alias and emits a
  warning when used.

### Fixed

- Generated Mermaid diagrams now contextually escape bounded Unicode labels,
  validate plugin class names, percent-encode validated relative links,
  deduplicate graph edges, and omit excess visual detail independently of
  separately generated table projections.
- Generated agent prompts, repository instructions, and bundled wiki-mutating
  skills now respect effective Git ignore rules: ignored or indeterminate wiki
  paths remain local-only, while commits require a nonignored path plus
  explicit user and repository authorization.
- Dense module dependency diagrams now prioritize direct and cyclic
  relationships while bounding visualization edges; complete inbound and
  outbound dependency tables remain unchanged.
- Media discovery now ignores Markdown and HTML examples inside backtick code
  spans, while persisted surface asset maps retain only canonical `assets/`
  paths without changing lint warnings or static-site copying for page-local
  media.
- Static-site link rewriting and validation now ignore Markdown-looking links
  inside fenced code blocks and backtick code spans, while continuing to
  rewrite resolvable live links and reject broken or unsafe live links.
- CLI documentation generation once again includes per-command flow pages for
  `bootstrap`, `context`, `extract`, and `lint` when their implementations are
  provided by service modules.
- `sync` now recognizes an untouched `init` scaffold and requires `bootstrap`
  before manifest seeding, preventing generated index links to pages that do
  not exist.
- Public projection output now omits native-only actors, private identities,
  credentials, absolute paths, source snippets, and unapproved extensions.
- Live knowledge freshness now recomputes the effective generation-options
  commitment instead of assuming the recorded snapshot hash is still current.
- MCP knowledge tools reject malformed or noncanonical concept coordinates
  before constructing the source-backed query service.
- Windows guarded reads now hold rename-blocking directory handles throughout
  traversal and compare path/handle metadata using values with stable semantics
  across supported Python versions.
- Windows protected-tree verification now uses fresh, identity-bearing pathname
  metadata instead of incomplete directory-entry metadata while preserving
  strict single-link checks.
- Run-local documentation skill hashes now use platform-independent relative
  path ordering and canonical UTF-8/LF bytes, avoiding false integrity failures
  on Windows, and reject ambiguous NUL-delimited content. Existing affected
  workspaces require an explicit `docs prepare --refresh`; recorded hashes are
  never rewritten silently.
- Case-only protected-artifact collisions consistently preserve the original
  artifact on case-insensitive filesystems.

### Security

- Calibration state uses a dedicated protected root with application-level
  create-once numbered artifacts, guarded no-follow writes, atomic snapshots, a
  cross-platform controller lock, generation/head compare-and-swap checks,
  bounded canonical JSON, replay detection, and fail-closed crash recovery.
  These are same-user content-integrity controls, not authentication against
  the filesystem owner, root, or offline modification. Intake-role packets
  exclude priorities, credentials, host paths, and other-role outputs; the
  verifier receives only the three frozen, sanitized proposals.
- Generated prompt artifacts now apply best-effort credential-pattern
  redaction and report the number of matched values. This pattern matching is
  not secret detection, so generated artifacts still require review before
  sharing.
- External source roots now disclose same-owner and
  system-administrator-owned symlink resolution while rejecting links owned by
  another user. Protected artifact stores also support an optional cumulative
  payload quota, coordinated by the existing root lock.
- Standalone runs treat source trees, adopted wikis, target instructions, and
  live-service responses as untrusted evidence. Source plugins are disabled by
  default, helper/build preparation is explicit, symlink/non-regular/path-escape
  inputs and overlapping roots are rejected, writes are constrained to declared
  roots, live-service flags record permission without making a request or
  capture, and remote publication remains a separately authorized handoff.
- Existing-wiki adoption validates descriptor-pinned manifest, surface, and
  knowledge bytes, their exact marker hashes, cross-artifact commitments, and
  canonical Markdown snapshot before accepting a native projection. Artifact
  metadata never selects or executes source plugins.
- Frozen standalone run contracts now reject coercible trusted-field values,
  inconsistent intake/policy provenance, unsupported imported schemas,
  noncanonical source revisions, and missing or id/path-mismatched run-local
  skills. Compatible resume verifies the anchored baseline evidence before
  comparing current source/input state.
- Source-tree baselines now enforce count, 128 MiB per-file, and 2 GiB aggregate
  limits while streaming. CLI intake/result files are bounded before full
  allocation, and authorized builder output is spooled to workspace-local
  temporary files with only 10,000-byte stdout/stderr tails retained.

## [1.4.0] - 2026-07-12

### Added
- Heavy source scans now report their requested, resolved, and effective
  extractor concurrency before work begins. Lint profile JSON and CI JSON add
  optional execution-plan metadata, and resource-capacity failures receive
  cross-platform recovery guidance without automatic retries.

### Changed
- Generated agent instructions, update prompts, and bundled wiki workflows now
  serialize interactive heavy gates, use `--jobs 1`, distinguish broad context
  discovery from narrow supplied-diff work, and reserve `--jobs auto` for
  isolated terminals or capacity-controlled CI. The reference skill documents
  that context budgets bound output after a full inventory rather than scan
  cost, and that host watcher-limit symptoms do not prove an `llm-wiki`
  watcher leak.

## [1.3.1] - 2026-07-11

### Changed
- Agent instructions for reporting `llm-wiki` tool issues are now opt-in
  instead of enabled by default. Use `init --issue-reporting` to enable them for
  a new project, or `upgrade --issue-reporting` / `--no-issue-reporting` to
  change and persist the preference for an existing project. The guidance only
  creates local report files; it never submits or uploads them automatically.
  Re-running `init` without `--agent` now preserves the stored agent while
  refreshing these preferences.

### Fixed
- Source discovery now follows Git's trailing-space handling for `.gitignore`
  entries: unescaped trailing ASCII spaces are ignored, while `\ ` preserves a
  literal final space.

## [1.3.0] - 2026-07-11

Implements [#10 — Add reconstructable Python/FastAPI API contracts and explicit
surface backfill](https://github.com/Denissvgn/python-wiki-llm/issues/10).

### Added
- Reconstructable Python contracts: deep inventory now preserves every
  parameter kind and normalizes Pydantic field metadata, validators/config,
  enums, literals, and type aliases without importing target code.
- Syntax-only FastAPI contract analysis with composed router prefixes,
  parameter locations and aliases, declared responses/content types, an
  optional canonical `api-contracts.md` surface, and authoritative exported
  OpenAPI 3.0/3.1 JSON/YAML reconciliation.
- Explicit `sync --initialize-surfaces` backfill for flows, dependency
  architecture, and API contracts, including category/test filters, a no-write
  preview, broad-surface guards, and persistent manifest v4 surface policy.
- New bundled `wiki-reference` skill holding contract-level detail
  (extraction contracts including the Haskell helper and inventory schema,
  helper toolchains and caches, dependency reconciliation and lockfile
  `versions` metadata, static-site export profiles, and `llm-wiki context`).
  The install location follows the configured agent: `.claude/skills/` for
  claude (natively indexed), the platform-neutral `.llm-wiki/skills/` for all
  other agents — and the constraint block pointer is rendered per agent.
  `init` installs it (`--no-skills` to opt out; the choice persists in config
  and `upgrade --skills/--no-skills` overrides it), `upgrade` force-refreshes
  it and relocates an unmodified copy when switching agents, `uninstall`
  sweeps every known location but removes only unmodified copies, and
  `skills install` defaults its `--dest` to the configured agent's directory.
  `status` reports whether the installed copy is current, and `init` prints a
  hint about the other bundled skills (`llm-wiki skills list`).
- Agent constraint block now includes a "Report llm-wiki tool issues" rule:
  agents must record CLI misbehavior in per-issue report files under
  `llm-wiki-issues/` at the project root instead of silently working around
  it.

### Changed
- Generated Python signature and model tables now render normalized contract
  metadata, so existing generated pages may change on their next bootstrap or
  sync as a correctness update.
- `PyYAML>=6` is now a required runtime dependency for safely loading
  user-supplied OpenAPI YAML. FastAPI and Pydantic remain unnecessary runtime
  dependencies, and target application code is not imported for extraction.
- The injected agent constraint block (`AGENTS.md`, `CLAUDE.md`, …) was
  deduplicated and slimmed via progressive disclosure: rarely-needed contract
  detail moved to the `wiki-reference` skill and the block now carries
  pointers with explicit trigger conditions, cutting the block by roughly a
  third (~6k to ~4k tokens) with no contract content lost.

## [1.2.0] - 2026-07-08

### Changed
- Minimum supported Python is now 3.10; release automation covers Python 3.10 and 3.13
  across Ubuntu, macOS, and Windows.

### Fixed
- Media parsing now handles parenthesized Markdown targets, same-page
  reference-style images, fenced media examples, and local `srcset`
  candidates consistently across lint, asset indexing, surface indexing, site
  export, and built-site checks.
- `site export` mirrors every referenced media file that resolves inside the
  wiki root, including page-local media outside `assets/`, and stale exported
  media detection now uses one shared reducer for export operations and
  `site check` warnings.
- Internal links with Markdown titles, including safe parenthesized page ids,
  now resolve in the surface index.
- `lint` validates plain markdown links to media targets again: link-style
  references such as `[Download demo](assets/guides/tour/demo.mp4)` are
  existence-checked under `media_link_broken`, count their targets as
  referenced assets for `media_orphan` and the surface-index asset map, and
  are mirrored by `site export`.
- Docusaurus export no longer MDX-escapes the closing `</video>` line of a
  multi-line raw video embed, and opening media tags followed by a tab or
  `/>` are recognized as raw media HTML.

### Added
- Media lint now reports warning-level `media_outside_assets`,
  `asset_unrecognized_type`, and `media_symlink_escape` diagnostics, and the
  surface-index asset counts include an additive `other` media-type bucket for
  non-hidden unrecognized files under `assets/`.
- User documentation usage media support: `lint` now validates local image and
  video references with stable media categories, the wiki surface index records
  `assets/` counts and page-to-asset references, and `site export` mirrors
  referenced assets into static-site output with separate asset operations.
- Built-site checks now validate `<img>`, `<video>`, and `<source>` media
  targets in both `http` and `file` link modes, and user-profile site checks
  warn when primary docs have no usage media.
- Bundled `usage-examples` agent skill plus autonomous-agent schema guidance
  for attaching evidence-linked screenshots or recordings under
  `assets/<surface>/<page-stem>/` and validating the media pipeline before
  publishing.
- Bundled `attack-surface` agent skill (from the 2026-07-04 self-hosted
  workflow review): defensive security-review preparation — prepare extractor
  helpers, run `extract --deep --read-only`, seed required coverage from
  `SECURITY.md`, treat data-flow gaps as unknown surface (never as
  evidence of safety), supplement bounded flow walks with a source-level
  sink scan, and write a prioritized `AS-NNN` exposure report with a
  security-model coverage matrix that hands suspicious paths to deeper
  review. Installable and exportable through the `skills` command group
  and shipped as wheel package data.
- Bundled `wiki-bootstrap` agent skill (from the 2026-07-04 skill spec): the
  first-adoption workflow for an existing codebase — prepare extractor
  helpers through the CLI, run deterministic `bootstrap --depth full
  --format json`, triage the summary, complete P0 pages then a
  centrality-ranked (`fan_in`-weighted) budgeted semantic pass, write an
  explicit `bootstrap-remainder.md` backlog with stable `WB-` item IDs for
  deferred pages, validate with `lint --strict`/`ci-check` to convergence,
  and commit the wiki separately. Installable and exportable through the
  `skills` command group and shipped as wheel package data.
- Bundled `dep-audit` agent skill for dependency-cycle,
  undeclared-dependency, and unused-dependency triage from existing lint,
  ci-check, review JSON, and wiki dependency outputs. The workflow requires
  source verification before source, manifest, or wiki edits and records
  deferred dependency findings explicitly.
- Bundled `doc-review` agent skill for documentation review follow-through
  from review JSON, branch diffs, patch findings, lint, or sync diagnostics.
  The workflow validates findings against source truth, updates semantic wiki
  or source-doc surfaces, runs lint/ci-check, and preserves unresolved
  findings with rationale.
- Bundled agent skills: the package now ships reusable `SKILL.md` workflow
  directories (Claude Code-compatible) under `llm_wiki_cli/skills/`, starting
  with `wiki-sync` — the post-change documentation loop (deterministic `sync`,
  semantic-only prose pass, `lint --strict` validation loop, separate
  `docs(wiki):` commit) with its guardrail reference.
- New `skills` command group: `llm-wiki skills list`, `llm-wiki skills
  install` (into a project's `.claude/skills/`), and `llm-wiki skills export
  --dest <dir>` (any destination, e.g. a personal `~/.claude/skills`).
  Existing identical files are kept, and locally edited skill files are never
  overwritten without `--force`.

## [1.1.0] - 2026-06-28

### Added
- **First-class Haskell source support** — `.hs` and `.lhs` files are now
  discovered as built-in source files, extracted through an explicitly prepared
  helper-backed GHC parser, rendered in generated wiki pages, and included in
  declared-module dependency maps.
- Haskell inventory is syntax-only in this release: it records module names,
  imports, top-level signatures and values, and type-oriented declarations
  without typechecking the target project, starting Haskell Language Server, or
  reconciling Cabal, Stack, or Nix dependency manifests.

### Changed
- Haskell helper preparation now documents GHC 9.6.x as the supported release
  line, treats newer GHC 9.x releases as best-effort, and fails clearly for
  malformed or too-old GHC version output.
- The default CI does not require GHC; real-compiler Haskell validation remains
  opt-in through environments where GHC is present.

## [1.0.0] - 2026-06-23

### Added
- Deep extraction now captures decorated functions defined inside other
  functions (e.g. factory-registered `@app.route`/`@server.tool` handlers) in an
  optional `nested_functions` field, so framework entry points registered inside
  a factory are detected. This surfaces MCP tool/resource handlers and similar
  nested handlers as user-flow entry points.
- Deep extraction now records an optional per-function `calls` list of in-body
  call targets (additive under `llm-wiki-extract/v1`; omitted when empty and
  absent in slim mode). A new internal `resolve_call_edges` resolver maps those
  calls to project symbols, tagging each caller→callee edge `internal`,
  `external`, or `unresolved`. This is the call-edge foundation for
  user-flow documentation.
- Deep extraction now records optional `all_exports` (names listed in `__all__`)
  and `main_block` (presence of an `if __name__ == "__main__"` guard) file-level
  fields (additive under `llm-wiki-extract/v1`; omitted when absent or in slim
  mode). A new internal `entrypoints` service detects user-reachable entry points
  (public API, framework-decorated CLI/HTTP/MCP handlers, and `__main__` /
  console-script processes) and assembles bounded, de-cycled user-flow call paths
  from the resolved call edges.
- `bootstrap` now generates `flows/` pages — one per detected entry point — each
  rendering a Mermaid `sequenceDiagram` of the resolved call path (dashed arrows
  mark external/unresolved calls) plus a semantic `Behavior` placeholder for the
  agent to fill in. `index.md` gains a grouped "User Flows" section, the JSON
  summary reports a `flows` count, and `--skip-flows` opts out. New pure
  `services/diagrams.py` provides reusable Mermaid `sequence_diagram` and
  `flowchart` renderers.
- `lint` (and `ci-check`) now validate `flows/`: a user-flow page whose entry
  point no longer exists is reported as `stale_flows` (existing broken-link and
  orphan checks already cover flow pages). `sync` re-indexes existing flow pages
  into the "User Flows" section without rewriting them. `extract --deep` now
  emits an optional top-level `entrypoints` array. README and generated agent
  instructions document the `flows/` page type.
- `sync` now regenerates flow-page diagrams from the current code when a wiki
  already contains flow pages, preserving any human-edited `## Behavior` section
  (subject to `--no-preserve-semantic`) and only rewriting pages whose generated
  content changed. Projects bootstrapped with `--skip-flows` are left untouched.
- Full `bootstrap` now renders generated entity `## Relationships` sections and
  module `## Local dependency map` sections with bounded Mermaid diagrams,
  compact tables, sanitized links, cycle highlighting, external package counts,
  and concise empty-state notes.
- `lint` now validates generated entity/module Mermaid `click` links as hard
  broken-link issues and emits warning diagnostics for over-large generated
  diagrams without failing old wikis that do not have those sections yet.
- Generated `index.md` is now a registry-backed landing page with a surface
  overview table, counts for every page kind, grouped user-flow links,
  dependency architecture links only when those pages exist, and a log link.
  `sync` preserves custom top-level index sections by default while
  regenerating the landing-page structure.
- Supported public integration surfaces include static-site export and checks,
  documentation graph queries through MCP, Python API context filters,
  deterministic plugin component types, migration and upgrade commands, and
  self-hosted documentation workflows.
- Cross-platform behavior covers Ubuntu, macOS, and Windows. Current Python
  requirements are declared by the package metadata.

## [0.6.2] - 2026-06-23

### Fixed
- Preserve custom top-level `index.md` sections during `sync` by default, so
  extra wiki page categories such as `config_docs/` remain linked and
  `lint --strict` does not report them as orphans after every sync.

## [0.6.1] - 2026-06-14

### Fixed
- Align Go, Rust, and TypeScript extractor inventory loader return annotations
  with their empty-dict fallback behavior, and add contract coverage to prevent
  the optional return type from regressing.

## [0.6.0] - 2026-05-30

### Added
- Preserve user-authored semantic fields during `sync` by default, including metadata-only line-number updates, and add `--no-preserve-semantic` to explicitly disable that preservation. The sync manifest now records semantic hashes and generated semantic snapshots for this merge behavior.

## [0.5.2] - 2026-05-10

### Added
- **Codebase source-adapter support** — `extract` now emits stable
  `llm-wiki-extract/v1` JSON, `extract` and `context` support explicit
  `--output`, `--read-only`, and `--allow-external-src`, bootstrap supports
  `--format json` summaries and `--source-adapter`, and `llm_wiki_cli.api`
  exposes supported extraction/context calls for library consumers.

## [0.5.1] - 2026-05-09

### Changed
- Generated agent instructions and default sync prompts now require a semantic
  enrichment pass after deterministic `sync`, so new or generic wiki pages are
  not considered complete just because structural lint passes.

## [0.5.0] - 2026-05-09

### Added
- **Lint and sync performance runtime** — shared source snapshots, persistent built-in inventory caching, cache diagnostics, and opt-in `--jobs` parallel extraction for `lint`, `sync`, and `ci-check`.
- **Lint profiling** — `llm-wiki lint --profile` emits one JSON object with lint issues, diagnostics, phase timings, and optional cache stats.
- **Prepared extractor helpers** — new `llm-wiki prepare-extractors` command prepares TypeScript, Go, and Rust helpers ahead of time, with helper cache resolution through `--cache-dir`, `LLM_WIKI_CACHE_DIR`, or `.git/llm-wiki-extractors/`.
- **Go toolchain override** — `LLM_WIKI_GO` selects the Go executable used for helper preparation, with clearer diagnostics when Go is found but cannot run.
- **Lint speed analysis** — documented the optimization phases and follow-up performance work.

### Changed
- `sync` now uses the same deep-inventory cache and `--jobs` execution path as `lint`, while preserving normal manifest and page output behavior.
- `lint --profile` now remains valid JSON even when source extraction fails; extractor failures are returned as `extractor_failure` issues and still exit nonzero.
- `ci-check --report` now treats the report path as an explicit output destination, allowing absolute paths and relative paths outside the project root.
- Built-in TypeScript, Go, and Rust extraction no longer installs dependencies or compiles helpers during lint, CI, sync, bootstrap, migrate, or extract runs.
- Relationship generation uses an indexed import resolver and small sync diffs build relationships only for affected entities.
- Generated agent instructions now recommend `sync --jobs auto`, strict lint with jobs, helper preparation, broad-diff handling, and `LLM_WIKI_GO` when needed.

### Fixed
- `sync` repairs manifests with missing or malformed source hashes without modifying wiki pages.
- `sync` stops unusually broad source diffs before page writes unless `--force` is provided.
- `sync` avoids no-op rewrites for unchanged generated pages and summarizes unchanged files instead of printing one line per skipped source.
- Entity name collisions across modules and languages are handled consistently during incremental sync, including index and module links.
- Local metrics writes are best-effort and no longer fail validation commands when the metrics file cannot be written.
- Go helper preparation distinguishes "Go not found" from "Go found but failed to run", uses helper-cache-local `GOCACHE` when needed, and preserves user-provided Go cache settings across platforms.
- Windows CI compatibility improved for helper cache paths, executable casing, and environment variable casing.

## [0.3.41] - 2026-05-07

### Added
- **Obsidian Integration** — `llm-wiki obsidian export|check|install-plugin` mirrors the canonical wiki into an Obsidian vault with frontmatter, wikilinks, related links, sidecar human notes, and a desktop companion plugin
- **MCP Server** — optional `llm-wiki mcp` command exposes read-only wiki tools/resources over stdio or local Streamable HTTP, including wiki search, entity/module fetch, context payloads, lint checks, and status
- **Plugin & Skills Marketplace** — local-only `llm-wiki install` plus `llm-wiki plugins list|remove|validate`; manifest-gated plugins can add extractors, prompt templates, lint rules, and managed agent skill blocks
- **Team Features** — shared `.llm-wiki/team.json` policy, `llm-wiki team init|check|resolve-conflicts`, team prompt-template defaults, required plugin checks, team convention linting, and conservative generated-wiki conflict resolution
- **Wiki-as-Context Protocol v1** — `llm-wiki context --request FILE|-` accepts versioned JSON context requests and returns stable success/error envelopes for agents, IDEs, and CI tools
- **Agent Quality Layer** — strict wiki validation (`lint --strict`), `ci-check` reports, opt-in validation hooks, local metrics, smart prompt change-type guidance, and static `llm-wiki review`

### Changed
- PyPI distribution renamed to `agent-wiki-cli`; the installed `llm-wiki` command and `llm_wiki_cli` import package remain unchanged.
- Generic agent instructions now use `AGENTS.md` for new installs and upgrades; legacy `.agents.md` files are still supported for cleanup but are not automatically migrated.

### Fixed
- Bootstrap workflow pages now link to collision-aware module pages when multiple modules share a stem, such as `models_task.md` and `schemas_task.md`.
- Migrate now repairs legacy workflow links like `../modules/task.md` per workflow using path-aware call graph metadata.
- Lint no longer double-counts broken workflow links already reported by the general markdown link pass.
- Restore CI compatibility for Python 3.9 and Windows, including MCP optional-dependency messaging and Windows path normalization in MCP results.
- Context protocol and MCP callers now receive structured extractor failure errors instead of terminating the process.

## [0.3.28] - 2026-05-02

### Added
- **`llm-wiki upgrade` command** — refreshes all framework-managed artifacts (schema constraint blocks, git hooks, wiki dirs, `.gitignore`) in a single idempotent command; supports agent switching via `--agent`
- **Context-optimized extract** — `--changed` flag restricts extraction to files modified in the last commit; `--summary` produces compact class/function-name-only output; `--paths FILE...` extracts specific files for drill-down
- **Chunked `llm-wiki migrate`** — `--chunk-size`, `--chunk`, and `--plan-chunks` split large legacy migrations into bounded page-operation batches
- **GitHub community health files** — code of conduct, security policy, and issue templates tailored to the CLI's local-agent workflow

### Changed
- Shared schema utilities extracted to `services/schema.py` — constraint block markers, `build_schema_content()`, `strip_wiki_block()`, `replace_schema_block()` now centralised; eliminates duplication across `init_cmd`, `uninstall_cmd`, `bootstrap_cmd`
- Source extraction skips more generated dependency/environment directories, including arbitrary virtualenv `site-packages` layouts, PEP 582 `__pypackages__`, `.nox`, `.direnv`, JS package-manager caches, and Go/Rust `--only-files` paths inside excluded trees

### Fixed
- Prevent wiki auto-sync bot commits from recursively triggering the post-commit hook.
- Preserve Python relative import levels in deep extraction and resolve relative import relationships correctly.
- Avoid wiki page collisions for same-directory multi-language files that share a stem.
- Apply `.gitignore` filtering consistently before TypeScript, Go, and Rust extractor subprocesses run.
- Deprecate qualified entity pages correctly during incremental sync after source deletion.
- Handle local markdown anchors and `mailto:` links correctly during wiki linting.

## [0.1.5] - 2026-04-11

### Added
- **Docker/Compose wiki support** — `bootstrap` now discovers Dockerfiles and docker-compose/compose YAML files, parses them, and generates structured `infrastructure/` wiki pages with build stages, ports, env vars, volumes, services, and cross-references to Python modules for COPY targets
- **Dockerfile parser** — line-based parser extracts FROM (multi-stage), EXPOSE, ENV, VOLUME, COPY/ADD, WORKDIR, ARG, LABEL, ENTRYPOINT, CMD, HEALTHCHECK; handles continuation lines
- **docker-compose parser** — lightweight line-based YAML parser (zero dependencies) extracting services, ports, volumes, environment, depends_on, command, networks, named volumes
- **`infrastructure/` wiki section** — new directory alongside entities, modules, workflows; scaffolded by `init`, populated by `bootstrap`, indexed in `index.md`
- **Infrastructure lint checks** — `lint` now detects undocumented Docker files and stale infrastructure pages
- **Compose parser rewrite** — arbitrary-depth nesting for deploy/healthcheck/depends_on/build, inline YAML list parsing (`["CMD", ...]` and `[infra]`), lazy list-to-dict promotion fixing environment/build/depends_on returning empty lists
- **Recursive Docker file discovery** — `get_docker_inventory()` now searches subdirectories and detects non-standard compose filenames (e.g., `core.yml`, `infra.yml`) via content-based heuristic

### Fixed
- Compose parser flush-list bug — nested key:value blocks (environment, build, depends_on, healthcheck, deploy) were overwritten with `[]` on the next sibling key
- Dockerfile discovery no longer matches `.md` documentation files as Dockerfiles
- **Docker inventory in prompts** — `generate-prompt` and `extract` now include Docker/Compose file inventory for agent context
- **`status` command** — displays wiki directory, configured agent, installed hooks, circuit breaker state, and page counts
- **`config.py` module** — centralized `DEFAULT_WIKI_DIR`, `AGENT_CHOICES`, `CLI_AGENTS`, `IDE_AGENTS` constants and `validate_path()` utility
- **Path validation** — `--wiki-dir` and `--src-dir` arguments are validated to prevent path traversal; rejects paths outside the project root
- **`.gitignore` auto-entries** — `init` appends llm-wiki temp file patterns (`.git/llm-wiki-*.txt`, `.lock`, `.json`, `.log`) to `.gitignore`
- **Global error handler** — `cli.py` catches unhandled exceptions and prints a friendly message instead of a raw traceback
- **`generate-prompt` command** — builds a diff + AST sync prompt and writes it to `.git/llm-wiki-prompt.txt` for pasting into IDE agent chats; supports `--print`, `--no-diff`, `--output`, `--wiki-dir`, `--src-dir`
- **IDE agent hook** — `install-hook` now installs a prompt-generation post-commit hook for `copilot`, `cursor`, and `generic` agents (instead of skipping); prints a reminder box after every commit
- **Agent config persistence** — `init` writes `{wiki_dir}/.llm-wiki-agent` so `install-hook` and `generate-prompt` automatically pick up the chosen agent without requiring `--agent` every time
- **`install-hook --agent` and `--wiki-dir` flags** — explicit override of the persisted agent config and wiki directory path
- **Agent install check** — `init` warns (without blocking) when a CLI agent (`claude`, `aider`, `opencode`) binary is not found on PATH
- **IDE-aware instructions** — `copilot`, `cursor`, and `generic` schema files now include an explicit "How to sync the wiki" section describing the `generate-prompt` workflow
- **`--wiki-dir` flag for `init`** — scaffold the wiki at a custom directory path instead of the default `docs/llm_wiki`

### Changed
- `install-hook` for CLI agents (`claude`, `aider`, `opencode`) now bakes the agent name directly into the post-commit script (`--agent <name>`) rather than relying on the default
- `install-hook` for IDE agents no longer skips installation — it installs the prompt-generation hook instead
- Standardized exit codes: `init`, `hook`, and `trigger-agent` now use `sys.exit(1)` on error paths (matching `lint`)
- `trigger-agent` prompt template now respects `--wiki-dir` instead of hardcoding `docs/llm_wiki`
- Expanded directory exclusions in `extract` — skips `env`, `.tox`, `node_modules`, `__pycache__`, `.eggs`, `build`, `dist`, `.git` in addition to `venv`/`.venv`
- Shell hook scripts now quote `"$CLI"` and shell variables for paths containing spaces

### Fixed
- **Python 3.9 crash** — added `from __future__ import annotations` to `init_cmd.py` and `hook_cmd.py` (used PEP 585/604 syntax without import)
- **Windows lock size** — `msvcrt.locking()` now locks 4096 bytes instead of 1 byte in `lockfile.py`
- **Windows unlock** — prints warning to stderr instead of silently swallowing `OSError` on unlock
- **Circuit breaker** — `trigger-agent` now records failure when `git diff` raises `CalledProcessError` (was silently returning)
- **Version write validation** — `write_version()` raises `ValueError` if the regex doesn't match (was silently writing unchanged content)
- Removed debug comment (`# Debug sync`) from `cli.py`

### Removed
- **`storage.py`** — removed unused `WikiStorage` class and `pydantic` runtime dependency (zero dependencies now)

## [0.1.1] - 2026-04-11

### Added
- New agent targets: `aider` (`.aider.conf.yml`) and `opencode` (`.opencode/instructions.md`)
- Improved agent constraint templates with structured sections and agent-specific preambles
- GitHub Actions CI matrix: Python 3.9 / 3.12 / 3.13 on Ubuntu, macOS, Windows
- PyPI publish workflow via OIDC trusted publisher on `v*` tags

### Fixed
- Python 3.9 compatibility: added `from __future__ import annotations` to source files using PEP 604/585 type hint syntax
- Windows: `os.rename()` → `os.replace()` in circuit breaker for atomic state writes on NTFS
- Windows: lock file opened in `w+` mode so PID can be read back through the lock's own file descriptor
- GitHub Actions: bumped `actions/checkout` to v6 and `actions/setup-python` to v6 (Node.js 24)

## [0.1.0] - 2026-04-11

### Added
- **Core CLI** with 8 subcommands: `init`, `extract`, `lint`, `install-hook`, `trigger-agent`, `bootstrap`, `bump`, `uninstall`
- **AST extraction** via Python `ast` module — deep mode extracts docstrings, attributes with types/defaults, method signatures, decorators, imports
- **Wiki bootstrap** — generates entity, module, and workflow pages from existing codebases with cross-reference relationship graphs
- **Wiki linting** — validates broken links, orphan pages, entity/module/workflow consistency against live AST (CI-compatible exit codes)
- **Post-commit automation** — detached background hook spawns LLM subagent with diff + AST context to autonomously update wiki
- **Agent support** — Claude Code, Aider, OpenCode (headless CLI); Cursor, Copilot, Generic (schema-only)
- **Semantic version bumping** — auto-detects pyproject.toml, setup.cfg, package.json, VERSION; patch on commit, minor on push (opt-in hooks)
- **Safety fuses:**
  - File-based exclusive lock (fcntl/msvcrt) prevents concurrent wiki syncs
  - Circuit breaker auto-disables after 3 consecutive subagent failures
  - Configurable timeout for subagent processes (default 5 min)
  - Diff size guard skips sync on oversized commits (default 1000 lines)
- **Workflow detection** — call-graph analysis identifies cross-module functions touching 3+ internal modules as workflow candidates
- **Clean uninstall** — safely removes hooks, strips constraint blocks from agent schema files, preserves user content
- **Cross-platform locking** — fcntl on POSIX, msvcrt on Windows
- **CI** — GitHub Actions matrix (Python 3.9–3.13, Linux/macOS/Windows) + PyPI publish on tag

[Unreleased]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.7.0...HEAD
[1.7.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.5.1...v1.6.0
[1.5.1]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.3.1...v1.4.0
[1.3.1]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.6.2...v1.0.0
[0.6.2]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.5.2...v0.6.0
[0.5.2]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.3.41...v0.5.0
[0.3.41]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.3.28...v0.3.41
[0.3.28]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.1.5...v0.3.28
[0.1.5]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.1.1...v0.1.5
[0.1.1]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Denissvgn/python-wiki-llm/releases/tag/v0.1.0
