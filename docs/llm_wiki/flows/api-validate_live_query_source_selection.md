# validate_live_query_source_selection

**Entry point:** `validate_live_query_source_selection` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), [documentation_queries](../modules/documentation_queries.md), and 10 more

**Complete modules touched:**

- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_state](../modules/maintenance_state.md)
- [manifest_storage](../modules/manifest_storage.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_live_query_source_selection
    participant p1 as SyncManifest.load
    participant p2 as _wiki_has_persisted_read_state
    participant p3 as DocumentationQueryError
    participant p4 as validate_persisted_source_selection_identity
    participant p5 as str (src/llm_wiki_cli/services…ve_query_source_selection)
    participant p6 as manifest_path.exists
    participant p7 as wiki_root.is_dir
    participant p8 as source_selection_identity_from_generation_inputs
    participant p9 as FileNotFoundError
    participant p10 as os.walk
    participant p11 as _validated_identity
    participant p12 as json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    participant p13 as (…).is_symlink
    participant p14 as source_selection_inputs_from_generation_inputs
    participant p15 as manifest_path.read_text
    participant p16 as Path (src/llm_wiki_cli/services…_has_persisted_read_state)
    participant p17 as _validated_selection_inputs
    participant p18 as isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    participant p19 as any (src/llm_wiki_cli/services…_has_persisted_read_state)
    participant p20 as SourceSelectionError
    participant p21 as data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    participant p22 as StorageReadSession
    participant p23 as StorageReadSession.read
    participant p24 as SyncManifest.from_payload
    participant p25 as decode_bytes
    p0->>p1: SyncManifest.load
    p0->>p2: _wiki_has_persisted_read_state
    p0->>p3: DocumentationQueryError
    p0->>p3: DocumentationQueryError
    p0->>p3: DocumentationQueryError
    p0->>p4: validate_persisted_source_selection_identity
    p0->>p4: validate_persisted_source_selection_identity
    p0->>p3: DocumentationQueryError
    p0-->>p5: str (src/llm_wiki_cli/services…ve_query_source_selection)(exc)
    p1-->>p6: manifest_path.exists
    p2-->>p7: wiki_root.is_dir
    p4->>p8: source_selection_identity_from_generation_inputs
    p1-->>p9: FileNotFoundError(manifest_path)
    p2-->>p10: os.walk(wiki_root, followlinks=False)
    p4->>p11: _validated_identity
    p1-->>p12: json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)(manifest_path.read_text(...), object_pairs_hook=unique_object, parse_constant=reject_constant)
    p2-->>p13: (…).is_symlink
    p4->>p14: source_selection_inputs_from_generation_inputs
    p1-->>p15: manifest_path.read_text(encoding='utf-8')
    p2-->>p16: Path (src/llm_wiki_cli/services…_has_persisted_read_state)(root)
    p4->>p17: _validated_selection_inputs
    p1-->>p18: isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load)(data, dict)
    p2-->>p19: any (src/llm_wiki_cli/services…_has_persisted_read_state)(...)
    p4->>p20: SourceSelectionError
    p1-->>p21: data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load)('version')
    p4->>p20: SourceSelectionError
    p1->>p22: StorageReadSession
    p1->>p23: StorageReadSession.read
    p1->>p24: SyncManifest.from_payload
    p1->>p25: decode_bytes
