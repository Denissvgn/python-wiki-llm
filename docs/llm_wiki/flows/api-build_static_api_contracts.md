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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_static_api_contracts
    participant p1 as _framework_records
    participant p2 as is_test_source_path
    participant p3 as fastapi.get (src/llm_wiki_cli/services…uild_static_api_contracts)
    participant p4 as isinstance (src/llm_wiki_cli/services…uild_static_api_contracts)
    participant p5 as sum
    participant p6 as max
    participant p7 as len (src/llm_wiki_cli/services…uild_static_api_contracts)
    participant p8 as _operation_methods
    participant p9 as any (src/llm_wiki_cli/services…uild_static_api_contracts)
    participant p10 as declarations.values
    participant p11 as diagnostics.append
    participant p12 as _diagnostic
    participant p13 as declarations.items
    participant p14 as inventory.items (src/llm_wiki_cli/services…uild_static_api_contracts)
    participant p15 as _declaration_nodes
    participant p16 as build_module_path_resolver
    participant p17 as dict (src/llm_wiki_cli/services…uild_static_api_contracts)
    participant p18 as defaultdict (src/llm_wiki_cli/services…uild_static_api_contracts)
    participant p19 as _resolve_binding
    participant p20 as str (src/llm_wiki_cli/services…uild_static_api_contracts)
    participant p21 as record.get (src/llm_wiki_cli/services…uild_static_api_contracts)
    p0->>p1: _framework_records
    p0->>p2: is_test_source_path
    p0-->>p3: fastapi.get (src/llm_wiki_cli/services…uild_static_api_contracts)(kind, [...])
    p0-->>p4: isinstance (src/llm_wiki_cli/services…uild_static_api_contracts)(record, Mapping)
    p0-->>p5: sum(...)
    p0-->>p6: max(1, len(...))
    p0-->>p7: len (src/llm_wiki_cli/services…uild_static_api_contracts)(...)
    p0->>p8: _operation_methods
    p0-->>p9: any (src/llm_wiki_cli/services…uild_static_api_contracts)(declarations.values(...))
    p0-->>p10: declarations.values
    p0-->>p11: diagnostics.append(_diagnostic(...))
    p0->>p12: _diagnostic
    p0-->>p7: len (src/llm_wiki_cli/services…uild_static_api_contracts)(records)
    p0-->>p13: declarations.items
    p0-->>p14: inventory.items (src/llm_wiki_cli/services…uild_static_api_contracts)
    p0->>p2: is_test_source_path
    p0->>p15: _declaration_nodes
    p0->>p16: build_module_path_resolver
    p0-->>p17: dict (src/llm_wiki_cli/services…uild_static_api_contracts)(inventory)
    p0-->>p18: defaultdict (src/llm_wiki_cli/services…uild_static_api_contracts)(list)
    p0-->>p18: defaultdict (src/llm_wiki_cli/services…uild_static_api_contracts)(list)
    p0->>p1: _framework_records
    p0-->>p3: fastapi.get (src/llm_wiki_cli/services…uild_static_api_contracts)('operations', [...])
    p0-->>p4: isinstance (src/llm_wiki_cli/services…uild_static_api_contracts)(record, Mapping)
    p0->>p19: _resolve_binding
    p0-->>p20: str (src/llm_wiki_cli/services…uild_static_api_contracts)(...)
    p0-->>p21: record.get (src/llm_wiki_cli/services…uild_static_api_contracts)('owner')
    p0-->>p20: str (src/llm_wiki_cli/services…uild_static_api_contracts)(...)
    p0-->>p21: record.get (src/llm_wiki_cli/services…uild_static_api_contracts)('handler_scope')
    p0-->>p11: diagnostics.append(_diagnostic(...))
```

> Call sequence diagram shows 30 of 591 interactions; 561 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 12 of 222 (210 omitted); unresolved 9 of 265 (256 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/api_contracts.py:_framework_records` | 2 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/api_contracts.py:_framework_records` | 2 | - | external | 2 |
| `src/llm_wiki_cli/services/paths.py:is_test_source_path` | 8 | - | unresolved | 8 |
| `src/llm_wiki_cli/services/paths.py:is_test_source_path` | 8 | - | external | 3 |
| `src/llm_wiki_cli/services/api_contracts.py:_operation_methods` | 25 | - | external | 4 |
| `src/llm_wiki_cli/services/api_contracts.py:_operation_methods` | 25 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/api_contracts.py:_operation_methods` | 25 | [src/llm_wiki_cli/services/api_contracts.py](../modules/api_contracts.md) | internal | 1 |
| `src/llm_wiki_cli/services/api_contracts.py:_kw_value` | 29 | - | unresolved | 1 |
> Omission summary shows 8 of 115 groups; 107 further groups are not expanded here. Counts above include all omitted interactions.
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
| build_static_api_contracts | _framework_records | 742 | `_framework_records(inventory)` |
| _framework_records | inventory.items (src/llm_wiki_cli/services…cts.py:_framework_records) | 219 | `inventory.items(data not statically known)` |
| _framework_records | file_data.get (src/llm_wiki_cli/services…cts.py:_framework_records) | 220 | `file_data.get('frameworks')` |
| _framework_records | isinstance (src/llm_wiki_cli/services…cts.py:_framework_records) | 221 | `isinstance(frameworks, Mapping)` |
| _framework_records | frameworks.get | 221 | `frameworks.get('fastapi')` |
| _framework_records | isinstance (src/llm_wiki_cli/services…cts.py:_framework_records) | 222 | `isinstance(fastapi, Mapping)` |
| build_static_api_contracts | is_test_source_path | 743 | `is_test_source_path(filepath)` |
| is_test_source_path | str(…).replace(…).strip | 41 | `str(value).replace('\\', '/').strip('/')` |
| is_test_source_path | str(…).replace (src/llm_wiki_cli/services…hs.py:is_test_source_path) | 41 | `str(value).replace('\\', '/')` |
| is_test_source_path | str (src/llm_wiki_cli/services…hs.py:is_test_source_path) | 41 | `str(value)` |
| is_test_source_path | PurePosixPath (src/llm_wiki_cli/services…hs.py:is_test_source_path) | 44 | `PurePosixPath(normalized)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `diagnostics.append` | `build_static_api_contracts` | 754 |
| mutation | `diagnostics.append` | `build_static_api_contracts` | 782 |
| mutation | `diagnostics.append` | `build_static_api_contracts` | 819 |
| mutation | `unknowns.append` | `build_static_api_contracts` | 836 |
| mutation | `unknowns.append` | `build_static_api_contracts` | 845 |
| mutation | `applications.append` | `build_static_api_contracts` | 854 |
| mutation | `diagnostics.append` | `build_static_api_contracts` | 1163 |
| mutation | `assembled.sort` | `build_static_api_contracts` | 1181 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_framework_records` | `inventory.items` | 219 |
| unresolved_call | `_framework_records` | `file_data.get` | 220 |
| external_call | `_framework_records` | `isinstance` | 221 |
| unresolved_call | `_framework_records` | `frameworks.get` | 221 |
| external_call | `_framework_records` | `isinstance` | 222 |
| unresolved_call | `is_test_source_path` | `str(value).replace('\\', '/').strip` | 41 |
| unresolved_call | `is_test_source_path` | `str(value).replace` | 41 |
| external_call | `is_test_source_path` | `PurePosixPath` | 44 |
| step_limit | `build_static_api_contracts` | `first 12 steps` | 0 |
| truncated_flow | `build_static_api_contracts` | `depth limit` | 0 |

## Behavior

This flow starts at `build_static_api_contracts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
