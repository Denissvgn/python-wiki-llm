# impact-analysis reference

Supporting detail for [SKILL.md](SKILL.md).

## Native-first access path and service reuse

Use one constructed Python query service for repeated native calls. The service
performs the source inventory/live evaluation and builds its indexes once;
passing `service=` to the wrappers reuses that exact qualified read view.

```python
from llm_wiki_cli.api import (
    build_documentation_query_service,
    explain_evidence,
    get_concept,
    traverse_typed_graph,
)

service = build_documentation_query_service(
    src_dir=".",
    wiki_dir="docs/llm_wiki",
    limit=20,
)
identity = get_concept(
    "llm-wiki://entities/User",
    service=service,
)
neighborhood = traverse_typed_graph(
    "llm-wiki://entities/User",
    direction="both",
    kinds=[
        "contains",
        "imports",
        "calls",
        "entrypoint_for",
        "reads",
        "writes",
        "depends_on",
        "supersedes",
    ],
    origins=["extracted", "inferred", "markdown", "governance"],
    resolutions=["resolved", "ambiguous", "external", "unresolved"],
    include_evidence=False,
    service=service,
)
decisive_detail = explain_evidence(
    "llm-wiki://entities/User",
    service=service,
)
```

Do not call `build_documentation_query_service` again for the same impact
report, and do not omit `service=` from a wrapper in that sequence. If native
identity is not ready, skip native traversal and continue only with the labeled
bounded source supplement allowed by the table below.

