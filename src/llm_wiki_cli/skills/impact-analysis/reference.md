# impact-analysis reference

Supporting detail for [SKILL.md](SKILL.md).

## Query selection by target type

| Target | Query | Access path |
|---|---|---|
| Callable symbol name | `callers`, `callees` | `context --request` `filters.symbol`, or MCP `query_graph {"query_type": "callers", "symbol": "..."}` |
| Source file path | `dependency_neighborhood` | MCP `query_graph {"query_type": "dependency_neighborhood", "path": "..."}` only — not exposed through `context`'s `filters` |
| Entry-point id or symbol | `flow_for_entrypoint`, `data_flow_for_entrypoint` | `context --request` `filters.entrypoint`, or MCP `query_graph` with the matching `query_type` |
| Symbol → covering wiki pages | `pages_for_symbol` | `context --request` `filters.symbol` (bundled with callers/callees), or MCP `query_graph {"query_type": "pages_for_symbol", "symbol": "..."}` |

## `context --request` payload (`llm-wiki-context/v1` protocol)

```json
{
  "protocol": "llm-wiki-context/v1",
  "budget_tokens": 16000,
  "filters": {
    "symbol": "build_context",
    "entrypoint": "http-chat_completions"
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

**Query:** callers/callees/pages_for_symbol, budget 16000
**Ambiguous:** no | **Truncated:** callers (47 results, limit 25)

### Blast radius
- Callers (25 of 47, truncated): `handle_request` (api.py), ...
- Callees: `read_source`, `build_flow`, ...
- Fan-in/fan-out: not computed (symbol query, not file query — see dependency_neighborhood for `src/context.py` if file-level fan-in matters)
- Cycle groups: none

### Docs-to-update checklist
| Page | Status | Note |
|---|---|---|
| flows/api-handle_request.md | valid documentation defect | Behavior section describes the old context budget default |
| modules/context.md | stale generated content | Call diagram will refresh via sync |
```

## Failure modes

| Symptom | Cause | Response |
|---|---|---|
| Query returns `found: false` | Symbol/file/entrypoint name doesn't match any indexed entry | Re-check spelling/path; do not assume "not found" means "not called anywhere." |
| `ambiguous: true` | Multiple symbols share the name across files | List `matches` and ask the user which one, or analyze each separately. |
| `truncated: true` on callers/callees | More results exist than the query limit | Report the exact `bounds.callers` or `bounds.callees` total and do not describe the emitted list as complete. |
| Need file-level fan-in, only have a symbol | `dependency_neighborhood` takes a path, not a symbol | Resolve the symbol's owning file first (via `pages_for_symbol` or the callable's `file` field), then query the file. |
