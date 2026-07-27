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

  `prepare-extractors --cache-dir <helper-cache>` selects the helper cache.
  `--helper-cache-dir <same-helper-cache>` selects prepared TypeScript/JavaScript/Go/Rust/Haskell helpers
  on source-reading commands. In particular, `sync`, `lint`, `ci-check`,
  `extract`, and `bootstrap` expose `--helper-cache-dir`;
  `--cache-dir` is a separate inventory-cache option only on `sync`, `lint`,
  and `extract`. Never copy `--cache-dir` onto a command whose parser does not
  expose it.

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
- Deep extract also exposes the additive
  `dependencies.version_details` contract, versioned as
  `llm-wiki-dependency-version-details/v1`. Its deterministic records preserve
  every supported scoped declaration, selected lock/module version, and
  checksum-only observation with repository-relative source path,
  declaration kind, selection confidence, ecosystem semantics, and truthful
  direct/transitive/unknown reach. `go.mod` selections remain distinct from
  `go.sum` observations. Check its `coverage` and `diagnostics`; legacy
  `versions` remains compatible but can collapse scope and versions.

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

### Normative native preflight

Every skill that consumes native state must inspect the `knowledge`
availability, stable `reason`, and `freshness_evaluated` before interpreting a
query result, including `found: false`. Apply this decision table; it is not a
scalar trust score:

| Native result | Permitted interpretation and action |
| --- | --- |
| `ready`, live `current` | The compatible observation is unchanged since it was recorded. It may support a qualified structural claim, but it does not mean the claim is true, human-reviewed, approved, secure, semantically verified, or current in a running system. |
| `ready`, live `nonsemantic-source-change` | The concept-scoped structural observation remains comparable and unchanged while source bytes changed. Preserve and report the byte-change diagnostic; do not call the source byte-current. |
| `ready`, live `source-changed`, `source-missing`, `basis-incompatible`, or `unknown` | Native data remains visible as qualified evidence, not an authoritative current claim. Inspect source, refresh through the owning workflow, defer, or report the limitation according to the task. `source-changed` is not by itself proof that semantic prose is false. |
| `ready`, `freshness_evaluated: false` | Projection commitments match only for the recorded snapshot. Report snapshot-only availability and do not infer any live freshness state. |
| `absent` (`knowledge-projection-not-present`) | Continue compatible surface, extract, or legacy-query behavior when useful and label it as a legacy fallback. Report that native qualification is unavailable; never reinterpret no native matches as an empty graph or negative fact. |
| `degraded` after invalid state (`policy-selected-surface-only-fallback-after-invalid`) | Use only an independently validated surface fallback. Report native knowledge unavailable; do not serve or infer from the rejected model. |
| `degraded` after a mixed snapshot (`policy-selected-surface-only-fallback-after-mixed-snapshot`) | Treat the manifest, surface, Markdown, and knowledge artifacts as one inconsistent commit. Use only an independently validated surface fallback and require an owning refresh before native conclusions. |
| `unsupported` (`knowledge-schema-version-unsupported`, `manifest-version-unsupported`, or `surface-schema-version-unsupported`) | Report the unsupported boundary and use no native payload. A missing match cannot establish absence. |

Invalid and mixed snapshot are underlying rejected states, not extra optimistic
availability values; the shared consumer exposes them as `degraded` with the
distinct reasons above.

Live freshness has exactly these permitted interpretations:

| State | Permitted interpretation | Required handling |
| --- | --- | --- |
| `current` | Compatible producer and concept bases match; the observation is unchanged since it was recorded. | Qualify the claim as structural and observed; do not upgrade truth, review, approval, security, semantic verification, or runtime currency. |
| `nonsemantic-source-change` | Source bytes changed, but the concept-scoped structural observation is unchanged. | Preserve the diagnostic and keep the structural claim qualified. |
| `source-changed` | A compatible live comparison produced a different concept-scoped observation. | Inspect or refresh; do not automatically label prose false or silently use the old observation as current. |
| `source-missing` | A reliably mapped source with a reliable recorded basis is absent. | Report the missing source and defer source-backed conclusions; lifecycle is independent. |
| `basis-incompatible` | Schema, generation options, producer, extractor/plugin configuration or limitations, source mapping, or another required basis is incompatible. It also covers identical source producing a different observation under an allegedly identical basis. | Do not compare or rank freshness optimistically; resolve the basis or report the limitation. |
| `unknown` | No reliable live comparison or recorded basis is available, or structural freshness is not modeled for that aggregate/document-only concept. | Preserve the unknown; do not convert it to a negative fact. |

