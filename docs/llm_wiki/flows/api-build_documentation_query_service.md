# build_documentation_query_service

**Entry point:** `build_documentation_query_service` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [common](../modules/common.md), [config](../modules/config.md), [context_packet](../modules/context_packet.md), and 12 more

**Complete modules touched:**

- [api](../modules/api.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [manifest_storage](../modules/manifest_storage.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_documentation_query_service
    participant p1 as isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service)
    participant p2 as InvalidRequestError
    participant p3 as normalize_documentation_query_limit
    participant p4 as isinstance (src/llm_wiki_cli/services…documentation_query_limit)
    participant p5 as DocumentationQueryError
    participant p6 as min (src/llm_wiki_cli/services…documentation_query_limit)
    participant p7 as validate_source_root
    participant p8 as validate_path
    participant p9 as PathValidationError
    participant p10 as (…).resolve
    participant p11 as Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    participant p12 as Path.cwd().resolve
    participant p13 as resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    participant p14 as Path(…).expanduser
    participant p15 as Path (src/llm_wiki_cli/config.py:validate_source_root)
    participant p16 as candidate.is_absolute
    participant p17 as Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    participant p18 as candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    participant p19 as resolved.is_dir
    participant p20 as os.path.abspath (src/llm_wiki_cli/config.py:validate_source_root)
    participant p21 as windows_current_user_sid
    participant p22 as WindowsSecurityGuardError
    p0-->>p1: isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service)
    p0->>p2: InvalidRequestError
    p0-->>p1: isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service)
    p0->>p2: InvalidRequestError
    p0->>p3: normalize_documentation_query_limit
    p3-->>p4: isinstance (src/llm_wiki_cli/services…documentation_query_limit)
    p3-->>p4: isinstance (src/llm_wiki_cli/services…documentation_query_limit)
    p3->>p5: DocumentationQueryError
    p3-->>p6: min (src/llm_wiki_cli/services…documentation_query_limit)
    p0->>p7: validate_source_root
    p7->>p8: validate_path
    p8->>p9: PathValidationError
    p8-->>p10: (…).resolve
    p8-->>p11: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p8-->>p12: Path.cwd().resolve
    p8-->>p11: Path.cwd (src/llm_wiki_cli/config.py:validate_path)
    p8-->>p13: resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)
    p8->>p9: PathValidationError
    p7-->>p14: Path(…).expanduser
    p7-->>p15: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p7-->>p16: candidate.is_absolute
    p7-->>p17: Path.cwd (src/llm_wiki_cli/config.py:validate_source_root)
    p7-->>p18: candidate.resolve (src/llm_wiki_cli/config.py:validate_source_root)
    p7->>p9: PathValidationError
    p7-->>p19: resolved.is_dir
    p7->>p9: PathValidationError
    p7-->>p15: Path (src/llm_wiki_cli/config.py:validate_source_root)
    p7-->>p20: os.path.abspath (src/llm_wiki_cli/config.py:validate_source_root)
    p7->>p21: windows_current_user_sid
    p21->>p22: WindowsSecurityGuardError
