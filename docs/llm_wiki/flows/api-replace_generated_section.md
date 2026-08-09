# replace_generated_section

**Entry point:** `replace_generated_section` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as replace_generated_section
    participant p1 as section_body
    participant p2 as splitlines
    participant p3 as normalize_markdown
    participant p4 as replace
    participant p5 as section_bounds
    participant p6 as casefold
    participant p7 as enumerate
    participant p8 as match
    participant p9 as strip
    participant p10 as len
    participant p11 as group
    participant p12 as range
    participant p13 as join
    participant p14 as trim_blank_lines
    participant p15 as replace_section_body
    p0->>p1: section_body
    p1-->>p2: splitlines
    p1->>p3: normalize_markdown
    p3-->>p4: replace
    p3-->>p4: replace
    p1->>p5: section_bounds
    p5-->>p6: casefold
    p5-->>p7: enumerate
    p5-->>p8: match
    p5-->>p9: strip
    p5-->>p10: len
    p5-->>p11: group
    p5-->>p6: casefold
    p5-->>p9: strip
    p5-->>p11: group
    p5-->>p10: len
    p5-->>p12: range
    p5-->>p10: len
    p5-->>p8: match
    p5-->>p9: strip
    p5-->>p10: len
    p5-->>p11: group
    p1-->>p9: strip
    p1-->>p13: join
    p1->>p14: trim_blank_lines
    p14-->>p10: len
    p14-->>p9: strip
    p14-->>p9: strip
    p0->>p1: section_body
    p0->>p15: replace_section_body
```

> Call sequence diagram shows 30 of 37 interactions; 7 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. replace_generated_section"]
    s2["2. section_body"]
    s3["3. splitlines"]
    s4["4. normalize_markdown"]
    s5["5. replace"]
    s6["6. replace"]
    s7["7. section_bounds"]
    s8["8. casefold"]
    s9["9. enumerate"]
    s10["10. match"]
    s11["11. strip"]
    s12["12. len"]
    s1 -->|"section_body(existing, heading)"| s2
    s2 -. "normalize_markdown(markdown).splitlines(data not statically known)" .-> s3
    s2 -->|"normalize_markdown(markdown)"| s4
    s4 -. "text.replace('\r\n', '\n').replace('\r', '\n')" .-> s5
    s4 -. "text.replace('\r\n', '\n')" .-> s6
    s2 -->|"section_bounds(lines, heading)"| s7
    s7 -. "heading.casefold(data not statically known)" .-> s8
    s7 -. "enumerate(lines)" .-> s9
    s7 -. "_LEGACY_HEADING_RE.match(line.strip(...))" .-> s10
    s7 -. "line.strip(data not statically known)" .-> s11
    s7 -. "len(match.group(...))" .-> s12
    click s1 "../modules/section_ownership.md"
    click s2 "../modules/markdown_sections.md"
    click s4 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `replace_generated_section` | `existing: str`, `generated: str`, `heading: str` | - | - | `existing`, `existing`, `updated` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| replace_generated_section | section_body | 1236 | `section_body(existing, heading)` |
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
| step_limit | `replace_generated_section` | `first 12 steps` | 0 |

## Behavior

This flow starts at `replace_generated_section` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
