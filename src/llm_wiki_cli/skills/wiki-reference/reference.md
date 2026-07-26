# wiki-reference reference

Supporting detail for [SKILL.md](SKILL.md). Each section stands alone; read
the one that matches the command or diagnostic in front of you. Commands
assume the project root; substitute the project's configured `--wiki-dir`
(default `docs/llm_wiki`) where a command takes one.

## Extractor helpers and toolchains

- TypeScript/JavaScript, Go, Rust, and Haskell extraction runs through
  prepared helper toolchains. If extraction or lint reports a missing prepared
  helper, run `llm-wiki prepare-extractors --src-dir .` once and repeat the
  failed command.
- Do not run npm/go/cargo/ghc helper setup manually; `prepare-extractors`
  owns that cache.
- If the Go executable on `PATH` cannot run, set `LLM_WIKI_GO=/path/to/go`
  and retry. If GHC needs to be selected explicitly, set
  `LLM_WIKI_GHC=/path/to/ghc` before preparing extractors.
- Go `_test.go` files are excluded by default; pass `--include-tests go` to
  document Go behavior-spec or integration-test files intentionally.
- To keep prepared helpers separate from the inventory cache, use separate
  paths:

  ```
  llm-wiki prepare-extractors --cache-dir .cache/llm-wiki-helpers
  llm-wiki sync --cache-dir .cache/llm-wiki-inventory --helper-cache-dir .cache/llm-wiki-helpers
  ```

  On `sync`, `lint`, `ci-check`, and `extract`, `--helper-cache-dir` selects
  prepared TypeScript/JavaScript/Go/Rust/Haskell helpers; `--cache-dir` controls only
  `llm-wiki-inventory-cache.json`.

## Haskell extraction contract

Haskell `.hs` and `.lhs` files are registered as built-in source files, and
normal CLI extraction invokes the prepared Haskell helper for syntax-only
inventory. The helper emits syntax-only Haskell inventory without
typechecking the target project and does not start Haskell Language Server.
GHC 9.6.x is the supported Haskell helper toolchain for this release; newer
GHC 9.x releases are best-effort, and older or malformed GHC version output
fails during helper preparation.

Haskell dependency reconciliation reads Cabal `build-depends` statically from
`*.cabal` manifests, scopes nested Cabal packages by nearest manifest
directory, treats library/executable/common dependencies as required, treats
test-suite, benchmark, setup, Stack `extra-deps` and Nix package hints as
optional advisory metadata, and keeps missing or malformed metadata
non-fatal. Unknown Haskell imports are ignored rather than guessed. Haskell
internal dependency edges resolve through declared module names from
inventory entries rather than filepath stems. Haskell lockfile pinning is
intentionally out of scope for lockfile `versions` metadata.

Generated Haskell module pages render declared module names, qualified
imports, aliases, signatures, values, and type-oriented declarations when
present. Haskell inventory stays additive under `llm-wiki-extract/v1`:
Haskell file entries include `language`, `imports`, `classes`, and
`functions`; `module` is present when the source declares one. Haskell import
records include `module`, `qualified`, `alias`, and `line`. `classes` stores
type-oriented declarations with `kind` set to
`data`, `newtype`, `type`, `class`, or `instance`; `functions` stores
top-level signatures, functions, and values with `kind` set to
`signature`, `function`, or `value`. Optional Haskell-specific fields such
as `language_pragmas`, `exports`, and `deriving` are best-effort additive
metadata.

## Python and FastAPI contract extraction

- Deep Python inventory records every parameter kind in declaration order and
  keeps required/nullable/default/factory state separate for model fields.
  Pydantic aliases, constraints, descriptions/examples, validators/config,
  enums, literals, and type aliases are extracted from syntax only; unknown
  expressions remain explicit and target modules are never imported.