MCP tool `get_concept`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "limit": 20
}
```

MCP tool `traverse_typed_graph`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "direction": "both",
  "kinds": ["contains", "imports", "calls", "entrypoint_for", "reads", "writes", "depends_on", "supersedes"],
  "origins": ["extracted", "inferred", "markdown", "governance"],
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

The first pass keeps detailed samples disabled. If one edge is decisive, rerun
a narrowly filtered typed traversal with `include_evidence: true` or inspect
the exact concept with `explain_evidence`; keep that repository-sensitive
detail internal unless the output policy explicitly permits it.

## Native decision and fallback table

| Native state | Required impact-analysis behavior |
|---|---|
| `ready` + typed graph `ready` | Resolve exact identity; preserve freshness, lifecycle, successor, review, and verification qualification; traverse with explicit filters; report query, evidence-sample, and analyzer bounds separately. |
| `ready` + `typed-graph-extension-not-present` | Use exact identity and its lifecycle/qualification, but make no typed-neighborhood conclusion. Run the labeled bounded source supplement and state that native graph coverage is absent. |
| `absent` (`knowledge-projection-not-present`) | Run bounded supplied-impact or explicitly authorized live source queries. Label native identity, lifecycle, typed evidence, and analyzer qualification unavailable; never report an empty native graph. |
| `degraded`, `unsupported`, invalid, or mixed snapshot | Serve no rejected native payload. Use only independently validated surface/source results, name the reason, and require the owning refresh for a native conclusion. |
| Ambiguous exact identity or persisted alias | Preserve `ambiguous` and every bounded `matches` item; obtain an owner choice or analyze each candidate separately. Do not fuzzy-resolve or merge candidates. |
| `ready` with `freshness_evaluated: false` | Treat identity/graph data as snapshot-only. Do not describe it as live-current; the separately labeled legacy source query may be live without upgrading the native snapshot. |

Supplemental detail can increase the known blast radius, but it cannot erase native
absence, stale/snapshot-only qualification, an unresolved or external edge,
alias ambiguity, or analyzer truncation.

## Typed graph filters and completeness

Always record the exact `direction`, `kinds`, `origins`, `resolutions`,
`include_evidence`, and service/MCP `limit`. A discovery pass includes
`resolved`, `ambiguous`, `external`, and `unresolved` resolution states so
unknown remainder remains visible.

Keep these independent:

| Bound | Response location | Meaning |
|---|---|---|
| Query bound | `bounds.edges` and query `total`/`returned`/`truncated` | Post-filter edges omitted by the response limit. |
| Evidence-sample bound | Each edge's `evidence` and `coverage` | Repeated observations aggregated and samples emitted/omitted for that edge. |
| Analyzer bound | `typed_graph.coverage[]` | Upstream analyzers' observed/emitted/omitted totals, limits, truncation, and limitations. |

`bounds.edges.truncated: false` says only that the persisted post-filter edge
set fit this response. It does not make an analyzer complete. Likewise, an
evidence sample may be truncated while the query returned every materialized
edge.

## Bounded source-query selection by target type

| Target | Query | Access path |
|---|---|---|
| Supplied file or diff | attributed impact | Python/MCP `query_documentation {"operation":"impact","paths":["<file>"],"limit":20,"include_raw_evidence":false}`; use `diff` instead of `paths` for unified-diff text; no full-inventory opt-in |
| Exact native identity | concept/related/typed | Python/MCP `query_documentation` with `operation` `concept`, `related`, or `typed`; committed snapshot only |
| Exact canonical page | surface | Python/MCP `query_documentation {"operation":"surface","value":"<canonical-path>","limit":20}`; committed snapshot only |
| Callable symbol name | pages/callers/callees | Python/MCP `query_documentation {"operation":"symbol","value":"<symbol>","limit":20,"allow_full_inventory":true}` |
| Source file path | dependency neighborhood | Python/MCP `query_documentation {"operation":"dependency","value":"<file>","limit":20,"allow_full_inventory":true}` |
| Entry-point id or symbol | flow/data flow | Python/MCP `query_documentation {"operation":"entrypoint","value":"<entrypoint>","limit":20,"allow_full_inventory":true}` |

Every dispatcher result carries `schema_version`, `operation`, `bounds`,
`truncated`, and a `cost` object. `snapshot-index-only` and
`targeted-extraction` do not perform a full inventory. The three topology
operations reject the request unless `allow_full_inventory` is exactly true.
Supplied evidence never upgrades snapshot knowledge to a live-current claim.

The older `context --request` and MCP `query_graph` routes remain supported for
compatibility. Use them only when a consumer specifically needs their legacy
response shape:

| Target | Compatibility access path |
|---|---|
| Callable symbol name | `context --request` `filters.symbol`, or MCP `query_graph {"type": "callers", "value": "<symbol>", "limit": 20}` |
| Source file path | MCP `query_graph {"type": "dependency_neighborhood", "value": "<file>", "limit": 20}` only — not exposed through `context`'s `filters` |
| Entry-point id or symbol | `context --request` `filters.entrypoint`, or MCP `query_graph {"type": "flow_for_entrypoint", "value": "<entrypoint>", "limit": 20}` |
| Symbol → covering wiki pages | `context --request` `filters.symbol`, or MCP `query_graph {"type": "pages_for_symbol", "value": "<symbol>", "limit": 20}` |

## Compatibility `context --request` payload (`llm-wiki-context/v1`)

```json
{
  "protocol": "llm-wiki-context/v1",
  "budget_tokens": 16000,
  "filters": {
    "symbol": "build_context",
    "entrypoint": "http-chat_completions",
    "relationship_kind": "calls",
    "relationship_origin": "extracted",
    "relationship_resolution": "resolved",
    "relationship_direction": "incoming"
  }
}
```

Response shape (relevant slice):

```json
{
  "graphs": {
    "symbol": {
      "callers": {"query": "build_context", "found": true, "ambiguous": false,
                  "matches": [...], "truncated": false,
                  "bounds": {
                    "matches": {"total": 1, "returned": 1, "truncated": false},
                    "callers": {"total": 3, "returned": 3, "truncated": false}
                  },
                  "callable": {"file": "...", "symbol": "build_context"},
                  "callers": [...]},
      "callees": {"...": "same shape, key is callees"},
      "pages": {"...": "same shape, key is pages"}
    },
    "entrypoint": {
      "flow": {"...": "flow_for_entrypoint result"},
      "data_flow": {"...": "data_flow_for_entrypoint result"}
    }
  }
}
```

Every one of `callers`/`callees`/`pages_for_symbol`/`dependency_neighborhood`/ `flow_for_entrypoint`/`data_flow_for_entrypoint` shares the same envelope fields via the query service's common selection result: `query`, `found`, `ambiguous`, `matches`, `bounds`, `truncated`. Each limited response path has exact `total`, `returned`, and `truncated` values under `bounds`. Always check `found` first — an unresolved query returns an empty result, not an error — and `ambiguous` before trusting a single match when multiple candidates exist.

## `dependency_neighborhood` result shape (MCP-only)

```json
{
  "query": "src/api.py", "found": true, "path": "src/api.py",
  "inbound": ["src/main.py"], "outbound": ["src/db.py"],
  "metrics": {"fan_in": 3, "fan_out": 1},
  "cycle_groups": [], "load_order_index": 4,
  "pages": [{"kind": "modules", "path": "modules/api.md"}],
  "bounds": {
    "matches": {"total": 1, "returned": 1, "truncated": false},
    "inbound": {"total": 1, "returned": 1, "truncated": false},
    "outbound": {"total": 1, "returned": 1, "truncated": false},
    "cycle_groups": {"total": 0, "returned": 0, "truncated": false},
    "pages": {"total": 1, "returned": 1, "truncated": false}
  }
}
```

`metrics.fan_in`/`fan_out` size the blast radius at a glance; `cycle_groups` lists any import cycles the file participates in — report these even when the query wasn't specifically about cycles, since a change to a cyclic module has a wider and less predictable blast radius than fan-in alone suggests.

## Checklist vocabulary (shared with `doc-review`)

| Status | Meaning | Typical action |
|---|---|---|
| valid documentation defect | The page describes behavior the change will alter. | Flag for a real prose edit. |
| stale generated content | Only a generated section (call diagram, dependency table) needs refreshing. | Note that `sync` will handle it; no manual edit needed. |
| needs human confirmation | Unclear whether the page needs a change. | Record the specific question, don't guess. |

Do not add statuses beyond these three — a `doc-review` pass consuming this checklist expects this exact vocabulary (it also has `source-code truth mismatch` and `duplicate finding`, which don't apply to a pre-change impact checklist since there's no existing docs/source disagreement to classify yet).

## Report format

```markdown
## Impact analysis: `build_context`

