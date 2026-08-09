# section_ownership_extension

**Entry point:** `section_ownership_extension` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [section_ownership](../modules/section_ownership.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as section_ownership_extension
    participant p1 as serialize_section_ownership
    participant p2 as sorted
    participant p3 as casefold
    participant p4 as set
    participant p5 as ValueError
    participant p6 as add
    participant p7 as len
    participant p8 as to_payload
    p0->>p1: serialize_section_ownership
    p1-->>p2: sorted
    p1-->>p3: casefold
    p1-->>p4: set
    p1-->>p5: ValueError
    p1-->>p6: add
    p1-->>p2: sorted
    p1-->>p7: len
    p1-->>p7: len
    p1-->>p4: set
    p1-->>p5: ValueError
    p1-->>p8: to_payload
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. section_ownership_extension"]
    s2["2. serialize_section_ownership"]
    s3["3. sorted"]
    s4["4. casefold"]
    s5["5. set"]
    s6["6. ValueError"]
    s7["7. add"]
    s8["8. sorted"]
    s9["9. len"]
    s10["10. len"]
    s11["11. set"]
    s12["12. ValueError"]
    s1 -->|"serialize_section_ownership(pages)"| s2
    s2 -. "sorted(pages, key=...)" .-> s3
    s2 -. "page.page_locator.casefold(data not statically known)" .-> s4
    s2 -. "set(data not statically known)" .-> s5
    s2 -. "ValueError(...)" .-> s6
    s2 -. "seen.add(page.page_locator)" .-> s7
    s2 -. "sorted(ordinals)" .-> s8
    s2 -. "len(ordinals)" .-> s9
    s2 -. "len(set(...))" .-> s10
    s2 -. "set(ordinals)" .-> s11
    s2 -. "ValueError(...)" .-> s12
    b0["mutation seen.add"]
    s2 -. "mutation seen.add" .-> b0
    click s1 "../modules/section_ownership.md"
    click s2 "../modules/section_ownership.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `section_ownership_extension` | `pages: Iterable[PageSectionObservations]` | `SECTION_OWNERSHIP_EXTENSION_KEY` | - | `{...}` |
| `serialize_section_ownership` | `pages: Iterable[PageSectionObservations]` | `SECTION_OWNERSHIP_SCHEMA_VERSION` | - | `{...}` |
| `sorted` | - | - | - | - |
| `casefold` | - | - | - | - |
| `set` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `add` | - | - | - | - |
| `sorted` | - | - | - | - |
| `len` | - | - | - | - |
| `len` | - | - | - | - |
| `set` | - | - | - | - |
| `ValueError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| section_ownership_extension | serialize_section_ownership | 1141 | `serialize_section_ownership(pages)` |
| serialize_section_ownership | sorted | 616 | `sorted(pages, key=...)` |
| serialize_section_ownership | casefold | 618 | `page.page_locator.casefold(data not statically known)` |
| serialize_section_ownership | set | 620 | `set(data not statically known)` |
| serialize_section_ownership | ValueError | 623 | `ValueError(...)` |
| serialize_section_ownership | add | 624 | `seen.add(page.page_locator)` |
| serialize_section_ownership | sorted | 626 | `sorted(ordinals)` |
| serialize_section_ownership | len | 626 | `len(ordinals)` |
| serialize_section_ownership | len | 626 | `len(set(...))` |
| serialize_section_ownership | set | 626 | `set(ordinals)` |
| serialize_section_ownership | ValueError | 627 | `ValueError(...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen.add` | `serialize_section_ownership` | 624 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `serialize_section_ownership` | `sorted` | 616 |
| unresolved_call | `serialize_section_ownership` | `page.page_locator.casefold` | 618 |
| unresolved_call | `serialize_section_ownership` | `ValueError` | 623 |
| unresolved_call | `serialize_section_ownership` | `sorted` | 626 |
| unresolved_call | `serialize_section_ownership` | `ValueError` | 627 |
| step_limit | `section_ownership_extension` | `first 12 steps` | 0 |

## Behavior

This flow starts at `section_ownership_extension` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