- Optional per-file `frameworks.fastapi` declarations are assembled into the
  top-level `api_contracts` block. Router and inclusion prefixes are composed,
  parameter locations/wire aliases and declared responses are normalized, and
  test-source plus `include_in_schema=False` operations are excluded from the
  production operation list by default.
- Inspect an exported contract with
  `llm-wiki extract --deep --openapi-file openapi.yaml`; `--openapi-file`
  requires `--deep`. The file must stay inside the source root and contain
  OpenAPI 3.0/3.1 JSON or YAML. JSON uses the standard library and YAML uses
  the package's required PyYAML safe loader. OpenAPI owns wire fields; static
  analysis supplies source/module/entity/flow links and diagnostics. External
  references are never fetched.
- `bootstrap --api-contracts` creates `api-contracts.md`. For an existing wiki,
  preview `sync --initialize-surfaces api-contracts --dry-run`, then rerun
  without `--dry-run` to create it. A surface-only sync may combine `flows`,
  `dependencies`, and `api-contracts`, filter flows with repeatable
  `--flow-category`, and omit test sources with `--exclude-tests`; ordinary
  entity/module changes are deferred during that pass. Operation sections are
  generated; only `api-contracts.md` `## Notes` and flow `## Behavior` are
  semantic.
- Persisted OpenAPI path/hash metadata and surface policy live in manifest v5.
  Later syncs refresh on specification-only changes; use
  `--clear-openapi-file` to return deliberately to static contract authority.

## Dependency reconciliation

- Interpret monorepo dependency diagnostics with manifest scope in mind:
  nested Python `pyproject.toml` and `requirements*.txt` files apply to their
  directory subtree. Python import/distribution aliases such as `grpc` ->
  `grpcio` and local monorepo distributions discovered from package manifests
  participate in reconciliation, while Go `// indirect` requirements are
  transitive rather than unused direct imports.
- Generic internal import matching is language-scoped before external
  dependency reconciliation, so same-stem files in other languages do not
  consume external imports. Python manifests inside generated agent worktree
  copies are ignored during reconciliation, matching the default source
  snapshot policy.
- Dependency reconciliation may expose optional lockfile-backed `versions`
  metadata for Go `go.sum`, Rust `Cargo.lock`, Python `poetry.lock` or exact
  `requirements*.txt` pins, npm `package-lock.json`, and supported
  `pnpm-lock.yaml` package entries. Missing or malformed lockfiles omit
  version metadata without changing lint pass/fail behavior.

## Knowledge observations, freshness, and availability

The generated `.llm-wiki-knowledge.json` artifact uses
`llm-wiki-knowledge/v1`. It records what a producer observed, the relative
source and producer basis for reproducible structural observations, and the
Markdown/surface snapshot to which those observations belong. It does not
persist a claim that the repository is still unchanged, that prose is true,
or that a concept is semantically verified.

Keep these fields separate when interpreting a result:

- Structural `evidence` is the recorded observation state:
  `present`, `missing`, `invalid`, `unknown`, or `not-applicable`. In
  particular, `present` records a producer's structural observation; it does
  not mean `current`, and strict validation separately checks the promised
  basis.
- `freshness` is computed for the current read operation by comparing the
  recorded basis with an already collected live source/inventory basis. It is
  not written back to the knowledge artifact.
- Semantic `verification` is independent of extraction and lint. Successful
  extraction, a matching hash, or a clean lint run never upgrades it.
  Describe `current` only as **unchanged since observation**, not as correct,
  trusted, or true.
- Lifecycle is also independent. A missing source does not by itself mean a
  concept is deprecated or deleted.

Live freshness states mean:

| State | Meaning |
| --- | --- |
| `current` | Compatible producer and concept bases match; the concept is unchanged since observation. |
| `nonsemantic-source-change` | Source bytes changed, but the concept-scoped structural observation is unchanged. |
| `source-changed` | A compatible live comparison produced a different concept-scoped observation. |
| `source-missing` | A reliably mapped source that had a reliable recorded basis is absent. |
| `basis-incompatible` | Schema, generation options, producer, extractor/plugin configuration or limitations, source mapping, or another required basis is incompatible. It also covers an identical source producing a different observation under an allegedly identical basis. |
| `unknown` | No reliable live comparison or recorded basis is available, or structural freshness is not modeled for that aggregate/document-only concept. |

