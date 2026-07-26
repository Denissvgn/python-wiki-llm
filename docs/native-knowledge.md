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

The `llm-wiki-context/v1` request protocol accepts `freshness` and `evidence`
as concept refinements. Each refinement must accompany `surface` or `symbol`,
because those fields produce the concept candidates to refine.

```json
{
  "protocol": "llm-wiki-context/v1",
  "budget_tokens": 8000,
  "focus": ["changed", "neighbors"],
  "format": "json",
  "filters": {
    "surface": "entities",
    "freshness": "current",
    "evidence": "present"
  }
}
```

`freshness` accepts the six computed states listed above. `evidence` accepts
`present`, `missing`, `invalid`, `unknown`, or `not-applicable`.

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

The `knowledge` object reports `availability`, `reason`, and
`freshness_evaluated`. Enriched page references use compact origin, evidence,
verification, and freshness summaries; they do not embed full evidence or
hashes in ordinary context.

## Python API

The supported API exports `get_concept`, `related_concepts`, and
`explain_evidence`. Build one service when running several queries so source
extraction, live evaluation, and indexes are reused:

```python
from llm_wiki_cli.api import (
    build_documentation_query_service,
    explain_evidence,
    get_concept,
    related_concepts,
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
- `explain_evidence` adds `concept` and full stored/computed `evidence`, with
  its relationship observations bounded by the query limit.

The default query limit is 20. A caller can pass a different positive limit
when building the Python service. Supplying `service=` to an API wrapper reuses
that service and performs no new extraction.

## MCP tools

The read-only MCP server exposes the same knowledge queries:

- `get_concept(locator_or_exact_route, limit=20)`;
- `related_concepts(locator_or_exact_route, direction="both", kinds=None,
  limit=20)`;
- `explain_evidence(locator_or_exact_route, limit=20)`.

Their result envelopes and degraded behavior match the Python query service.
MCP accepts positive limits, caps them at 100, and reports truncation. Existing
Markdown resources and `llm-wiki://...` resource URIs are unchanged.

`query_graph` provides bounded flow, call, dependency-neighborhood, and
page-for-symbol queries. `search_wiki` defaults to 20 results, applies the same
MCP cap of 100, and returns `count`, `truncated`, and `results`.

MCP `get_status` is snapshot-only. Its `knowledge` object contains
`availability`, `reason`, and `freshness_evaluated: false`; when a projection
is present it also returns a low-cardinality `knowledge_summary`. Status does
not run source extraction and does not claim current freshness.

## Bounds and truncation

Bounded query collections default to 20 items. For Python callers, the service
limit controls the bound; externally supplied MCP limits never exceed 100.
Filtering is applied before limiting, and results are ordered deterministically.

For knowledge relationship and evidence queries:

- `total` is the number of matching relationship observations before the
  limit;
- `returned` is the number emitted;
- `truncated` is `true` when `total > returned`.

Treat `truncated: true` as an incomplete graph. Increase the limit within the
supported boundary or narrow the direction/kind/filter; never infer that an
omitted neighbor does not exist.

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
