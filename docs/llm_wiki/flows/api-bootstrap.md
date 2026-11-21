# bootstrap

**Entry point:** `bootstrap` (`api`)
**Source:** [wiki_operations](../modules/wiki_operations.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [engine_events](../modules/engine_events.md), [gitignore](../modules/gitignore.md), [host](../modules/host.md), and 7 more

**Complete modules touched:**

- [canonical_json](../modules/canonical_json.md)
- [engine_events](../modules/engine_events.md)
- [gitignore](../modules/gitignore.md)
- [host](../modules/host.md)
- [integrations](../modules/integrations.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [pack_interfaces](../modules/pack_interfaces.md)
- [path_policy](../modules/path_policy.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_operations](../modules/wiki_operations.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as bootstrap
    participant p1 as _pack
    participant p2 as _roots
    participant p3 as _extract
    participant p4 as _classified_sources
    participant p5 as _render
    participant p6 as _manifest
    participant p7 as _content_hashes
    participant p8 as _append_log
    participant p9 as emit
    participant p10 as WikiOperationError
    participant p11 as _write
    participant p12 as _index_markdown
    participant p13 as BootstrapResult
    participant p14 as build_gitignore_matcher
    participant p15 as SyncManifest.build_from_inventory
    participant p16 as _publish_message
    participant p17 as _rendered_entity
    participant p18 as _module_markdown
    participant p19 as _entity_markdown
    participant p20 as _captured_source_hashes
    participant p21 as _text
    participant p22 as _build_module_page_map
    participant p23 as _build_entity_occurrence_page_map
    participant p24 as is_agent_worktree_path
    participant p25 as _parse_gitignore_file
    participant p26 as _page_path
    participant p27 as _put_page_mapping
    participant p28 as hash_file
    participant p29 as sorted (src/llm_wiki_engine/wiki_operations.py:bootstrap)
    participant p30 as (…).exists
    p0->>p1: _pack
    p0->>p2: _roots
    p0->>p3: _extract
    p0->>p4: _classified_sources
    p0->>p5: _render
    p0->>p6: _manifest
    p0->>p7: _content_hashes
    p0->>p8: _append_log
    p0->>p9: emit
    p0->>p10: WikiOperationError
    p0->>p11: _write
    p0->>p12: _index_markdown
    p0->>p13: BootstrapResult
    p4->>p14: build_gitignore_matcher
    p6->>p15: SyncManifest.build_from_inventory
    p9->>p16: _publish_message
    p5->>p17: _rendered_entity
    p5->>p18: _module_markdown
    p17->>p19: _entity_markdown
    p15->>p20: _captured_source_hashes
    p17->>p21: _text
    p15->>p22: _build_module_page_map
    p15->>p23: _build_entity_occurrence_page_map
    p14->>p24: is_agent_worktree_path
    p14->>p25: _parse_gitignore_file
    p15->>p26: _page_path
    p15->>p27: _put_page_mapping
    p15->>p28: hash_file
    p0-->>p29: sorted (src/llm_wiki_engine/wiki_operations.py:bootstrap)(pages.items(...))
    p0-->>p30: (…).exists
```

> Call sequence diagram shows 30 of 396 interactions; 366 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 114 (113 omitted); unresolved 1 of 163 (162 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_engine/wiki_operations.py:_pack` | 2 | [src/llm_wiki_engine/pack_interfaces.py](../modules/pack_interfaces.md) | internal | 1 |
| `src/llm_wiki_engine/pack_interfaces.py:active_pack` | 3 | - | unresolved | 1 |
| `src/llm_wiki_engine/wiki_operations.py:_pack` | 2 | [src/llm_wiki_engine/wiki_operations.py](../modules/wiki_operations.md) | internal | 1 |
| `src/llm_wiki_engine/wiki_operations.py:_roots` | 6 | - | external | 2 |
| `src/llm_wiki_engine/wiki_operations.py:_roots` | 6 | - | unresolved | 1 |
| `src/llm_wiki_engine/wiki_operations.py:_roots` | 6 | [src/llm_wiki_engine/wiki_operations.py](../modules/wiki_operations.md) | internal | 1 |
| `src/llm_wiki_engine/wiki_operations.py:_extract` | 13 | - | unresolved | 9 |
| `src/llm_wiki_engine/wiki_operations.py:_extract` | 13 | - | external | 9 |
> Omission summary shows 8 of 114 groups; 106 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 120; effect analysis evaluated: 77, partial: 3, unavailable: 40. Counts include steps omitted from the displayed trace.

Collector observations for 80 source steps with known totals: observed: 337, emitted: 308, omitted: 29. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `bootstrap` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `_pack` | `available` | `evaluated` | `available` | `1` | `1` | `0` |
| `active_pack` | `available` | `evaluated` | `available` | `1` | `1` | `0` |
| `_ACTIVE_PACK.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `WikiOperationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_roots` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `Path (src/llm_wiki_engine/wiki_operations.py:_roots)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `Path (src/llm_wiki_engine/wiki_operations.py:_roots)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `source.is_dir` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `WikiOperationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `(…).exists` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `WikiOperationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. bootstrap"]
    s2["2. _pack"]
    s3["3. active_pack"]
    s4["4. _ACTIVE_PACK.get"]
    s5["5. WikiOperationError"]
    s6["6. _roots"]
    s7["7. Path (src/llm_wiki_engine/wiki_operations.py:_roots)"]
    s8["8. Path (src/llm_wiki_engine/wiki_operations.py:_roots)"]
    s9["9. source.is_dir"]
    s10["10. WikiOperationError"]
    s11["11. (…).exists"]
    s12["12. WikiOperationError"]
    s1 -->|"_pack(data not statically known)"| s2
    s2 -->|"active_pack(data not statically known)"| s3
    s3 -. "_ACTIVE_PACK.get(data not statically known)" .-> s4
    s2 -->|"WikiOperationError('no domain pack is active; run inside an engine operation')"| s5
    s1 -->|"_roots(request)"| s6
    s6 -. "Path (src/llm_wiki_engine/wiki_operations.py:_roots)(request.source_root)" .-> s7
    s6 -. "Path (src/llm_wiki_engine/wiki_operations.py:_roots)(request.wiki_root)" .-> s8
    s6 -. "source.is_dir(data not statically known)" .-> s9
    s6 -->|"WikiOperationError(...)"| s10
    s1 -. "(…).exists(data not statically known)" .-> s11
    s1 -->|"WikiOperationError(...)"| s12
    click s1 "../modules/wiki_operations.md"
    click s2 "../modules/wiki_operations.md"
    click s3 "../modules/pack_interfaces.md"
    click s5 "../modules/wiki_operations.md"
    click s6 "../modules/wiki_operations.md"
    click s10 "../modules/wiki_operations.md"
    click s12 "../modules/wiki_operations.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `bootstrap` | `request: BootstrapRequest` | `INDEX_PAGE` | - | `BootstrapResult(...)` |
| `_pack` | - | - | - | `pack` |
| `active_pack` | - | - | - | `_ACTIVE_PACK.get(...)` |
| `_ACTIVE_PACK.get` | - | - | - | - |
| `WikiOperationError` | - | - | - | - |
| `_roots` | `request: Any` | - | - | `(...)` |
| `Path (src/llm_wiki_engine/wiki_operations.py:_roots)` | - | - | - | - |
| `Path (src/llm_wiki_engine/wiki_operations.py:_roots)` | - | - | - | - |
| `source.is_dir` | - | - | - | - |
| `WikiOperationError` | - | - | - | - |
| `(…).exists` | - | - | - | - |
| `WikiOperationError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| bootstrap | _pack | 346 | `_pack(data not statically known)` |
| _pack | active_pack | 119 | `active_pack(data not statically known)` |
| active_pack | _ACTIVE_PACK.get | 643 | `_ACTIVE_PACK.get(data not statically known)` |
| _pack | WikiOperationError | 121 | `WikiOperationError('no domain pack is active; run inside an engine operation')` |
| bootstrap | _roots | 347 | `_roots(request)` |
| _roots | Path (src/llm_wiki_engine/wiki_operations.py:_roots) | 126 | `Path(request.source_root)` |
| _roots | Path (src/llm_wiki_engine/wiki_operations.py:_roots) | 127 | `Path(request.wiki_root)` |
| _roots | source.is_dir | 128 | `source.is_dir(data not statically known)` |
| _roots | WikiOperationError | 129 | `WikiOperationError(...)` |
| bootstrap | (…).exists | 348 | `(wiki / MANIFEST_FILENAME).exists(data not statically known)` |
| bootstrap | WikiOperationError | 349 | `WikiOperationError(...)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `active_pack` | `_ACTIVE_PACK.get` | 643 |
| unresolved_call | `_roots` | `source.is_dir` | 128 |
| unresolved_call | `bootstrap` | `(wiki / MANIFEST_FILENAME).exists` | 348 |
| step_limit | `bootstrap` | `first 12 steps` | 0 |
| truncated_flow | `bootstrap` | `depth limit` | 0 |

## Behavior

This flow starts at `bootstrap` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