Every native consumer reports one knowledge availability plus a stable
`reason`:

- `ready` means the manifest, surface, Markdown, and knowledge commitments
  form one validated projection. A ready snapshot can still have
  `freshness_evaluated: false`. Its reason is
  `all-projection-commitments-match`.
- `absent` is the compatible legacy/no-projection case. The ordinary wiki
  surface remains usable, but there is no knowledge graph to trust. Its reason
  is `knowledge-projection-not-present`.
- `degraded` means invalid or mixed projection state was rejected. An
  independently validated surface may be used as a surface-only fallback, but
  consumers expose no knowledge model or optimistic freshness claim. The
  reason distinguishes `policy-selected-surface-only-fallback-after-invalid`
  from `policy-selected-surface-only-fallback-after-mixed-snapshot`.
- `unsupported` distinguishes an unsupported knowledge, manifest, or surface
  schema from both absence and malformed current-version data. No unsupported
  payload is served as knowledge. Its reason identifies the unsupported
  boundary: `knowledge-schema-version-unsupported`,
  `manifest-version-unsupported`, or
  `surface-schema-version-unsupported`.

`llm-wiki status` and MCP status use snapshot-only inspection: they may report
projection availability and aggregate evidence issues, but do not run source
extraction and must report freshness as not evaluated. Use strict lint or a
live context/query operation when a read-time comparison is required. Invalid
or mixed artifacts are never silently repaired by a reader.

## Strict knowledge lint and context ranking

Knowledge enforcement belongs to `llm-wiki lint --strict`; `llm-wiki
ci-check` inherits the strict result. Strict reports use the categories
`knowledge_schema`, `knowledge_projection`, `knowledge_snapshot`,
`knowledge_evidence`, and `knowledge_freshness`, with a stable reason and the
affected artifact, concept locator, or canonical path.

- A declared knowledge artifact that is missing, malformed, unsupported,
  hash-mismatched, or from a mixed snapshot is an error.
- Module/entity concepts promise concept-scoped structural evidence. Any
  non-present state—including `not-applicable`—or an incomplete or wrongly
  scoped promised basis is an error.
- For those promised module/entity observations, `source-changed`,
  `source-missing`, `basis-incompatible`, and `unknown` are errors.
  `nonsemantic-source-change` is diagnostic rather than a strict failure.
- Unknown freshness for aggregate or document-only concepts is allowed because
  live structural comparison is not modeled for them.
- Semantic `untracked`/`unverified` state is not converted into structural
  failure. Lint reports state; it does not repair artifacts, change lifecycle,
  or mutate semantic verification.
- A legacy wiki that does not declare a knowledge projection keeps its
  compatible absence behavior.

The `llm-wiki-context/v1` request protocol accepts `freshness` and `evidence`
as concept refinements only when `filters.surface` or `filters.symbol` is also
present. For example:

```json
{
  "protocol": "llm-wiki-context/v1",
  "budget_tokens": 8000,
  "focus": ["changed", "neighbors"],
  "format": "json",
  "filters": {
    "surface": "entities",
    "freshness": "source-changed",
    "evidence": "present"
  }
}
```

`freshness` accepts `current`, `nonsemantic-source-change`, `unknown`,
`source-changed`, `source-missing`, or `basis-incompatible`. `evidence`
accepts the five structural evidence values listed above. Refinements are
applied before the 20-item concept-reference limit. The
`knowledge_selection` object discloses `unfiltered_total`, `filtered_total`,
`returned`, and `truncated`.