```

> Call sequence diagram shows 30 of 1037 interactions; 1007 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_documentation_query_service"]
    s2["2. isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service)"]
    s3["3. InvalidRequestError"]
    s4["4. isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service)"]
    s5["5. InvalidRequestError"]
    s6["6. normalize_documentation_query_limit"]
    s7["7. isinstance (src/llm_wiki_cli/services…documentation_query_limit)"]
    s8["8. isinstance (src/llm_wiki_cli/services…documentation_query_limit)"]
    s9["9. DocumentationQueryError"]
    s10["10. min (src/llm_wiki_cli/services…documentation_query_limit)"]
    s11["11. validate_source_root"]
    s12["12. validate_path"]
    s1 -. "isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service)(value, bool)" .-> s2
    s1 -->|"InvalidRequestError('must be a boolean', code='invalid-request', details={...})"| s3
    s1 -. "isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service)(helper_cache_dir, (...))" .-> s4
    s1 -->|"InvalidRequestError('must be a path', code='invalid-request', details={...})"| s5
    s1 -->|"normalize_documentation_query_limit(limit)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…documentation_query_limit)(value, bool)" .-> s7
    s6 -. "isinstance (src/llm_wiki_cli/services…documentation_query_limit)(value, int)" .-> s8
    s6 -->|"DocumentationQueryError('limit must be a positive integer.')"| s9
    s6 -. "min (src/llm_wiki_cli/services…documentation_query_limit)(value, MAX_DOCUMENTATION_QUERY_LIMIT)" .-> s10
    s1 -->|"validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)"| s11
    s11 -->|"validate_path(path, label)"| s12
    click s1 "../modules/api.md"
    click s3 "../modules/api.md"
    click s5 "../modules/api.md"
    click s6 "../modules/documentation_query_builder.md"
    click s9 "../modules/documentation_queries.md"
    click s11 "../modules/config.md"
    click s12 "../modules/config.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_documentation_query_service` | `src_dir: str`, `wiki_dir: str`, `limit: int`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None`, `helper_cache_dir: str \| Path \| None` | `Path`, `extract_cmd`, `extract_cmd`, `extract_cmd`, `build_flow`, `evaluate_surface_index`, `context_cmd`, `context_cmd` | - | `build_live_documentation_query_service(...)` |
| `isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service)` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service)` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `normalize_documentation_query_limit` | `value: object` | `MAX_DOCUMENTATION_QUERY_LIMIT` | - | `min(...)` |
| `isinstance (src/llm_wiki_cli/services…documentation_query_limit)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…documentation_query_limit)` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `min (src/llm_wiki_cli/services…documentation_query_limit)` | - | - | - | - |
| `validate_source_root` | `path: str`, `label: str`, `allow_external: bool` | `sys`, `os`, `WindowsSecurityGuardError`, `sys` | - | `validate_path(...)`, `resolved` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_documentation_query_service | isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service) | 1630 | `isinstance(value, bool)` |
| build_documentation_query_service | InvalidRequestError | 1631 | `InvalidRequestError('must be a boolean', code='invalid-request', details={...})` |
| build_documentation_query_service | isinstance (src/llm_wiki_cli/api.py:b…cumentation_query_service) | 1636 | `isinstance(helper_cache_dir, (...))` |
| build_documentation_query_service | InvalidRequestError | 1639 | `InvalidRequestError('must be a path', code='invalid-request', details={...})` |
| build_documentation_query_service | normalize_documentation_query_limit | 1644 | `normalize_documentation_query_limit(limit)` |
| normalize_documentation_query_limit | isinstance (src/llm_wiki_cli/services…documentation_query_limit) | 52 | `isinstance(value, bool)` |
| normalize_documentation_query_limit | isinstance (src/llm_wiki_cli/services…documentation_query_limit) | 52 | `isinstance(value, int)` |
| normalize_documentation_query_limit | DocumentationQueryError | 53 | `DocumentationQueryError('limit must be a positive integer.')` |
| normalize_documentation_query_limit | min (src/llm_wiki_cli/services…documentation_query_limit) | 54 | `min(value, MAX_DOCUMENTATION_QUERY_LIMIT)` |
| build_documentation_query_service | validate_source_root | 1645 | `validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)` |
| validate_source_root | validate_path | 160 | `validate_path(path, label)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_documentation_query_service` | `isinstance` | 1630 |
| external_call | `build_documentation_query_service` | `isinstance` | 1636 |
| external_call | `normalize_documentation_query_limit` | `isinstance` | 52 |
| external_call | `normalize_documentation_query_limit` | `min` | 54 |
| step_limit | `build_documentation_query_service` | `first 12 steps` | 0 |
| truncated_flow | `build_documentation_query_service` | `depth limit` | 0 |

## Behavior

This flow starts at `build_documentation_query_service` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
