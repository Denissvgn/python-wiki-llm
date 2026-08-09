# merge_semantic_markdown

**Entry point:** `merge_semantic_markdown` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as merge_semantic_markdown
    participant p1 as normalize_markdown
    participant p2 as replace
    participant p3 as section_body
    participant p4 as splitlines
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
    p0->>p1: normalize_markdown
    p1-->>p2: replace
    p1-->>p2: replace
    p0->>p3: section_body
    p3-->>p4: splitlines
    p3->>p1: normalize_markdown
    p3->>p5: section_bounds
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
    p3-->>p9: strip
    p3-->>p13: join
    p3->>p14: trim_blank_lines
    p14-->>p10: len
    p14-->>p9: strip
    p14-->>p9: strip
    p0->>p3: section_body
```

> Call sequence diagram shows 30 of 103 interactions; 73 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. merge_semantic_markdown"]
    s2["2. normalize_markdown"]
    s3["3. replace"]
    s4["4. replace"]
    s5["5. section_body"]
    s6["6. splitlines"]
    s7["7. normalize_markdown"]
    s8["8. section_bounds"]
    s9["9. casefold"]
    s10["10. enumerate"]
    s11["11. match"]
    s12["12. strip"]
    s1 -->|"normalize_markdown(generated)"| s2
    s2 -. "text.replace('\r\n', '\n').replace('\r', '\n')" .-> s3
    s2 -. "text.replace('\r\n', '\n')" .-> s4
    s1 -->|"section_body(existing, 'Description')"| s5
    s5 -. "normalize_markdown(markdown).splitlines(data not statically known)" .-> s6
    s5 -->|"normalize_markdown(markdown)"| s7
    s5 -->|"section_bounds(lines, heading)"| s8
    s8 -. "heading.casefold(data not statically known)" .-> s9
    s8 -. "enumerate(lines)" .-> s10
    s8 -. "_LEGACY_HEADING_RE.match(line.strip(...))" .-> s11
    s8 -. "line.strip(data not statically known)" .-> s12
    click s1 "../modules/section_ownership.md"
    click s2 "../modules/markdown_sections.md"
    click s5 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
    click s8 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `merge_semantic_markdown` | `existing: str`, `generated: str`, `table_headings: tuple[str, ...]`, `old_description: str \| None`, `old_table_descriptions: dict[str, dict[str, str]] \| None` | - | - | `SemanticMergeResult(...)` |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `section_body` | `markdown: str`, `heading: str` | - | - | `None`, `...` |
| `splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `section_bounds` | `lines: list[str]`, `heading: str` | - | - | `(...)`, `None` |
| `casefold` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `match` | - | - | - | - |
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| merge_semantic_markdown | normalize_markdown | 1155 | `normalize_markdown(generated)` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n')` |
| merge_semantic_markdown | section_body | 1157 | `section_body(existing, 'Description')` |
| section_body | splitlines | 695 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| section_body | normalize_markdown | 695 | `normalize_markdown(markdown)` |
| section_body | section_bounds | 696 | `section_bounds(lines, heading)` |
| section_bounds | casefold | 661 | `heading.casefold(data not statically known)` |
| section_bounds | enumerate | 662 | `enumerate(lines)` |
| section_bounds | match | 663 | `_LEGACY_HEADING_RE.match(line.strip(...))` |
| section_bounds | strip | 663 | `line.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| external_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `section_body` | `normalize_markdown(markdown).splitlines` | 695 |
| unresolved_call | `section_bounds` | `heading.casefold` | 661 |
| unresolved_call | `section_bounds` | `enumerate` | 662 |
| unresolved_call | `section_bounds` | `_LEGACY_HEADING_RE.match` | 663 |
| unresolved_call | `section_bounds` | `line.strip` | 663 |
| step_limit | `merge_semantic_markdown` | `first 12 steps` | 0 |

## Behavior

This flow starts at `merge_semantic_markdown` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