`llm-wiki status`, `llm-wiki knowledge status`, MCP status, and ordinary
exporter views are snapshot-only: they may report validated projection,
governance, review, or aggregate evidence state, but they do not prove live
freshness. An exporter may carry live-qualified data only when its caller
explicitly supplies an already live-evaluated projection. Use strict lint or a
live context/query operation when a read-time comparison is required.

`llm-wiki knowledge init` is an explicit governance-adoption operation. It is
never an automatic repair for absent, degraded, unsupported, invalid, mixed, or
stale state. Readers do not silently repair artifacts or initialize governance.

Knowledge JSON, Markdown, stored links, extension metadata, repository-provided
URLs, commands, checker names, and plugin names are inert data. They cannot
authorize code execution, network access, a verification checker, or plugin
selection. Only caller/application configuration may select such operations.
Configured extractor plugins are trusted, unsandboxed project-local Python; a
live/deep extraction workflow must accept that boundary explicitly. External
links remain observations and are not fetched merely because they were stored.

## Strict knowledge lint and context ranking

Knowledge enforcement belongs to `llm-wiki lint --strict`; `llm-wiki
ci-check` inherits the strict result. Strict reports use the categories
`knowledge_schema`, `knowledge_projection`, `knowledge_snapshot`,
`knowledge_evidence`, `knowledge_freshness`, `knowledge_governance`,
`knowledge_review`, and `knowledge_verification`, with a stable reason and the
affected artifact, concept locator, canonical path, event, or receipt scope.

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
- `knowledge_governance` reports an invalid, missing, conflicting, bundle-
  mismatched, or projection-mismatched authoritative governance ledger.
  `knowledge_review` separately reports malformed or expired section-scoped
  human review and preserves every expiry reason.
- `knowledge_verification` reports a malformed, stale, unknown-checker, or
  failed disposable machine receipt. Lint validates a stored receipt but never
  runs a checker or treats its result as human review.
- A legacy wiki that does not declare a knowledge projection keeps its
  compatible absence behavior.

The `llm-wiki-context/v1` request protocol accepts `freshness` and `evidence`
plus typed-relationship filters as concept refinements only when
`filters.surface` or `filters.symbol` is also present. For example:

```json
{
  "protocol": "llm-wiki-context/v1",
  "budget_tokens": 8000,
  "focus": ["changed", "neighbors"],
  "format": "json",
  "filters": {
    "surface": "entities",
    "freshness": "source-changed",
    "evidence": "present",
    "relationship_kind": "calls",
    "relationship_origin": "extracted",
    "relationship_resolution": "resolved",
    "relationship_direction": "incoming"
  }
}
```

`freshness` accepts `current`, `nonsemantic-source-change`, `unknown`,
`source-changed`, `source-missing`, or `basis-incompatible`. `evidence`
accepts the five structural evidence values listed above. Refinements are
applied before the 20-item concept-reference limit. The
`knowledge_selection` object discloses `unfiltered_total`, `filtered_total`,
`returned`, and `truncated`.

`relationship_kind` accepts a core typed kind or a qualified plugin kind such
as `vendor.plugin/relationship`; `relationship_origin` accepts `extracted`,
`inferred`, `markdown`, or `governance`; `relationship_resolution` accepts
`resolved`, `ambiguous`, `external`, or `unresolved`; and
`relationship_direction` accepts `incoming`, `outgoing`, or `both`. Typed
enrichment appears only when at least one relationship refinement is present.
It returns graph availability/reason, selected filters, all-incident and
filtered totals, returned/truncated counts, compact returned-edge coverage, and
top-level analyzer coverage. It never embeds graph edges, evidence samples, or
hashes. An unavailable extension is reported, not treated as an empty graph.

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
paths, durable UIDs, persisted locator/natural-key aliases, and relationship
adjacency when it is constructed. Knowledge identity lookups are exact. An
accepted coordinate is a current concept locator/MCP URI, exact canonical wiki
path, durable UID, or persisted governance alias; display titles, case-folded
paths, fragments, source paths, and approximate routes do not fuzzy-match.
Always check `found`, `ambiguous`, and `matches` before selecting a concept.

