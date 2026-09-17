# run

**Entry point:** `run` (`api`)
**Source:** [knowledge_cmd](../modules/knowledge_cmd.md)
**Modules touched:** [api](../modules/api.md), [canonical_json](../modules/canonical_json.md), [common](../modules/common.md), [concept_identity](../modules/concept_identity.md), and 56 more

**Complete modules touched:**

- [api](../modules/api.md)
- [canonical_json](../modules/canonical_json.md)
- [common](../modules/common.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [immutable](../modules/immutable.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_audit](../modules/knowledge_audit.md)
- [knowledge_cmd](../modules/knowledge_cmd.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_coverage](../modules/knowledge_coverage.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [knowledge_storage_cmd](../modules/knowledge_storage_cmd.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [knowledge_stream_audit](../modules/knowledge_stream_audit.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [manifest_storage](../modules/manifest_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [plugins](../modules/plugins.md)
- [python_calls](../modules/python_calls.md)
- [python_imports](../modules/python_imports.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [storage_sort](../modules/storage_sort.md)
- [storage_spool](../modules/storage_spool.md)
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
    participant p0 as run (src/llm_wiki_cli/commands/knowledge_cmd.py)
    participant p1 as run (src/llm_wiki_cli/commands/knowledge_storage_cmd.py)
    participant p2 as _wiki_root
    participant p3 as Path (src/llm_wiki_cli/commands…owledge_cmd.py:_wiki_root)
    participant p4 as first_unsafe_path_component
    participant p5 as Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p6 as os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p7 as os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p8 as lexical.is_absolute
    participant p9 as Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p10 as list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p11 as pending_parts.pop
    participant p12 as current.lstat (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p13 as getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p14 as stat.S_ISLNK (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p15 as bool (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p16 as trusted_symlink_owner
    participant p17 as callable (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p18 as os.readlink
    participant p19 as link_target.is_absolute
    participant p20 as GovernanceError
    p0->>p1: run (src/llm_wiki_cli/commands/knowledge_storage_cmd.py)
    p1->>p2: _wiki_root
    p2-->>p3: Path (src/llm_wiki_cli/commands…owledge_cmd.py:_wiki_root)
    p2->>p4: first_unsafe_path_component
    p4-->>p5: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p6: os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p5: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p7: os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p8: lexical.is_absolute
    p4-->>p9: Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p5: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p10: list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p11: pending_parts.pop
    p4-->>p12: current.lstat (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p13: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p13: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p14: stat.S_ISLNK (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p15: bool (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p15: bool (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p13: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p16: trusted_symlink_owner
    p4-->>p17: callable (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p13: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p5: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p5: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p18: os.readlink
    p4-->>p19: link_target.is_absolute
    p4-->>p5: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p4-->>p10: list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p2->>p20: GovernanceError
```

> Call sequence diagram shows 30 of 4121 interactions; 4091 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    s2["2. run (src/llm_wiki_cli/commands/knowledge_storage_cmd.py)"]
    s3["3. _wiki_root"]
    s4["4. Path (src/llm_wiki_cli/commands…owledge_cmd.py:_wiki_root)"]
    s5["5. first_unsafe_path_component"]
    s6["6. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s7["7. os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s8["8. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s9["9. os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s10["10. lexical.is_absolute"]
    s11["11. Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s12["12. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s1 -->|"run (src/llm_wiki_cli/commands/knowledge_storage_cmd.py)(args)"| s2
    s2 -->|"_wiki_root(args.wiki_dir)"| s3
    s3 -. "Path (src/llm_wiki_cli/commands…owledge_cmd.py:_wiki_root)(value)" .-> s4
    s3 -->|"first_unsafe_path_component(root)"| s5
    s5 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))" .-> s6
    s5 -. "os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)(path)" .-> s7
    s5 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.path.abspath(...))" .-> s8
    s5 -. "os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)(lexical)" .-> s9
    s5 -. "lexical.is_absolute(data not statically known)" .-> s10
    s5 -. "Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)(data not statically known)" .-> s11
    s5 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(absolute.anchor)" .-> s12
    b0["output print"]
    s2 -. "output print" .-> b0
    b1["output print"]
    s2 -. "output print" .-> b1
    b2["mutation pending_parts.pop"]
    s5 -. "mutation pending_parts.pop" .-> b2
    click s1 "../modules/knowledge_cmd.md"
    click s2 "../modules/knowledge_storage_cmd.md"
    click s3 "../modules/knowledge_cmd.md"
    click s5 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run (src/llm_wiki_cli/commands/knowledge_cmd.py)` | `args` | `Lifecycle`, `Lifecycle`, `Lifecycle`, `Lifecycle` | - | - |
| `run (src/llm_wiki_cli/commands/knowledge_storage_cmd.py)` | `args` | - | - | - |
| `_wiki_root` | `value: str \| Path` | - | - | `root` |
| `Path (src/llm_wiki_cli/commands…owledge_cmd.py:_wiki_root)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `lexical.is_absolute` | - | - | - | - |
| `Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run (src/llm_wiki_cli/commands/knowledge_cmd.py) | run (src/llm_wiki_cli/commands/knowledge_storage_cmd.py) | 965 | `run_storage(args)` |
| run (src/llm_wiki_cli/commands/knowledge_storage_cmd.py) | _wiki_root | 17 | `_wiki_root(args.wiki_dir)` |
| _wiki_root | Path (src/llm_wiki_cli/commands…owledge_cmd.py:_wiki_root) | 106 | `Path(value)` |
| _wiki_root | first_unsafe_path_component | 107 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |
| first_unsafe_path_component | os.fspath (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `os.fspath(path)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 59 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | os.path.abspath (src/llm_wiki_cli/services…rst_unsafe_path_component) | 59 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | lexical.is_absolute | 60 | `lexical.is_absolute(data not statically known)` |
| first_unsafe_path_component | Path.cwd (src/llm_wiki_cli/services…rst_unsafe_path_component) | 66 | `Path.cwd(data not statically known)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 67 | `Path(absolute.anchor)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 56 |
| output | `print` | `run` | 58 |
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 71 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `first_unsafe_path_component` | `os.fspath` | 51 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 59 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 60 |
| external_call | `first_unsafe_path_component` | `Path.cwd` | 66 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
