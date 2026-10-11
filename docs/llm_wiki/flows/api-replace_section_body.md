# replace_section_body

**Entry point:** `replace_section_body` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as replace_section_body
    participant p1 as normalize_markdown(…).splitlines
    participant p2 as normalize_markdown
    participant p3 as section_bounds
    participant p4 as body.splitlines
    participant p5 as '\n'.join
    participant p6 as text.replace(…).replace
    participant p7 as heading.casefold
    participant p8 as text.replace
    participant p9 as enumerate
    participant p10 as _LEGACY_HEADING_RE.match
    participant p11 as line.strip
    participant p12 as len
    participant p13 as match.group
    participant p14 as match.group(…).strip().casefold
    participant p15 as match.group(…).strip
    participant p16 as range
    participant p17 as lines[…].strip
    participant p18 as next_match.group
    p0-->>p1: normalize_markdown(…).splitlines
    p0->>p2: normalize_markdown
    p0->>p3: section_bounds
    p0-->>p4: body.splitlines
    p0-->>p5: '\n'.join(...)
    p2-->>p6: text.replace(…).replace('\r', '\n')
    p3-->>p7: heading.casefold
    p2-->>p8: text.replace('\r\n', '\n')
    p3-->>p9: enumerate(lines)
    p3-->>p10: _LEGACY_HEADING_RE.match(line.strip(...))
    p3-->>p11: line.strip
    p3-->>p12: len(match.group(...))
    p3-->>p13: match.group(1)
    p3-->>p14: match.group(…).strip().casefold
    p3-->>p15: match.group(…).strip
    p3-->>p13: match.group(2)
    p3-->>p12: len(lines)
    p3-->>p16: range(..., len(...))
    p3-->>p12: len(lines)
    p3-->>p10: _LEGACY_HEADING_RE.match(...)
    p3-->>p17: lines[…].strip
    p3-->>p12: len(next_match.group(...))
    p3-->>p18: next_match.group(1)
```

> Call sequence diagram shows 23 of 23 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 6 of 6 (0 omitted); unresolved 15 of 15 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. replace_section_body"]
    s2["2. normalize_markdown(…).splitlines"]
    s3["3. normalize_markdown"]
    s4["4. text.replace(…).replace"]
    s5["5. text.replace"]
    s6["6. section_bounds"]
    s7["7. heading.casefold"]
    s8["8. enumerate"]
    s9["9. _LEGACY_HEADING_RE.match"]
    s10["10. line.strip"]
    s11["11. len"]
    s12["12. match.group"]
    s1 -. "normalize_markdown(…).splitlines(data not statically known)" .-> s2
    s1 -->|"normalize_markdown(markdown)"| s3
    s3 -. "text.replace(…).replace('\r', '\n')" .-> s4
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
| `replace_section_body` | `markdown: str`, `heading: str`, `body: str` | - | - | `markdown`, `...` |
| `normalize_markdown(…).splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `section_bounds` | `lines: list[str]`, `heading: str` | - | - | `(...)`, `None` |
| `heading.casefold` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `_LEGACY_HEADING_RE.match` | - | - | - | - |
| `line.strip` | - | - | - | - |
| `len` | - | - | - | - |
| `match.group` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| replace_section_body | normalize_markdown(…).splitlines | 706 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| replace_section_body | normalize_markdown | 706 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 81 | `text.replace('\r\n', '\n')` |
| replace_section_body | section_bounds | 707 | `section_bounds(lines, heading)` |
| section_bounds | heading.casefold | 661 | `heading.casefold(data not statically known)` |
| section_bounds | enumerate | 662 | `enumerate(lines)` |
| section_bounds | _LEGACY_HEADING_RE.match | 663 | `_LEGACY_HEADING_RE.match(line.strip(...))` |
| section_bounds | line.strip | 663 | `line.strip(data not statically known)` |
| section_bounds | len | 666 | `len(match.group(...))` |
| section_bounds | match.group | 666 | `match.group(1)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `replace_section_body` | `normalize_markdown(markdown).splitlines` | 706 |
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| unresolved_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `section_bounds` | `heading.casefold` | 661 |
| external_call | `section_bounds` | `enumerate` | 662 |
| unresolved_call | `section_bounds` | `_LEGACY_HEADING_RE.match` | 663 |
| unresolved_call | `section_bounds` | `line.strip` | 663 |
| unresolved_call | `section_bounds` | `match.group` | 666 |
| step_limit | `replace_section_body` | `first 12 steps` | 0 |

## Behavior

This flow starts at `replace_section_body` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