The stable core relationship vocabulary remains the recorded `derived_from`
and Markdown-observation `links_to` kinds—prose is not inferred as a structural
edge. `related_concepts` continues to expose those compact relationships,
resolved concepts, and unresolved/external targets. The independently
versioned typed graph is additive and does not alter core results or legacy MCP
`query_graph` callers/callees/flows/dependency-neighborhood/page queries.

`get_concept`, `list_concept_sections`, `related_concepts`,
`traverse_typed_graph`, and `explain_evidence` return the same
JSON-serializable query contract through the Python API and MCP adapters:

- `knowledge` always identifies availability, reason, and whether freshness
  was evaluated. Absence or degradation is explicit rather than represented
  as an empty trustworthy graph.
- Selection fields include `query`, `found`, `ambiguous`, and `matches`.
  Every limited collection has a `bounds` entry keyed by its response path,
  containing exact `total`, `returned`, and `truncated` values. Knowledge
  collections retain their top-level count aliases.
- `get_concept` adds the one selected compact concept, including UID, aliases,
  lifecycle, optional successor, bounded lifecycle/review state, and separate
  machine-verification state when governance is present.
- `list_concept_sections` adds section-ownership extension availability,
  optional ownership filtering, and bounded document-order section locators
  with heading path, occurrence, ownership, and compact review state. Duplicate
  headings remain occurrence-specific and unknown
  ownership remains `unknown`. When the extension is absent, degraded, or
  unsupported, availability/reason is explicit and the empty returned list is
  not evidence that the concept has no sections.
- `related_concepts` additionally reports direction, selected core kinds,
  compact relationships/concepts, and unresolved or external targets.
- `traverse_typed_graph` additionally reports extension availability, selected
  direction/kind/origin/resolution filters, compact edges, and
  `bounds.edges`.
- Ordinary concept/context results carry compact evidence and freshness.
  Full stored basis details and relationship evidence stay behind
  `explain_evidence`; treat that response as sensitive diagnostic material.

### Typed graph traversal and independent bounds

`traverse_typed_graph` filters before response limiting:

- `direction`: `incoming`, `outgoing`, or `both`;
- `kinds`: `contains`, `imports`, `calls`, `entrypoint_for`, `reads`,
  `writes`, `depends_on`, `supersedes`, or a qualified plugin kind;
- `origins`: `extracted`, `inferred`, `markdown`, or `governance`;
- `resolutions`: `resolved`, `ambiguous`, `external`, or `unresolved`;
- `include_evidence`: `false` by default; opt into repository-sensitive
  samples and their aggregate input hash only for a decisive diagnostic.

Resolved, ambiguous, external, and unresolved endpoints remain in the returned
edge list when selected; do not silently keep only resolved concepts.
`typed_graph.coverage` describes upstream analyzer materialization.
Per-edge `coverage` describes observations and evidence-sample omission for
that materialized edge. `bounds.edges` describes post-filter response limiting.
These are independent: query `truncated: false` does not prove an analyzer was
complete, and evidence-sample truncation does not change the query edge total.

Build one Python service for a related query sequence, then pass `service=` to
every wrapper:

```python
from llm_wiki_cli.api import (
    build_documentation_query_service,
    explain_evidence,
    get_concept,
    list_concept_sections,
    related_concepts,
    traverse_typed_graph,
)

service = build_documentation_query_service(
    src_dir=".",
    wiki_dir="docs/llm_wiki",
    limit=20,
)
concept = get_concept("llm-wiki://entities/User", service=service)
sections = list_concept_sections(
    "llm-wiki://entities/User",
    ownership="semantic",
    service=service,
)
core = related_concepts(
    "llm-wiki://entities/User",
    direction="both",
    kinds=["derived_from", "links_to"],
    service=service,
)
typed = traverse_typed_graph(
    "llm-wiki://entities/User",
    direction="incoming",
    kinds=["calls"],
    origins=["extracted"],
    resolutions=["resolved", "ambiguous", "external", "unresolved"],
    include_evidence=False,
    service=service,
)
detail = explain_evidence("llm-wiki://entities/User", service=service)
```

Supplying `service=` performs no new extraction. Query methods on the
constructed service perform no file I/O, extraction, network access, writes,
or adapter registration.

The read-only MCP server exposes the same knowledge operations. These complete
request examples use tool arguments directly rather than the legacy
`query_graph` wrapper.

