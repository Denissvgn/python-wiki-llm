# section_bounds

**Entry point:** `section_bounds` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as section_bounds
    participant p1 as casefold
    participant p2 as enumerate
    participant p3 as match
    participant p4 as strip
    participant p5 as len
    participant p6 as group
    participant p7 as range
    p0-->>p1: casefold
    p0-->>p2: enumerate
    p0-->>p3: match
    p0-->>p4: strip
    p0-->>p5: len
    p0-->>p6: group
    p0-->>p1: casefold
    p0-->>p4: strip
    p0-->>p6: group
    p0-->>p5: len
    p0-->>p7: range
    p0-->>p5: len
    p0-->>p3: match
    p0-->>p4: strip
    p0-->>p5: len
    p0-->>p6: group
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. section_bounds"]
    s2["2. casefold"]
    s3["3. enumerate"]
    s4["4. match"]
    s5["5. strip"]
    s6["6. len"]
    s7["7. group"]
    s8["8. casefold"]
    s9["9. strip"]
    s10["10. group"]
    s11["11. len"]
    s12["12. range"]
    s1 -. "heading.casefold(data not statically known)" .-> s2
    s1 -. "enumerate(lines)" .-> s3
    s1 -. "_LEGACY_HEADING_RE.match(line.strip(...))" .-> s4
    s1 -. "line.strip(data not statically known)" .-> s5
    s1 -. "len(match.group(...))" .-> s6
    s1 -. "match.group(1)" .-> s7
    s1 -. "match.group(2).strip().casefold(data not statically known)" .-> s8
    s1 -. "match.group(2).strip(data not statically known)" .-> s9
    s1 -. "match.group(2)" .-> s10
    s1 -. "len(lines)" .-> s11
    s1 -. "range(..., len(...))" .-> s12
    click s1 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `section_bounds` | `lines: list[str]`, `heading: str` | - | - | `(...)`, `None` |
| `casefold` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `match` | - | - | - | - |
| `strip` | - | - | - | - |
| `len` | - | - | - | - |
| `group` | - | - | - | - |
| `casefold` | - | - | - | - |
| `strip` | - | - | - | - |
| `group` | - | - | - | - |
| `len` | - | - | - | - |
| `range` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| section_bounds | casefold | 661 | `heading.casefold(data not statically known)` |
| section_bounds | enumerate | 662 | `enumerate(lines)` |
| section_bounds | match | 663 | `_LEGACY_HEADING_RE.match(line.strip(...))` |
| section_bounds | strip | 663 | `line.strip(data not statically known)` |
| section_bounds | len | 666 | `len(match.group(...))` |
| section_bounds | group | 666 | `match.group(1)` |
| section_bounds | casefold | 667 | `match.group(2).strip().casefold(data not statically known)` |
| section_bounds | strip | 667 | `match.group(2).strip(data not statically known)` |
| section_bounds | group | 667 | `match.group(2)` |
| section_bounds | len | 670 | `len(lines)` |
| section_bounds | range | 671 | `range(..., len(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `section_bounds` | `heading.casefold` | 661 |
| unresolved_call | `section_bounds` | `enumerate` | 662 |
| unresolved_call | `section_bounds` | `_LEGACY_HEADING_RE.match` | 663 |
| unresolved_call | `section_bounds` | `line.strip` | 663 |
| unresolved_call | `section_bounds` | `match.group` | 666 |
| unresolved_call | `section_bounds` | `match.group(2).strip().casefold` | 667 |
| unresolved_call | `section_bounds` | `match.group(2).strip` | 667 |
| unresolved_call | `section_bounds` | `match.group` | 667 |
| unresolved_call | `section_bounds` | `range` | 671 |
| step_limit | `section_bounds` | `first 12 steps` | 0 |

## Behavior

This flow starts at `section_bounds` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
