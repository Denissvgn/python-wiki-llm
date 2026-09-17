# build_knowledge_commit_plan

**Entry point:** `build_knowledge_commit_plan` (`api`)
**Source:** [knowledge_artifacts](../modules/knowledge_artifacts.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), [filesystem_guard](../modules/filesystem_guard.md), and 23 more

**Complete modules touched:**

- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [manifest_storage](../modules/manifest_storage.md)
- [progress](../modules/progress.md)
- [section_ownership](../modules/section_ownership.md)
- [storage_spool](../modules/storage_spool.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_knowledge_commit_plan
    participant p1 as Path (src/llm_wiki_cli/services…ild_knowledge_commit_plan)
    participant p2 as KnowledgeArtifactError
    participant p3 as current_manifest_format
    participant p4 as Path (src/llm_wiki_cli/services…y:current_manifest_format)
    participant p5 as path.exists (src/llm_wiki_cli/services…y:current_manifest_format)
    participant p6 as path.is_symlink (src/llm_wiki_cli/services…y:current_manifest_format)
    participant p7 as (…).exists (src/llm_wiki_cli/services…y:current_manifest_format)
    participant p8 as KnowledgeStorageError
    participant p9 as json.loads (src/llm_wiki_cli/services…y:current_manifest_format)
    participant p10 as read_guarded
    participant p11 as _validate_range
    participant p12 as type (src/llm_wiki_cli/services…age_io.py:_validate_range)
    participant p13 as _absolute_path
    participant p14 as Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)
    participant p15 as os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)
    participant p16 as first_unsafe_path_component
    participant p17 as Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p18 as os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p19 as os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p20 as lexical.is_absolute
    participant p21 as Path.cwd
    participant p22 as list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p23 as pending_parts.pop
    p0-->>p1: Path (src/llm_wiki_cli/services…ild_knowledge_commit_plan)
    p0->>p2: KnowledgeArtifactError
    p0->>p3: current_manifest_format
    p3-->>p4: Path (src/llm_wiki_cli/services…y:current_manifest_format)
    p3-->>p5: path.exists (src/llm_wiki_cli/services…y:current_manifest_format)
    p3-->>p6: path.is_symlink (src/llm_wiki_cli/services…y:current_manifest_format)
    p3-->>p7: (…).exists (src/llm_wiki_cli/services…y:current_manifest_format)
    p3->>p8: KnowledgeStorageError
    p3-->>p9: json.loads (src/llm_wiki_cli/services…y:current_manifest_format)
    p3->>p10: read_guarded
    p10->>p11: _validate_range
    p11-->>p12: type (src/llm_wiki_cli/services…age_io.py:_validate_range)
    p11->>p8: KnowledgeStorageError
    p11-->>p12: type (src/llm_wiki_cli/services…age_io.py:_validate_range)
    p11-->>p12: type (src/llm_wiki_cli/services…age_io.py:_validate_range)
    p11-->>p12: type (src/llm_wiki_cli/services…age_io.py:_validate_range)
    p11->>p8: KnowledgeStorageError
    p10->>p13: _absolute_path
    p13-->>p14: Path (src/llm_wiki_cli/services…rage_io.py:_absolute_path)
    p13-->>p15: os.path.abspath (src/llm_wiki_cli/services…rage_io.py:_absolute_path)
    p13->>p16: first_unsafe_path_component
    p16-->>p17: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p16-->>p18: os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p16-->>p17: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p16-->>p19: os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p16-->>p20: lexical.is_absolute
    p16-->>p21: Path.cwd
    p16-->>p17: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p16-->>p22: list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p16-->>p23: pending_parts.pop
