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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as current_infrastructure_bases
    participant p1 as build_infrastructure_page_map
    participant p2 as build_infrastructure_observation_basis
    participant p3 as _source_hash
    participant p4 as _observation_hash
    participant p5 as sorted (src/llm_wiki_cli/services…rent_infrastructure_bases)
    participant p6 as inventory.items
    participant p7 as sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)
    participant p8 as _validate_source_path
    participant p9 as snapshot.captured_content_hashes.get
    participant p10 as hash_json
    participant p11 as infrastructure_page_name
    participant p12 as _validate_hash
    participant p13 as is_valid_sha256
    participant p14 as str
    participant p15 as by_stem.setdefault(…).append
    participant p16 as InfrastructureSyncError
    participant p17 as info.get
    participant p18 as by_stem.setdefault
    participant p19 as _validate_extractor_ref
    participant p20 as dict
    participant p21 as ConceptObservationBasis
    participant p22 as by_stem.items
    participant p23 as len (src/llm_wiki_cli/services…d_infrastructure_page_map)
    participant p24 as hash_json(…).removeprefix
    participant p25 as source_path.replace(…).replace(…).replace
    participant p26 as sha256_bytes
    participant p27 as require_repository_relative_path
    p0->>p1: build_infrastructure_page_map
    p0->>p2: build_infrastructure_observation_basis
    p0->>p3: _source_hash
    p0->>p4: _observation_hash
    p0-->>p5: sorted (src/llm_wiki_cli/services…rent_infrastructure_bases)(inventory.items(...))
    p0-->>p6: inventory.items
    p1-->>p7: sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)(source_paths)
    p2->>p8: _validate_source_path
    p3-->>p9: snapshot.captured_content_hashes.get(source_path)
    p4->>p10: hash_json
    p1->>p11: infrastructure_page_name
    p2->>p12: _validate_hash
    p3->>p13: is_valid_sha256
    p4-->>p14: str(...)
    p1-->>p15: by_stem.setdefault(…).append(source_path)
    p2->>p12: _validate_hash
    p3->>p16: InfrastructureSyncError
    p4-->>p17: info.get('type')
    p1-->>p18: by_stem.setdefault(stem, [...])
    p2->>p19: _validate_extractor_ref
    p4-->>p20: dict(info)
    p1-->>p7: sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)(by_stem.items(...))
    p2->>p21: ConceptObservationBasis
    p1-->>p22: by_stem.items
    p1-->>p23: len (src/llm_wiki_cli/services…d_infrastructure_page_map)(grouped_paths)
    p1-->>p24: hash_json(…).removeprefix('sha256:')
    p1->>p10: hash_json
    p11-->>p25: source_path.replace(…).replace(…).replace('.', '_')
    p10->>p26: sha256_bytes
    p8->>p27: require_repository_relative_path
```

> Call sequence diagram shows 30 of 130 interactions; 100 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 6 of 41 (35 omitted); unresolved 8 of 41 (33 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/infrastructure_inventory.py:infrastructure_page_name` | 4 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 15 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 15 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:hash_json` | 14 | [src/llm_wiki_cli/services/knowledge_evidence.py](../modules/knowledge_evidence.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:canonical_json_bytes` | 18 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:canonical_json_bytes` | 18 | [src/llm_wiki_cli/services/knowledge_evidence.py](../modules/knowledge_evidence.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:canonical_json_text` | 20 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 24 | - | external | 7 |
> Omission summary shows 8 of 40 groups; 32 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. current_infrastructure_bases"]
    s2["2. build_infrastructure_page_map"]
    s3["3. sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)"]
    s4["4. infrastructure_page_name"]
    s5["5. source_path.replace(…).replace(…).replace"]
    s6["6. source_path.replace(…).replace"]
    s7["7. source_path.replace"]
    s8["8. by_stem.setdefault(…).append"]
    s9["9. by_stem.setdefault"]
    s10["10. sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)"]
    s11["11. by_stem.items"]
    s12["12. len (src/llm_wiki_cli/services…d_infrastructure_page_map)"]
    s1 -->|"build_infrastructure_page_map(inventory)"| s2
    s2 -. "sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)(source_paths)" .-> s3
    s2 -->|"infrastructure_page_name(source_path)"| s4
    s4 -. "source_path.replace(…).replace(…).replace('.', '_')" .-> s5
    s4 -. "source_path.replace(…).replace('/', '_')" .-> s6
    s4 -. "source_path.replace('\\', '/')" .-> s7
    s2 -. "by_stem.setdefault(…).append(source_path)" .-> s8
    s2 -. "by_stem.setdefault(stem, [...])" .-> s9
    s2 -. "sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)(by_stem.items(...))" .-> s10
    s2 -. "by_stem.items(data not statically known)" .-> s11
    s2 -. "len (src/llm_wiki_cli/services…d_infrastructure_page_map)(grouped_paths)" .-> s12
    click s1 "../modules/infrastructure_sync.md"
    click s2 "../modules/infrastructure_sync.md"
    click s4 "../modules/infrastructure_inventory.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `current_infrastructure_bases` | `snapshot: SourceSnapshot`, `inventory: Mapping[str, Mapping[str, object]]` | `INFRASTRUCTURE_EXTRACTOR_REF` | - | `...` |
| `build_infrastructure_page_map` | `source_paths: Mapping[str, object] \| tuple[str, ...] \| list[str] \| set[str]` | - | `result[...]` | `result` |
| `sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)` | - | - | - | - |
| `infrastructure_page_name` | `source_path: str` | - | - | `...` |
| `source_path.replace(…).replace(…).replace` | - | - | - | - |
| `source_path.replace(…).replace` | - | - | - | - |
| `source_path.replace` | - | - | - | - |
| `by_stem.setdefault(…).append` | - | - | - | - |
| `by_stem.setdefault` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…d_infrastructure_page_map)` | - | - | - | - |
| `by_stem.items` | - | - | - | - |
| `len (src/llm_wiki_cli/services…d_infrastructure_page_map)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| current_infrastructure_bases | build_infrastructure_page_map | 296 | `build_infrastructure_page_map(inventory)` |
| build_infrastructure_page_map | sorted (src/llm_wiki_cli/services…d_infrastructure_page_map) | 42 | `sorted(source_paths)` |
| build_infrastructure_page_map | infrastructure_page_name | 45 | `infrastructure_page_name(source_path)` |
| infrastructure_page_name | source_path.replace(…).replace(…).replace | 28 | `source_path.replace('\\', '/').replace('/', '_').replace('.', '_')` |
| infrastructure_page_name | source_path.replace(…).replace | 28 | `source_path.replace('\\', '/').replace('/', '_')` |
| infrastructure_page_name | source_path.replace | 28 | `source_path.replace('\\', '/')` |
| build_infrastructure_page_map | by_stem.setdefault(…).append | 46 | `by_stem.setdefault(stem, []).append(source_path)` |
| build_infrastructure_page_map | by_stem.setdefault | 46 | `by_stem.setdefault(stem, [...])` |
| build_infrastructure_page_map | sorted (src/llm_wiki_cli/services…d_infrastructure_page_map) | 48 | `sorted(by_stem.items(...))` |
| build_infrastructure_page_map | by_stem.items | 48 | `by_stem.items(data not statically known)` |
| build_infrastructure_page_map | len (src/llm_wiki_cli/services…d_infrastructure_page_map) | 49 | `len(grouped_paths)` |

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
| step_limit | `current_infrastructure_bases` | `first 12 steps` | 0 |
| truncated_flow | `current_infrastructure_bases` | `depth limit` | 0 |

## Behavior

This flow starts at `current_infrastructure_bases` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
