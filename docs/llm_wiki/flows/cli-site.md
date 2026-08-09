# site

**Entry point:** `run` (`cli`)
**Source:** [site_cmd](../modules/site_cmd.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [config](../modules/config.md), [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), and 18 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_projection](../modules/knowledge_projection.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [site_cmd](../modules/site_cmd.md)
- [site_export](../modules/site_export.md)
- [site_html_check](../modules/site_html_check.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_media](../modules/wiki_media.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as getattr
    participant p2 as validate_path
    participant p3 as PathValidationError
    participant p4 as resolve
    participant p5 as cwd
    participant p6 as relative_to
    participant p7 as _hub_requested
    participant p8 as bool
    participant p9 as _validate_hub_args
    participant p10 as list
    participant p11 as _load_hub_knowledge_projections
    participant p12 as _knowledge_metadata
    participant p13 as SiteExportError
    participant p14 as join
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0-->>p1: getattr
    p0->>p2: validate_path
    p2->>p3: PathValidationError
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p6: relative_to
    p2->>p3: PathValidationError
    p0->>p7: _hub_requested
    p7-->>p8: bool
    p7-->>p1: getattr
    p7-->>p1: getattr
    p0->>p9: _validate_hub_args
    p9-->>p1: getattr
    p9-->>p10: list
    p9-->>p1: getattr
    p9->>p2: validate_path
    p9->>p2: validate_path
    p0->>p11: _load_hub_knowledge_projections
    p11->>p12: _knowledge_metadata
    p12-->>p1: getattr
    p12-->>p1: getattr
    p12-->>p1: getattr
    p12->>p13: SiteExportError
    p12-->>p14: join
    p12->>p13: SiteExportError
```

> Call sequence diagram shows 30 of 2452 interactions; 2422 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr"]
    s3["3. getattr"]
    s4["4. getattr"]
    s5["5. getattr"]
    s6["6. validate_path"]
    s7["7. PathValidationError"]
    s8["8. resolve"]
    s9["9. cwd"]
    s10["10. resolve"]
    s11["11. cwd"]
    s12["12. relative_to"]
    s1 -. "getattr(args, 'site_action', None)" .-> s2
    s1 -. "getattr(args, 'output_format', 'text')" .-> s3
    s1 -. "getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s4
    s1 -. "getattr(args, 'out_dir')" .-> s5
    s1 -->|"validate_path(out_dir, '--out-dir')"| s6
    s6 -->|"PathValidationError(...)"| s7
    s6 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s8
    s6 -. "Path.cwd(data not statically known)" .-> s9
    s6 -. "Path.cwd().resolve(data not statically known)" .-> s10
    s6 -. "Path.cwd(data not statically known)" .-> s11
    s6 -. "resolved.relative_to(cwd)" .-> s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    click s1 "../modules/site_cmd.md"
    click s6 "../modules/config.md"
    click s7 "../modules/config.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `DEFAULT_WIKI_DIR`, `DEFAULT_WIKI_DIR`, `SiteExportError`, `sys`, `sys` | - | `none`, `none` |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `getattr` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `relative_to` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr | 138 | `getattr(args, 'site_action', None)` |
| run | getattr | 139 | `getattr(args, 'output_format', 'text')` |
| run | getattr | 143 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr | 144 | `getattr(args, 'out_dir')` |
| run | validate_path | 145 | `validate_path(out_dir, '--out-dir')` |
| validate_path | PathValidationError | 128 | `PathValidationError(...)` |
| validate_path | resolve | 131 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 131 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 132 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 132 | `Path.cwd(data not statically known)` |
| validate_path | relative_to | 134 | `resolved.relative_to(cwd)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 229 |
| output | `print` | `run` | 232 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `run` | `getattr` | 138 |
| unresolved_call | `run` | `getattr` | 139 |
| unresolved_call | `run` | `getattr` | 143 |
| unresolved_call | `run` | `getattr` | 144 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 131 |
| external_call | `validate_path` | `Path.cwd` | 131 |
| external_call | `validate_path` | `Path.cwd().resolve` | 132 |
| external_call | `validate_path` | `Path.cwd` | 132 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 134 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
