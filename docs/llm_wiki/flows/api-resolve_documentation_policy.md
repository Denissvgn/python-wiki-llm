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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as resolve_documentation_policy
    participant p1 as _resolve_path
    participant p2 as _resolve_optional_root
    participant p3 as resolve_source_selection
    participant p4 as _resolve_optional_path
    participant p5 as _overlap
    participant p6 as _validate_live_service
    participant p7 as DocumentationPolicyError
    participant p8 as DocumentationMutationPolicy
    participant p9 as _resolve_existing_directory
    participant p10 as _override_text
    participant p11 as _locate_exact_path
    participant p12 as _read_config
    participant p13 as _policy_from_content
    participant p14 as _validate_policy_filesystem
    participant p15 as _decode_config
    participant p16 as _lstat
    participant p17 as path_is_selected
    participant p18 as _assert_safe_directory
    participant p19 as _selection_path
    participant p20 as is_agent_worktree_path
    participant p21 as _assert_same_file_identity
    participant p22 as _register_portable_filesystem_path
    participant p23 as _bounded_directory_entries
    participant p24 as windows_object_identity
    participant p25 as _require_selection_path
    participant p26 as windows_object_identity_from_values
    participant p27 as require_repository_relative_path
    participant p28 as _contains
    participant p29 as tuple (src/llm_wiki_cli/services…olve_documentation_policy)
    participant p30 as Path(…).expanduser().resolve
    p0->>p1: _resolve_path
    p0->>p2: _resolve_optional_root
    p0->>p3: resolve_source_selection
    p0->>p4: _resolve_optional_path
    p0->>p5: _overlap
    p0->>p6: _validate_live_service
    p0->>p7: DocumentationPolicyError
    p0->>p8: DocumentationMutationPolicy
    p2->>p9: _resolve_existing_directory
    p3->>p10: _override_text
    p3->>p11: _locate_exact_path
    p3->>p12: _read_config
    p3->>p13: _policy_from_content
    p3->>p14: _validate_policy_filesystem
    p13->>p15: _decode_config
    p9->>p16: _lstat
    p14->>p17: path_is_selected
    p9->>p18: _assert_safe_directory
    p10->>p19: _selection_path
    p14->>p20: is_agent_worktree_path
    p9->>p21: _assert_same_file_identity
    p14->>p22: _register_portable_filesystem_path
    p14->>p23: _bounded_directory_entries
    p21->>p24: windows_object_identity
    p19->>p25: _require_selection_path
    p24->>p26: windows_object_identity_from_values
    p25->>p27: require_repository_relative_path
    p5->>p28: _contains
    p0-->>p29: tuple (src/llm_wiki_cli/services…olve_documentation_policy)(...)
    p1-->>p30: Path(…).expanduser().resolve(strict=False)
```

> Call sequence diagram shows 30 of 238 interactions; 208 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 86 (85 omitted); unresolved 1 of 35 (34 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_path` | 2 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_path` | 2 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_path` | 2 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_resolve_existing_directory` | 8 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 11 | - | external | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_lstat` | 11 | [src/llm_wiki_cli/services/documentation_policy.py](../modules/documentation_policy.md) | internal | 1 |
| `src/llm_wiki_cli/services/documentation_policy.py:_assert_safe_directory` | 14 | - | external | 2 |
> Omission summary shows 8 of 70 groups; 62 further groups are not expanded here. Counts above include all omitted interactions.
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
