# list_wiki_pages

**Entry point:** `list_wiki_pages` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [host](../modules/host.md), [path_policy](../modules/path_policy.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as list_wiki_pages
    participant p1 as _validate_wiki_dir
    participant p2 as collect_wiki_pages
    participant p3 as _wiki_page_counts
    participant p4 as _wiki_page_payload
    participant p5 as InvalidRequestError
    participant p6 as _wiki_path_policy_details
    participant p7 as WorkspaceStateError
    participant p8 as _display_path
    participant p9 as validate_path
    participant p10 as _collect_directory_pages
    participant p11 as resolve_wiki_page_path
    participant p12 as _is_legacy_path
    participant p13 as is_safe_page_id
    participant p14 as _surface_page
    participant p15 as mcp_uri
    participant p16 as is_portable_path_component
    participant p17 as require_portable_path_component
    participant p18 as _entry_for
    participant p19 as _validate_page_id
    participant p20 as iter_page_kinds
    participant p21 as PathValidationError
    participant p22 as WikiSurfacePathError
    participant p23 as current_host
    participant p24 as path_is_in_top_level_directory
    participant p25 as WikiSurfacePage
    participant p26 as WikiSurfaceError
    participant p27 as SharedValidationError
    participant p28 as PageKind
    participant p29 as str (src/llm_wiki_cli/api.py:list_wiki_pages)
    participant p30 as path.relative_to(…).as_posix (src/llm_wiki_cli/api.py:_display_path)
    p0->>p1: _validate_wiki_dir
    p0->>p2: collect_wiki_pages
    p0->>p3: _wiki_page_counts
    p0->>p4: _wiki_page_payload
    p0->>p5: InvalidRequestError
    p0->>p6: _wiki_path_policy_details
    p0->>p7: WorkspaceStateError
    p0->>p8: _display_path
    p1->>p9: validate_path
    p2->>p10: _collect_directory_pages
    p10->>p11: resolve_wiki_page_path
    p10->>p12: _is_legacy_path
    p10->>p13: is_safe_page_id
    p10->>p14: _surface_page
    p14->>p15: mcp_uri
    p13->>p16: is_portable_path_component
    p16->>p17: require_portable_path_component
    p15->>p18: _entry_for
    p15->>p19: _validate_page_id
    p3->>p20: iter_page_kinds
    p9->>p21: PathValidationError
    p10->>p22: WikiSurfacePathError
    p9->>p23: current_host
    p12->>p24: path_is_in_top_level_directory
    p14->>p25: WikiSurfacePage
    p15->>p26: WikiSurfaceError
    p17->>p27: SharedValidationError
    p18->>p28: PageKind
    p0-->>p29: str (src/llm_wiki_cli/api.py:list_wiki_pages)(exc)
    p8-->>p30: path.relative_to(…).as_posix (src/llm_wiki_cli/api.py:_display_path)
```

> Call sequence diagram shows 30 of 115 interactions; 85 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 26 (25 omitted); unresolved 1 of 42 (41 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_engine/path_policy.py:validate_path` | 3 | - | unresolved | 5 |
| `src/llm_wiki_engine/host.py:current_host` | 7 | - | unresolved | 1 |
| `src/llm_wiki_engine/path_policy.py:validate_path` | 3 | [src/llm_wiki_engine/host.py](../modules/host.md) | internal | 1 |
| `src/llm_wiki_engine/path_policy.py:validate_path` | 3 | [src/llm_wiki_engine/path_policy.py](../modules/path_policy.md) | internal | 1 |
| `src/llm_wiki_engine/wiki_surface.py:collect_wiki_pages` | 15 | - | external | 1 |
| `src/llm_wiki_engine/wiki_surface.py:collect_wiki_pages` | 15 | - | unresolved | 4 |
| `src/llm_wiki_engine/wiki_surface.py:_collect_directory_pages` | 18 | - | unresolved | 7 |
| `src/llm_wiki_engine/wiki_surface.py:_collect_directory_pages` | 18 | - | external | 1 |
> Omission summary shows 8 of 31 groups; 23 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 48; effect analysis evaluated: 25, partial: 1, unavailable: 22. Counts include steps omitted from the displayed trace.

Collector observations for 26 source steps with known totals: observed: 102, emitted: 101, omitted: 1. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `list_wiki_pages` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `_validate_wiki_dir` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `validate_path` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `PathValidationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `(…).resolve` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `current_host().cwd` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `current_host` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_ACTIVE.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `current_host().cwd().resolve` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `current_host().cwd` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `current_host` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `resolved.relative_to (src/llm_wiki_engine/path_policy.py:validate_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. list_wiki_pages"]
    s2["2. _validate_wiki_dir"]
    s3["3. validate_path"]
    s4["4. PathValidationError"]
    s5["5. (…).resolve"]
    s6["6. current_host().cwd"]
    s7["7. current_host"]
    s8["8. _ACTIVE.get"]
    s9["9. current_host().cwd().resolve"]
    s10["10. current_host().cwd"]
    s11["11. current_host"]
    s12["12. resolved.relative_to (src/llm_wiki_engine/path_policy.py:validate_path)"]
    s1 -->|"_validate_wiki_dir(wiki_dir)"| s2
    s2 -->|"validate_path(wiki_dir, '--wiki-dir')"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(…).resolve(data not statically known)" .-> s5
    s3 -. "current_host().cwd(data not statically known)" .-> s6
    s3 -->|"current_host(data not statically known)"| s7
    s7 -. "_ACTIVE.get(data not statically known)" .-> s8
    s3 -. "current_host().cwd().resolve(data not statically known)" .-> s9
    s3 -. "current_host().cwd(data not statically known)" .-> s10
    s3 -->|"current_host(data not statically known)"| s11
    s3 -. "resolved.relative_to (src/llm_wiki_engine/path_policy.py:validate_path)(cwd)" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
    click s3 "../modules/path_policy.md"
    click s4 "../modules/path_policy.md"
    click s7 "../modules/host.md"
    click s11 "../modules/host.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `list_wiki_pages` | `wiki_dir: str` | `PathValidationError`, `wiki_surface`, `wiki_surface` | - | `{...}` |
| `_validate_wiki_dir` | `wiki_dir: str` | - | - | `validate_path(...)` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `(…).resolve` | - | - | - | - |
| `current_host().cwd` | - | - | - | - |
| `current_host` | - | `_DEFAULT` | - | `...` |
| `_ACTIVE.get` | - | - | - | - |
| `current_host().cwd().resolve` | - | - | - | - |
| `current_host().cwd` | - | - | - | - |
| `current_host` | - | `_DEFAULT` | - | `...` |
| `resolved.relative_to (src/llm_wiki_engine/path_policy.py:validate_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| list_wiki_pages | _validate_wiki_dir | 2082 | `_validate_wiki_dir(wiki_dir)` |
| _validate_wiki_dir | validate_path | 3575 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 100 | `PathValidationError(...)` |
| validate_path | (…).resolve | 101 | `(current_host().cwd() / path).resolve(data not statically known)` |
| validate_path | current_host().cwd | 101 | `current_host().cwd(data not statically known)` |
| validate_path | current_host | 101 | `current_host(data not statically known)` |
| current_host | _ACTIVE.get | 166 | `_ACTIVE.get(data not statically known)` |
| validate_path | current_host().cwd().resolve | 102 | `current_host().cwd().resolve(data not statically known)` |
| validate_path | current_host().cwd | 102 | `current_host().cwd(data not statically known)` |
| validate_path | current_host | 102 | `current_host(data not statically known)` |
| validate_path | resolved.relative_to (src/llm_wiki_engine/path_policy.py:validate_path) | 104 | `resolved.relative_to(cwd)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_path` | `(current_host().cwd() / path).resolve` | 101 |
| unresolved_call | `validate_path` | `current_host().cwd` | 101 |
| unresolved_call | `current_host` | `_ACTIVE.get` | 166 |
| unresolved_call | `validate_path` | `current_host().cwd().resolve` | 102 |
| unresolved_call | `validate_path` | `current_host().cwd` | 102 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 104 |
| step_limit | `list_wiki_pages` | `first 12 steps` | 0 |

## Behavior

This flow starts at `list_wiki_pages` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
