# build_infrastructure_sync_plan

**Entry point:** `build_infrastructure_sync_plan` (`api`)
**Source:** [infrastructure_sync](../modules/infrastructure_sync.md)
**Modules touched:** [infrastructure_inventory](../modules/infrastructure_inventory.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 1 more

**Complete modules touched:**

- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_infrastructure_sync_plan
    participant p1 as deepcopy (src/llm_wiki_cli/services…_infrastructure_sync_plan)
    participant p2 as dict (src/llm_wiki_cli/services…_infrastructure_sync_plan)
    participant p3 as sorted (src/llm_wiki_cli/services…_infrastructure_sync_plan)
    participant p4 as inventory.items
    participant p5 as build_infrastructure_page_map
    participant p6 as _prior_infrastructure_state
    participant p7 as _record_mapping
    participant p8 as prior_state.get (src/llm_wiki_cli/services…_infrastructure_sync_plan)
    participant p9 as raw_prior_sources.items
    participant p10 as snapshot.path_is_effectively_selected (src/llm_wiki_cli/services…_infrastructure_sync_plan)
    participant p11 as _selected_prior_tombstones
    participant p12 as deselected_records.update
    participant p13 as _deselection_only_state
    participant p14 as _source_record
    participant p15 as normalized_inventory.items
    participant p16 as set (src/llm_wiki_cli/services…_infrastructure_sync_plan)
    participant p17 as _detect_moves
    participant p18 as moved.values
    participant p19 as _unsupported_yaml_records
    participant p20 as _candidate_roots
    participant p21 as tombstones.pop
    p0-->>p1: deepcopy (src/llm_wiki_cli/services…_infrastructure_sync_plan)(dict(...))
    p0-->>p2: dict (src/llm_wiki_cli/services…_infrastructure_sync_plan)(info)
    p0-->>p3: sorted (src/llm_wiki_cli/services…_infrastructure_sync_plan)(inventory.items(...))
    p0-->>p4: inventory.items
    p0->>p5: build_infrastructure_page_map
    p0->>p6: _prior_infrastructure_state
    p0->>p7: _record_mapping
    p0-->>p8: prior_state.get (src/llm_wiki_cli/services…_infrastructure_sync_plan)('sources')
    p0->>p7: _record_mapping
    p0-->>p8: prior_state.get (src/llm_wiki_cli/services…_infrastructure_sync_plan)('tombstones')
    p0-->>p9: raw_prior_sources.items
    p0-->>p10: snapshot.path_is_effectively_selected (src/llm_wiki_cli/services…_infrastructure_sync_plan)(source_path)
    p0->>p11: _selected_prior_tombstones
    p0-->>p12: deselected_records.update(...)
    p0-->>p9: raw_prior_sources.items
    p0-->>p10: snapshot.path_is_effectively_selected (src/llm_wiki_cli/services…_infrastructure_sync_plan)(source_path)
    p0->>p13: _deselection_only_state
    p0-->>p1: deepcopy (src/llm_wiki_cli/services…_infrastructure_sync_plan)(selected_prior_tombstones)
    p0->>p14: _source_record
    p0-->>p15: normalized_inventory.items
    p0-->>p16: set (src/llm_wiki_cli/services…_infrastructure_sync_plan)(prior_sources)
    p0-->>p16: set (src/llm_wiki_cli/services…_infrastructure_sync_plan)(current_sources)
    p0->>p17: _detect_moves
    p0-->>p16: set (src/llm_wiki_cli/services…_infrastructure_sync_plan)(moved)
    p0-->>p16: set (src/llm_wiki_cli/services…_infrastructure_sync_plan)(moved.values(...))
    p0-->>p18: moved.values
    p0->>p19: _unsupported_yaml_records
    p0->>p20: _candidate_roots
    p0-->>p21: tombstones.pop(source_path, None)
    p0-->>p3: sorted (src/llm_wiki_cli/services…_infrastructure_sync_plan)(...)
```

> Call sequence diagram shows 30 of 284 interactions; 254 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 9 of 119 (110 omitted); unresolved 11 of 88 (77 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/infrastructure_sync.py:build_infrastructure_page_map` | 6 | - | external | 3 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:build_infrastructure_page_map` | 6 | [src/llm_wiki_cli/services/infrastructure_inventory.py](../modules/infrastructure_inventory.md) | internal | 1 |
| `src/llm_wiki_cli/services/infrastructure_inventory.py:infrastructure_page_name` | 8 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:build_infrastructure_page_map` | 6 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:build_infrastructure_page_map` | 6 | [src/llm_wiki_cli/services/knowledge_evidence.py](../modules/knowledge_evidence.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:hash_json` | 18 | [src/llm_wiki_cli/services/knowledge_evidence.py](../modules/knowledge_evidence.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 19 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 19 | - | external | 1 |
> Omission summary shows 8 of 69 groups; 61 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_infrastructure_sync_plan"]
    s2["2. deepcopy (src/llm_wiki_cli/services…_infrastructure_sync_plan)"]
    s3["3. dict (src/llm_wiki_cli/services…_infrastructure_sync_plan)"]
    s4["4. sorted (src/llm_wiki_cli/services…_infrastructure_sync_plan)"]
    s5["5. inventory.items"]
    s6["6. build_infrastructure_page_map"]
    s7["7. sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)"]
    s8["8. infrastructure_page_name"]
    s9["9. source_path.replace(…).replace(…).replace"]
    s10["10. source_path.replace(…).replace"]
    s11["11. source_path.replace"]
    s12["12. by_stem.setdefault(…).append"]
    s1 -. "deepcopy (src/llm_wiki_cli/services…_infrastructure_sync_plan)(dict(...))" .-> s2
    s1 -. "dict (src/llm_wiki_cli/services…_infrastructure_sync_plan)(info)" .-> s3
    s1 -. "sorted (src/llm_wiki_cli/services…_infrastructure_sync_plan)(inventory.items(...))" .-> s4
    s1 -. "inventory.items(data not statically known)" .-> s5
    s1 -->|"build_infrastructure_page_map(normalized_inventory)"| s6
    s6 -. "sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)(source_paths)" .-> s7
    s6 -->|"infrastructure_page_name(source_path)"| s8
    s8 -. "source_path.replace(…).replace(…).replace('.', '_')" .-> s9
    s8 -. "source_path.replace(…).replace('/', '_')" .-> s10
    s8 -. "source_path.replace('\\', '/')" .-> s11
    s6 -. "by_stem.setdefault(…).append(source_path)" .-> s12
    b0["mutation deselected_records.update"]
    s1 -. "mutation deselected_records.update" .-> b0
    b1["mutation tombstones.pop"]
    s1 -. "mutation tombstones.pop" .-> b1
    click s1 "../modules/infrastructure_sync.md"
    click s6 "../modules/infrastructure_sync.md"
    click s8 "../modules/infrastructure_inventory.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_infrastructure_sync_plan` | `snapshot: SourceSnapshot`, `inventory: Mapping[str, Mapping[str, object]]`, `generation_inputs: Mapping[str, object] \| None` | `INFRASTRUCTURE_SYNC_SCHEMA_VERSION` | `tombstones[...]`, `tombstones[...]` | `InfrastructureSyncPlan(...)` |
| `deepcopy (src/llm_wiki_cli/services…_infrastructure_sync_plan)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…_infrastructure_sync_plan)` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…_infrastructure_sync_plan)` | - | - | - | - |
| `inventory.items` | - | - | - | - |
| `build_infrastructure_page_map` | `source_paths: Mapping[str, object] \| tuple[str, ...] \| list[str] \| set[str]` | - | `result[...]` | `result` |
| `sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)` | - | - | - | - |
| `infrastructure_page_name` | `source_path: str` | - | - | `...` |
| `source_path.replace(…).replace(…).replace` | - | - | - | - |
| `source_path.replace(…).replace` | - | - | - | - |
| `source_path.replace` | - | - | - | - |
| `by_stem.setdefault(…).append` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_infrastructure_sync_plan | deepcopy (src/llm_wiki_cli/services…_infrastructure_sync_plan) | 628 | `deepcopy(dict(...))` |
| build_infrastructure_sync_plan | dict (src/llm_wiki_cli/services…_infrastructure_sync_plan) | 628 | `dict(info)` |
| build_infrastructure_sync_plan | sorted (src/llm_wiki_cli/services…_infrastructure_sync_plan) | 629 | `sorted(inventory.items(...))` |
| build_infrastructure_sync_plan | inventory.items | 629 | `inventory.items(data not statically known)` |
| build_infrastructure_sync_plan | build_infrastructure_page_map | 631 | `build_infrastructure_page_map(normalized_inventory)` |
| build_infrastructure_page_map | sorted (src/llm_wiki_cli/services…d_infrastructure_page_map) | 42 | `sorted(source_paths)` |
| build_infrastructure_page_map | infrastructure_page_name | 45 | `infrastructure_page_name(source_path)` |
| infrastructure_page_name | source_path.replace(…).replace(…).replace | 28 | `source_path.replace('\\', '/').replace('/', '_').replace('.', '_')` |
| infrastructure_page_name | source_path.replace(…).replace | 28 | `source_path.replace('\\', '/').replace('/', '_')` |
| infrastructure_page_name | source_path.replace | 28 | `source_path.replace('\\', '/')` |
| build_infrastructure_page_map | by_stem.setdefault(…).append | 46 | `by_stem.setdefault(stem, []).append(source_path)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `deselected_records.update` | `build_infrastructure_sync_plan` | 655 |
| mutation | `tombstones.pop` | `build_infrastructure_sync_plan` | 697 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_infrastructure_sync_plan` | `deepcopy` | 628 |
| external_call | `build_infrastructure_sync_plan` | `sorted` | 629 |
| unresolved_call | `build_infrastructure_sync_plan` | `inventory.items` | 629 |
| external_call | `build_infrastructure_page_map` | `sorted` | 42 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace('/', '_').replace` | 28 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace` | 28 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace` | 28 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.setdefault(stem, []).append` | 46 |
| step_limit | `build_infrastructure_sync_plan` | `first 12 steps` | 0 |
| truncated_flow | `build_infrastructure_sync_plan` | `depth limit` | 0 |

## Behavior

This flow starts at `build_infrastructure_sync_plan` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
