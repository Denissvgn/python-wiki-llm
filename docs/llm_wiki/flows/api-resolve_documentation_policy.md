# resolve_documentation_policy

**Entry point:** `resolve_documentation_policy` (`api`)
**Source:** [documentation_policy](../modules/documentation_policy.md)
**Modules touched:** [config](../modules/config.md), [documentation_policy](../modules/documentation_policy.md), [filesystem_guard](../modules/filesystem_guard.md), [source_selection](../modules/source_selection.md), and 1 more

**Complete modules touched:**

- [config](../modules/config.md)
- [documentation_policy](../modules/documentation_policy.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [source_selection](../modules/source_selection.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as resolve_documentation_policy
    participant p1 as _resolve_path
    participant p2 as _resolve_optional_root
    participant p3 as DocumentationPolicyError
    participant p4 as resolve_source_selection
    participant p5 as _resolve_optional_path
    participant p6 as _overlap
    participant p7 as _validate_live_service
    participant p8 as tuple (src/llm_wiki_cli/services…olve_documentation_policy)
    participant p9 as DocumentationMutationPolicy
    participant p10 as Path(…).expanduser().resolve
    participant p11 as _resolve_existing_directory
    participant p12 as Path(…).resolve
    participant p13 as _contains
    participant p14 as Path(…).expanduser (src/llm_wiki_cli/services…n_policy.py:_resolve_path)
    participant p15 as Path (src/llm_wiki_cli/services…:resolve_source_selection)
    participant p16 as Path (src/llm_wiki_cli/services…n_policy.py:_resolve_path)
    participant p17 as SourceSelectionError
    participant p18 as urlsplit
    p0->>p1: _resolve_path
    p0->>p2: _resolve_optional_root
    p0->>p3: DocumentationPolicyError
    p0->>p3: DocumentationPolicyError
    p0->>p4: resolve_source_selection
    p0->>p3: DocumentationPolicyError
    p0->>p2: _resolve_optional_root
    p0->>p5: _resolve_optional_path
    p0->>p5: _resolve_optional_path
    p0->>p6: _overlap
    p0->>p3: DocumentationPolicyError
    p0->>p6: _overlap
    p0->>p3: DocumentationPolicyError
    p0->>p7: _validate_live_service
    p0-->>p8: tuple (src/llm_wiki_cli/services…olve_documentation_policy)(...)
    p0-->>p8: tuple (src/llm_wiki_cli/services…olve_documentation_policy)(...)
    p0->>p9: DocumentationMutationPolicy
    p1-->>p10: Path(…).expanduser().resolve(strict=False)
    p2->>p11: _resolve_existing_directory
    p4-->>p12: Path(…).resolve
    p5->>p1: _resolve_path
    p6->>p13: _contains
    p7->>p3: DocumentationPolicyError
    p1-->>p14: Path(…).expanduser (src/llm_wiki_cli/services…n_policy.py:_resolve_path)
    p4-->>p15: Path (src/llm_wiki_cli/services…:resolve_source_selection)(root)
    p6->>p13: _contains
    p7->>p3: DocumentationPolicyError
    p1-->>p16: Path (src/llm_wiki_cli/services…n_policy.py:_resolve_path)(path)
    p4->>p17: SourceSelectionError
    p7-->>p18: urlsplit(url)
```

> Call sequence diagram shows 30 of 238 interactions; 208 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 86 (81 omitted); unresolved 3 of 35 (32 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_path` | 2 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 8 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 8 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 9 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 11 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 11 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 14 | - | external | 2 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 14 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 4 |
> Omission summary shows 8 of 65 groups; 57 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. resolve_documentation_policy"]
    s2["2. _resolve_path"]
    s3["3. Path(…).expanduser().resolve"]
    s4["4. Path(…).expanduser (src/llm_wiki_cli/services…n_policy.py:_resolve_path)"]
    s5["5. Path (src/llm_wiki_cli/services…n_policy.py:_resolve_path)"]
    s6["6. DocumentationPolicyError"]
    s7["7. _resolve_optional_root"]
    s8["8. _resolve_existing_directory"]
    s9["9. Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)"]
    s10["10. Path (src/llm_wiki_cli/services…esolve_existing_directory)"]
    s11["11. _lstat"]
    s12["12. os.lstat"]
    s1 -->|"_resolve_path(workspace_root)"| s2
    s2 -. "Path(…).expanduser().resolve(strict=False)" .-> s3
    s2 -. "Path(…).expanduser (src/llm_wiki_cli/services…n_policy.py:_resolve_path)(data not statically known)" .-> s4
    s2 -. "Path (src/llm_wiki_cli/services…n_policy.py:_resolve_path)(path)" .-> s5
    s2 -->|"DocumentationPolicyError(...)"| s6
    s1 -->|"_resolve_optional_root(source_root, 'source root')"| s7
    s7 -->|"_resolve_existing_directory(path, label)"| s8
    s8 -. "Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)(data not statically known)" .-> s9
    s8 -. "Path (src/llm_wiki_cli/services…esolve_existing_directory)(path)" .-> s10
    s8 -->|"_lstat(candidate, context=label)"| s11
    s11 -. "os.lstat(path)" .-> s12
    click s1 "../modules/documentation_policy.md"
    click s2 "../modules/documentation_policy.md"
    click s6 "../modules/documentation_policy.md"
    click s7 "../modules/documentation_policy.md"
    click s8 "../modules/documentation_policy.md"
    click s11 "../modules/documentation_policy.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `resolve_documentation_policy` | `workspace_root: str \| Path`, `source_root: str \| Path \| None`, `source_selection: str \| Path \| None`, `input_wiki_root: str \| Path \| None`, `helper_cache_root: str \| Path \| None`, `capture_root: str \| Path \| None`, `trust_source_plugins: bool`, `live_service_url: str \| None` | `SourceSelectionError` | - | `DocumentationMutationPolicy(...)` |
| `_resolve_path` | `path: str \| Path` | - | - | `...` |
| `Path(…).expanduser().resolve` | - | - | - | - |
| `Path(…).expanduser (src/llm_wiki_cli/services…n_policy.py:_resolve_path)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…n_policy.py:_resolve_path)` | - | - | - | - |
| `DocumentationPolicyError` | - | - | - | - |
| `_resolve_optional_root` | `path: str \| Path \| None`, `label: str` | - | - | `None`, `_resolve_existing_directory(...)` |
| `_resolve_existing_directory` | `path: str \| Path`, `label: str` | - | - | `resolved` |
| `Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory)` | - | - | - | - |
| `Path (src/llm_wiki_cli/services…esolve_existing_directory)` | - | - | - | - |
| `_lstat` | `path: Path`, `context: str` | - | - | `os.lstat(...)` |
| `os.lstat` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| resolve_documentation_policy | _resolve_path | 217 | `_resolve_path(workspace_root)` |
| _resolve_path | Path(…).expanduser().resolve | 983 | `Path(path).expanduser().resolve(strict=False)` |
| _resolve_path | Path(…).expanduser (src/llm_wiki_cli/services…n_policy.py:_resolve_path) | 983 | `Path(path).expanduser(data not statically known)` |
| _resolve_path | Path (src/llm_wiki_cli/services…n_policy.py:_resolve_path) | 983 | `Path(path)` |
| _resolve_path | DocumentationPolicyError | 985 | `DocumentationPolicyError(...)` |
| resolve_documentation_policy | _resolve_optional_root | 218 | `_resolve_optional_root(source_root, 'source root')` |
| _resolve_optional_root | _resolve_existing_directory | 974 | `_resolve_existing_directory(path, label)` |
| _resolve_existing_directory | Path(…).expanduser (src/llm_wiki_cli/services…esolve_existing_directory) | 948 | `Path(path).expanduser(data not statically known)` |
| _resolve_existing_directory | Path (src/llm_wiki_cli/services…esolve_existing_directory) | 948 | `Path(path)` |
| _resolve_existing_directory | _lstat | 949 | `_lstat(candidate, context=label)` |
| _lstat | os.lstat | 782 | `os.lstat(path)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_resolve_path` | `Path(path).expanduser().resolve` | 983 |
| unresolved_call | `_resolve_path` | `Path(path).expanduser` | 983 |
| unresolved_call | `_resolve_existing_directory` | `Path(path).expanduser` | 948 |
| external_call | `_lstat` | `os.lstat` | 782 |
| step_limit | `resolve_documentation_policy` | `first 12 steps` | 0 |
| truncated_flow | `resolve_documentation_policy` | `depth limit` | 0 |

## Behavior

This flow starts at `resolve_documentation_policy` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
