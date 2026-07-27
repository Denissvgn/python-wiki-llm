# Native knowledge reads

LLM Wiki keeps human-editable Markdown as the canonical documentation. The
experimental generated `.llm-wiki-knowledge.json` file is a validated,
deterministic read projection of observations about those pages and their
source basis. It is not an editable source of truth, an approval record, or
proof that an observation is still current.

Knowledge-aware commands read the projection together with
`.llm-wiki-surface.json` and the artifact commitments in
`.llm-wiki-manifest.json`. A consumer never serves knowledge from a mismatched
set of those files.

## Observation basis and computed freshness

A persisted observation basis records what was evaluated when a concept was
generated. Depending on the concept, that basis can include a
repository-relative source path, observation scope, extractor identity,
source-content hash, concept-observation hash, and producer configuration
basis. These values explain an observation; they do not persist a timeless
`current` verdict.

Freshness is computed for one read operation by comparing the recorded basis
with an already-collected live source and producer basis:

| State | Meaning |
|---|---|
| `current` | The complete comparable live basis matches the recorded basis. |
| `nonsemantic-source-change` | Source bytes changed, but the concept-scoped observation did not. |
| `unknown` | The comparison lacks enough reliable information for a stronger result. |
| `source-changed` | The concept-scoped observation changed. |
| `source-missing` | A reliably mapped source is confirmed missing. |
| `basis-incompatible` | The producer, configuration, schema, mapping, or observation basis cannot support a positive comparison. |

The live generation-options commitment is recomputed from the validated
manifest policy, the reader's active options and defaults, and the actual
inventory mode. Readers never reuse the recorded hash as the live value. A
different effective option basis reports `basis-incompatible`; an option basis
that cannot be evaluated leaves freshness unavailable. When strict lint opts
into test-language extraction, use the same `--include-tests` selection that
was used to generate the projection if a positive freshness comparison is
required.

Freshness does not imply truth, human review, lifecycle, or authorization. A
hash match means only that the compared observation basis is unchanged. It
does not make an unverified concept verified or an active concept approved.

Snapshot-only operations, including `llm-wiki status` and MCP `get_status`, do
not collect a live source basis. They report that freshness was not evaluated
instead of returning zero freshness counts or claiming that concepts are
current.

## Availability states

Every native read exposes an availability and a stable reason:

| Availability | Consumer behavior |
|---|---|
| `ready` | All projection commitments match. Validated concepts, relationships, and optionally computed freshness are available. |
| `absent` | No knowledge projection is committed. The independently validated wiki surface remains usable. Absence is not an empty trustworthy graph. |
| `degraded` | Invalid or mixed projection state was rejected and policy selected a surface-only fallback. Knowledge, evidence, and freshness are unavailable. |
| `unsupported` | A knowledge, surface, or manifest schema is newer than the reader supports. The unsupported knowledge is not served. |

Examples of stable reasons include
`all-projection-commitments-match`,
`knowledge-projection-not-present`,
`policy-selected-surface-only-fallback-after-invalid`,
`policy-selected-surface-only-fallback-after-mixed-snapshot`, and the
corresponding `*-version-unsupported` reason.

Callers should branch on `availability`, not interpret `found: false` as proof
that no concept exists. In degraded, unsupported, and absent states, native
queries return explicit status and do not fabricate empty knowledge,
evidence, or freshness.

## Typed graph and section ownership extensions

The knowledge index keeps its closed `llm-wiki-knowledge/v1` core contract.
Richer structural relationships and section-scoped ownership are published as
two reserved, independently versioned extensions:

| Extension key | Extension schema | Purpose |
|---|---|---|
| `llm-wiki/typed-graph-v1` | `llm-wiki-typed-graph/v1` | Evidence-backed structural relationships and analyzer coverage. |
| `llm-wiki/section-ownership-v1` | `llm-wiki-section-ownership/v1` | Ordered Markdown sections, ownership, and scoped hashes. |

