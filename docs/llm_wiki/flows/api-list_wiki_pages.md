# list_wiki_pages

**Entry point:** `list_wiki_pages` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [config](../modules/config.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as list_wiki_pages
    participant p1 as _validate_wiki_dir
    participant p2 as validate_path
    participant p3 as PathValidationError
    participant p4 as resolve
    participant p5 as cwd
    participant p6 as relative_to
    participant p7 as _wiki_page_payload
    participant p8 as collect_wiki_pages
    participant p9 as PathPolicyError
    participant p10 as str
    participant p11 as _wiki_path_policy_details
    participant p12 as set
    participant p13 as id
    participant p14 as add
    participant p15 as isinstance
    participant p16 as InvalidRequestError
    participant p17 as WorkspaceStateError
    participant p18 as _display_path
    participant p19 as as_posix
    p0->>p1: _validate_wiki_dir
    p1->>p2: validate_path
    p2->>p3: PathValidationError
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p4: resolve
    p2-->>p5: cwd
    p2-->>p6: relative_to
    p2->>p3: PathValidationError
    p0->>p7: _wiki_page_payload
    p0-->>p8: collect_wiki_pages
    p0-->>p9: PathPolicyError
    p0-->>p10: str
    p0-->>p9: PathPolicyError
    p0-->>p10: str
    p0->>p11: _wiki_path_policy_details
    p11-->>p12: set
    p11-->>p13: id
    p11-->>p14: add
    p11-->>p13: id
    p11-->>p15: isinstance
    p0->>p16: InvalidRequestError
    p0-->>p10: str
    p0->>p17: WorkspaceStateError
    p0-->>p10: str
    p0->>p18: _display_path
    p18-->>p19: as_posix
    p18-->>p6: relative_to
    p18-->>p4: resolve
    p18-->>p5: cwd
```

> Call sequence diagram shows 30 of 35 interactions; 5 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. list_wiki_pages"]
    s2["2. _validate_wiki_dir"]
    s3["3. validate_path"]
    s4["4. PathValidationError"]
    s5["5. resolve"]
    s6["6. cwd"]
    s7["7. resolve"]
    s8["8. cwd"]
    s9["9. relative_to"]
    s10["10. PathValidationError"]
    s11["11. _wiki_page_payload"]
    s12["12. collect_wiki_pages"]
    s1 -->|"_validate_wiki_dir(wiki_dir)"| s2
    s2 -->|"validate_path(wiki_dir, '--wiki-dir')"| s3
    s3 -->|"PathValidationError(...)"| s4
    s3 -. "(Path.cwd() / path).resolve(data not statically known)" .-> s5
    s3 -. "Path.cwd(data not statically known)" .-> s6
    s3 -. "Path.cwd().resolve(data not statically known)" .-> s7
    s3 -. "Path.cwd(data not statically known)" .-> s8
    s3 -. "resolved.relative_to(cwd)" .-> s9
    s3 -->|"PathValidationError(...)"| s10
    s1 -->|"_wiki_page_payload(page)"| s11
    s1 -. "wiki_surface.collect_wiki_pages(wiki_root)" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
    click s3 "../modules/config.md"
    click s4 "../modules/config.md"
    click s10 "../modules/config.md"
    click s11 "../modules/api.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `list_wiki_pages` | `wiki_dir: str` | `PathValidationError`, `wiki_surface`, `wiki_surface` | - | `{...}` |
| `_validate_wiki_dir` | `wiki_dir: str` | - | - | `validate_path(...)` |
| `validate_path` | `path: str`, `label: str` | - | - | `resolved` |
| `PathValidationError` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `resolve` | - | - | - | - |
| `cwd` | - | - | - | - |
| `relative_to` | - | - | - | - |
| `PathValidationError` | - | - | - | - |
| `_wiki_page_payload` | `page: wiki_surface.WikiSurfacePage` | - | - | `{...}` |
| `collect_wiki_pages` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| list_wiki_pages | _validate_wiki_dir | 1018 | `_validate_wiki_dir(wiki_dir)` |
| _validate_wiki_dir | validate_path | 2326 | `validate_path(wiki_dir, '--wiki-dir')` |
| validate_path | PathValidationError | 132 | `PathValidationError(...)` |
| validate_path | resolve | 133 | `(Path.cwd() / path).resolve(data not statically known)` |
| validate_path | cwd | 133 | `Path.cwd(data not statically known)` |
| validate_path | resolve | 134 | `Path.cwd().resolve(data not statically known)` |
| validate_path | cwd | 134 | `Path.cwd(data not statically known)` |
| validate_path | relative_to | 136 | `resolved.relative_to(cwd)` |
| validate_path | PathValidationError | 138 | `PathValidationError(...)` |
| list_wiki_pages | _wiki_page_payload | 1020 | `_wiki_page_payload(page)` |
| list_wiki_pages | collect_wiki_pages | 1021 | `wiki_surface.collect_wiki_pages(wiki_root)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_path` | `(Path.cwd() / path).resolve` | 133 |
| external_call | `validate_path` | `Path.cwd` | 133 |
| external_call | `validate_path` | `Path.cwd().resolve` | 134 |
| external_call | `validate_path` | `Path.cwd` | 134 |
| unresolved_call | `validate_path` | `resolved.relative_to` | 136 |
| external_call | `list_wiki_pages` | `wiki_surface.collect_wiki_pages` | 1021 |
| step_limit | `list_wiki_pages` | `first 12 steps` | 0 |

## Behavior

This flow starts at `list_wiki_pages` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
