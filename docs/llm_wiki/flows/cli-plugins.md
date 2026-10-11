# plugins

**Entry point:** `run` (`cli`)
**Source:** [plugins_cmd](../modules/plugins_cmd.md)
**Modules touched:** [config](../modules/config.md), [io](../modules/io.md), [plugin_samples](../modules/plugin_samples.md), [plugins](../modules/plugins.md), and 4 more

**Complete modules touched:**

- [config](../modules/config.md)
- [io](../modules/io.md)
- [plugin_samples](../modules/plugin_samples.md)
- [plugins](../modules/plugins.md)
- [plugins_cmd](../modules/plugins_cmd.md)
- [services_schema](../modules/services_schema.md)
- [validation](../modules/validation.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as run
    participant p1 as list_plugins
    participant p2 as export_sample
    participant p3 as validate_plugin
    participant p4 as validate_path
    participant p5 as remove_plugin
    participant p6 as strip_plugin_skill_blocks
    participant p7 as _render_components
    participant p8 as list_samples
    participant p9 as read_lock
    participant p10 as _resolve_sample_id
    participant p11 as _manifest_root
    participant p12 as require_safe_schema_path
    participant p13 as _sample_resource
    participant p14 as _ensure_no_reserved_plugin_sources
    participant p15 as _resolve_destination
    participant p16 as _prepare_destination
    participant p17 as _copy_resource_tree
    participant p18 as plugin_store
    participant p19 as strip_skill_blocks
    participant p20 as write_bytes_atomic
    participant p21 as _ensure_id
    participant p22 as write_lock
    participant p23 as _version_satisfies
    participant p24 as _normalize_component
    participant p25 as lock_path
    participant p26 as _ensure_entry_point
    participant p27 as _safe_component_path
    participant p28 as _validate_prompt_template_vcs_boundary
    participant p29 as getattr (src/llm_wiki_cli/commands/plugins_cmd.py:run)
    participant p30 as plugin.get
    p0->>p1: list_plugins
    p0->>p2: export_sample
    p0->>p3: validate_plugin
    p0->>p4: validate_path
    p0->>p5: remove_plugin
    p0->>p6: strip_plugin_skill_blocks
    p0->>p7: _render_components
    p0->>p8: list_samples
    p1->>p9: read_lock
    p2->>p10: _resolve_sample_id
    p3->>p11: _manifest_root
    p6->>p12: require_safe_schema_path
    p2->>p13: _sample_resource
    p3->>p14: _ensure_no_reserved_plugin_sources
    p2->>p15: _resolve_destination
    p2->>p16: _prepare_destination
    p2->>p17: _copy_resource_tree
    p5->>p18: plugin_store
    p6->>p19: strip_skill_blocks
    p6->>p20: write_bytes_atomic
    p3->>p21: _ensure_id
    p5->>p22: write_lock
    p3->>p23: _version_satisfies
    p3->>p24: _normalize_component
    p9->>p25: lock_path
    p24->>p26: _ensure_entry_point
    p24->>p27: _safe_component_path
    p24->>p28: _validate_prompt_template_vcs_boundary
    p0-->>p29: getattr (src/llm_wiki_cli/commands/plugins_cmd.py:run)(args, 'plugins_action', None)
    p7-->>p30: plugin.get('components', [...])
```

> Call sequence diagram shows 30 of 368 interactions; 338 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 121 (120 omitted); unresolved 1 of 133 (132 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/plugins.py:lock_path` | 5 | [src/llm_wiki_cli/services/plugins.py](../modules/plugins.md) | internal | 1 |
| `src/llm_wiki_cli/services/plugins.py:plugin_home` | 6 | - | external | 1 |
| `src/llm_wiki_cli/services/plugins.py:read_lock` | 4 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/plugins.py:read_lock` | 4 | [src/llm_wiki_cli/services/plugins.py](../modules/plugins.md) | internal | 3 |
| `src/llm_wiki_cli/services/plugins.py:read_lock` | 4 | - | external | 3 |
| `src/llm_wiki_cli/services/plugins.py:list_plugins` | 3 | - | external | 1 |
| `src/llm_wiki_cli/services/plugins.py:list_plugins` | 3 | - | unresolved | 2 |
| `src/llm_wiki_cli/commands/plugins_cmd.py:run` | 1 | - | external | 28 |
> Omission summary shows 8 of 98 groups; 90 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. run"]
    s2["2. getattr (src/llm_wiki_cli/commands/plugins_cmd.py:run)"]
    s3["3. list_plugins"]
    s4["4. read_lock"]
    s5["5. lock_path"]
    s6["6. plugin_home"]
    s7["7. Path (src/llm_wiki_cli/services/plugins.py:plugin_home)"]
    s8["8. path.exists (src/llm_wiki_cli/services/plugins.py:read_lock)"]
    s9["9. _default_lock"]
    s10["10. json.loads (src/llm_wiki_cli/services/plugins.py:read_lock)"]
    s11["11. path.read_text"]
    s12["12. PluginError"]
    s1 -. "getattr (src/llm_wiki_cli/commands/plugins_cmd.py:run)(args, 'plugins_action', None)" .-> s2
    s1 -->|"list_plugins(data not statically known)"| s3
    s3 -->|"read_lock(root)"| s4
    s4 -->|"lock_path(root)"| s5
    s5 -->|"plugin_home(root)"| s6
    s6 -. "Path (src/llm_wiki_cli/services/plugins.py:plugin_home)(root)" .-> s7
    s4 -. "path.exists (src/llm_wiki_cli/services/plugins.py:read_lock)(data not statically known)" .-> s8
    s4 -->|"_default_lock(data not statically known)"| s9
    s4 -. "json.loads (src/llm_wiki_cli/services/plugins.py:read_lock)(path.read_text(...))" .-> s10
    s4 -. "path.read_text(encoding='utf-8')" .-> s11
    s4 -->|"PluginError(...)"| s12
    b0["output print"]
    s1 -. "output print" .-> b0
    b1["output print"]
    s1 -. "output print" .-> b1
    b2["output print"]
    s1 -. "output print" .-> b2
    b3["output print"]
    s1 -. "output print" .-> b3
    b4["output print"]
    s1 -. "output print" .-> b4
    b5["output print"]
    s1 -. "output print" .-> b5
    b6["output print"]
    s1 -. "output print" .-> b6
    b7["output print"]
    s1 -. "output print" .-> b7
    click s1 "../modules/plugins_cmd.md"
    click s3 "../modules/plugins.md"
    click s4 "../modules/plugins.md"
    click s5 "../modules/plugins.md"
    click s6 "../modules/plugins.md"
    click s9 "../modules/plugins.md"
    click s12 "../modules/plugins.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
    class b7 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `run` | `args` | `PluginError`, `sys`, `DEFAULT_WIKI_DIR`, `PluginError`, `sys`, `PluginError`, `sys`, `sys` | - | `none`, `none`, `none`, `none`, `none`, `none`, `none` |
| `getattr (src/llm_wiki_cli/commands/plugins_cmd.py:run)` | - | - | - | - |
| `list_plugins` | `root: str \| Path` | - | - | `...` |
| `read_lock` | `root: str \| Path` | `json` | - | `_default_lock(...)`, `data` |
| `lock_path` | `root: str \| Path` | `LOCK_FILENAME` | - | `...` |
| `plugin_home` | `root: str \| Path` | `PLUGIN_HOME` | - | `...` |
| `Path (src/llm_wiki_cli/services/plugins.py:plugin_home)` | - | - | - | - |
| `path.exists (src/llm_wiki_cli/services/plugins.py:read_lock)` | - | - | - | - |
| `_default_lock` | - | - | - | `{...}` |
| `json.loads (src/llm_wiki_cli/services/plugins.py:read_lock)` | - | - | - | - |
| `path.read_text` | - | - | - | - |
| `PluginError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| run | getattr (src/llm_wiki_cli/commands/plugins_cmd.py:run) | 26 | `getattr(args, 'plugins_action', None)` |
| run | list_plugins | 29 | `list_plugins(data not statically known)` |
| list_plugins | read_lock | 500 | `read_lock(root)` |
| read_lock | lock_path | 77 | `lock_path(root)` |
| lock_path | plugin_home | 69 | `plugin_home(root)` |
| plugin_home | Path (src/llm_wiki_cli/services/plugins.py:plugin_home) | 61 | `Path(root)` |
| read_lock | path.exists (src/llm_wiki_cli/services/plugins.py:read_lock) | 78 | `path.exists(data not statically known)` |
| read_lock | _default_lock | 79 | `_default_lock(data not statically known)` |
| read_lock | json.loads (src/llm_wiki_cli/services/plugins.py:read_lock) | 81 | `json.loads(path.read_text(...))` |
| read_lock | path.read_text | 81 | `path.read_text(encoding='utf-8')` |
| read_lock | PluginError | 83 | `PluginError(...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| output | `print` | `run` | 31 |
| output | `print` | `run` | 34 |
| output | `print` | `run` | 35 |
| output | `print` | `run` | 43 |
| output | `print` | `run` | 46 |
| output | `print` | `run` | 58 |
| output | `print` | `run` | 60 |
| output | `print` | `run` | 61 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `run` | `getattr` | 26 |
| unresolved_call | `read_lock` | `path.exists` | 78 |
| external_call | `read_lock` | `json.loads` | 81 |
| unresolved_call | `read_lock` | `path.read_text` | 81 |
| step_limit | `run` | `first 12 steps` | 0 |
| truncated_flow | `run` | `depth limit` | 0 |

## Behavior

This flow starts at `run` and is classified as `cli`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
