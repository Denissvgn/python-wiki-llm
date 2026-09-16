# validate_live_query_source_selection

**Entry point:** `validate_live_query_source_selection` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [common](../modules/common.md), [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), and 7 more

**Complete modules touched:**

- [common](../modules/common.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [manifest_storage](../modules/manifest_storage.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_live_query_source_selection
    participant p1 as SyncManifest.load
    participant p2 as manifest_path.exists
    participant p3 as FileNotFoundError
    participant p4 as json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    participant p5 as manifest_path.read_text
    participant p6 as isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    participant p7 as data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    participant p8 as StorageReadSession
    participant p9 as session.read
    participant p10 as SyncManifest.from_payload
    participant p11 as _mapping_value
    participant p12 as require_mapping
    participant p13 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p14 as key.encode
    participant p15 as SyncManifestError
    participant p16 as data.get (src/llm_wiki_cli/services…SyncManifest.from_payload)
    participant p17 as type
    participant p18 as ManifestStoreReader
    participant p19 as reader.materialize
    participant p20 as isinstance (src/llm_wiki_cli/services…SyncManifest.from_payload)
    participant p21 as _copy_sources
    p0->>p1: SyncManifest.load
    p1-->>p2: manifest_path.exists
    p1-->>p3: FileNotFoundError
    p1-->>p4: json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    p1-->>p5: manifest_path.read_text
    p1-->>p6: isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    p1-->>p7: data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    p1->>p8: StorageReadSession
    p1-->>p9: session.read
    p1->>p10: SyncManifest.from_payload
    p10->>p11: _mapping_value
    p11->>p12: require_mapping
    p12-->>p13: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p12-->>p13: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p12-->>p14: key.encode
    p11->>p15: SyncManifestError
    p11->>p15: SyncManifestError
    p10-->>p16: data.get (src/llm_wiki_cli/services…SyncManifest.from_payload)
    p10-->>p17: type
    p10->>p15: SyncManifestError
    p10->>p18: ManifestStoreReader
    p10->>p10: SyncManifest.from_payload
    p10-->>p19: reader.materialize
    p10-->>p20: isinstance (src/llm_wiki_cli/services…SyncManifest.from_payload)
    p10-->>p20: isinstance (src/llm_wiki_cli/services…SyncManifest.from_payload)
    p10->>p15: SyncManifestError
    p10->>p15: SyncManifestError
    p10->>p15: SyncManifestError
    p10->>p21: _copy_sources
    p21->>p11: _mapping_value
```

> Call sequence diagram shows 30 of 316 interactions; 286 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
    s10["10. session.read"]
    s11["11. SyncManifest.from_payload"]
    s12["12. _mapping_value"]
    s1 -->|"SyncManifest.load(wiki_root)"| s2
    s2 -. "manifest_path.exists(data not statically known)" .-> s3
    s2 -. "FileNotFoundError(manifest_path)" .-> s4
    s2 -. "json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)(manifest_path.read_text(...), object_pairs_hook=unique_object, parse_constant=reject_constant)" .-> s5
    s2 -. "manifest_path.read_text(encoding='utf-8')" .-> s6
    s2 -. "isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load)(data, dict)" .-> s7
    s2 -. "data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load)('version')" .-> s8
    s2 -->|"StorageReadSession(wiki_dir)"| s9
    s2 -. "session.read(MANIFEST_FILENAME, MAX_EXPANDED_BYTES)" .-> s10
    s2 -->|"SyncManifest.from_payload(decode_bytes(...), object_reader=session.read)"| s11
    s11 -->|"_mapping_value(value, 'manifest')"| s12
    b0["filesystem_read manifest_path.read_text"]
    s2 -. "filesystem_read manifest_path.read_text" .-> b0
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/sync_manifest.md"
    click s9 "../modules/knowledge_storage_io.md"
    click s11 "../modules/sync_manifest.md"
    click s12 "../modules/sync_manifest.md"
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
| `session.read` | - | - | - | - |
| `SyncManifest.from_payload` | `value: object`, `object_reader` | `MANIFEST_VERSION`, `LEGACY_MANIFEST_VERSION`, `Mapping`, `LEGACY_MANIFEST_VERSION`, `Mapping`, `LEGACY_MANIFEST_VERSION`, `Mapping`, `Mapping` | `manifest.storage_version`, `manifest.storage_objects`, `legacy_surfaces[...]`, `surfaces[...]` | `manifest`, `manifest`, `manifest` |
| `_mapping_value` | `value: object`, `field_name: str` | - | - | `require_mapping(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_live_query_source_selection | SyncManifest.load | 298 | `SyncManifest.load(wiki_root)` |
| SyncManifest.load | manifest_path.exists | 1125 | `manifest_path.exists(data not statically known)` |
| SyncManifest.load | FileNotFoundError | 1126 | `FileNotFoundError(manifest_path)` |
| SyncManifest.load | json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load) | 1145 | `json.loads(manifest_path.read_text(...), object_pairs_hook=unique_object, parse_constant=reject_constant)` |
| SyncManifest.load | manifest_path.read_text | 1146 | `manifest_path.read_text(encoding='utf-8')` |
| SyncManifest.load | isinstance (src/llm_wiki_cli/services…fest.py:SyncManifest.load) | 1150 | `isinstance(data, dict)` |
| SyncManifest.load | data.get (src/llm_wiki_cli/services…fest.py:SyncManifest.load) | 1150 | `data.get('version')` |
| SyncManifest.load | StorageReadSession | 1153 | `StorageReadSession(wiki_dir)` |
| SyncManifest.load | session.read | 1154 | `session.read(MANIFEST_FILENAME, MAX_EXPANDED_BYTES)` |
| SyncManifest.load | SyncManifest.from_payload | 1155 | `cls.from_payload(decode_bytes(...), object_reader=session.read)` |
| SyncManifest.from_payload | _mapping_value | 992 | `_mapping_value(value, 'manifest')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `manifest_path.read_text` | `SyncManifest.load` | 1146 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `SyncManifest.load` | `manifest_path.exists` | 1125 |
| external_call | `SyncManifest.load` | `FileNotFoundError` | 1126 |
| external_call | `SyncManifest.load` | `json.loads` | 1145 |
| external_call | `SyncManifest.load` | `isinstance` | 1150 |
| unresolved_call | `SyncManifest.load` | `data.get` | 1150 |
| unresolved_call | `SyncManifest.load` | `session.read` | 1154 |
| step_limit | `validate_live_query_source_selection` | `first 12 steps` | 0 |
| truncated_flow | `validate_live_query_source_selection` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_live_query_source_selection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