The source-file budget discloses `bounds.files` with exact candidate and
returned counts. `bounds.files.truncated` means a file was omitted; the
top-level context `truncated` field can also report a returned file whose detail
was downgraded to fit the token budget.

Without an explicit freshness filter, stale and unknown concept references
remain eligible and the response warns about them. Ready live results rank
`current`, `nonsemantic-source-change`, `unknown`, `source-changed`,
`source-missing`, then `basis-incompatible`; evidence-present references win
ties, followed by canonical path. If knowledge is absent, degraded,
unsupported, or not live-evaluated, no optimistic freshness ordering is
applied: references stay in deterministic path order, unavailable refinements
match no references, and the response explains the limitation. Knowledge
enrichment does not change source-file priority or consume the source-file
token budget.

## Knowledge query, API, and MCP boundaries

The shared query service indexes locators, canonical paths/MCP URIs, source
paths, and relationship adjacency when it is constructed. Knowledge identity
lookups are exact; they do not fuzzy-match a locator, route, or URI. The
initial relationship vocabulary is the recorded `derived_from` and
Markdown-observation `links_to` kinds—prose is not inferred as a structural
edge.

`get_concept`, `related_concepts`, and `explain_evidence` return the same
JSON-serializable query contract through the Python API and MCP adapters:

- `knowledge` always identifies availability, reason, and whether freshness
  was evaluated. Absence or degradation is explicit rather than represented
  as an empty trustworthy graph.
- Selection fields include `query`, `found`, `ambiguous`, and `matches`.
  Every limited collection has a `bounds` entry keyed by its response path,
  containing exact `total`, `returned`, and `truncated` values. Knowledge
  collections retain their top-level count aliases.
- `related_concepts` additionally reports direction, selected kinds, compact
  relationships/concepts, and unresolved or external targets.
- Ordinary concept/context results carry compact evidence and freshness.
  Full stored basis details and relationship evidence stay behind
  `explain_evidence`; treat that response as sensitive diagnostic material.

The default query/list limit is 20. MCP validates positive limits, caps
external requests at 100, and reports truncation instead of silently dropping
additional results. MCP Markdown search follows the same default/cap and
returns exact `total` and `returned` values, retains `count` as the returned
alias, and exposes `bounds.results`. MCP rejects malformed or noncanonical
knowledge coordinates before constructing the live service; a canonical but
absent coordinate returns `found: false`. Python callers may construct one
`DocumentationGraphQueryService` and pass it as `service=` to reuse the same
validated read view; query methods on that constructed service perform no file
I/O, extraction, network access, writes, or adapter registration.

The core MCP knowledge adapters expose no write operation. Stored knowledge or
extension metadata cannot select executable code, an extractor/plugin, a
subprocess, a network request, or an LLM operation, and no document-provided
operation is executed. Normal service construction may run the application's
configured extraction path; built-in extractors and prepared helpers do not
import or execute the target application. Installed extractor plugins remain
trusted, unsandboxed project-local Python and can have effects outside the core
read contract. That executable selection comes from application configuration,
never from the knowledge artifact. External link targets remain observations
and are not fetched. No metadata field enforces access control, and semantic
verification execution is outside this read contract.

## JavaScript and TypeScript flows

- JavaScript `.js` and `.jsx` files use the TypeScript extractor helper and
  appear in inventory with `language: "javascript"` when extracted.
- Raw Node `http.createServer` and `https.createServer` calls create built-in
  `http` entry points for supported module-level server patterns. Lint keeps
  `javascript_flow_unsupported` only for uncovered `createServer` patterns
  outside that raw Node shape.

## Static-site export

Use `llm-wiki site export|check` or the site export service to build and
validate plain, MkDocs-compatible, or Docusaurus-compatible Markdown as
generated distribution output. The default `--profile reference` mirror
preserves the agent/reference wiki shape. `--profile user --site-name ...` is
an opt-in human-docs profile that writes a concise landing page, expects
authored guide pages, and moves the exhaustive generated inventory to
`generated-reference.md`. MkDocs exports include generated `llm_wiki` front
matter and `mkdocs.yml` navigation; `--file-friendly` is MkDocs-only and
writes direct-file-safe configuration plus a theme override for local disk
handoffs. Docusaurus exports include generated front matter and sidebars.json.

