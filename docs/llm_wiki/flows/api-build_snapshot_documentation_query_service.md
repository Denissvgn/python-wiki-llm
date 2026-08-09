# build_snapshot_documentation_query_service

**Entry point:** `build_snapshot_documentation_query_service` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [documentation_query_builder](../modules/documentation_query_builder.md), [infrastructure_sync](../modules/infrastructure_sync.md), [io](../modules/io.md), and 15 more

**Complete modules touched:**

- [documentation_query_builder](../modules/documentation_query_builder.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_snapshot_documentation_query_service
    participant p1 as load_knowledge_read_view
    participant p2 as isinstance
    participant p3 as TypeError
    participant p4 as load_knowledge_state
    participant p5 as KnowledgeMismatchPolicy
    participant p6 as ValueError
    participant p7 as callable
    participant p8 as Path
    participant p9 as _load_once
    participant p10 as _read_artifact
    participant p11 as is_symlink
    participant p12 as KnowledgeLoadIssue
    participant p13 as exists
    participant p14 as is_file
    participant p15 as read_bytes
    participant p16 as KnowledgeLoadResult
    participant p17 as validate_surface_index_bytes
    participant p18 as _decode_json_object
    participant p19 as KnowledgeArtifactError
    participant p20 as decode
    participant p21 as loads
    participant p22 as _unique_json_object
    p0->>p1: load_knowledge_read_view
    p1-->>p2: isinstance
    p1-->>p3: TypeError
    p1->>p4: load_knowledge_state
    p4-->>p2: isinstance
    p4->>p5: KnowledgeMismatchPolicy
    p4-->>p6: ValueError
    p4-->>p6: ValueError
    p4-->>p7: callable
    p4-->>p3: TypeError
    p4-->>p8: Path
    p4->>p9: _load_once
    p9->>p10: _read_artifact
    p10-->>p11: is_symlink
    p10->>p12: KnowledgeLoadIssue
    p10-->>p13: exists
    p10->>p12: KnowledgeLoadIssue
    p10-->>p14: is_file
    p10->>p12: KnowledgeLoadIssue
    p10-->>p15: read_bytes
    p10->>p12: KnowledgeLoadIssue
    p9->>p16: KnowledgeLoadResult
    p9->>p17: validate_surface_index_bytes
    p17->>p18: _decode_json_object
    p18-->>p2: isinstance
    p18->>p19: KnowledgeArtifactError
    p18-->>p20: decode
    p18->>p19: KnowledgeArtifactError
    p18-->>p21: loads
    p18->>p22: _unique_json_object
```

> Call sequence diagram shows 30 of 704 interactions; 674 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_snapshot_documentation_query_service"]
    s2["2. load_knowledge_read_view"]
    s3["3. isinstance"]
    s4["4. TypeError"]
    s5["5. load_knowledge_state"]
    s6["6. isinstance"]
    s7["7. KnowledgeMismatchPolicy"]
    s8["8. ValueError"]
    s9["9. ValueError"]
    s10["10. callable"]
    s11["11. TypeError"]
    s12["12. Path"]
    s1 -->|"load_knowledge_read_view(wiki_root, snapshot_only=True, include_machine_verification=True)"| s2
    s2 -. "isinstance(include_machine_verification, bool)" .-> s3
    s2 -. "TypeError('include_machine_verification must be a boolean')" .-> s4
    s2 -->|"load_knowledge_state(wiki_dir, policy=KnowledgeMismatchPolicy.DEGRADED, markdown_pages=markdown_pages)"| s5
    s5 -. "isinstance(policy, KnowledgeMismatchPolicy)" .-> s6
    s5 -->|"KnowledgeMismatchPolicy(policy)"| s7
    s5 -. "ValueError(#34;policy must be 'reject', 'rebuild', or 'degraded'#34;)" .-> s8
    s5 -. "ValueError('rebuild policy requires rebuild_callback')" .-> s9
    s5 -. "callable(rebuild_callback)" .-> s10
    s5 -. "TypeError('rebuild_callback must be callable')" .-> s11
    s5 -. "Path(wiki_dir)" .-> s12
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/knowledge_consumption.md"
    click s5 "../modules/knowledge_loader.md"
    click s7 "../modules/knowledge_loader.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_snapshot_documentation_query_service` | `wiki_root: Path`, `limit: int` | - | - | `build_documentation_query_service_from_view(...)` |
| `load_knowledge_read_view` | `wiki_dir: str \| Path`, `live_evaluation: LiveKnowledgeEvaluation \| None`, `snapshot_only: bool`, `mode: KnowledgeReadMode \| str \| None`, `markdown_pages: Mapping[str, str \| bytes] \| None`, `include_machine_verification: bool` | `KnowledgeMismatchPolicy`, `KnowledgeStateLoadError`, `KnowledgeLoadState` | - | `view`, `attach_machine_verification_read_view(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `load_knowledge_state` | `wiki_dir: str \| Path`, `policy: KnowledgeMismatchPolicy \| str`, `rebuild_callback: RebuildCallback \| None`, `markdown_pages: Mapping[str, str \| bytes] \| None` | `KnowledgeMismatchPolicy`, `KnowledgeMismatchPolicy`, `KnowledgeLoadState`, `KnowledgeMismatchPolicy`, `KnowledgeLoadState`, `KnowledgeMismatchPolicy`, `KnowledgeLoadState` | - | `result`, `replace(...)`, `KnowledgeLoadResult(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeMismatchPolicy` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `callable` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_snapshot_documentation_query_service | load_knowledge_read_view | 196 | `load_knowledge_read_view(wiki_root, snapshot_only=True, include_machine_verification=True)` |
| load_knowledge_read_view | isinstance | 677 | `isinstance(include_machine_verification, bool)` |
| load_knowledge_read_view | TypeError | 678 | `TypeError('include_machine_verification must be a boolean')` |
| load_knowledge_read_view | load_knowledge_state | 680 | `load_knowledge_state(wiki_dir, policy=KnowledgeMismatchPolicy.DEGRADED, markdown_pages=markdown_pages)` |
| load_knowledge_state | isinstance | 105 | `isinstance(policy, KnowledgeMismatchPolicy)` |
| load_knowledge_state | KnowledgeMismatchPolicy | 106 | `KnowledgeMismatchPolicy(policy)` |
| load_knowledge_state | ValueError | 109 | `ValueError("policy must be 'reject', 'rebuild', or 'degraded'")` |
| load_knowledge_state | ValueError | 111 | `ValueError('rebuild policy requires rebuild_callback')` |
| load_knowledge_state | callable | 112 | `callable(rebuild_callback)` |
| load_knowledge_state | TypeError | 113 | `TypeError('rebuild_callback must be callable')` |
| load_knowledge_state | Path | 115 | `Path(wiki_dir)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `load_knowledge_read_view` | `isinstance` | 677 |
| unresolved_call | `load_knowledge_read_view` | `TypeError` | 678 |
| unresolved_call | `load_knowledge_state` | `isinstance` | 105 |
| unresolved_call | `load_knowledge_state` | `ValueError` | 109 |
| unresolved_call | `load_knowledge_state` | `ValueError` | 111 |
| unresolved_call | `load_knowledge_state` | `callable` | 112 |
| unresolved_call | `load_knowledge_state` | `TypeError` | 113 |
| step_limit | `build_snapshot_documentation_query_service` | `first 12 steps` | 0 |
| truncated_flow | `build_snapshot_documentation_query_service` | `depth limit` | 0 |

## Behavior

This flow starts at `build_snapshot_documentation_query_service` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