This keeps the existing `derived_from` and `links_to` records and their query
behavior unchanged. A v1 consumer that does not use these extensions can
continue to use the core projection. A knowledge projection can also be
`ready` while the typed-graph extension is absent; graph traversal then reports
`typed-graph-extension-not-present` rather than claiming that an empty graph
was observed.

### Typed relationship contract

Every typed edge has a deterministic `key`, `kind`, `from`, `target`, `origin`,
`resolution`, `evidence`, and `coverage`. Core directions are fixed:

| Kind | Direction and meaning | Required evidence |
|---|---|---|
| `contains` | Source-module concept → code-entity concept. | `containment` sample with source and target symbols. |
| `imports` | Importing source-module concept → imported module concept or unresolved/external endpoint. | `import` sample with source and target; location when the extractor provides one. |
| `calls` | Caller-owner concept → callee-owner concept or unresolved/external endpoint. | `call` sample with exact callable endpoints; ambiguous candidates retain their source symbols. |
| `entrypoint_for` | Callable-owner concept → user-flow concept. | `entrypoint` sample with callable endpoints and detector identity/version. |
| `reads` / `writes` | Observed flow or owner concept → concept or external resource. | `data-effect` sample with its observed owner and resource. |
| `depends_on` | Concept → explicitly declared package or external dependency; it is not a duplicate of every import. | `dependency` sample tied to the explicit declaration analysis. |
| `supersedes` | Reserved for governance-backed stable identity and is not emitted by structural analysis. | Governance-origin `supersession` sample with source, successor, and reason. |

Endpoints are one of a concept locator/UID, a source symbol, an external
resource, or an unresolved raw target with optional candidates. `origin` is
`extracted`, `inferred`, `markdown`, or `governance`; `resolution` is
`resolved`, `ambiguous`, `external`, or `unresolved`. Ambiguous and unresolved
analyzer observations remain so after concept lifting. Qualified plugin edge
kinds use `namespace/name` spelling and cannot shadow an unqualified core kind.

Repeated observations with the same edge identity are aggregated. Evidence
retains the full observed and unique counts, an input-basis hash, and a
deterministically selected bounded sample. Evidence `emitted` and `omitted`
describe that sample; the corresponding edge `coverage.truncated` states
whether samples were omitted. Per-edge `coverage` describes the materialized
observations for that edge; top-level graph `coverage` describes each upstream
analyzer, including its limitations. Query `bounds` are a third, independent
boundary applied after filtering. A non-truncated query therefore does not
imply complete analyzer coverage, and a truncated evidence sample does not
change the query's edge total.

The graph records static observations, not transitive truth or runtime
completeness. Import resolution is relative to the evaluated inventory; call
ownership is lifted while preserving source symbols; entry-point evidence
identifies its detector; and reads, writes, and dependencies appear only when
their analyzers provide supported observations. Missing locations stay unknown
instead of becoming line `0`. Analyzer depth limits, unsupported language
semantics, unresolved targets, and omitted evidence are disclosed rather than
upgraded to resolved facts.

Analyzer limitation codes are part of the graph's committed input basis.
`deep-analysis-disabled`, `flow-analysis-disabled`, and
`data-flow-analysis-disabled` mean the corresponding collection was not
evaluated. Dependency analysis additionally distinguishes disabled,
not-evaluated, and test-excluding scopes. Import locations depend on extractor
support; unavailable locations remain absent. Entry-point coverage identifies
invalid plugin records and failed detectors. Flow and data-flow coverage
reports static-inference, depth, per-collection, and upstream-total limits;
when an older extractor cannot supply pre-limit effect totals, the graph says
that those totals may be unavailable instead of claiming completeness.

### Section ownership contract

Section observations are built from final post-merge Markdown. The parser
normalizes line endings, follows the heading hierarchy, and ignores headings in
frontmatter, fenced blocks, and indented code. A section locator is derived
from its page locator, heading path, and duplicate occurrence. Renaming a
heading intentionally changes its locator. Ordinals, parent locators, and a
page ordering hash make removal and reordering observable.

