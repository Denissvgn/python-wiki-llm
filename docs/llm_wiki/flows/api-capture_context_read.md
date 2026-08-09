# capture_context_read

**Entry point:** `capture_context_read` (`api`)
**Source:** [context_packet](../modules/context_packet.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [context_packet](../modules/context_packet.md), [dependency_versions](../modules/dependency_versions.md), and 13 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [dependency_versions](../modules/dependency_versions.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [imports](../modules/imports.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as capture_context_read
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as callable
    participant p4 as validate_source_root
    participant p5 as validate_path
    participant p6 as PathValidationError
    participant p7 as resolve
    participant p8 as cwd
    participant p9 as relative_to
    participant p10 as resolve_source_selection
    participant p11 as capture_source_selection_inputs
    participant p12 as Path
    participant p13 as _resolve_snapshot_selection
    participant p14 as SourceSelectionError
    participant p15 as _override_text
    participant p16 as fspath
    participant p17 as _selection_path
    participant p18 as _require_selection_path
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: callable
    p0-->>p2: TypeError
    p0-->>p4: validate_source_root
    p0->>p5: validate_path
    p5->>p6: PathValidationError
    p5-->>p7: resolve
    p5-->>p8: cwd
    p5-->>p7: resolve
    p5-->>p8: cwd
    p5-->>p9: relative_to
    p5->>p6: PathValidationError
    p0-->>p10: resolve_source_selection
    p0->>p11: capture_source_selection_inputs
    p11-->>p7: resolve
    p11-->>p12: Path
    p11->>p13: _resolve_snapshot_selection
    p13->>p10: resolve_source_selection
    p10-->>p7: resolve
    p10-->>p12: Path
    p10->>p14: SourceSelectionError
    p10->>p15: _override_text
    p15-->>p16: fspath
    p15->>p14: SourceSelectionError
    p15-->>p1: isinstance
    p15->>p14: SourceSelectionError
    p15->>p17: _selection_path
    p17->>p18: _require_selection_path
    p17->>p14: SourceSelectionError
```

> Call sequence diagram shows 30 of 1436 interactions; 1406 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. capture_context_read"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. callable"]
    s5["5. TypeError"]
    s6["6. validate_source_root"]
    s7["7. validate_path"]
    s8["8. PathValidationError"]
    s9["9. resolve"]
    s10["10. cwd"]
    s11["11. resolve"]
    s12["12. cwd"]
    s1 -. "isinstance(read_only, bool)" .-> s2
    s1 -. "TypeError('read_only must be a boolean')" .-> s3
    s1 -. "callable(plan_reporter)" .-> s4
    s1 -. "TypeError('plan_reporter must be callable or None')" .-> s5
    s1 -. "context_service.validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)" .-> s6
    s1 -->|"validate_path(wiki_dir, '--wiki-dir')"| s7
    s7 -->|"PathValidationError(...)"| s8
    s7 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s9
    s7 -. "Path.cwd(data not statically known)" .-> s10
    s7 -. "Path.cwd().resolve(data not statically known)" .-> s11
    s7 -. "Path.cwd(data not statically known)" .-> s12
    click s1 "../modules/context_packet.md"
    click s7 "../modules/config.md"
    click s8 "../modules/config.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `capture_context_read` | `src_dir: str`, `wiki_dir: str`, `allow_external_src: bool`, `read_only: bool`, `job_request: ExtractionJobRequest \| None`, `plan_reporter: Callable[[ExtractionJobPlan], None] \| None`, `source_selection: str \| Path \| None` | `PathValidationError`, `DocumentationQueryError`, `context_service`, `InventoryResult`, `SourceSnapshot`, `DocumentationQueryError`, `DocumentationQueryError`, `DocumentationQueryError` | - | `CapturedContextRead(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `callable` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `validate_source_root` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| capture_context_read | isinstance | 498 | `isinstance(read_only, bool)` |
| capture_context_read | TypeError | 499 | `TypeError('read_only must be a boolean')` |
| capture_context_read | callable | 500 | `callable(plan_reporter)` |
| capture_context_read | TypeError | 501 | `TypeError('plan_reporter must be callable or None')` |
| capture_context_read | validate_source_root | 504 | `context_service.validate_source_root(src_dir, '--src-dir', allow_external=allow_external_src)` |
| capture_context_read | validate_path | 509 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 128 | `PathValidationError(...)` |
| validate_path | resolve | 131 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 131 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 132 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 132 | `Path.cwd(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `capture_context_read` | `isinstance` | 498 |
| unresolved_call | `capture_context_read` | `TypeError` | 499 |
| unresolved_call | `capture_context_read` | `callable` | 500 |
| unresolved_call | `capture_context_read` | `TypeError` | 501 |
| external_call | `capture_context_read` | `context_service.validate_source_root` | 504 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 131 |
| external_call | `validate_path` | `Path.cwd` | 131 |
| external_call | `validate_path` | `Path.cwd().resolve` | 132 |
| external_call | `validate_path` | `Path.cwd` | 132 |
| step_limit | `capture_context_read` | `first 12 steps` | 0 |
| truncated_flow | `capture_context_read` | `depth limit` | 0 |

## Behavior

This flow starts at `capture_context_read` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
