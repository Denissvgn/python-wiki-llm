# section_locator

**Entry point:** `section_locator` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as section_locator
    participant p1 as isinstance
    participant p2 as ValueError
    participant p3 as tuple
    participant p4 as len
    participant p5 as any
    participant p6 as quote
    participant p7 as zip
    participant p8 as join
    p0-->>p1: isinstance
    p0-->>p2: ValueError
    p0-->>p2: ValueError
    p0-->>p3: tuple
    p0-->>p3: tuple
    p0-->>p4: len
    p0-->>p4: len
    p0-->>p2: ValueError
    p0-->>p5: any
    p0-->>p1: isinstance
    p0-->>p2: ValueError
    p0-->>p5: any
    p0-->>p1: isinstance
    p0-->>p2: ValueError
    p0-->>p6: quote
    p0-->>p7: zip
    p0-->>p8: join
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. section_locator"]
    s2["2. isinstance"]
    s3["3. ValueError"]
    s4["4. ValueError"]
    s5["5. tuple"]
    s6["6. tuple"]
    s7["7. len"]
    s8["8. len"]
    s9["9. ValueError"]
    s10["10. any"]
    s11["11. isinstance"]
    s12["12. ValueError"]
    s1 -. "isinstance(page_locator, str)" .-> s2
    s1 -. "ValueError('page_locator must be a non-empty string')" .-> s3
    s1 -. "ValueError('page_locator must not already contain a fragment')" .-> s4
    s1 -. "tuple(heading_path)" .-> s5
    s1 -. "tuple(occurrence_path)" .-> s6
    s1 -. "len(headings)" .-> s7
    s1 -. "len(occurrences)" .-> s8
    s1 -. "ValueError('heading_path and occurrence_path must be non-empty peers')" .-> s9
    s1 -. "any(...)" .-> s10
    s1 -. "isinstance(value, str)" .-> s11
    s1 -. "ValueError('heading_path entries must be strings')" .-> s12
    click s1 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `section_locator` | `page_locator: str`, `heading_path: Iterable[str]`, `occurrence_path: Iterable[int]` | - | - | `...` |
| `isinstance` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `tuple` | - | - | - | - |
| `tuple` | - | - | - | - |
| `len` | - | - | - | - |
| `len` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `any` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `ValueError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| section_locator | isinstance | 300 | `isinstance(page_locator, str)` |
| section_locator | ValueError | 301 | `ValueError('page_locator must be a non-empty string')` |
| section_locator | ValueError | 303 | `ValueError('page_locator must not already contain a fragment')` |
| section_locator | tuple | 304 | `tuple(heading_path)` |
| section_locator | tuple | 305 | `tuple(occurrence_path)` |
| section_locator | len | 306 | `len(headings)` |
| section_locator | len | 306 | `len(occurrences)` |
| section_locator | ValueError | 307 | `ValueError('heading_path and occurrence_path must be non-empty peers')` |
| section_locator | any | 308 | `any(...)` |
| section_locator | isinstance | 308 | `isinstance(value, str)` |
| section_locator | ValueError | 309 | `ValueError('heading_path entries must be strings')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `section_locator` | `isinstance` | 300 |
| unresolved_call | `section_locator` | `ValueError` | 301 |
| unresolved_call | `section_locator` | `ValueError` | 303 |
| unresolved_call | `section_locator` | `ValueError` | 307 |
| unresolved_call | `section_locator` | `any` | 308 |
| unresolved_call | `section_locator` | `isinstance` | 308 |
| unresolved_call | `section_locator` | `ValueError` | 309 |
| step_limit | `section_locator` | `first 12 steps` | 0 |

## Behavior

This flow starts at `section_locator` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