Every section has an exact hash and one conservative ownership state:

- `generated` sections have a structural hash;
- `semantic` sections have a semantic hash;
- `mixed` tables have separate structural and semantic projection hashes;
- `unknown` sections have neither scoped hash, so an unrecognized structure is
  never treated optimistically.

The policy mirrors the existing generation and sync authority boundary.
Descriptions and guide prose are semantic. Entity `Attributes`/`Methods` and
module `Classes`/`Functions` tables are mixed: generated row structure is
separate from the human-preserved description cells. Relationship, import,
local-dependency, flow, API, dependency-architecture, load-order, and known
infrastructure sections are generated. Flow `Behavior` and architecture
`Notes` sections are semantic. Recognized navigation sections are generated;
custom navigation sections carried forward by sync are semantic. Duplicate
canonical headings and unrecognized sections fall back to `unknown` unless a
document-specific rule explicitly preserves them. `SurfaceRole` remains the
coarse whole-page compatibility summary.

## Strict lint policy

`llm-wiki lint --strict` and `llm-wiki ci-check` validate native knowledge only
when the wiki contains or declares knowledge-capable artifacts. A legacy wiki
with no knowledge projection remains valid in surface-only mode.

Strict validation treats these conditions as hard issues:

- malformed, schema-invalid, unsupported, uncommitted, or mixed projection
  state;
- a mismatch between canonical Markdown, the surface index, the knowledge
  index, and manifest artifact commitments;
- missing or invalid promised structural evidence for module and entity
  concepts;
- `unknown`, `source-changed`, `source-missing`, or `basis-incompatible`
  freshness for promised structural evidence;
- failure to construct a reliable live evaluation.

`nonsemantic-source-change` is a warning diagnostic rather than a hard issue:
the source bytes changed, but the concept-scoped structural observation did
not. Dependency diagnostics such as cycles, undeclared dependencies, and
unused dependencies also remain non-failing diagnostics.

Use profile output when an integration needs the structured report and
separate knowledge load, evaluation, and check durations:

```bash
llm-wiki lint --strict --profile \
  --src-dir . \
  --wiki-dir docs/llm_wiki
```

When present, `knowledge_summary` contains aggregate availability, concept,
freshness, evidence-issue, degraded-reason, and phase-duration values. It does
not contain concept locators, source hashes, actors, private remotes, or
absolute paths.

## Context filters and ranking

The `llm-wiki-context/v1` request protocol accepts `freshness`, `evidence`, and
typed-relationship filters as concept refinements. Each refinement must
accompany `surface` or `symbol`, because those fields produce the concept
candidates to refine.

```json
{
  "protocol": "llm-wiki-context/v1",
  "budget_tokens": 8000,
  "focus": ["changed", "neighbors"],
  "format": "json",
  "filters": {
    "surface": "entities",
    "freshness": "current",
    "evidence": "present",
    "relationship_kind": "calls",
    "relationship_origin": "extracted",
    "relationship_resolution": "resolved",
    "relationship_direction": "incoming"
  }
}
```

`freshness` accepts the six computed states listed above. `evidence` accepts
`present`, `missing`, `invalid`, `unknown`, or `not-applicable`.
`relationship_kind` accepts a core or qualified plugin edge kind;
`relationship_origin` and `relationship_resolution` accept the typed-graph
values described above; and `relationship_direction` accepts `incoming`,
`outgoing`, or `both`.

Knowledge refinements affect concept references, not the source-file token
budget or source-file priority. Candidates are filtered before the context
limit is applied. With live freshness available, the deterministic ranking is:

1. `current`;
2. `nonsemantic-source-change`;
3. `unknown`;
4. `source-changed`;
5. `source-missing`;
6. `basis-incompatible`;
7. evidence presence, then canonical path, as tie-breakers.

Without an explicit freshness filter, stale and unknown candidates are retained
and a warning explains their presence. If knowledge or live freshness is
unavailable, context does not apply optimistic ranking: it uses deterministic
path order, reports the availability reason, and explains whether a requested
refinement matched no candidates.

