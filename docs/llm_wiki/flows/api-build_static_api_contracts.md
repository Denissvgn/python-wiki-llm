# build_static_api_contracts

**Entry point:** `build_static_api_contracts` (`api`)
**Source:** [api_contracts](../modules/api_contracts.md)
**Modules touched:** [api_contracts](../modules/api_contracts.md), [config](../modules/config.md), [imports](../modules/imports.md), [packages](../modules/packages.md), and 2 more

**Complete modules touched:**

- [api_contracts](../modules/api_contracts.md)
- [config](../modules/config.md)
- [imports](../modules/imports.md)
- [packages](../modules/packages.md)
- [paths](../modules/paths.md)
- [python_imports](../modules/python_imports.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_static_api_contracts
    participant p1 as _operation_methods
    participant p2 as _declaration_nodes
    participant p3 as build_module_path_resolver
    participant p4 as _resolve_binding
    participant p5 as _first_arg
    participant p6 as _display_value
    participant p7 as _canonical_imported_reference
    participant p8 as _kw_unknown
    participant p9 as _framework_records
    participant p10 as is_test_source_path
    participant p11 as _diagnostic
    participant p12 as _kw_value
    participant p13 as _kwargs
    participant p14 as _record_value
    participant p15 as _operation_id
    participant p16 as ModulePathResolver.build
    participant p17 as _import_bindings
    participant p18 as _display_call
    participant p19 as stamp_inventory_packages
    participant p20 as discover_packages
    participant p21 as _is_typescript_index
    participant p22 as _read_go_module_scopes
    participant p23 as _inventory_go_scopes
    participant p24 as _read_ts_path_aliases
    participant p25 as PythonModuleIndex.build
    participant p26 as _package_import_scope
    participant p27 as _go_module_dir_is_agent_worktree
    participant p28 as _parse_tsconfig_aliases
    participant p29 as isinstance (src/llm_wiki_cli/services…uild_static_api_contracts)
    participant p30 as fastapi.get (src/llm_wiki_cli/services…uild_static_api_contracts)
    p0->>p1: _operation_methods
    p0->>p2: _declaration_nodes
    p0->>p3: build_module_path_resolver
    p0->>p4: _resolve_binding
    p0->>p5: _first_arg
    p0->>p6: _display_value
    p0->>p7: _canonical_imported_reference
    p0->>p8: _kw_unknown
    p0->>p9: _framework_records
    p0->>p10: is_test_source_path
    p0->>p11: _diagnostic
    p0->>p12: _kw_value
    p0->>p13: _kwargs
    p0->>p14: _record_value
    p0->>p15: _operation_id
    p3->>p16: ModulePathResolver.build
    p4->>p17: _import_bindings
    p6->>p18: _display_call
    p16->>p19: stamp_inventory_packages
    p16->>p20: discover_packages
    p16->>p21: _is_typescript_index
    p16->>p22: _read_go_module_scopes
    p16->>p23: _inventory_go_scopes
    p16->>p24: _read_ts_path_aliases
    p16->>p25: PythonModuleIndex.build
    p19->>p26: _package_import_scope
    p22->>p27: _go_module_dir_is_agent_worktree
    p24->>p28: _parse_tsconfig_aliases
    p0-->>p29: isinstance (src/llm_wiki_cli/services…uild_static_api_contracts)(record, Mapping)
    p0-->>p30: fastapi.get (src/llm_wiki_cli/services…uild_static_api_contracts)(kind, [...])
```

> Call sequence diagram shows 30 of 610 interactions; 580 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 225 (224 omitted); unresolved 1 of 280 (279 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/api_contracts.py:_framework_records` | 2 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/api_contracts.py:_framework_records` | 2 | - | external | 2 |
| `src/llm_wiki_cli/services/paths.py:is_test_source_path` | 8 | - | unresolved | 8 |
| `src/llm_wiki_cli/services/paths.py:is_test_source_path` | 8 | - | external | 3 |
| `src/llm_wiki_cli/services/api_contracts.py:build_static_api_contracts` | 1 | - | external | 26 |
| `src/llm_wiki_cli/services/api_contracts.py:_operation_methods` | 25 | - | external | 4 |
| `src/llm_wiki_cli/services/api_contracts.py:_operation_methods` | 25 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/api_contracts.py:_operation_methods` | 25 | [src/llm_wiki_cli/services/api_contracts.py](../modules/api_contracts.md) | internal | 1 |
> Omission summary shows 8 of 116 groups; 108 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_static_api_contracts"]
    s2["2. _framework_records"]
    s3["3. inventory.items (src/llm_wiki_cli/services…cts.py:_framework_records)"]
    s4["4. file_data.get (src/llm_wiki_cli/services…cts.py:_framework_records)"]
    s5["5. isinstance (src/llm_wiki_cli/services…cts.py:_framework_records)"]
    s6["6. frameworks.get"]
    s7["7. isinstance (src/llm_wiki_cli/services…cts.py:_framework_records)"]
    s8["8. is_test_source_path"]
    s9["9. str(…).replace(…).strip"]
    s10["10. str(…).replace (src/llm_wiki_cli/services…hs.py:is_test_source_path)"]
    s11["11. str (src/llm_wiki_cli/services…hs.py:is_test_source_path)"]
    s12["12. PurePosixPath (src/llm_wiki_cli/services…hs.py:is_test_source_path)"]
    s1 -->|"_framework_records(inventory)"| s2
    s2 -. "inventory.items (src/llm_wiki_cli/services…cts.py:_framework_records)(data not statically known)" .-> s3
    s2 -. "file_data.get (src/llm_wiki_cli/services…cts.py:_framework_records)('frameworks')" .-> s4
    s2 -. "isinstance (src/llm_wiki_cli/services…cts.py:_framework_records)(frameworks, Mapping)" .-> s5
    s2 -. "frameworks.get('fastapi')" .-> s6
    s2 -. "isinstance (src/llm_wiki_cli/services…cts.py:_framework_records)(fastapi, Mapping)" .-> s7
    s1 -->|"is_test_source_path(filepath)"| s8
    s8 -. "str(…).replace(…).strip('/')" .-> s9
    s8 -. "str(…).replace (src/llm_wiki_cli/services…hs.py:is_test_source_path)('\\', '/')" .-> s10
    s8 -. "str (src/llm_wiki_cli/services…hs.py:is_test_source_path)(value)" .-> s11
    s8 -. "PurePosixPath (src/llm_wiki_cli/services…hs.py:is_test_source_path)(normalized)" .-> s12
    b0["mutation diagnostics.append"]
    s1 -. "mutation diagnostics.append" .-> b0
    b1["mutation diagnostics.append"]
    s1 -. "mutation diagnostics.append" .-> b1
    b2["mutation diagnostics.append"]
    s1 -. "mutation diagnostics.append" .-> b2
    b3["mutation unknowns.append"]
    s1 -. "mutation unknowns.append" .-> b3
    b4["mutation unknowns.append"]
    s1 -. "mutation unknowns.append" .-> b4
    b5["mutation applications.append"]
    s1 -. "mutation applications.append" .-> b5
    b6["mutation diagnostics.append"]
    s1 -. "mutation diagnostics.append" .-> b6
    b7["mutation assembled.sort"]
    s1 -. "mutation assembled.sort" .-> b7
    click s1 "../modules/api_contracts.md"
    click s2 "../modules/api_contracts.md"
    click s8 "../modules/paths.md"
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
| `build_static_api_contracts` | `inventory: Mapping[str, Mapping[str, Any]]` | `Mapping`, `Mapping`, `Mapping`, `_UNKNOWN`, `_UNKNOWN` | `config[...]`, `ids[...]`, `operation[...]` | `{...}` |
| `_framework_records` | `inventory: Mapping[str, Mapping[str, Any]]` | `Mapping`, `Mapping` | - | - |
| `inventory.items (src/llm_wiki_cli/services…cts.py:_framework_records)` | - | - | - | - |
| `file_data.get (src/llm_wiki_cli/services…cts.py:_framework_records)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…cts.py:_framework_records)` | - | - | - | - |
| `frameworks.get` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…cts.py:_framework_records)` | - | - | - | - |
| `is_test_source_path` | `value: str \| Path \| None` | `_TEST_FILE_STEMS` | - | `False`, `False`, `True`, `True`, `True`, `...` |
| `str(…).replace(…).strip` | - | - | - | - |
| `str(…).replace (src/llm_wiki_cli/services…hs.py:is_test_source_path)` | - | - | - | - |
| `str (src/llm_wiki_cli/services…hs.py:is_test_source_path)` | - | - | - | - |
| `PurePosixPath (src/llm_wiki_cli/services…hs.py:is_test_source_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_static_api_contracts | _framework_records | 743 | `_framework_records(inventory)` |
| _framework_records | inventory.items (src/llm_wiki_cli/services…cts.py:_framework_records) | 220 | `inventory.items(data not statically known)` |
| _framework_records | file_data.get (src/llm_wiki_cli/services…cts.py:_framework_records) | 221 | `file_data.get('frameworks')` |
| _framework_records | isinstance (src/llm_wiki_cli/services…cts.py:_framework_records) | 222 | `isinstance(frameworks, Mapping)` |
| _framework_records | frameworks.get | 222 | `frameworks.get('fastapi')` |
| _framework_records | isinstance (src/llm_wiki_cli/services…cts.py:_framework_records) | 223 | `isinstance(fastapi, Mapping)` |
| build_static_api_contracts | is_test_source_path | 744 | `is_test_source_path(filepath)` |
| is_test_source_path | str(…).replace(…).strip | 41 | `str(value).replace('\\', '/').strip('/')` |
| is_test_source_path | str(…).replace (src/llm_wiki_cli/services…hs.py:is_test_source_path) | 41 | `str(value).replace('\\', '/')` |
| is_test_source_path | str (src/llm_wiki_cli/services…hs.py:is_test_source_path) | 41 | `str(value)` |
| is_test_source_path | PurePosixPath (src/llm_wiki_cli/services…hs.py:is_test_source_path) | 44 | `PurePosixPath(normalized)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `diagnostics.append` | `build_static_api_contracts` | 755 |
| mutation | `diagnostics.append` | `build_static_api_contracts` | 783 |
| mutation | `diagnostics.append` | `build_static_api_contracts` | 820 |
| mutation | `unknowns.append` | `build_static_api_contracts` | 837 |
| mutation | `unknowns.append` | `build_static_api_contracts` | 846 |
| mutation | `applications.append` | `build_static_api_contracts` | 855 |
| mutation | `diagnostics.append` | `build_static_api_contracts` | 1164 |
| mutation | `assembled.sort` | `build_static_api_contracts` | 1182 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_framework_records` | `inventory.items` | 220 |
| unresolved_call | `_framework_records` | `file_data.get` | 221 |
| external_call | `_framework_records` | `isinstance` | 222 |
| unresolved_call | `_framework_records` | `frameworks.get` | 222 |
| external_call | `_framework_records` | `isinstance` | 223 |
| unresolved_call | `is_test_source_path` | `str(value).replace('\\', '/').strip` | 41 |
| unresolved_call | `is_test_source_path` | `str(value).replace` | 41 |
| external_call | `is_test_source_path` | `PurePosixPath` | 44 |
| step_limit | `build_static_api_contracts` | `first 12 steps` | 0 |
| truncated_flow | `build_static_api_contracts` | `depth limit` | 0 |

## Behavior

This flow starts at `build_static_api_contracts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.

Global Python response aliases are normalized through matching captured module bindings. Local dependency imports cannot supply unrelated global model aliases; static output is not runtime validation.
