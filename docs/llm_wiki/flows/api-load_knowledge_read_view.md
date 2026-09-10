# load_knowledge_read_view

**Entry point:** `load_knowledge_read_view` (`api`)
**Source:** [knowledge_consumption](../modules/knowledge_consumption.md)
**Modules touched:** [immutable](../modules/immutable.md), [infrastructure_sync](../modules/infrastructure_sync.md), [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), and 17 more

**Complete modules touched:**

- [immutable](../modules/immutable.md)
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
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as load_knowledge_read_view
    participant p1 as isinstance (src/llm_wiki_cli/services…:load_knowledge_read_view)
    participant p2 as TypeError (src/llm_wiki_cli/services…:load_knowledge_read_view)
    participant p3 as load_knowledge_state
    participant p4 as isinstance (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    participant p5 as KnowledgeMismatchPolicy
    participant p6 as ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    participant p7 as callable (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    participant p8 as TypeError (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    participant p9 as Path (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    participant p10 as _load_once
    participant p11 as _read_artifact
    participant p12 as path.is_symlink (src/llm_wiki_cli/services…_loader.py:_read_artifact)
    participant p13 as KnowledgeLoadIssue
    participant p14 as path.exists (src/llm_wiki_cli/services…_loader.py:_read_artifact)
    participant p15 as path.is_file (src/llm_wiki_cli/services…_loader.py:_read_artifact)
    participant p16 as path.read_bytes (src/llm_wiki_cli/services…_loader.py:_read_artifact)
    participant p17 as KnowledgeLoadResult
    participant p18 as validate_surface_index_bytes
    participant p19 as _decode_json_object
    participant p20 as isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    participant p21 as KnowledgeArtifactError
    participant p22 as content.decode (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    participant p23 as json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    participant p24 as _unique_json_object
    p0-->>p1: isinstance (src/llm_wiki_cli/services…:load_knowledge_read_view)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…:load_knowledge_read_view)
    p0->>p3: load_knowledge_state
    p3-->>p4: isinstance (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    p3->>p5: KnowledgeMismatchPolicy
    p3-->>p6: ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    p3-->>p6: ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    p3-->>p7: callable (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    p3-->>p8: TypeError (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    p3-->>p9: Path (src/llm_wiki_cli/services…r.py:load_knowledge_state)
    p3->>p10: _load_once
    p10->>p11: _read_artifact
    p11-->>p12: path.is_symlink (src/llm_wiki_cli/services…_loader.py:_read_artifact)
    p11->>p13: KnowledgeLoadIssue
    p11-->>p14: path.exists (src/llm_wiki_cli/services…_loader.py:_read_artifact)
    p11->>p13: KnowledgeLoadIssue
    p11-->>p15: path.is_file (src/llm_wiki_cli/services…_loader.py:_read_artifact)
    p11->>p13: KnowledgeLoadIssue
    p11-->>p16: path.read_bytes (src/llm_wiki_cli/services…_loader.py:_read_artifact)
    p11->>p13: KnowledgeLoadIssue
    p10->>p17: KnowledgeLoadResult
    p10->>p18: validate_surface_index_bytes
    p18->>p19: _decode_json_object
    p19-->>p20: isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p19->>p21: KnowledgeArtifactError
    p19-->>p22: content.decode (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p19->>p21: KnowledgeArtifactError
    p19-->>p23: json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p19->>p24: _unique_json_object
    p24->>p21: KnowledgeArtifactError
```

> Call sequence diagram shows 30 of 1198 interactions; 1168 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_knowledge_read_view"]
    s2["2. isinstance (src/llm_wiki_cli/services…:load_knowledge_read_view)"]
    s3["3. TypeError (src/llm_wiki_cli/services…:load_knowledge_read_view)"]
    s4["4. load_knowledge_state"]
    s5["5. isinstance (src/llm_wiki_cli/services…r.py:load_knowledge_state)"]
    s6["6. KnowledgeMismatchPolicy"]
    s7["7. ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state)"]
    s8["8. ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state)"]
    s9["9. callable (src/llm_wiki_cli/services…r.py:load_knowledge_state)"]
    s10["10. TypeError (src/llm_wiki_cli/services…r.py:load_knowledge_state)"]
    s11["11. Path (src/llm_wiki_cli/services…r.py:load_knowledge_state)"]
    s12["12. _load_once"]
    s1 -. "isinstance (src/llm_wiki_cli/services…:load_knowledge_read_view)(include_machine_verification, bool)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…:load_knowledge_read_view)('include_machine_verification must be a boolean')" .-> s3
    s1 -->|"load_knowledge_state(wiki_dir, policy=KnowledgeMismatchPolicy.DEGRADED, markdown_pages=markdown_pages)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…r.py:load_knowledge_state)(policy, KnowledgeMismatchPolicy)" .-> s5
    s4 -->|"KnowledgeMismatchPolicy(policy)"| s6
    s4 -. "ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state)(#34;policy must be 'reject', 'rebuild', or 'degraded'#34;)" .-> s7
    s4 -. "ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state)('rebuild policy requires rebuild_callback')" .-> s8
    s4 -. "callable (src/llm_wiki_cli/services…r.py:load_knowledge_state)(rebuild_callback)" .-> s9
    s4 -. "TypeError (src/llm_wiki_cli/services…r.py:load_knowledge_state)('rebuild_callback must be callable')" .-> s10
    s4 -. "Path (src/llm_wiki_cli/services…r.py:load_knowledge_state)(wiki_dir)" .-> s11
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
| `isinstance (src/llm_wiki_cli/services…:load_knowledge_read_view)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…:load_knowledge_read_view)` | - | - | - | - |
| `load_knowledge_state` | `wiki_dir: str \| Path`, `policy: KnowledgeMismatchPolicy \| str`, `rebuild_callback: RebuildCallback \| None`, `markdown_pages: Mapping[str, str \| bytes] \| None` | `KnowledgeMismatchPolicy`, `KnowledgeMismatchPolicy`, `KnowledgeLoadState`, `KnowledgeMismatchPolicy`, `KnowledgeLoadState`, `KnowledgeMismatchPolicy`, `KnowledgeLoadState` | - | `result`, `replace(...)`, `KnowledgeLoadResult(...)` |
| `isinstance (src/llm_wiki_cli/services…r.py:load_knowledge_state)` | - | - | - | - |
| `KnowledgeMismatchPolicy` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state)` | - | - | - | - |
| `callable (src/llm_wiki_cli/services…r.py:load_knowledge_state)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…r.py:load_knowledge_state)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…r.py:load_knowledge_state)` | - | - | - | - |
| `_load_once` | `root: Path`, `markdown_pages: Mapping[str, str \| bytes] \| None` | `SURFACE_INDEX_FILENAME`, `KnowledgeLoadState`, `KnowledgeArtifactError`, `SURFACE_INDEX_FILENAME`, `KnowledgeLoadState`, `WikiSurfacePathError`, `KnowledgeEnvelopeError`, `SURFACE_INDEX_FILENAME` | - | `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)`, `(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_knowledge_read_view | isinstance (src/llm_wiki_cli/services…:load_knowledge_read_view) | 671 | `isinstance(include_machine_verification, bool)` |
| load_knowledge_read_view | TypeError (src/llm_wiki_cli/services…:load_knowledge_read_view) | 672 | `TypeError('include_machine_verification must be a boolean')` |
| load_knowledge_read_view | load_knowledge_state | 674 | `load_knowledge_state(wiki_dir, policy=KnowledgeMismatchPolicy.DEGRADED, markdown_pages=markdown_pages)` |
| load_knowledge_state | isinstance (src/llm_wiki_cli/services…r.py:load_knowledge_state) | 112 | `isinstance(policy, KnowledgeMismatchPolicy)` |
| load_knowledge_state | KnowledgeMismatchPolicy | 113 | `KnowledgeMismatchPolicy(policy)` |
| load_knowledge_state | ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state) | 116 | `ValueError("policy must be 'reject', 'rebuild', or 'degraded'")` |
| load_knowledge_state | ValueError (src/llm_wiki_cli/services…r.py:load_knowledge_state) | 118 | `ValueError('rebuild policy requires rebuild_callback')` |
| load_knowledge_state | callable (src/llm_wiki_cli/services…r.py:load_knowledge_state) | 119 | `callable(rebuild_callback)` |
| load_knowledge_state | TypeError (src/llm_wiki_cli/services…r.py:load_knowledge_state) | 120 | `TypeError('rebuild_callback must be callable')` |
| load_knowledge_state | Path (src/llm_wiki_cli/services…r.py:load_knowledge_state) | 122 | `Path(wiki_dir)` |
| load_knowledge_state | _load_once | 123 | `_load_once(root, markdown_pages=markdown_pages)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `load_knowledge_read_view` | `isinstance` | 671 |
| external_call | `load_knowledge_read_view` | `TypeError` | 672 |
| external_call | `load_knowledge_state` | `isinstance` | 112 |
| external_call | `load_knowledge_state` | `ValueError` | 116 |
| external_call | `load_knowledge_state` | `ValueError` | 118 |
| external_call | `load_knowledge_state` | `callable` | 119 |
| external_call | `load_knowledge_state` | `TypeError` | 120 |
| step_limit | `load_knowledge_read_view` | `first 12 steps` | 0 |
| truncated_flow | `load_knowledge_read_view` | `depth limit` | 0 |

## Behavior

This flow starts at `load_knowledge_read_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