MCP tool `get_concept`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "limit": 20
}
```

MCP tool `related_concepts`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "direction": "both",
  "kinds": ["derived_from", "links_to"],
  "limit": 20
}
```

MCP tool `list_concept_sections`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "ownership": "semantic",
  "limit": 20
}
```

MCP tool `traverse_typed_graph`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "direction": "incoming",
  "kinds": ["calls"],
  "origins": ["extracted"],
  "resolutions": ["resolved", "ambiguous", "external", "unresolved"],
  "include_evidence": false,
  "limit": 20
}
```

MCP tool `explain_evidence`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "limit": 20
}
```

The default query/list limit is 20. MCP validates positive limits, caps
external requests at 100, and reports truncation instead of silently dropping
additional results. MCP Markdown search follows the same default/cap and
returns exact `total` and `returned` values, retains `count` as the returned
alias, and exposes `bounds.results`. MCP rejects malformed or noncanonical
knowledge coordinates before constructing the live service; a canonical but
absent coordinate returns `found: false`.

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

## Durable governance, lifecycle, review, and verification

Governance is optional. Without `.llm-wiki-governance.json`, current locators
remain compatible coordinates but are not described as durable IDs. Adopt
durable identity only as a separate, confirmed operation after a complete
knowledge-capable snapshot exists:

```bash
llm-wiki knowledge init --wiki-dir docs/llm_wiki --dry-run
llm-wiki knowledge init --wiki-dir docs/llm_wiki
llm-wiki knowledge status --wiki-dir docs/llm_wiki --format json
```

The version-controlled governance ledger is the non-rebuildable authority for
bundle identity, UID allocation, aliases, lifecycle events, and human review.
Its joined `.llm-wiki-knowledge.json` extension is disposable. All governance
mutations support `--dry-run`, validate an unchanged committed snapshot, use a
compare-and-swap ledger write, and reject ownership or event conflicts instead
of picking a winner.

Public governance actions are deliberately narrow: `knowledge init` adopts
governance; `knowledge status` reads bounded lifecycle/review history;
`knowledge move` changes a current locator/natural key; `knowledge alias` adds
one historical coordinate; `knowledge lifecycle set` authors an allowed state;
`knowledge deprecate` and `knowledge supersede` are explicit lifecycle
shortcuts (the equivalent nested lifecycle actions are also accepted);
`knowledge review` records one digest-bound human section event; and
`knowledge verify` runs selected registered machine checkers. None is an
implicit side effect of bootstrap, sync, lint, query, status, or export.

Supported unambiguous sync/migration renames carry the UID automatically and
retain old locator and natural-key coordinates as aliases. For an ambiguous
manual rename, rename the filesystem page/source first, preview the exact
identity move, obtain the governance owner's confirmation that it is the same
logical concept and that the target is unowned, apply the move, then sync
immediately:

```bash
llm-wiki knowledge move \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --to-locator llm-wiki://modules/accounts-renamed \
  --to-natural-key source-module:modules/accounts-renamed.md \
  --dry-run
llm-wiki knowledge move \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --to-locator llm-wiki://modules/accounts-renamed \
  --to-natural-key source-module:modules/accounts-renamed.md
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
```

The staged ledger/projection mismatch is rejected by readers until sync
restores parity. A coordinate already owned by another UID is a conflict; no
implicit merge, reallocation, or overwrite occurs. Add a historical coordinate
without moving the current allocation with `knowledge alias --type locator` or
`--type natural-key`:

```bash
llm-wiki knowledge alias \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --type locator \
  --value llm-wiki://modules/legacy-accounts \
  --dry-run
```

Lifecycle is authored independently of source/evidence state. Source
disappearance does not deprecate, supersede, or delete a concept. A
supersession names a different existing successor UID and creates a
governance-origin typed edge:

```bash
llm-wiki knowledge lifecycle set \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --state active \
  --actor-kind human \
  --actor-id maintainer.example \
  --authored-at 2026-07-27T12:00:00Z \
  --dry-run
llm-wiki knowledge supersede \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --successor-uid lw:module:fedcba9876543210fedcba9876543210 \
  --actor-kind human \
  --actor-id maintainer.example \
  --authored-at 2026-07-27T12:30:00Z \
  --dry-run
