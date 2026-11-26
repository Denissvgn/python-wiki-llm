# list_wiki_pages

**Entry point:** `list_wiki_pages` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [host](../modules/host.md), [path_policy](../modules/path_policy.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as list_wiki_pages
    participant p1 as _validate_wiki_dir
    participant p2 as _wiki_page_payload
    participant p3 as InvalidRequestError
    participant p4 as _wiki_path_policy_details
    participant p5 as WorkspaceStateError
    participant p6 as _display_path
    participant p7 as _wiki_page_counts
    participant p8 as validate_path
    participant p9 as PathValidationError
    participant p10 as current_host
    participant p11 as str (src/llm_wiki_cli/api.py:list_wiki_pages)
    participant p12 as wiki_surface.collect_wiki_pages
    participant p13 as set
    participant p14 as path.relative_to(…).as_posix
    participant p15 as wiki_surface.iter_page_kinds
    participant p16 as id
    participant p17 as path.relative_to
    participant p18 as str (src/llm_wiki_cli/api.py:_wiki_page_counts)
    participant p19 as seen.add
    participant p20 as Path.cwd().resolve
    participant p21 as len
    participant p22 as Path.cwd
    participant p23 as isinstance
    participant p24 as path.as_posix
    participant p25 as (…).resolve
    participant p26 as current_host().cwd
    p0->>p1: _validate_wiki_dir
    p0->>p2: _wiki_page_payload
    p0->>p3: InvalidRequestError
    p0->>p4: _wiki_path_policy_details
    p0->>p5: WorkspaceStateError
    p0->>p6: _display_path
    p0->>p7: _wiki_page_counts
    p1->>p8: validate_path
    p8->>p9: PathValidationError
    p8->>p10: current_host
    p0-->>p11: str (src/llm_wiki_cli/api.py:list_wiki_pages)(exc)
    p0-->>p12: wiki_surface.collect_wiki_pages(wiki_root)
    p0-->>p11: str (src/llm_wiki_cli/api.py:list_wiki_pages)(exc)
    p0-->>p11: str (src/llm_wiki_cli/api.py:list_wiki_pages)(exc)
    p0-->>p11: str (src/llm_wiki_cli/api.py:list_wiki_pages)(exc)
    p4-->>p13: set
    p6-->>p14: path.relative_to(…).as_posix
    p7-->>p15: wiki_surface.iter_page_kinds
    p4-->>p16: id(current)
    p6-->>p17: path.relative_to(...)
    p7-->>p18: str (src/llm_wiki_cli/api.py:_wiki_page_counts)(page[...])
    p4-->>p19: seen.add(id(...))
    p6-->>p20: Path.cwd().resolve
    p7-->>p21: len(pages)
    p4-->>p16: id(current)
    p6-->>p22: Path.cwd
    p4-->>p23: isinstance(current, wiki_surface.WikiSurfacePathError)
    p6-->>p24: path.as_posix
    p8-->>p25: (…).resolve
    p8-->>p26: current_host().cwd
```

> Call sequence diagram shows 30 of 38 interactions; 8 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 11 (0 omitted); unresolved 9 of 13 (4 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_engine/host.py:current_host` | 7 | - | unresolved | 1 |
| `src/llm_wiki_engine/path_policy.py:validate_path` | 3 | - | unresolved | 3 |
| `src/llm_wiki_engine/path_policy.py:validate_path` | 3 | [src/llm_wiki_engine/host.py](../modules/host.md) | internal | 1 |
| `src/llm_wiki_engine/path_policy.py:validate_path` | 3 | [src/llm_wiki_engine/path_policy.py](../modules/path_policy.md) | internal | 1 |
| `src/llm_wiki_cli/api.py:list_wiki_pages` | 1 | [src/llm_wiki_cli/api.py](../modules/api.md) | internal | 2 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 15; effect analysis evaluated: 9, partial: 0, unavailable: 6. Counts include steps omitted from the displayed trace.

Collector observations for 9 source steps with known totals: observed: 29, emitted: 29, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
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
| `resolved.relative_to` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

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
    s12["12. resolved.relative_to"]
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
    s3 -. "resolved.relative_to(cwd)" .-> s12
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
| `resolved.relative_to` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| list_wiki_pages | _validate_wiki_dir | 2101 | `_validate_wiki_dir(wiki_dir)` |
| _validate_wiki_dir | validate_path | 3924 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 102 | `PathValidationError(...)` |
| validate_path | (…).resolve | 103 | `(current_host().cwd() / path).resolve(data not statically known)` |
| validate_path | current_host().cwd | 103 | `current_host().cwd(data not statically known)` |
| validate_path | current_host | 103 | `current_host(data not statically known)` |
| current_host | _ACTIVE.get | 167 | `_ACTIVE.get(data not statically known)` |
| validate_path | current_host().cwd().resolve | 104 | `current_host().cwd().resolve(data not statically known)` |
| validate_path | current_host().cwd | 104 | `current_host().cwd(data not statically known)` |
| validate_path | current_host | 104 | `current_host(data not statically known)` |
| validate_path | resolved.relative_to | 106 | `resolved.relative_to(cwd)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_path` | `(current_host().cwd() / path).resolve` | 103 |
| unresolved_call | `validate_path` | `current_host().cwd` | 103 |
| unresolved_call | `current_host` | `_ACTIVE.get` | 167 |
| unresolved_call | `validate_path` | `current_host().cwd().resolve` | 104 |
| unresolved_call | `validate_path` | `current_host().cwd` | 104 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 106 |
| step_limit | `list_wiki_pages` | `first 12 steps` | 0 |

## Behavior

This flow starts at `list_wiki_pages` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
