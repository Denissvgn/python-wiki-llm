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

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_infrastructure_sync_plan
    participant p1 as deepcopy
    participant p2 as dict
    participant p3 as sorted
    participant p4 as items
    participant p5 as build_infrastructure_page_map
    participant p6 as infrastructure_page_name
    participant p7 as replace
    participant p8 as append
    participant p9 as setdefault
    participant p10 as len
    participant p11 as removeprefix
    participant p12 as hash_json
    participant p13 as sha256_bytes
    participant p14 as hexdigest
    participant p15 as sha256
    participant p16 as canonical_json_bytes
    participant p17 as encode
    participant p18 as canonical_json_text
    participant p19 as dumps
    participant p20 as _prior_infrastructure_state
    participant p21 as isinstance
    participant p22 as InfrastructureSyncError
    participant p23 as get
    p0-->>p1: deepcopy
    p0-->>p2: dict
    p0-->>p3: sorted
    p0-->>p4: items
    p0->>p5: build_infrastructure_page_map
    p5-->>p3: sorted
    p5->>p6: infrastructure_page_name
    p6-->>p7: replace
    p6-->>p7: replace
    p6-->>p7: replace
    p5-->>p8: append
    p5-->>p9: setdefault
    p5-->>p3: sorted
    p5-->>p4: items
    p5-->>p10: len
    p5-->>p11: removeprefix
    p5->>p12: hash_json
    p12->>p13: sha256_bytes
    p13-->>p14: hexdigest
    p13-->>p15: sha256
    p12->>p16: canonical_json_bytes
    p16-->>p17: encode
    p16->>p18: canonical_json_text
    p18-->>p19: dumps
    p0->>p20: _prior_infrastructure_state
    p20-->>p21: isinstance
    p20-->>p21: isinstance
    p20->>p22: InfrastructureSyncError
    p20-->>p23: get
    p20->>p22: InfrastructureSyncError
```

> Call sequence diagram shows 30 of 270 interactions; 240 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_infrastructure_sync_plan"]
    s2["2. deepcopy"]
    s3["3. dict"]
    s4["4. sorted"]
    s5["5. items"]
    s6["6. build_infrastructure_page_map"]
    s7["7. sorted"]
    s8["8. infrastructure_page_name"]
    s9["9. replace"]
    s10["10. replace"]
    s11["11. replace"]
    s12["12. append"]
    s1 -. "deepcopy(dict(...))" .-> s2
    s1 -. "dict(info)" .-> s3
    s1 -. "sorted(inventory.items(...))" .-> s4
    s1 -. "inventory.items(data not statically known)" .-> s5
    s1 -->|"build_infrastructure_page_map(normalized_inventory)"| s6
    s6 -. "sorted(source_paths)" .-> s7
    s6 -->|"infrastructure_page_name(source_path)"| s8
    s8 -. "source_path.replace('\\', '/').replace('/', '_').replace('.', '_')" .-> s9
    s8 -. "source_path.replace('\\', '/').replace('/', '_')" .-> s10
    s8 -. "source_path.replace('\\', '/')" .-> s11
    s6 -. "by_stem.setdefault(stem, []).append(source_path)" .-> s12
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
| `deepcopy` | - | - | - | - |
| `dict` | - | - | - | - |
| `sorted` | - | - | - | - |
| `items` | - | - | - | - |
| `build_infrastructure_page_map` | `source_paths: Mapping[str, object] \| tuple[str, ...] \| list[str] \| set[str]` | - | `result[...]` | `result` |
| `sorted` | - | - | - | - |
| `infrastructure_page_name` | `source_path: str` | - | - | `...` |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `append` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_infrastructure_sync_plan | deepcopy | 628 | `deepcopy(dict(...))` |
| build_infrastructure_sync_plan | dict | 628 | `dict(info)` |
| build_infrastructure_sync_plan | sorted | 629 | `sorted(inventory.items(...))` |
| build_infrastructure_sync_plan | items | 629 | `inventory.items(data not statically known)` |
| build_infrastructure_sync_plan | build_infrastructure_page_map | 631 | `build_infrastructure_page_map(normalized_inventory)` |
| build_infrastructure_page_map | sorted | 42 | `sorted(source_paths)` |
| build_infrastructure_page_map | infrastructure_page_name | 45 | `infrastructure_page_name(source_path)` |
| infrastructure_page_name | replace | 28 | `source_path.replace('\\', '/').replace('/', '_').replace('.', '_')` |
| infrastructure_page_name | replace | 28 | `source_path.replace('\\', '/').replace('/', '_')` |
| infrastructure_page_name | replace | 28 | `source_path.replace('\\', '/')` |
| build_infrastructure_page_map | append | 46 | `by_stem.setdefault(stem, []).append(source_path)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `deselected_records.update` | `build_infrastructure_sync_plan` | 655 |
| mutation | `tombstones.pop` | `build_infrastructure_sync_plan` | 697 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_infrastructure_sync_plan` | `deepcopy` | 628 |
| unresolved_call | `build_infrastructure_sync_plan` | `sorted` | 629 |
| unresolved_call | `build_infrastructure_sync_plan` | `inventory.items` | 629 |
| unresolved_call | `build_infrastructure_page_map` | `sorted` | 42 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace('/', '_').replace` | 28 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace` | 28 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace` | 28 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.setdefault(stem, []).append` | 46 |
| step_limit | `build_infrastructure_sync_plan` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_infrastructure_sync_plan` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