Generated static-site labels may include page-id context when duplicate
Markdown headings would otherwise make navigation ambiguous. Mermaid fences
are preserved for the site's configured Markdown/Mermaid renderer. The
static-site checker validates missing pages, local Markdown links, generated
front matter metadata, duplicate Docusaurus ids, and output path containment
without invoking external builders. When `--built-site-dir` is supplied it
also parses built HTML links; `--link-mode http` accepts hosted MkDocs
directory URLs, while `--link-mode file` requires direct `.html` targets.
User-profile checks add quality gates for default site names, missing guides,
oversized landing pages, and placeholder text in primary human docs.
Warning-only findings do not fail the check.

## Resource-aware execution

Treat `context`, full tests, coverage, builds, browser suites, `sync`, `lint`,
and `ci-check` as heavy gates. Use this environment matrix when scheduling
them:

| Environment | Extractor jobs | Scheduling rule |
| --- | --- | --- |
| Interactive IDE or unknown capacity | `--jobs 1` | Run one heavy gate at a time. The supervisor owns the schedule; subagents may inspect bounded files and diffs but must not launch heavy gates unless explicitly assigned. |
| Isolated terminal | `--jobs auto` is allowed | Use only when the terminal's process is the sole heavy gate and host capacity is available; do not nest another test/build/context fan-out. |
| Controlled CI | `--jobs auto` is allowed with reserved capacity | Run one top-level gate per reserved runner allocation and avoid nested parallel fan-out. Use `--jobs 1` when capacity is shared or unknown. |

Extractor plan diagnostics distinguish three values:

- `requested_jobs` is the user's raw selection, such as `1` or `auto`.
- `resolved_jobs` is the integer concurrency ceiling; `auto` resolves to the
  visible logical CPU count, with a minimum of one.
- `effective_workers` is the maximum number of extraction plans that can run
  simultaneously after absent languages, cache-elided work, sequential-only
  plugins, and eligible-plan caps are applied. It is zero when no extraction
  remains and one for sequential-only work.

The eligible parallel, parallel-plan, sequential-plan, and cache-elided plan
fields explain why effective concurrency may be lower than the requested or
resolved value. `auto` is intentionally not a global host-resource cap.

On ENOSPC, inotify, file-descriptor, severe swapping, or editor-responsiveness
failures, stop launching work and do not retry the same parallel burst. Treat
unfinished gates as inconclusive until capacity is recovered; one later manual
retry may use `--jobs 1`. Watcher-limit symptoms are host/IDE resource evidence,
not proof that `llm-wiki` leaked a watcher.

## `llm-wiki context` for large codebases

`context` produces a token-budgeted, priority-ranked snapshot of the codebase
— ideal for feeding into an LLM prompt when the full extract output is too
large:

```
llm-wiki context --budget 8000 --src-dir . --format markdown --focus changed --read-only
```

- **`--budget`** (required): maximum token count for the output.
- **`--focus changed`** (default): prioritises files from the last git commit.
  Changed files get full detail, their 1-hop import neighbours get slim
  detail, everything else gets names only. Use `--focus all` to treat every
  file equally.
- **`--format`**: `json` (default, structured) or `markdown` (human-readable
  with tier-labelled sections).
- **Cost boundary:** the budget and focus bound emitted output after a full
  deep inventory. They do not bound scan work or make `context`
  computationally cheap.
- **When to use:** for broad repository-wide work, run one serialized context
  scan, then read only the source and wiki pages it selects. For a narrow task
  with supplied files or a supplied diff, skip context and use the wiki index
  only for navigation.
