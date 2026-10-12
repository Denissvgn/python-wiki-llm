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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as current_infrastructure_bases
    participant p1 as build_infrastructure_page_map
    participant p2 as build_infrastructure_observation_basis
    participant p3 as _source_hash
    participant p4 as _observation_hash
    participant p5 as _validate_source_path
    participant p6 as _validate_hash
    participant p7 as _validate_extractor_ref
    participant p8 as hash_json
    participant p9 as require_repository_relative_path
    participant p10 as require_sha256
    participant p11 as canonical_json_bytes
    participant p12 as require_trimmed_text
    participant p13 as require_portable_relative_path
    participant p14 as require_nonempty_text
    participant p15 as _default_path_error
    participant p16 as _check_path_collision
    participant p17 as require_portable_path_component
    participant p18 as infrastructure_page_name
    participant p19 as is_valid_sha256
    participant p20 as InfrastructureSyncError
    participant p21 as ConceptObservationBasis
    participant p22 as sha256_bytes
    participant p23 as require_string
    participant p24 as canonical_json_text
    participant p25 as _syntax_key
    participant p26 as _known_syntax
    participant p27 as _remember_syntax
    participant p28 as SharedValidationError
    participant p29 as sorted (src/llm_wiki_cli/services…rent_infrastructure_bases)
    participant p30 as inventory.items
    p0->>p1: build_infrastructure_page_map
    p0->>p2: build_infrastructure_observation_basis
    p0->>p3: _source_hash
    p0->>p4: _observation_hash
    p2->>p5: _validate_source_path
    p2->>p6: _validate_hash
    p2->>p7: _validate_extractor_ref
    p1->>p8: hash_json
    p5->>p9: require_repository_relative_path
    p6->>p10: require_sha256
    p8->>p11: canonical_json_bytes
    p10->>p12: require_trimmed_text
    p9->>p13: require_portable_relative_path
    p12->>p14: require_nonempty_text
    p13->>p15: _default_path_error
    p13->>p16: _check_path_collision
    p13->>p17: require_portable_path_component
    p1->>p18: infrastructure_page_name
    p3->>p19: is_valid_sha256
    p3->>p20: InfrastructureSyncError
    p2->>p21: ConceptObservationBasis
    p8->>p22: sha256_bytes
    p7->>p23: require_string
    p11->>p24: canonical_json_text
    p9->>p25: _syntax_key
    p9->>p26: _known_syntax
    p9->>p27: _remember_syntax
    p15->>p28: SharedValidationError
    p0-->>p29: sorted (src/llm_wiki_cli/services…rent_infrastructure_bases)(inventory.items(...))
    p0-->>p30: inventory.items
```

> Call sequence diagram shows 30 of 130 interactions; 100 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 41 (40 omitted); unresolved 1 of 41 (40 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/infrastructure_sync.py:build_infrastructure_page_map` | 2 | - | external | 3 |
| `src/llm_wiki_cli/services/infrastructure_inventory.py:infrastructure_page_name` | 4 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/infrastructure_sync.py:build_infrastructure_page_map` | 2 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 15 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 15 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:canonical_json_bytes` | 18 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:canonical_json_text` | 20 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 24 | - | external | 7 |
> Omission summary shows 8 of 39 groups; 31 further groups are not expanded here. Counts above include all omitted interactions.
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
| infrastructure_page_name | source_path.replace(…).replace(…).replace | 31 | `source_path.replace('\\', '/').replace('/', '_').replace('.', '_')` |
| infrastructure_page_name | source_path.replace(…).replace | 31 | `source_path.replace('\\', '/').replace('/', '_')` |
| infrastructure_page_name | source_path.replace | 31 | `source_path.replace('\\', '/')` |
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
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace('/', '_').replace` | 31 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace('\\', '/').replace` | 31 |
| unresolved_call | `infrastructure_page_name` | `source_path.replace` | 31 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.setdefault(stem, []).append` | 46 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.setdefault` | 46 |
| external_call | `build_infrastructure_page_map` | `sorted` | 48 |
| unresolved_call | `build_infrastructure_page_map` | `by_stem.items` | 48 |
| step_limit | `current_infrastructure_bases` | `first 12 steps` | 0 |
| truncated_flow | `current_infrastructure_bases` | `depth limit` | 0 |

## Behavior

This flow starts at `current_infrastructure_bases` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
