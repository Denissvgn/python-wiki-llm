# merge_entity_semantics

**Entry point:** `merge_entity_semantics` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as merge_entity_semantics
    participant p1 as get
    participant p2 as merge_semantic_markdown
    participant p3 as normalize_markdown
    participant p4 as replace
    participant p5 as section_body
    participant p6 as splitlines
    participant p7 as section_bounds
    participant p8 as casefold
    participant p9 as enumerate
    participant p10 as match
    participant p11 as strip
    participant p12 as len
    participant p13 as group
    participant p14 as range
    participant p15 as join
    participant p16 as trim_blank_lines
    p0-->>p1: get
    p0-->>p1: get
    p0-->>p1: get
    p0->>p2: merge_semantic_markdown
    p2->>p3: normalize_markdown
    p3-->>p4: replace
    p3-->>p4: replace
    p2->>p5: section_body
    p5-->>p6: splitlines
    p5->>p3: normalize_markdown
    p5->>p7: section_bounds
    p7-->>p8: casefold
    p7-->>p9: enumerate
    p7-->>p10: match
    p7-->>p11: strip
    p7-->>p12: len
    p7-->>p13: group
    p7-->>p8: casefold
    p7-->>p11: strip
    p7-->>p13: group
    p7-->>p12: len
    p7-->>p14: range
    p7-->>p12: len
    p7-->>p10: match
    p7-->>p11: strip
    p7-->>p12: len
    p7-->>p13: group
    p5-->>p11: strip
    p5-->>p15: join
    p5->>p16: trim_blank_lines
```

> Call sequence diagram shows 30 of 112 interactions; 82 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. merge_entity_semantics"]
    s2["2. get"]
    s3["3. get"]
    s4["4. get"]
    s5["5. merge_semantic_markdown"]
    s6["6. normalize_markdown"]
    s7["7. replace"]
    s8["8. replace"]
    s9["9. section_body"]
    s10["10. splitlines"]
    s11["11. normalize_markdown"]
    s12["12. section_bounds"]
    s1 -. "semantics.get('attributes', {...})" .-> s2
    s1 -. "semantics.get('methods', {...})" .-> s3
    s1 -. "semantics.get('description')" .-> s4
    s1 -->|"merge_semantic_markdown(existing, generated, (...), old_description=..., old_table_descriptions={...})"| s5
    s5 -->|"normalize_markdown(generated)"| s6
    s6 -. "text.replace('\r\n', '\n').replace('\r', '\n')" .-> s7
    s6 -. "text.replace('\r\n', '\n')" .-> s8
    s5 -->|"section_body(existing, 'Description')"| s9
    s9 -. "normalize_markdown(markdown).splitlines(data not statically known)" .-> s10
    s9 -->|"normalize_markdown(markdown)"| s11
    s9 -->|"section_bounds(lines, heading)"| s12
    click s1 "../modules/section_ownership.md"
    click s5 "../modules/section_ownership.md"
    click s6 "../modules/markdown_sections.md"
    click s9 "../modules/markdown_sections.md"
    click s11 "../modules/markdown_sections.md"
    click s12 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `merge_entity_semantics` | `existing: str`, `generated: str`, `old_semantics: Mapping[str, object] \| None` | `Mapping`, `Mapping` | - | `merge_semantic_markdown(...)` |
| `get` | - | - | - | - |
| `get` | - | - | - | - |
| `get` | - | - | - | - |
| `merge_semantic_markdown` | `existing: str`, `generated: str`, `table_headings: tuple[str, ...]`, `old_description: str \| None`, `old_table_descriptions: dict[str, dict[str, str]] \| None` | - | - | `SemanticMergeResult(...)` |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `section_body` | `markdown: str`, `heading: str` | - | - | `None`, `...` |
| `splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `section_bounds` | `lines: list[str]`, `heading: str` | - | - | `(...)`, `None` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| merge_entity_semantics | get | 1191 | `semantics.get('attributes', {...})` |
| merge_entity_semantics | get | 1192 | `semantics.get('methods', {...})` |
| merge_entity_semantics | get | 1193 | `semantics.get('description')` |
| merge_entity_semantics | merge_semantic_markdown | 1194 | `merge_semantic_markdown(existing, generated, (...), old_description=..., old_table_descriptions={...})` |
| merge_semantic_markdown | normalize_markdown | 1155 | `normalize_markdown(generated)` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n')` |
| merge_semantic_markdown | section_body | 1157 | `section_body(existing, 'Description')` |
| section_body | splitlines | 695 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| section_body | normalize_markdown | 695 | `normalize_markdown(markdown)` |
| section_body | section_bounds | 696 | `section_bounds(lines, heading)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `merge_entity_semantics` | `semantics.get` | 1191 |
| unresolved_call | `merge_entity_semantics` | `semantics.get` | 1192 |
| unresolved_call | `merge_entity_semantics` | `semantics.get` | 1193 |
| external_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| external_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `section_body` | `normalize_markdown(markdown).splitlines` | 695 |
| step_limit | `merge_entity_semantics` | `first 12 steps` | 0 |

## Behavior

This flow starts at `merge_entity_semantics` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
