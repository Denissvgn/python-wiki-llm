# build_infrastructure_page_map

**Entry point:** `build_infrastructure_page_map` (`api`)
**Source:** [infrastructure_sync](../modules/infrastructure_sync.md)
**Modules touched:** [infrastructure_inventory](../modules/infrastructure_inventory.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_infrastructure_page_map
    participant p1 as sorted
    participant p2 as infrastructure_page_name
    participant p3 as by_stem.setdefault(…).append
    participant p4 as by_stem.setdefault
    participant p5 as by_stem.items
    participant p6 as len
    participant p7 as hash_json(…).removeprefix
    participant p8 as hash_json
    participant p9 as source_path.replace(…).replace(…).replace
    participant p10 as sha256_bytes
    participant p11 as source_path.replace(…).replace
    participant p12 as canonical_json_bytes
    participant p13 as source_path.replace
    participant p14 as hashlib.sha256(…).hexdigest
    participant p15 as canonical_json_text(…).encode
    participant p16 as hashlib.sha256
    participant p17 as canonical_json_text
    participant p18 as json.dumps
    p0-->>p1: sorted(source_paths)
    p0->>p2: infrastructure_page_name
    p0-->>p3: by_stem.setdefault(…).append(source_path)
    p0-->>p4: by_stem.setdefault(stem, [...])
    p0-->>p1: sorted(by_stem.items(...))
    p0-->>p5: by_stem.items
    p0-->>p6: len(grouped_paths)
    p0-->>p7: hash_json(…).removeprefix('sha256:')
    p0->>p8: hash_json
    p2-->>p9: source_path.replace(…).replace(…).replace('.', '_')
    p8->>p10: sha256_bytes
    p2-->>p11: source_path.replace(…).replace('/', '_')
    p8->>p12: canonical_json_bytes
    p2-->>p13: source_path.replace('\\', '/')
    p10-->>p14: hashlib.sha256(…).hexdigest
    p12-->>p15: canonical_json_text(…).encode('utf-8')
    p10-->>p16: hashlib.sha256(value)
    p12->>p17: canonical_json_text
    p17-->>p18: json.dumps(value, ensure_ascii=False, separators=(...), sort_keys=True, allow_nan=False)
```

> Call sequence diagram shows 19 of 19 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 5 (0 omitted); unresolved 9 of 9 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
