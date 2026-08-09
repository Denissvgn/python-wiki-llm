# serialize_section_ownership

**Entry point:** `serialize_section_ownership` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [section_ownership](../modules/section_ownership.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as serialize_section_ownership
    participant p1 as sorted
    participant p2 as casefold
    participant p3 as set
    participant p4 as ValueError
    participant p5 as add
    participant p6 as len
    participant p7 as to_payload
    p0-->>p1: sorted
    p0-->>p2: casefold
    p0-->>p3: set
    p0-->>p4: ValueError
    p0-->>p5: add
    p0-->>p1: sorted
    p0-->>p6: len
    p0-->>p6: len
    p0-->>p3: set
    p0-->>p4: ValueError
    p0-->>p7: to_payload
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. serialize_section_ownership"]
    s2["2. sorted"]
    s3["3. casefold"]
    s4["4. set"]
    s5["5. ValueError"]
    s6["6. add"]
    s7["7. sorted"]
    s8["8. len"]
    s9["9. len"]
    s10["10. set"]
    s11["11. ValueError"]
    s12["12. to_payload"]
    s1 -. "sorted(pages, key=...)" .-> s2
    s1 -. "page.page_locator.casefold(data not statically known)" .-> s3
    s1 -. "set(data not statically known)" .-> s4
    s1 -. "ValueError(...)" .-> s5
    s1 -. "seen.add(page.page_locator)" .-> s6
    s1 -. "sorted(ordinals)" .-> s7
    s1 -. "len(ordinals)" .-> s8
    s1 -. "len(set(...))" .-> s9
    s1 -. "set(ordinals)" .-> s10
    s1 -. "ValueError(...)" .-> s11
    s1 -. "page.to_payload(data not statically known)" .-> s12
    b0["mutation seen.add"]
    s1 -. "mutation seen.add" .-> b0
    click s1 "../modules/section_ownership.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `to_payload` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| serialize_section_ownership | to_payload | 632 | `page.to_payload(data not statically known)` |

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
| unresolved_call | `serialize_section_ownership` | `page.to_payload` | 632 |

## Behavior

This flow starts at `serialize_section_ownership` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
