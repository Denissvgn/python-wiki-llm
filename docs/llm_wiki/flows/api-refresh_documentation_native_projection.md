# refresh_documentation_native_projection

**Entry point:** `refresh_documentation_native_projection` (`api`)
**Source:** [documentation_native](../modules/documentation_native.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), and 47 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [documentation_native](../modules/documentation_native.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [immutable](../modules/immutable.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [inventory_cache](../modules/inventory_cache.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [markdown_sections](../modules/markdown_sections.md)
- [packages](../modules/packages.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [progress](../modules/progress.md)
- [python_calls](../modules/python_calls.md)
- [python_contracts](../modules/python_contracts.md)
- [python_imports](../modules/python_imports.md)
- [python_observations](../modules/python_observations.md)
- [resource_diagnostics](../modules/resource_diagnostics.md)
- [section_ownership](../modules/section_ownership.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as refresh_documentation_native_projection
    participant p1 as _validated_directory
    participant p2 as Path(…).expanduser
    participant p3 as Path (src/llm_wiki_cli/services…e.py:_validated_directory)
    participant p4 as candidate.lstat
    participant p5 as DocumentationNativeError
    participant p6 as stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory)
    participant p7 as stat.S_ISDIR (src/llm_wiki_cli/services…e.py:_validated_directory)
    participant p8 as candidate.resolve (src/llm_wiki_cli/services…e.py:_validated_directory)
    participant p9 as _refresh_manifest_version
    participant p10 as json.loads (src/llm_wiki_cli/services…_refresh_manifest_version)
    participant p11 as path.read_text
    participant p12 as isinstance (src/llm_wiki_cli/services…_refresh_manifest_version)
    participant p13 as payload.get (src/llm_wiki_cli/services…_refresh_manifest_version)
    participant p14 as SyncManifest.load
    participant p15 as manifest_path.exists
    participant p16 as FileNotFoundError (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    participant p17 as json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    participant p18 as manifest_path.read_text
    participant p19 as SyncManifest.from_payload
    participant p20 as _mapping_value
    participant p21 as require_mapping
    participant p22 as isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    participant p23 as key.encode
    p0->>p1: _validated_directory
    p1-->>p2: Path(…).expanduser
    p1-->>p3: Path (src/llm_wiki_cli/services…e.py:_validated_directory)
    p1-->>p4: candidate.lstat
    p1->>p5: DocumentationNativeError
    p1-->>p6: stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory)
    p1-->>p7: stat.S_ISDIR (src/llm_wiki_cli/services…e.py:_validated_directory)
    p1->>p5: DocumentationNativeError
    p1-->>p8: candidate.resolve (src/llm_wiki_cli/services…e.py:_validated_directory)
    p0->>p1: _validated_directory
    p0->>p9: _refresh_manifest_version
    p9-->>p10: json.loads (src/llm_wiki_cli/services…_refresh_manifest_version)
    p9-->>p11: path.read_text
    p9->>p5: DocumentationNativeError
    p9-->>p12: isinstance (src/llm_wiki_cli/services…_refresh_manifest_version)
    p9->>p5: DocumentationNativeError
    p9-->>p13: payload.get (src/llm_wiki_cli/services…_refresh_manifest_version)
    p9->>p5: DocumentationNativeError
    p9-->>p12: isinstance (src/llm_wiki_cli/services…_refresh_manifest_version)
    p0->>p14: SyncManifest.load
    p14-->>p15: manifest_path.exists
    p14-->>p16: FileNotFoundError (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    p14-->>p17: json.loads (src/llm_wiki_cli/services…fest.py:SyncManifest.load)
    p14-->>p18: manifest_path.read_text
    p14->>p19: SyncManifest.from_payload
    p19->>p20: _mapping_value
    p20->>p21: require_mapping
    p21-->>p22: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p21-->>p22: isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)
    p21-->>p23: key.encode
```

> Call sequence diagram shows 30 of 4814 interactions; 4784 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. refresh_documentation_native_projection"]
    s2["2. _validated_directory"]
    s3["3. Path(…).expanduser"]
    s4["4. Path (src/llm_wiki_cli/services…e.py:_validated_directory)"]
    s5["5. candidate.lstat"]
    s6["6. DocumentationNativeError"]
    s7["7. stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory)"]
    s8["8. stat.S_ISDIR (src/llm_wiki_cli/services…e.py:_validated_directory)"]
    s9["9. DocumentationNativeError"]
    s10["10. candidate.resolve (src/llm_wiki_cli/services…e.py:_validated_directory)"]
    s11["11. _validated_directory"]
    s12["12. _refresh_manifest_version"]
    s1 -->|"_validated_directory(source_root, 'source_root')"| s2
    s2 -. "Path(…).expanduser(data not statically known)" .-> s3
    s2 -. "Path (src/llm_wiki_cli/services…e.py:_validated_directory)(value)" .-> s4
    s2 -. "candidate.lstat(data not statically known)" .-> s5
    s2 -->|"DocumentationNativeError(...)"| s6
    s2 -. "stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory)(metadata.st_mode)" .-> s7
    s2 -. "stat.S_ISDIR (src/llm_wiki_cli/services…e.py:_validated_directory)(metadata.st_mode)" .-> s8
    s2 -->|"DocumentationNativeError(...)"| s9
    s2 -. "candidate.resolve (src/llm_wiki_cli/services…e.py:_validated_directory)(data not statically known)" .-> s10
    s1 -->|"_validated_directory(wiki_root, 'wiki_root')"| s11
    s1 -->|"_refresh_manifest_version(wiki)"| s12
    b0["filesystem_read path.read_text"]
    s12 -. "filesystem_read path.read_text" .-> b0
    click s1 "../modules/documentation_native.md"
    click s2 "../modules/documentation_native.md"
    click s6 "../modules/documentation_native.md"
    click s9 "../modules/documentation_native.md"
    click s11 "../modules/documentation_native.md"
    click s12 "../modules/documentation_native.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `refresh_documentation_native_projection` | `source_root: str \| Path`, `wiki_root: str \| Path`, `trust_source_plugins: bool`, `helper_cache_dir: str \| Path \| None`, `source_selection: str \| Path \| None`, `fault_injector: Callable[[CommitStage], None] \| None` | `RUNTIME_GENERATION_OPTION_DEFAULTS`, `RUNTIME_GENERATION_OPTION_DEFAULTS`, `DocumentationNativeError` | - | `DocumentationNativeRefresh(...)` |
| `_validated_directory` | `value: str \| Path`, `field_name: str` | - | - | `candidate.resolve(...)` |
| `Path(…).expanduser` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…e.py:_validated_directory)` | - | - | - | - |
| `candidate.lstat` | - | - | - | - |
| `DocumentationNativeError` | - | - | - | - |
| `stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory)` | - | - | - | - |
| `stat.S_ISDIR (src/llm_wiki_cli/services…e.py:_validated_directory)` | - | - | - | - |
| `DocumentationNativeError` | - | - | - | - |
| `candidate.resolve (src/llm_wiki_cli/services…e.py:_validated_directory)` | - | - | - | - |
| `_validated_directory` | `value: str \| Path`, `field_name: str` | - | - | `candidate.resolve(...)` |
| `_refresh_manifest_version` | `wiki_root: Path` | `MANIFEST_FILENAME`, `Mapping`, `LEGACY_MANIFEST_VERSION`, `MANIFEST_VERSION`, `LEGACY_MANIFEST_VERSION`, `MANIFEST_VERSION` | - | `version` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| refresh_documentation_native_projection | _validated_directory | 313 | `_validated_directory(source_root, 'source_root')` |
| _validated_directory | Path(…).expanduser | 1078 | `Path(value).expanduser(data not statically known)` |
| _validated_directory | Path (src/llm_wiki_cli/services…e.py:_validated_directory) | 1078 | `Path(value)` |
| _validated_directory | candidate.lstat | 1080 | `candidate.lstat(data not statically known)` |
| _validated_directory | DocumentationNativeError | 1082 | `DocumentationNativeError(...)` |
| _validated_directory | stat.S_ISLNK (src/llm_wiki_cli/services…e.py:_validated_directory) | 1085 | `stat.S_ISLNK(metadata.st_mode)` |
| _validated_directory | stat.S_ISDIR (src/llm_wiki_cli/services…e.py:_validated_directory) | 1085 | `stat.S_ISDIR(metadata.st_mode)` |
| _validated_directory | DocumentationNativeError | 1086 | `DocumentationNativeError(...)` |
| _validated_directory | candidate.resolve (src/llm_wiki_cli/services…e.py:_validated_directory) | 1089 | `candidate.resolve(data not statically known)` |
| refresh_documentation_native_projection | _validated_directory | 314 | `_validated_directory(wiki_root, 'wiki_root')` |
| refresh_documentation_native_projection | _refresh_manifest_version | 315 | `_refresh_manifest_version(wiki)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| filesystem_read | `path.read_text` | `_refresh_manifest_version` | 943 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_validated_directory` | `Path(value).expanduser` | 1078 |
| unresolved_call | `_validated_directory` | `candidate.lstat` | 1080 |
| external_call | `_validated_directory` | `stat.S_ISLNK` | 1085 |
| external_call | `_validated_directory` | `stat.S_ISDIR` | 1085 |
| unresolved_call | `_validated_directory` | `candidate.resolve` | 1089 |
| step_limit | `refresh_documentation_native_projection` | `first 12 steps` | 0 |
| truncated_flow | `refresh_documentation_native_projection` | `depth limit` | 0 |

## Behavior

This flow starts at `refresh_documentation_native_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