The `knowledge_selection` object on a knowledge-aware surface or symbol result
discloses:

- `unfiltered_total`;
- `filtered_total`;
- `returned`;
- `truncated`.

The context source-file budget also returns
`bounds.files = {total, returned, truncated}`. Here `truncated` means files were
omitted. The existing top-level context `truncated` field is broader and can
also be true when a returned file was downgraded to a smaller detail level.
JSON and Markdown protocol envelopes retain these bounds together with the
omitted- and downgraded-file summaries.

The `knowledge` object reports `availability`, `reason`, and
`freshness_evaluated`. Enriched page references use compact origin, evidence,
verification, and freshness summaries; they do not embed full evidence or
hashes in ordinary context.

Typed-graph enrichment appears only when at least one relationship filter is
supplied. It reports graph availability/reason, direction, all-incident and
filtered totals, returned/truncated counts, and compact analyzer/edge coverage.
It never embeds graph edges, evidence samples, or hashes. When the extension is
absent or the knowledge projection is unavailable, context reports that state
instead of treating the graph as empty.

## Python API

The supported API exports `get_concept`, `related_concepts`,
`traverse_typed_graph`, and `explain_evidence`. Build one service when running
several queries so source extraction, live evaluation, and indexes are reused:

```python
from llm_wiki_cli.api import (
    build_documentation_query_service,
    explain_evidence,
    get_concept,
    related_concepts,
    traverse_typed_graph,
)

service = build_documentation_query_service(
    src_dir=".",
    wiki_dir="docs/llm_wiki",
)

concept = get_concept(
    "llm-wiki://entities/User",
    service=service,
)
neighbors = related_concepts(
    "llm-wiki://entities/User",
    direction="both",
    kinds=["derived_from", "links_to"],
    service=service,
)
typed_neighbors = traverse_typed_graph(
    "llm-wiki://entities/User",
    direction="incoming",
    kinds=["calls"],
    origins=["extracted"],
    resolutions=["resolved"],
    include_evidence=False,
    service=service,
)
evidence = explain_evidence(
    "llm-wiki://entities/User",
    service=service,
)
```

The identity lookup is exact. Accepted coordinates are a concept locator/MCP
URI or exact canonical wiki path; there is no fuzzy identity match.

Knowledge query results share this envelope (compact concept fields are
abbreviated here):

```json
{
  "knowledge": {
    "availability": "ready",
    "reason": "all-projection-commitments-match",
    "freshness_evaluated": true
  },
  "query": "llm-wiki://entities/User",
  "found": true,
  "ambiguous": false,
  "matches": [
    {
      "locator": "llm-wiki://entities/User",
      "canonical_path": "entities/User.md"
    }
  ],
  "bounds": {
    "matches": {
      "total": 1,
      "returned": 1,
      "truncated": false
    }
  },
  "total": 1,
  "returned": 1,
  "truncated": false
}
```

Method-specific fields are additive:

- `get_concept` adds one compact `concept`;
- `related_concepts` adds `concept`, `direction`, `kinds`, bounded
  `relationships`, `related_concepts`, `unresolved_targets`, and
  `external_targets`;
- `traverse_typed_graph` adds typed-graph availability, the selected
  direction/kind/origin/resolution filters, and bounded `edges`;
- `explain_evidence` adds `concept` and full stored/computed `evidence`, with
  its relationship observations bounded by the query limit.

Typed traversal omits evidence samples and their aggregate input hash by
default. Pass `include_evidence=True` only when the repository-sensitive
source-symbol, location, detector, reason, and attribute samples are needed.
Compact results still carry evidence counts and coverage, so omission is not
presented as completeness.

The default query limit is 20. A caller can pass a different positive limit
when building the Python service. Supplying `service=` to an API wrapper reuses
that service and performs no new extraction.

## MCP tools

The read-only MCP server exposes the same knowledge queries:

- `get_concept(locator_or_exact_route, limit=20)`;
- `related_concepts(locator_or_exact_route, direction="both", kinds=None,
  limit=20)`;
