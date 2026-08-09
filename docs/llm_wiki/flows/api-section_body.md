# section_body

**Entry point:** `section_body` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as section_body
    participant p1 as splitlines
    participant p2 as normalize_markdown
    participant p3 as replace
    participant p4 as section_bounds
    participant p5 as casefold
    participant p6 as enumerate
    participant p7 as match
    participant p8 as strip
    participant p9 as len
    participant p10 as group
    participant p11 as range
    participant p12 as join
    participant p13 as trim_blank_lines
    p0-->>p1: splitlines
    p0->>p2: normalize_markdown
    p2-->>p3: replace
    p2-->>p3: replace
    p0->>p4: section_bounds
    p4-->>p5: casefold
    p4-->>p6: enumerate
    p4-->>p7: match
    p4-->>p8: strip
    p4-->>p9: len
    p4-->>p10: group
    p4-->>p5: casefold
    p4-->>p8: strip
    p4-->>p10: group
    p4-->>p9: len
    p4-->>p11: range
    p4-->>p9: len
    p4-->>p7: match
    p4-->>p8: strip
    p4-->>p9: len
    p4-->>p10: group
    p0-->>p8: strip
    p0-->>p12: join
    p0->>p13: trim_blank_lines
    p13-->>p9: len
    p13-->>p8: strip
    p13-->>p8: strip
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. section_body"]
    s2["2. splitlines"]
    s3["3. normalize_markdown"]
    s4["4. replace"]
    s5["5. replace"]
    s6["6. section_bounds"]
    s7["7. casefold"]
    s8["8. enumerate"]
    s9["9. match"]
    s10["10. strip"]
    s11["11. len"]
    s12["12. group"]
    s1 -. "normalize_markdown(markdown).splitlines(data not statically known)" .-> s2
    s1 -->|"normalize_markdown(markdown)"| s3
    s3 -. "text.replace('\r\n', '\n').replace('\r', '\n')" .-> s4
    s3 -. "text.replace('\r\n', '\n')" .-> s5
    s1 -->|"section_bounds(lines, heading)"| s6
    s6 -. "heading.casefold(data not statically known)" .-> s7
    s6 -. "enumerate(lines)" .-> s8
    s6 -. "_LEGACY_HEADING_RE.match(line.strip(...))" .-> s9
    s6 -. "line.strip(data not statically known)" .-> s10
    s6 -. "len(match.group(...))" .-> s11
    s6 -. "match.group(1)" .-> s12
    click s1 "../modules/markdown_sections.md"
    click s3 "../modules/markdown_sections.md"
    click s6 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `section_body` | `markdown: str`, `heading: str` | - | - | `None`, `...` |
| `splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `section_bounds` | `lines: list[str]`, `heading: str` | - | - | `(...)`, `None` |
| `casefold` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `match` | - | - | - | - |
| `strip` | - | - | - | - |
| `len` | - | - | - | - |
| `group` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| section_body | splitlines | 695 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| section_body | normalize_markdown | 695 | `normalize_markdown(markdown)` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n')` |
| section_body | section_bounds | 696 | `section_bounds(lines, heading)` |
| section_bounds | casefold | 661 | `heading.casefold(data not statically known)` |
| section_bounds | enumerate | 662 | `enumerate(lines)` |
| section_bounds | match | 663 | `_LEGACY_HEADING_RE.match(line.strip(...))` |
| section_bounds | strip | 663 | `line.strip(data not statically known)` |
| section_bounds | len | 666 | `len(match.group(...))` |
| section_bounds | group | 666 | `match.group(1)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `section_body` | `normalize_markdown(markdown).splitlines` | 695 |
| external_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| external_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `section_bounds` | `heading.casefold` | 661 |
| unresolved_call | `section_bounds` | `enumerate` | 662 |
| unresolved_call | `section_bounds` | `_LEGACY_HEADING_RE.match` | 663 |
| unresolved_call | `section_bounds` | `line.strip` | 663 |
| unresolved_call | `section_bounds` | `match.group` | 666 |
| step_limit | `section_body` | `first 12 steps` | 0 |

## Behavior

This flow starts at `section_body` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
