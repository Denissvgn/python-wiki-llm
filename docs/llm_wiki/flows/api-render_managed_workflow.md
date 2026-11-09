# render_managed_workflow

**Entry point:** `render_managed_workflow` (`api`)
**Source:** [ci_installer](../modules/ci_installer.md)
**Modules touched:** [ci_installer](../modules/ci_installer.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_managed_workflow
    participant p1 as normalize_action_ref
    participant p2 as _portable_project_path
    participant p3 as _workflow_body
    participant p4 as _with_ownership_checksum
    participant p5 as _without_github_expression
    participant p6 as _validated_project_path
    participant p7 as require_repository_relative_path
    participant p8 as require_portable_relative_path
    participant p9 as _default_path_error
    participant p10 as _check_path_collision
    participant p11 as require_portable_path_component
    participant p12 as InstallCiError
    participant p13 as _syntax_key
    participant p14 as _known_syntax
    participant p15 as _remember_syntax
    participant p16 as SharedValidationError
    participant p17 as portable_path_key
    participant p18 as isinstance (src/llm_wiki_cli/services…er.py:normalize_action_ref)
    participant p19 as hashlib.sha256(…).hexdigest
    participant p20 as json.dumps
    participant p21 as _ACTION_REF_RE.fullmatch
    participant p22 as hashlib.sha256
    participant p23 as body.encode
    participant p24 as value.lower
    participant p25 as (…).encode
    participant p26 as isinstance (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p27 as value.strip
    participant p28 as any (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p29 as ord (src/llm_wiki_cli/services…e_repository_relative_path)
    p0->>p1: normalize_action_ref
    p0->>p2: _portable_project_path
    p0->>p3: _workflow_body
    p0->>p4: _with_ownership_checksum
    p2->>p5: _without_github_expression
    p2->>p6: _validated_project_path
    p6->>p7: require_repository_relative_path
    p7->>p8: require_portable_relative_path
    p8->>p9: _default_path_error
    p8->>p10: _check_path_collision
    p8->>p11: require_portable_path_component
    p1->>p12: InstallCiError
    p7->>p13: _syntax_key
    p7->>p14: _known_syntax
    p7->>p15: _remember_syntax
    p9->>p16: SharedValidationError
    p10->>p17: portable_path_key
    p1-->>p18: isinstance (src/llm_wiki_cli/services…er.py:normalize_action_ref)(value, str)
    p4-->>p19: hashlib.sha256(…).hexdigest
    p3-->>p20: json.dumps(src_dir)
    p1-->>p21: _ACTION_REF_RE.fullmatch(value)
    p3-->>p20: json.dumps(wiki_dir)
    p4-->>p22: hashlib.sha256(body.encode(...))
    p4-->>p23: body.encode('utf-8')
    p1-->>p24: value.lower
    p4-->>p25: (…).encode('utf-8')
    p7-->>p26: isinstance (src/llm_wiki_cli/services…e_repository_relative_path)(value, str)
    p7-->>p27: value.strip
    p7-->>p28: any (src/llm_wiki_cli/services…e_repository_relative_path)(...)
    p7-->>p29: ord (src/llm_wiki_cli/services…e_repository_relative_path)(character)
```

> Call sequence diagram shows 30 of 98 interactions; 68 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 27 (20 omitted); unresolved 6 of 29 (23 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/ci_installer.py:_without_github_expression` | 8 | [src/llm_wiki_cli/services/ci_installer.py](../modules/ci_installer.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 13 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 20 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 11 | - | external | 4 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 11 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 34 | - | external | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 34 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 10 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 43 | - | unresolved | 2 |
> Omission summary shows 8 of 17 groups; 9 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 43; effect analysis evaluated: 24, partial: 3, unavailable: 16. Counts include steps omitted from the displayed trace.

Collector observations for 27 source steps with known totals: observed: 132, emitted: 117, omitted: 15. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `render_managed_workflow` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `normalize_action_ref` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `isinstance (src/llm_wiki_cli/services…er.py:normalize_action_ref)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_ACTION_REF_RE.fullmatch` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `InstallCiError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `value.lower` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_portable_project_path` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `_without_github_expression` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `InstallCiError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_validated_project_path` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `require_repository_relative_path` | `available` | `partial` | `available` | `14` | `10` | `4` |
| `isinstance (src/llm_wiki_cli/services…e_repository_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. render_managed_workflow"]
    s2["2. normalize_action_ref"]
    s3["3. isinstance (src/llm_wiki_cli/services…er.py:normalize_action_ref)"]
    s4["4. _ACTION_REF_RE.fullmatch"]
    s5["5. InstallCiError"]
    s6["6. value.lower"]
    s7["7. _portable_project_path"]
    s8["8. _without_github_expression"]
    s9["9. InstallCiError"]
    s10["10. _validated_project_path"]
    s11["11. require_repository_relative_path"]
    s12["12. isinstance (src/llm_wiki_cli/services…e_repository_relative_path)"]
    s1 -->|"normalize_action_ref(action_ref)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…er.py:normalize_action_ref)(value, str)" .-> s3
    s2 -. "_ACTION_REF_RE.fullmatch(value)" .-> s4
    s2 -->|"InstallCiError('--action-ref must be exactly 40 hexadecimal characters')"| s5
    s2 -. "value.lower(data not statically known)" .-> s6
    s1 -->|"_portable_project_path(src_dir, label='--src-dir', allow_root=True)"| s7
    s7 -->|"_without_github_expression(_validated_project_path(...), label=label)"| s8
    s8 -->|"InstallCiError(...)"| s9
    s7 -->|"_validated_project_path(value, label=label)"| s10
    s10 -->|"require_repository_relative_path(…)"| s11
    s11 -. "isinstance (src/llm_wiki_cli/services…e_repository_relative_path)(value, str)" .-> s12
    click s1 "../modules/ci_installer.md"
    click s2 "../modules/ci_installer.md"
    click s5 "../modules/ci_installer.md"
    click s7 "../modules/ci_installer.md"
    click s8 "../modules/ci_installer.md"
    click s9 "../modules/ci_installer.md"
    click s10 "../modules/ci_installer.md"
    click s11 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `render_managed_workflow` | `action_ref: str`, `src_dir: str`, `wiki_dir: str` | - | - | `_with_ownership_checksum(...)` |
| `normalize_action_ref` | `value: object` | - | - | `value.lower(...)` |
| `isinstance (src/llm_wiki_cli/services…er.py:normalize_action_ref)` | - | - | - | - |
| `_ACTION_REF_RE.fullmatch` | - | - | - | - |
| `InstallCiError` | - | - | - | - |
| `value.lower` | - | - | - | - |
| `_portable_project_path` | `value: object`, `label: str`, `allow_root: bool` | - | - | `'.'`, `_without_github_expression(...)` |
| `_without_github_expression` | `path: str`, `label: str` | - | - | `path` |
| `InstallCiError` | - | - | - | - |
| `_validated_project_path` | `value: object`, `label: str` | - | - | `require_repository_relative_path(...)` |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…e_repository_relative_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_managed_workflow | normalize_action_ref | 229 | `normalize_action_ref(action_ref)` |
| normalize_action_ref | isinstance (src/llm_wiki_cli/services…er.py:normalize_action_ref) | 75 | `isinstance(value, str)` |
| normalize_action_ref | _ACTION_REF_RE.fullmatch | 75 | `_ACTION_REF_RE.fullmatch(value)` |
| normalize_action_ref | InstallCiError | 76 | `InstallCiError('--action-ref must be exactly 40 hexadecimal characters')` |
| normalize_action_ref | value.lower | 77 | `value.lower(data not statically known)` |
| render_managed_workflow | _portable_project_path | 230 | `_portable_project_path(src_dir, label='--src-dir', allow_root=True)` |
| _portable_project_path | _without_github_expression | 112 | `_without_github_expression(_validated_project_path(...), label=label)` |
| _without_github_expression | InstallCiError | 105 | `InstallCiError(...)` |
| _portable_project_path | _validated_project_path | 113 | `_validated_project_path(value, label=label)` |
| _validated_project_path | require_repository_relative_path | 81 | `require_repository_relative_path(value, text_error=InstallCiError(...), posix_error=InstallCiError(...), normalized_error=InstallCiError(...), absolute_error=InstallCiError(...), separator_error=InstallCiError(...), control_error=InstallCiError(...), reject_delete_character=True, leading_backslash_is_absolute=True, portability_error=InstallCiError(...))` |
| require_repository_relative_path | isinstance (src/llm_wiki_cli/services…e_repository_relative_path) | 304 | `isinstance(value, str)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `normalize_action_ref` | `isinstance` | 75 |
| unresolved_call | `normalize_action_ref` | `_ACTION_REF_RE.fullmatch` | 75 |
| unresolved_call | `normalize_action_ref` | `value.lower` | 77 |
| external_call | `require_repository_relative_path` | `isinstance` | 304 |
| step_limit | `render_managed_workflow` | `first 12 steps` | 0 |
| truncated_flow | `render_managed_workflow` | `depth limit` | 0 |

## Behavior

This flow starts at `render_managed_workflow` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