**Exact native identity:** `lw:code-entity:...` → `llm-wiki://entities/Context`
**Native qualification:** ready; freshness current (unchanged since observation);
lifecycle active; typed graph ready
**Typed selection:** both; calls/imports; extracted/inferred;
resolved/ambiguous/external/unresolved; evidence compact; limit 20
**Native bounds:** edges 20/47 (query truncated); calls analyzer 80/100
(analyzer truncated); one returned edge has omitted evidence samples
**Legacy supplement:** live callers/callees/pages_for_symbol, budget 16000

### Blast radius
- Native persisted/qualified: resolved incoming `calls` from `handle_request`;
  unresolved target `dynamic_hook`; external `redis`
- Legacy live supplement: callers 20 of 47 (truncated), plus
  `dependency_neighborhood(src/context.py)` cycle group 2
- Corroborated by both: `handle_request`

### Docs-to-update checklist
| Concept / page / section | Source | Status | Note |
|---|---|---|---|
| `lw:flow:...` / `flows/api-handle_request.md` / `## Behavior` | corroborated by both | valid documentation defect | Semantic behavior describes the old context budget default |
| `lw:module:...` / `modules/context.md` / generated call map | native persisted/qualified | stale generated content | Owning sync refreshes the generated block |
| `modules/plugins.md` / `## Description` | legacy live supplement | needs human confirmation | Native analyzer did not resolve `dynamic_hook` |
```

## Failure modes

| Symptom | Cause | Response |
|---|---|---|
| Query returns `found: false` | Symbol/file/entrypoint name doesn't match any indexed entry | Re-check spelling/path; do not assume "not found" means "not called anywhere." |
| `ambiguous: true` | Multiple symbols share the name across files | List `matches` and ask the user which one, or analyze each separately. |
| `truncated: true` on callers/callees | More results exist than the query limit | Report the exact `bounds.callers` or `bounds.callees` total and do not describe the emitted list as complete. |
| Need file-level fan-in, only have a symbol | `dependency_neighborhood` takes a path, not a symbol | Resolve the symbol's owning file first (via `pages_for_symbol` or the callable's `file` field), then query the file. |
| Native concept is found but typed graph is absent | The optional typed-graph extension was not committed | Keep exact identity/lifecycle qualification, label typed coverage absent, and use the legacy live supplement without calling native edges empty. |
| Typed query is not truncated but analyzer coverage is | Every materialized edge fit the response, but upstream analysis omitted observations | Report the analyzer limitation; do not call the neighborhood complete. |
| Legacy result adds a caller missing from native results | Live inventory has useful detail outside persisted/native analyzer coverage | Add it under the legacy label and retain the native limitation; never use it to rewrite native resolution or coverage state. |