```

> Call sequence diagram shows 30 of 2489 interactions; 2459 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_knowledge_commit_plan"]
    s2["2. Path (src/llm_wiki_cli/services…ild_knowledge_commit_plan)"]
    s3["3. KnowledgeArtifactError"]
    s4["4. current_manifest_format"]
    s5["5. Path (src/llm_wiki_cli/services…y:current_manifest_format)"]
    s6["6. path.exists (src/llm_wiki_cli/services…y:current_manifest_format)"]
    s7["7. path.is_symlink (src/llm_wiki_cli/services…y:current_manifest_format)"]
    s8["8. (…).exists (src/llm_wiki_cli/services…y:current_manifest_format)"]
    s9["9. KnowledgeStorageError"]
    s10["10. json.loads (src/llm_wiki_cli/services…y:current_manifest_format)"]
    s11["11. read_guarded"]
    s12["12. _validate_range"]
    s1 -. "Path (src/llm_wiki_cli/services…ild_knowledge_commit_plan)(wiki_dir)" .-> s2
    s1 -->|"KnowledgeArtifactError('manifest_format', 'must be v5 or indexed-v6')"| s3
    s1 -->|"current_manifest_format(root)"| s4
    s4 -. "Path (src/llm_wiki_cli/services…y:current_manifest_format)(wiki_dir)" .-> s5
    s4 -. "path.exists (src/llm_wiki_cli/services…y:current_manifest_format)(data not statically known)" .-> s6
    s4 -. "path.is_symlink (src/llm_wiki_cli/services…y:current_manifest_format)(data not statically known)" .-> s7
    s4 -. "(…).exists (src/llm_wiki_cli/services…y:current_manifest_format)(data not statically known)" .-> s8
    s4 -->|"KnowledgeStorageError('manifest', 'indexed manifest root is missing; recover it first')"| s9
    s4 -. "json.loads (src/llm_wiki_cli/services…y:current_manifest_format)(...)" .-> s10
    s4 -->|"read_guarded(path, MAX_EXPANDED_BYTES)"| s11
    s11 -->|"_validate_range(maximum, offset, length, file_bytes)"| s12
    b0["mutation pinned.append"]
    s11 -. "mutation pinned.append" .-> b0
    b1["mutation directories_list.append"]
    s11 -. "mutation directories_list.append" .-> b1
    click s1 "../modules/knowledge_artifacts.md"
    click s3 "../modules/knowledge_artifacts.md"
    click s4 "../modules/manifest_storage.md"
    click s9 "../modules/knowledge_storage.md"
    click s11 "../modules/knowledge_storage_io.md"
    click s12 "../modules/knowledge_storage_io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_knowledge_commit_plan` | `wiki_dir: str \| Path`, `surface_index_bytes: bytes`, `knowledge_index_bytes: bytes \| None`, `manifest: SyncManifest`, `knowledge_format: str \| None`, `knowledge_index: KnowledgeIndex \| None`, `manifest_format: str \| None`, `prior: ValidatedKnowledgeArtifacts \| None` | `PACKED_FORMATS`, `KnowledgeStorageError`, `KnowledgeStorageError`, `SyncManifest`, `SURFACE_INDEX_FILENAME`, `SURFACE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME`, `KNOWLEDGE_INDEX_FILENAME` | `committed_manifest.storage_version`, `committed_manifest.storage_objects`, `committed_manifest.storage_version`, `committed_manifest.storage_objects` | `KnowledgeCommitPlan(...)` |
| `Path (src/llm_wiki_cli/services…ild_knowledge_commit_plan)` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `current_manifest_format` | `wiki_dir: str \| Path` | `MAX_EXPANDED_BYTES`, `VERSION` | - | `'v5'`, `'v5'`, `'v5'`, `'indexed-v6'` |
| `Path (src/llm_wiki_cli/services…y:current_manifest_format)` | - | - | - | - |
| `path.exists (src/llm_wiki_cli/services…y:current_manifest_format)` | - | - | - | - |
| `path.is_symlink (src/llm_wiki_cli/services…y:current_manifest_format)` | - | - | - | - |
| `(…).exists (src/llm_wiki_cli/services…y:current_manifest_format)` | - | - | - | - |
| `KnowledgeStorageError` | - | - | - | - |
| `json.loads (src/llm_wiki_cli/services…y:current_manifest_format)` | - | - | - | - |
| `read_guarded` | `path: Path`, `maximum: int`, `offset: int`, `length: int \| None`, `file_bytes: int \| None` | `os`, `os`, `os`, `os`, `os`, `os`, `KnowledgeStorageError` | - | `ReadObservation(...)` |
| `_validate_range` | `maximum`, `offset`, `length`, `file_bytes` | `MAX_EXPANDED_BYTES`, `MAX_EXPANDED_BYTES` | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_knowledge_commit_plan | Path (src/llm_wiki_cli/services…ild_knowledge_commit_plan) | 500 | `Path(wiki_dir)` |
| build_knowledge_commit_plan | KnowledgeArtifactError | 503 | `KnowledgeArtifactError('manifest_format', 'must be v5 or indexed-v6')` |
| build_knowledge_commit_plan | current_manifest_format | 504 | `current_manifest_format(root)` |
| current_manifest_format | Path (src/llm_wiki_cli/services…y:current_manifest_format) | 239 | `Path(wiki_dir)` |
| current_manifest_format | path.exists (src/llm_wiki_cli/services…y:current_manifest_format) | 240 | `path.exists(data not statically known)` |
| current_manifest_format | path.is_symlink (src/llm_wiki_cli/services…y:current_manifest_format) | 240 | `path.is_symlink(data not statically known)` |
| current_manifest_format | (…).exists (src/llm_wiki_cli/services…y:current_manifest_format) | 241 | `(path.parent / '.llm-wiki-manifest').exists(data not statically known)` |
| current_manifest_format | KnowledgeStorageError | 242 | `KnowledgeStorageError('manifest', 'indexed manifest root is missing; recover it first')` |
| current_manifest_format | json.loads (src/llm_wiki_cli/services…y:current_manifest_format) | 245 | `json.loads(...)` |
| current_manifest_format | read_guarded | 245 | `read_guarded(path, MAX_EXPANDED_BYTES)` |
| read_guarded | _validate_range | 223 | `_validate_range(maximum, offset, length, file_bytes)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pinned.append` | `read_guarded` | 268 |
| mutation | `directories_list.append` | `read_guarded` | 270 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `current_manifest_format` | `path.exists` | 240 |
| unresolved_call | `current_manifest_format` | `path.is_symlink` | 240 |
| unresolved_call | `current_manifest_format` | `(path.parent / '.llm-wiki-manifest').exists` | 241 |
| external_call | `current_manifest_format` | `json.loads` | 245 |
| step_limit | `build_knowledge_commit_plan` | `first 12 steps` | 0 |
| truncated_flow | `build_knowledge_commit_plan` | `depth limit` | 0 |

## Behavior

This flow starts at `build_knowledge_commit_plan` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