llm-wiki knowledge deprecate \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --actor-kind human \
  --actor-id maintainer.example \
  --authored-at 2026-07-27T13:00:00Z \
  --dry-run
```

Human review binds a real human actor to one exact semantic section locator and
its scoped hash/evidence basis; agent review cannot satisfy it. Generated-only
churn preserves a valid event, while changed scope/evidence/basis or a missing
section/concept expires it with every reason retained:

```bash
llm-wiki knowledge review \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --section 'llm-wiki://modules/accounts#section/accounts%20Module~1/Description~1' \
  --reviewer-kind human \
  --reviewer-id reviewer.example \
  --method manual-review \
  --method-version 1 \
  --authored-at 2026-07-27T13:00:00Z \
  --dry-run
```

Machine verification is a separate explicit operation over fixed,
application-owned pure checkers:

```bash
llm-wiki knowledge verify \
  --wiki-dir docs/llm_wiki \
  --checker artifact-integrity \
  --checker internal-links \
  --dry-run
```

Only that command may run registered checkers. Reads and lint merely validate
the disposable `.llm-wiki-verification.json` receipt against its selected
scope, hashes, governance input, and checker versions; they do not rerun it or
turn it into review, truth, or approval.

Resolve ledger conflicts manually while preserving every allocation and
non-conflicting event, giving every UID/current coordinate/alias exactly one
owner, and explicitly resolving lifecycle forks. Then run sync and
`knowledge status`. If a governed manifest/projection exists but the ledger is
missing, restore the exact `.llm-wiki-governance.json` from version control or
backup. Never run `knowledge init` or reconstruct it from generated artifacts.
If only generated artifacts or a receipt are damaged, retain the ledger and
regenerate the disposable state through its owning command.

## JavaScript and TypeScript flows

- Deep extract keeps legacy `data_flows` compatible and adds the independently
  versioned `data_flow_details` sibling
  (`llm-wiki-extract-data-flow-details/v1`). Its state distinguishes
  `not_evaluated`, `unsupported`, and `evaluated`; top-level coverage bounds
  flows; and each detailed flow reports observed/emitted/omitted counts,
  truncation reason, upstream analyzer limitations, and effective limits for
  steps, effects, boundaries, transfers, and gaps. Empty evaluated output is
  not the same as disabled or unsupported analysis.
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

### Opt-in native metadata for Site and Obsidian

Site and Obsidian keep their ordinary output byte contract unless
`--knowledge-metadata summary` is explicitly selected. Enriched export/check
must use matching knowledge options:

```bash
llm-wiki site export \
  --wiki-dir docs/llm_wiki \
  --out-dir site \
  --format mkdocs \
  --knowledge-metadata summary \
  --knowledge-profile public-portable
llm-wiki site check \
  --wiki-dir docs/llm_wiki \
  --out-dir site \
  --knowledge-metadata summary \
  --knowledge-profile public-portable
llm-wiki obsidian export \
  --wiki-dir docs/llm_wiki \
  --vault-dir vault \
  --knowledge-metadata summary \
  --knowledge-profile public-portable
llm-wiki obsidian check \
  --wiki-dir docs/llm_wiki \
  --vault-dir vault \
  --knowledge-metadata summary \
  --knowledge-profile public-portable
```

The command adapters load one validated snapshot-only view, including
governance/review and any existing machine receipt. They do not scan source to
claim live freshness, so exported freshness is `not-evaluated`. A service
caller may project an already complete live-evaluated view, but ordinary
exporter/status output never upgrades its snapshot.

`public-portable` is the public allowlist profile. It omits raw evidence,
source coordinates, local actors, producer/plugin detail, private repository
identity, non-parity hashes, environment detail, credentials, and absolute
paths. Public repository identity remains `unknown` unless trusted current
configuration supplies `--knowledge-public-repository-identity` and the value
exactly corroborates a committed `configured-public` identity. Use `internal`
only for a controlled internal destination; it can retain additional safe
repository, producer, actor, evidence, and extension detail but still excludes
credentials, raw private remotes, raw plugin settings, environment dumps, and
machine-local paths.

The profile governs only added native metadata. Canonical Markdown bodies and
copied media are preserved publication input, not redacted or reviewed by the
knowledge projection. Review prose, links, screenshots, and other media
separately before public publication. Both outputs are disposable views:
rebuild them from the validated canonical snapshot rather than hand-editing
projected front matter or Obsidian typed-relationship sections.

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
