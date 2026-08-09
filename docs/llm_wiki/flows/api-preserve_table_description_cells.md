# preserve_table_description_cells

**Entry point:** `preserve_table_description_cells` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as preserve_table_description_cells
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
    participant p12 as split_table_row
    participant p13 as startswith
    participant p14 as endswith
    participant p15 as extend
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
    p0-->>p11: range
    p0->>p12: split_table_row
    p12-->>p8: strip
    p12-->>p13: startswith
    p12-->>p14: endswith
    p12-->>p9: len
    p12-->>p9: len
    p12-->>p15: extend
    p12-->>p9: len
```

> Call sequence diagram shows 30 of 60 interactions; 30 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. preserve_table_description_cells"]
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
| `preserve_table_description_cells` | `markdown: str`, `heading: str`, `descriptions: dict[str, str]`, `old_descriptions: dict[str, str] \| None`, `should_preserve: Callable[[str \| None, str \| None, str \| None], bool] \| None` | `should_preserve_semantic_value` | `row[...]`, `lines[...]` | `(...)`, `(...)`, `(...)`, `(...)` |
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
| preserve_table_description_cells | splitlines | 877 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| preserve_table_description_cells | normalize_markdown | 877 | `normalize_markdown(markdown)` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n')` |
| preserve_table_description_cells | section_bounds | 878 | `section_bounds(lines, heading)` |
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
| unresolved_call | `preserve_table_description_cells` | `normalize_markdown(markdown).splitlines` | 877 |
| external_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| external_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `section_bounds` | `heading.casefold` | 661 |
| unresolved_call | `section_bounds` | `enumerate` | 662 |
| unresolved_call | `section_bounds` | `_LEGACY_HEADING_RE.match` | 663 |
| unresolved_call | `section_bounds` | `line.strip` | 663 |
| unresolved_call | `section_bounds` | `match.group` | 666 |
| step_limit | `preserve_table_description_cells` | `first 12 steps` | 0 |

## Behavior

This flow starts at `preserve_table_description_cells` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
