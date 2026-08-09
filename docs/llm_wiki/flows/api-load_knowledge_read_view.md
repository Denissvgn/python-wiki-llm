# load_knowledge_read_view

**Entry point:** `load_knowledge_read_view` (`api`)
**Source:** [knowledge_consumption](../modules/knowledge_consumption.md)
**Modules touched:** [infrastructure_sync](../modules/infrastructure_sync.md), [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_consumption](../modules/knowledge_consumption.md), and 14 more

**Complete modules touched:**

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
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_knowledge_read_view
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as load_knowledge_state
    participant p4 as KnowledgeMismatchPolicy
    participant p5 as ValueError
    participant p6 as callable
    participant p7 as Path
    participant p8 as _load_once
    participant p9 as _read_artifact
    participant p10 as is_symlink
    participant p11 as KnowledgeLoadIssue
    participant p12 as exists
    participant p13 as is_file
    participant p14 as read_bytes
    participant p15 as KnowledgeLoadResult
    participant p16 as validate_surface_index_bytes
    participant p17 as _decode_json_object
    participant p18 as KnowledgeArtifactError
    participant p19 as decode
    participant p20 as loads
    participant p21 as _unique_json_object
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: load_knowledge_state
    p3-->>p1: isinstance
    p3->>p4: KnowledgeMismatchPolicy
    p3-->>p5: ValueError
    p3-->>p5: ValueError
    p3-->>p6: callable
    p3-->>p2: TypeError
    p3-->>p7: Path
    p3->>p8: _load_once
    p8->>p9: _read_artifact
    p9-->>p10: is_symlink
    p9->>p11: KnowledgeLoadIssue
    p9-->>p12: exists
    p9->>p11: KnowledgeLoadIssue
    p9-->>p13: is_file
    p9->>p11: KnowledgeLoadIssue
    p9-->>p14: read_bytes
    p9->>p11: KnowledgeLoadIssue
    p8->>p15: KnowledgeLoadResult
    p8->>p16: validate_surface_index_bytes
    p16->>p17: _decode_json_object
    p17-->>p1: isinstance
    p17->>p18: KnowledgeArtifactError
    p17-->>p19: decode
    p17->>p18: KnowledgeArtifactError
    p17-->>p20: loads
    p17->>p21: _unique_json_object
    p21->>p18: KnowledgeArtifactError
```

> Call sequence diagram shows 30 of 1117 interactions; 1087 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_knowledge_read_view"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. load_knowledge_state"]
    s5["5. isinstance"]
    s6["6. KnowledgeMismatchPolicy"]
    s7["7. ValueError"]
    s8["8. ValueError"]
    s9["9. callable"]
    s10["10. TypeError"]
    s11["11. Path"]
    s12["12. _load_once"]
    s1 -. "isinstance(include_machine_verification, bool)" .-> s2
    s1 -. "TypeError('include_machine_verification must be a boolean')" .-> s3
    s1 -->|"load_knowledge_state(wiki_dir, policy=KnowledgeMismatchPolicy.DEGRADED, markdown_pages=markdown_pages)"| s4
    s4 -. "isinstance(policy, KnowledgeMismatchPolicy)" .-> s5
    s4 -->|"KnowledgeMismatchPolicy(policy)"| s6
    s4 -. "ValueError(#34;policy must be 'reject', 'rebuild', or 'degraded'#34;)" .-> s7
    s4 -. "ValueError('rebuild policy requires rebuild_callback')" .-> s8
    s4 -. "callable(rebuild_callback)" .-> s9
    s4 -. "TypeError('rebuild_callback must be callable')" .-> s10
    s4 -. "Path(wiki_dir)" .-> s11
    s4 -->|"_load_once(root, markdown_pages=markdown_pages)"| s12
    click s1 "../modules/knowledge_consumption.md"
    click s4 "../modules/knowledge_loader.md"
    click s6 "../modules/knowledge_loader.md"
    click s12 "../modules/knowledge_loader.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `_load_once` | `root: Path`, `markdown_pages: Mapping[str, str \| bytes] \| None` | `SURFACE_INDEX_FILENAME`, `KnowledgeLoadState`, `KnowledgeArtifactError`, `SURFACE_INDEX_FILENAME`, `KnowledgeLoadState`, `KnowledgeEnvelopeError`, `SURFACE_INDEX_FILENAME`, `KnowledgeLoadState` | - | `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| load_knowledge_state | _load_once | 116 | `_load_once(root, markdown_pages=markdown_pages)` |

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
| step_limit | `load_knowledge_read_view` | `first 12 steps` | 0 |
| truncated_flow | `load_knowledge_read_view` | `depth limit` | 0 |

## Behavior

This flow starts at `load_knowledge_read_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
