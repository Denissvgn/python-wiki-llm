# site

**Entry point:** `run` (`cli`)
**Source:** [site_cmd](../modules/site_cmd.md)
**Modules touched:** [bootstrap_recovery](../modules/bootstrap_recovery.md), [concept_identity](../modules/concept_identity.md), [config](../modules/config.md), [filesystem_guard](../modules/filesystem_guard.md), and 27 more

**Complete modules touched:**

- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [concept_identity](../modules/concept_identity.md)
- [config](../modules/config.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [implementation_evidence](../modules/implementation_evidence.md)
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
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [site_cmd](../modules/site_cmd.md)
- [site_export](../modules/site_export.md)
- [site_html_check](../modules/site_html_check.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as validate_path
    participant p2 as _validate_hub_args
    participant p3 as _load_hub_knowledge_projections
    participant p4 as export_site_hub
    participant p5 as _print_report
    participant p6 as check_site_hub
    participant p7 as _hub_requested
    participant p8 as _knowledge_metadata
    participant p9 as _load_knowledge_projection
    participant p10 as export_site_mirror
    participant p11 as check_site_mirror
    participant p12 as _validate_format
    participant p13 as _validate_link_mode (src/llm_wiki_cli/services/site_export.py)
    participant p14 as resolve_site_hub_sources
    participant p15 as _validate_file_friendly
    participant p16 as _validate_profile
    participant p17 as render_report_text
    participant p18 as _preflight_hub_knowledge_projections
    participant p19 as _preflight_hub_root_output_collisions
    participant p20 as _validate_output_base
    participant p21 as _preflight_existing_unexpected_knowledge_pages
    participant p22 as _expected_hub_markdown_paths
    participant p23 as _source_identity
    participant p24 as _build_publication_selection
    participant p25 as _check_publication_receipt
    participant p26 as _preflight_publication_export
    participant p27 as _selection_mismatch_issues
    participant p28 as _begin_publication_export
    participant p29 as getattr (src/llm_wiki_cli/commands/site_cmd.py:run)
    participant p30 as (…).resolve (src/llm_wiki_cli/config.py:validate_path)
    p0->>p1: validate_path
    p0->>p2: _validate_hub_args
    p0->>p3: _load_hub_knowledge_projections
    p0->>p4: export_site_hub
    p0->>p5: _print_report
    p0->>p6: check_site_hub
    p0->>p7: _hub_requested
    p0->>p8: _knowledge_metadata
    p0->>p9: _load_knowledge_projection
    p0->>p10: export_site_mirror
    p0->>p11: check_site_mirror
    p4->>p12: _validate_format
    p6->>p13: _validate_link_mode (src/llm_wiki_cli/services/site_export.py)
    p3->>p14: resolve_site_hub_sources
    p4->>p15: _validate_file_friendly
    p4->>p16: _validate_profile
    p5->>p17: render_report_text
    p4->>p18: _preflight_hub_knowledge_projections
    p4->>p19: _preflight_hub_root_output_collisions
    p4->>p20: _validate_output_base
    p4->>p21: _preflight_existing_unexpected_knowledge_pages
    p4->>p22: _expected_hub_markdown_paths
    p4->>p23: _source_identity
    p4->>p24: _build_publication_selection
    p6->>p25: _check_publication_receipt
    p4->>p26: _preflight_publication_export
    p6->>p27: _selection_mismatch_issues
    p4->>p28: _begin_publication_export
    p0-->>p29: getattr (src/llm_wiki_cli/commands/site_cmd.py:run)(args, 'site_action', None)
    p1-->>p30: (…).resolve (src/llm_wiki_cli/config.py:validate_path)
```

> Call sequence diagram shows 30 of 2532 interactions; 2502 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 681 (680 omitted); unresolved 1 of 799 (798 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/commands/site_cmd.py:run` | 1 | - | external | 37 |
| `src/llm_wiki_cli/config.py:validate_path` | 6 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 6 | - | external | 2 |
| `src/llm_wiki_cli/config.py:validate_path` | 6 | - | unresolved | 2 |
| `src/llm_wiki_cli/commands/site_cmd.py:_hub_requested` | 14 | - | external | 3 |
| `src/llm_wiki_cli/commands/site_cmd.py:_validate_hub_args` | 18 | - | external | 3 |
| `src/llm_wiki_cli/commands/site_cmd.py:_validate_hub_args` | 18 | [src/llm_wiki_cli/config.py](../modules/config.md) | internal | 2 |
| `src/llm_wiki_cli/commands/site_cmd.py:_load_hub_knowledge_projections` | 24 | [src/llm_wiki_cli/commands/site_cmd.py](../modules/site_cmd.md) | internal | 2 |
> Omission summary shows 8 of 548 groups; 540 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/site_cmd.py:run)"]
    s3["3. getattr (src/llm_wiki_cli/commands/site_cmd.py:run)"]
    s4["4. getattr (src/llm_wiki_cli/commands/site_cmd.py:run)"]
    s5["5. getattr (src/llm_wiki_cli/commands/site_cmd.py:run)"]
    s6["6. validate_path"]
    s7["7. PathValidationError"]
    s8["8. (…).resolve (src/llm_wiki_cli/config.py:validate_path)"]
    s9["9. Path.cwd"]
    s10["10. Path.cwd().resolve"]
    s11["11. Path.cwd"]
    s12["12. resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)"]
    s1 -. "getattr (src/llm_wiki_cli/commands/site_cmd.py:run)(args, 'site_action', None)" .-> s2
    s1 -. "getattr (src/llm_wiki_cli/commands/site_cmd.py:run)(args, 'output_format', 'text')" .-> s3
    s1 -. "getattr (src/llm_wiki_cli/commands/site_cmd.py:run)(args, 'wiki_dir', DEFAULT_WIKI_DIR)" .-> s4
    s1 -. "getattr (src/llm_wiki_cli/commands/site_cmd.py:run)(args, 'out_dir')" .-> s5
    s1 -->|"validate_path(out_dir, '--out-dir')"| s6
    s6 -->|"PathValidationError(...)"| s7
    s6 -. "(…).resolve (src/llm_wiki_cli/config.py:validate_path)(data not statically known)" .-> s8
    s6 -. "Path.cwd(data not statically known)" .-> s9
    s6 -. "Path.cwd().resolve(data not statically known)" .-> s10
    s6 -. "Path.cwd(data not statically known)" .-> s11
    s6 -. "resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)(cwd)" .-> s12
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
| `getattr (src/llm_wiki_cli/commands/site_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/site_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/site_cmd.py:run)` | - | - | - | - |
| `getattr (src/llm_wiki_cli/commands/site_cmd.py:run)` | - | - | - | - |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |
| `Path.cwd` | - | - | - | - |
| `Path.cwd().resolve` | - | - | - | - |
| `Path.cwd` | - | - | - | - |
| `resolved.relative_to (src/llm_wiki_cli/config.py:validate_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/site_cmd.py:run) | 138 | `getattr(args, 'site_action', None)` |
| run | getattr (src/llm_wiki_cli/commands/site_cmd.py:run) | 139 | `getattr(args, 'output_format', 'text')` |
| run | getattr (src/llm_wiki_cli/commands/site_cmd.py:run) | 143 | `getattr(args, 'wiki_dir', DEFAULT_WIKI_DIR)` |
| run | getattr (src/llm_wiki_cli/commands/site_cmd.py:run) | 144 | `getattr(args, 'out_dir')` |
| run | validate_path | 145 | `validate_path(out_dir, '--out-dir')` |
| validate_path | PathValidationError | 134 | `PathValidationError(...)` |
| validate_path | (…).resolve (src/llm_wiki_cli/config.py:validate_path) | 135 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | Path.cwd | 135 | `Path.cwd(data not statically known)` |
| validate_path | Path.cwd().resolve | 136 | `Path.cwd().resolve(data not statically known)` |
| validate_path | Path.cwd | 136 | `Path.cwd(data not statically known)` |
| validate_path | resolved.relative_to (src/llm_wiki_cli/config.py:validate_path) | 138 | `resolved.relative_to(cwd)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 229 |
| output | `print` | `run` | 232 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 138 |
| external_call | `run` | `getattr` | 139 |
| external_call | `run` | `getattr` | 143 |
| external_call | `run` | `getattr` | 144 |
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 135 |
| external_call | `validate_path` | `Path.cwd` | 135 |
| unresolved_call | `validate_path` | `Path.cwd().resolve` | 136 |
| external_call | `validate_path` | `Path.cwd` | 136 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 138 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
