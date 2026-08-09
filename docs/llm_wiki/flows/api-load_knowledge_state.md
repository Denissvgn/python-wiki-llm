# load_knowledge_state

**Entry point:** `load_knowledge_state` (`api`)
**Source:** [knowledge_loader](../modules/knowledge_loader.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [infrastructure_sync](../modules/infrastructure_sync.md), [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), and 12 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_knowledge_state
    participant p1 as isinstance
    participant p2 as KnowledgeMismatchPolicy
    participant p3 as ValueError
    participant p4 as callable
    participant p5 as TypeError
    participant p6 as Path
    participant p7 as _load_once
    participant p8 as _read_artifact
    participant p9 as is_symlink
    participant p10 as KnowledgeLoadIssue
    participant p11 as exists
    participant p12 as is_file
    participant p13 as read_bytes
    participant p14 as KnowledgeLoadResult
    participant p15 as validate_surface_index_bytes
    participant p16 as _decode_json_object
    participant p17 as KnowledgeArtifactError
    participant p18 as decode
    participant p19 as loads
    participant p20 as _unique_json_object
    participant p21 as _reject_json_constant
    p0-->>p1: isinstance
    p0->>p2: KnowledgeMismatchPolicy
    p0-->>p3: ValueError
    p0-->>p3: ValueError
    p0-->>p4: callable
    p0-->>p5: TypeError
    p0-->>p6: Path
    p0->>p7: _load_once
    p7->>p8: _read_artifact
    p8-->>p9: is_symlink
    p8->>p10: KnowledgeLoadIssue
    p8-->>p11: exists
    p8->>p10: KnowledgeLoadIssue
    p8-->>p12: is_file
    p8->>p10: KnowledgeLoadIssue
    p8-->>p13: read_bytes
    p8->>p10: KnowledgeLoadIssue
    p7->>p14: KnowledgeLoadResult
    p7->>p15: validate_surface_index_bytes
    p15->>p16: _decode_json_object
    p16-->>p1: isinstance
    p16->>p17: KnowledgeArtifactError
    p16-->>p18: decode
    p16->>p17: KnowledgeArtifactError
    p16-->>p19: loads
    p16->>p20: _unique_json_object
    p20->>p17: KnowledgeArtifactError
    p16->>p21: _reject_json_constant
    p21->>p17: KnowledgeArtifactError
    p16-->>p1: isinstance
```

> Call sequence diagram shows 30 of 1085 interactions; 1055 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_knowledge_state"]
    s2["2. isinstance"]
    s3["3. KnowledgeMismatchPolicy"]
    s4["4. ValueError"]
    s5["5. ValueError"]
    s6["6. callable"]
    s7["7. TypeError"]
    s8["8. Path"]
    s9["9. _load_once"]
    s10["10. _read_artifact"]
    s11["11. is_symlink"]
    s12["12. KnowledgeLoadIssue"]
    s1 -. "isinstance(policy, KnowledgeMismatchPolicy)" .-> s2
    s1 -->|"KnowledgeMismatchPolicy(policy)"| s3
    s1 -. "ValueError(#34;policy must be 'reject', 'rebuild', or 'degraded'#34;)" .-> s4
    s1 -. "ValueError('rebuild policy requires rebuild_callback')" .-> s5
    s1 -. "callable(rebuild_callback)" .-> s6
    s1 -. "TypeError('rebuild_callback must be callable')" .-> s7
    s1 -. "Path(wiki_dir)" .-> s8
    s1 -->|"_load_once(root, markdown_pages=markdown_pages)"| s9
    s9 -->|"_read_artifact(root, SURFACE_INDEX_FILENAME)"| s10
    s10 -. "path.is_symlink(data not statically known)" .-> s11
    s10 -->|"KnowledgeLoadIssue(code='artifact-not-regular', artifact_path=filename, message='artifact must be a regular file, not a symbolic link')"| s12
    b0["filesystem_read path.read_bytes"]
    s10 -. "filesystem_read path.read_bytes" .-> b0
    click s1 "../modules/knowledge_loader.md"
    click s3 "../modules/knowledge_loader.md"
    click s9 "../modules/knowledge_loader.md"
    click s10 "../modules/knowledge_loader.md"
    click s12 "../modules/knowledge_loader.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_knowledge_state` | `wiki_dir: str \| Path`, `policy: KnowledgeMismatchPolicy \| str`, `rebuild_callback: RebuildCallback \| None`, `markdown_pages: Mapping[str, str \| bytes] \| None` | `KnowledgeMismatchPolicy`, `KnowledgeMismatchPolicy`, `KnowledgeLoadState`, `KnowledgeMismatchPolicy`, `KnowledgeLoadState`, `KnowledgeMismatchPolicy`, `KnowledgeLoadState` | - | `result`, `replace(...)`, `KnowledgeLoadResult(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeMismatchPolicy` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `callable` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `Path` | - | - | - | - |
| `_load_once` | `root: Path`, `markdown_pages: Mapping[str, str \| bytes] \| None` | `SURFACE_INDEX_FILENAME`, `KnowledgeLoadState`, `KnowledgeArtifactError`, `SURFACE_INDEX_FILENAME`, `KnowledgeLoadState`, `KnowledgeEnvelopeError`, `SURFACE_INDEX_FILENAME`, `KnowledgeLoadState` | - | `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)` |
| `_read_artifact` | `root: Path`, `filename: str`, `absent_is_issue: bool` | - | - | `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)` |
| `is_symlink` | - | - | - | - |
| `KnowledgeLoadIssue` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_knowledge_state | isinstance | 105 | `isinstance(policy, KnowledgeMismatchPolicy)` |
| load_knowledge_state | KnowledgeMismatchPolicy | 106 | `KnowledgeMismatchPolicy(policy)` |
| load_knowledge_state | ValueError | 109 | `ValueError("policy must be 'reject', 'rebuild', or 'degraded'")` |
| load_knowledge_state | ValueError | 111 | `ValueError('rebuild policy requires rebuild_callback')` |
| load_knowledge_state | callable | 112 | `callable(rebuild_callback)` |
| load_knowledge_state | TypeError | 113 | `TypeError('rebuild_callback must be callable')` |
| load_knowledge_state | Path | 115 | `Path(wiki_dir)` |
| load_knowledge_state | _load_once | 116 | `_load_once(root, markdown_pages=markdown_pages)` |
| _load_once | _read_artifact | 149 | `_read_artifact(root, SURFACE_INDEX_FILENAME)` |
| _read_artifact | is_symlink | 473 | `path.is_symlink(data not statically known)` |
| _read_artifact | KnowledgeLoadIssue | 474 | `KnowledgeLoadIssue(code='artifact-not-regular', artifact_path=filename, message='artifact must be a regular file, not a symbolic link')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `path.read_bytes` | `_read_artifact` | 494 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `load_knowledge_state` | `isinstance` | 105 |
| unresolved_call | `load_knowledge_state` | `ValueError` | 109 |
| unresolved_call | `load_knowledge_state` | `ValueError` | 111 |
| unresolved_call | `load_knowledge_state` | `callable` | 112 |
| unresolved_call | `load_knowledge_state` | `TypeError` | 113 |
| unresolved_call | `_read_artifact` | `path.is_symlink` | 473 |
| step_limit | `load_knowledge_state` | `first 12 steps` | 0 |
| truncated_flow | `load_knowledge_state` | `depth limit` | 0 |

## Behavior

This flow starts at `load_knowledge_state` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