```

> Call sequence diagram shows 30 of 491 interactions; 461 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 142 (135 omitted); unresolved 5 of 90 (85 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:StorageReadSession.read` | 10 | [src/llm_wiki_cli/services/knowledge_storage_io.py](../modules/knowledge_storage_io.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_require_relative_name` | 11 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:is_portable_relative_path` | 12 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 13 | - | external | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 13 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 13 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 13 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:_require_relative_name` | 11 | [src/llm_wiki_cli/services/knowledge_storage.py](../modules/knowledge_storage.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_storage_io.py:StorageReadSession.read` | 10 | [src/llm_wiki_cli/services/knowledge_storage.py](../modules/knowledge_storage.md) | internal | 3 |
> Omission summary shows 8 of 140 groups; 132 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_live_query_source_selection"]
    s2["2. SyncManifest.load"]
    s3["3. manifest_path.exists"]
    s4["4. FileNotFoundError"]
    s5["5. json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)"]
    s6["6. manifest_path.read_text"]
    s7["7. isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load)"]
    s8["8. data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load)"]
    s9["9. StorageReadSession"]
    s10["10. StorageReadSession.read"]
    s11["11. _require_relative_name"]
    s12["12. is_portable_relative_path"]
    s1 -->|"SyncManifest.load(wiki_root)"| s2
    s2 -. "manifest_path.exists(data not statically known)" .-> s3
    s2 -. "FileNotFoundError(manifest_path)" .-> s4
    s2 -. "json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)(manifest_path.read_text(...), object_pairs_hook=unique_object, parse_constant=reject_constant)" .-> s5
    s2 -. "manifest_path.read_text(encoding='utf-8')" .-> s6
    s2 -. "isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load)(data, dict)" .-> s7
    s2 -. "data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load)('version')" .-> s8
    s2 -->|"StorageReadSession(wiki_dir)"| s9
    s2 -->|"StorageReadSession.read(MANIFEST_FILENAME, MAX_EXPANDED_BYTES)"| s10
    s10 -->|"_require_relative_name(relative)"| s11
    s11 -->|"is_portable_relative_path(relative)"| s12
    b0["filesystem_read manifest_path.read_text"]
    s2 -. "filesystem_read manifest_path.read_text" .-> b0
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/sync_manifest.md"
    click s9 "../modules/knowledge_storage_io.md"
    click s10 "../modules/knowledge_storage_io.md"
    click s11 "../modules/knowledge_storage_io.md"
    click s12 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_live_query_source_selection` | `source_root: Path`, `wiki_root: Path`, `live_identity: Mapping[str, object] \| None`, `live_selection_inputs: Mapping[str, object] \| None \| object`, `operation: str`, `allow_empty_wiki: bool` | `SyncManifestError`, `_UNSET_LIVE_SELECTION_INPUTS`, `SourceSelectionError` | - | `none` |
| `SyncManifest.load` | `wiki_dir: Path` | `MANIFEST_FILENAME`, `MANIFEST_FILENAME` | - | `manifest`, `cls.from_payload(...)` |
| `manifest_path.exists` | - | - | - | - |
| `FileNotFoundError` | - | - | - | - |
| `json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)` | - | - | - | - |
| `manifest_path.read_text` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load)` | - | - | - | - |
| `data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load)` | - | - | - | - |
| `StorageReadSession` | - | - | - | - |
| `StorageReadSession.read` | `relative: str`, `maximum: int` | `self.maximum`, `self.bytes_read`, `self.root`, `KnowledgeStorageError` | `self.bytes_read`, `self.reads`, `self.observations[...]` | `observed.content` |
| `_require_relative_name` | `relative: str` | - | - | - |
| `is_portable_relative_path` | `value: object`, `normalize_backslashes: bool` | `SharedValidationError` | - | `False`, `True` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_live_query_source_selection | SyncManifest.load | 302 | `SyncManifest.load(wiki_root)` |
| SyncManifest.load | manifest_path.exists | 1160 | `manifest_path.exists(data not statically known)` |
| SyncManifest.load | FileNotFoundError | 1161 | `FileNotFoundError(manifest_path)` |
| SyncManifest.load | json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load) | 1180 | `json.loads(manifest_path.read_text(...), object_pairs_hook=unique_object, parse_constant=reject_constant)` |
| SyncManifest.load | manifest_path.read_text | 1181 | `manifest_path.read_text(encoding='utf-8')` |
| SyncManifest.load | isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load) | 1185 | `isinstance(data, dict)` |
| SyncManifest.load | data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load) | 1185 | `data.get('version')` |
| SyncManifest.load | StorageReadSession | 1188 | `StorageReadSession(wiki_dir)` |
| SyncManifest.load | StorageReadSession.read | 1189 | `session.read(MANIFEST_FILENAME, MAX_EXPANDED_BYTES)` |
| StorageReadSession.read | _require_relative_name | 354 | `_require_relative_name(relative)` |
| _require_relative_name | is_portable_relative_path | 44 | `is_portable_relative_path(relative)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `manifest_path.read_text` | `SyncManifest.load` | 1181 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `SyncManifest.load` | `manifest_path.exists` | 1160 |
| external_call | `SyncManifest.load` | `FileNotFoundError` | 1161 |
| external_call | `SyncManifest.load` | `json.loads` | 1180 |
| external_call | `SyncManifest.load` | `isinstance` | 1185 |
| unresolved_call | `SyncManifest.load` | `data.get` | 1185 |
| step_limit | `validate_live_query_source_selection` | `first 12 steps` | 0 |
| truncated_flow | `validate_live_query_source_selection` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_live_query_source_selection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
