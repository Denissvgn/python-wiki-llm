# current_infrastructure_bases

**Entry point:** `current_infrastructure_bases` (`api`)
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
    participant p0 as current_infrastructure_bases
    participant p1 as build_infrastructure_page_map
    participant p2 as sorted
    participant p3 as infrastructure_page_name
    participant p4 as replace
    participant p5 as append
    participant p6 as setdefault
    participant p7 as items
    participant p8 as len
    participant p9 as removeprefix
    participant p10 as hash_json
    participant p11 as sha256_bytes
    participant p12 as hexdigest
    participant p13 as sha256
    participant p14 as canonical_json_bytes
    participant p15 as encode
    participant p16 as canonical_json_text
    participant p17 as dumps
    participant p18 as build_infrastructure_observation_basis
    participant p19 as _validate_source_path
    participant p20 as require_repository_relative_path
    participant p21 as isinstance
    participant p22 as strip
    participant p23 as any
    participant p24 as ord
    participant p25 as startswith
    p0->>p1: build_infrastructure_page_map
    p1-->>p2: sorted
    p1->>p3: infrastructure_page_name
    p3-->>p4: replace
    p3-->>p4: replace
    p3-->>p4: replace
    p1-->>p5: append
    p1-->>p6: setdefault
    p1-->>p2: sorted
    p1-->>p7: items
    p1-->>p8: len
    p1-->>p9: removeprefix
    p1->>p10: hash_json
    p10->>p11: sha256_bytes
    p11-->>p12: hexdigest
    p11-->>p13: sha256
    p10->>p14: canonical_json_bytes
    p14-->>p15: encode
    p14->>p16: canonical_json_text
    p16-->>p17: dumps
    p0->>p18: build_infrastructure_observation_basis
    p18->>p19: _validate_source_path
    p19->>p20: require_repository_relative_path
    p20-->>p21: isinstance
    p20-->>p22: strip
    p20-->>p23: any
    p20-->>p24: ord
    p20-->>p24: ord
    p20-->>p25: startswith
    p20-->>p25: startswith
```

> Call sequence diagram shows 30 of 115 interactions; 85 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. current_infrastructure_bases"]
    s2["2. build_infrastructure_page_map"]
    s3["3. sorted"]
    s4["4. infrastructure_page_name"]
    s5["5. replace"]
    s6["6. replace"]
    s7["7. replace"]
    s8["8. append"]
    s9["9. setdefault"]
    s10["10. sorted"]
    s11["11. items"]
    s12["12. len"]
    s1 -->|"build_infrastructure_page_map(inventory)"| s2
    s2 -. "sorted(source_paths)" .-> s3
    s2 -->|"infrastructure_page_name(source_path)"| s4
    s4 -. "source_path.replace('\\', '/').replace('/', '_').replace('.', '_')" .-> s5
    s4 -. "source_path.replace('\\', '/').replace('/', '_')" .-> s6
    s4 -. "source_path.replace('\\', '/')" .-> s7
    s2 -. "by_stem.setdefault(stem, []).append(source_path)" .-> s8
    s2 -. "by_stem.setdefault(stem, [...])" .-> s9
    s2 -. "sorted(by_stem.items(...))" .-> s10
    s2 -. "by_stem.items(data not statically known)" .-> s11
    s2 -. "len(grouped_paths)" .-> s12
    click s1 "../modules/infrastructure_sync.md"
    click s2 "../modules/infrastructure_sync.md"
    click s4 "../modules/infrastructure_inventory.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `current_infrastructure_bases` | `snapshot: SourceSnapshot`, `inventory: Mapping[str, Mapping[str, object]]` | `INFRASTRUCTURE_EXTRACTOR_REF` | - | `...` |
| `build_infrastructure_page_map` | `source_paths: Mapping[str, object] \| tuple[str, ...] \| list[str] \| set[str]` | - | `result[...]` | `result` |
| `sorted` | - | - | - | - |
| `infrastructure_page_name` | `source_path: str` | - | - | `...` |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `append` | - | - | - | - |
| `setdefault` | - | - | - | - |
| `sorted` | - | - | - | - |
| `items` | - | - | - | - |
| `len` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| current_infrastructure_bases | build_infrastructure_page_map | 296 | `build_infrastructure_page_map(inventory)` |
| build_infrastructure_page_map | sorted | 42 | `sorted(source_paths)` |
| build_infrastructure_page_map | infrastructure_page_name | 45 | `infrastructure_page_name(source_path)` |
| infrastructure_page_name | replace | 28 | `source_path.replace('\\', '/').replace('/', '_').replace('.', '_')` |
| infrastructure_page_name | replace | 28 | `source_path.replace('\\', '/').replace('/', '_')` |
| infrastructure_page_name | replace | 28 | `source_path.replace('\\', '/')` |
| build_infrastructure_page_map | append | 46 | `by_stem.setdefault(stem, []).append(source_path)` |
| build_infrastructure_page_map | setdefault | 46 | `by_stem.setdefault(stem, [...])` |
| build_infrastructure_page_map | sorted | 48 | `sorted(by_stem.items(...))` |
| build_infrastructure_page_map | items | 48 | `by_stem.items(data not statically known)` |
| build_infrastructure_page_map | len | 49 | `len(grouped_paths)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_infrastructure_page_map` | `sorted` | 42 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace('/', '_').replace` | 28 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace` | 28 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace` | 28 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.setdefault(stem, []).append` | 46 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.setdefault` | 46 |
| unresolved_call | `build_infrastructure_page_map` | `sorted` | 48 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.items` | 48 |
| step_limit | `current_infrastructure_bases` | `first 12 steps` | 0 |

## Behavior

This flow starts at `current_infrastructure_bases` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