- `traverse_typed_graph(locator_or_exact_route, direction="both", kinds=None,
  origins=None, resolutions=None, include_evidence=false, limit=20)`;
- `explain_evidence(locator_or_exact_route, limit=20)`.

Their result envelopes and degraded behavior match the Python query service.
MCP accepts positive limits, caps them at 100, and reports truncation. Existing
Markdown resources and `llm-wiki://...` resource URIs are unchanged.

MCP validates knowledge coordinates before constructing the live query service.
It accepts only canonical wiki paths and their exact `llm-wiki://` URI forms.
Malformed, unsafe, unknown-kind, or noncanonical coordinates fail before source
extraction. A syntactically valid coordinate whose concept is absent still
returns the standard `found: false` query envelope.

`query_graph` continues to provide the legacy bounded flow, call,
dependency-neighborhood, and page-for-symbol queries. Typed traversal is
additive and does not change those operations. `search_wiki` defaults to 20
results, applies the same MCP cap of 100, and returns exact `total`, `returned`,
`truncated`, and `results`; legacy `count` remains an alias for `returned`.

MCP `get_status` is snapshot-only. Its `knowledge` object contains
`availability`, `reason`, and `freshness_evaluated: false`; when a projection
is present it also returns a low-cardinality `knowledge_summary`. Status does
not run source extraction and does not claim current freshness.

## Bounds and truncation

Bounded query collections default to 20 items. For Python callers, the service
limit controls the bound; externally supplied MCP limits never exceed 100.
Filtering is applied before limiting, and results are ordered deterministically.

Every bounded query envelope includes a `bounds` mapping keyed by the response
path of the limited collection, for example `matches`, `callers`, `flow.steps`,
`pages`, `relationships`, `edges`, or `evidence.relationships`. Each entry
contains:

- `total`, the exact post-filter and post-deduplication candidate count before
  the response limit;
- `returned` is the number emitted;
- `truncated` is `true` when `total > returned`.

Knowledge relationship and evidence queries retain their top-level
`total`/`returned` aliases. Surface and MCP search responses retain `count` as
an alias for `returned`. These counts describe response-layer limiting, not
whether an upstream analyzer stopped at its own depth boundary.

Treat `truncated: true` as an incomplete graph. Increase the limit within the
supported boundary or narrow the direction/kind/filter; never infer that an
omitted neighbor does not exist.

There is no supported in-place edit or partial deletion for either reserved
extension. Consumers that do not need typed relationships can omit graph
filters and continue using the stable core queries. Operational rollback of
the generated knowledge projection follows the manifest-last procedure:
disable knowledge generation, remove the projection and its manifest
commitment through an authorized writer or migration, and continue from the
independently validated surface index. Deleting or editing one extension by
hand makes the committed artifact invalid or mixed rather than rolling it back.

## Read-only and no-execution rules

Knowledge artifacts are inert data. Loading, validation, serialization,
freshness comparison, status, and query methods never execute a command,
subprocess, hook, plugin, URL, or extension value obtained from the artifact.
Artifact contents cannot grant access, authorize an operation, or select a
projection/redaction policy.

After a documentation query service is built, its query methods perform no
filesystem or network I/O. Building a live service performs static source
analysis through application configuration and may use explicitly prepared
language helpers. Built-in extractors and helpers do not import or execute the
target application. The core MCP knowledge adapters expose no write operation
and core-owned paths do not write wiki, manifest, cache, hook, or configuration
files.

Installed extractor plugins remain trusted, unsandboxed project-local Python.
They can perform I/O or other effects while a live service is being built, so
their behavior remains governed by the existing trusted-plugin security model.
Plugin selection comes from application configuration, never from knowledge
artifact metadata.

`explain_evidence` intentionally returns detailed stored and computed evidence.
Treat that response as repository-sensitive and avoid copying it into public
logs. Ordinary context, status, and metrics surfaces use compact or aggregate
summaries instead.
