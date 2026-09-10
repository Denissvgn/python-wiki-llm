# build_infrastructure_page_map

**Entry point:** `build_infrastructure_page_map` (`api`)
**Source:** [infrastructure_sync](../modules/infrastructure_sync.md)
**Modules touched:** [infrastructure_inventory](../modules/infrastructure_inventory.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_infrastructure_page_map
    participant p1 as sorted
    participant p2 as infrastructure_page_name
    participant p3 as source_path.replace(…).replace(…).replace
    participant p4 as source_path.replace(…).replace
    participant p5 as source_path.replace
    participant p6 as by_stem.setdefault(…).append
    participant p7 as by_stem.setdefault
    participant p8 as by_stem.items
    participant p9 as len
    participant p10 as hash_json(…).removeprefix
    participant p11 as hash_json
    participant p12 as sha256_bytes
    participant p13 as hashlib.sha256(…).hexdigest
    participant p14 as hashlib.sha256
    participant p15 as canonical_json_bytes
    participant p16 as canonical_json_text(…).encode
    participant p17 as canonical_json_text
    participant p18 as json.dumps
    p0-->>p1: sorted
    p0->>p2: infrastructure_page_name
    p2-->>p3: source_path.replace(…).replace(…).replace
    p2-->>p4: source_path.replace(…).replace
    p2-->>p5: source_path.replace
    p0-->>p6: by_stem.setdefault(…).append
    p0-->>p7: by_stem.setdefault
    p0-->>p1: sorted
    p0-->>p8: by_stem.items
    p0-->>p9: len
    p0-->>p10: hash_json(…).removeprefix
    p0->>p11: hash_json
    p11->>p12: sha256_bytes
    p12-->>p13: hashlib.sha256(…).hexdigest
    p12-->>p14: hashlib.sha256
    p11->>p15: canonical_json_bytes
    p15-->>p16: canonical_json_text(…).encode
    p15->>p17: canonical_json_text
    p17-->>p18: json.dumps
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_infrastructure_page_map"]
    s2["2. sorted"]
    s3["3. infrastructure_page_name"]
    s4["4. source_path.replace(…).replace(…).replace"]
    s5["5. source_path.replace(…).replace"]
    s6["6. source_path.replace"]
    s7["7. by_stem.setdefault(…).append"]
    s8["8. by_stem.setdefault"]
    s9["9. sorted"]
    s10["10. by_stem.items"]
    s11["11. len"]
    s12["12. hash_json(…).removeprefix"]
    s1 -. "sorted(source_paths)" .-> s2
    s1 -->|"infrastructure_page_name(source_path)"| s3
    s3 -. "source_path.replace(…).replace(…).replace('.', '_')" .-> s4
    s3 -. "source_path.replace(…).replace('/', '_')" .-> s5
    s3 -. "source_path.replace('\\', '/')" .-> s6
    s1 -. "by_stem.setdefault(…).append(source_path)" .-> s7
    s1 -. "by_stem.setdefault(stem, [...])" .-> s8
    s1 -. "sorted(by_stem.items(...))" .-> s9
    s1 -. "by_stem.items(data not statically known)" .-> s10
    s1 -. "len(grouped_paths)" .-> s11
    s1 -. "hash_json(…).removeprefix('sha256:')" .-> s12
    click s1 "../modules/infrastructure_sync.md"
    click s3 "../modules/infrastructure_inventory.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_infrastructure_page_map` | `source_paths: Mapping[str, object] \| tuple[str, ...] \| list[str] \| set[str]` | - | `result[...]` | `result` |
| `sorted` | - | - | - | - |
| `infrastructure_page_name` | `source_path: str` | - | - | `...` |
| `source_path.replace(…).replace(…).replace` | - | - | - | - |
| `source_path.replace(…).replace` | - | - | - | - |
| `source_path.replace` | - | - | - | - |
| `by_stem.setdefault(…).append` | - | - | - | - |
| `by_stem.setdefault` | - | - | - | - |
| `sorted` | - | - | - | - |
| `by_stem.items` | - | - | - | - |
| `len` | - | - | - | - |
| `hash_json(…).removeprefix` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_infrastructure_page_map | sorted | 42 | `sorted(source_paths)` |
| build_infrastructure_page_map | infrastructure_page_name | 45 | `infrastructure_page_name(source_path)` |
| infrastructure_page_name | source_path.replace(…).replace(…).replace | 28 | `source_path.replace('\\', '/').replace('/', '_').replace('.', '_')` |
| infrastructure_page_name | source_path.replace(…).replace | 28 | `source_path.replace('\\', '/').replace('/', '_')` |
| infrastructure_page_name | source_path.replace | 28 | `source_path.replace('\\', '/')` |
| build_infrastructure_page_map | by_stem.setdefault(…).append | 46 | `by_stem.setdefault(stem, []).append(source_path)` |
| build_infrastructure_page_map | by_stem.setdefault | 46 | `by_stem.setdefault(stem, [...])` |
| build_infrastructure_page_map | sorted | 48 | `sorted(by_stem.items(...))` |
| build_infrastructure_page_map | by_stem.items | 48 | `by_stem.items(data not statically known)` |
| build_infrastructure_page_map | len | 49 | `len(grouped_paths)` |
| build_infrastructure_page_map | hash_json(…).removeprefix | 53 | `hash_json(source_path).removeprefix('sha256:')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_infrastructure_page_map` | `sorted` | 42 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace('/', '_').replace` | 28 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace` | 28 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace` | 28 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.setdefault(stem, []).append` | 46 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.setdefault` | 46 |
| external_call | `build_infrastructure_page_map` | `sorted` | 48 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.items` | 48 |
| unresolved_call | `build_infrastructure_page_map` | `hash_json(source_path).removeprefix` | 53 |
| step_limit | `build_infrastructure_page_map` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_infrastructure_page_map` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
