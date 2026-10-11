# merge_entity_semantics

**Entry point:** `merge_entity_semantics` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as merge_entity_semantics
    participant p1 as merge_semantic_markdown
    participant p2 as section_body
    participant p3 as should_preserve_semantic_value
    participant p4 as replace_section_body
    participant p5 as table_description_cells
    participant p6 as preserve_table_description_cells
    participant p7 as normalize_markdown
    participant p8 as SemanticMergeResult
    participant p9 as is_placeholder_description
    participant p10 as section_bounds
    participant p11 as split_table_row
    participant p12 as trim_blank_lines
    participant p13 as is_table_separator
    participant p14 as semantic_table_key
    participant p15 as format_table_row
    participant p16 as isinstance
    participant p17 as semantics.get
    participant p18 as dict
    participant p19 as (…).get (src/llm_wiki_cli/services…y:merge_semantic_markdown)
    participant p20 as text.replace(…).replace
    participant p21 as normalize_markdown(…).splitlines (src/llm_wiki_cli/services…_sections.py:section_body)
    participant p22 as normalize_markdown(…).splitlines (src/llm_wiki_cli/services…s.py:replace_section_body)
    participant p23 as normalize_markdown(…).splitlines (src/llm_wiki_cli/services…y:table_description_cells)
    participant p24 as normalize_markdown(…).splitlines (src/llm_wiki_cli/services…e_table_description_cells)
    participant p25 as text.replace
    p0->>p1: merge_semantic_markdown
    p1->>p2: section_body
    p1->>p3: should_preserve_semantic_value
    p1->>p4: replace_section_body
    p1->>p5: table_description_cells
    p1->>p6: preserve_table_description_cells
    p1->>p7: normalize_markdown
    p1->>p8: SemanticMergeResult
    p3->>p9: is_placeholder_description
    p2->>p10: section_bounds
    p5->>p11: split_table_row
    p2->>p12: trim_blank_lines
    p5->>p13: is_table_separator
    p5->>p14: semantic_table_key
    p6->>p15: format_table_row
    p0-->>p16: isinstance(description, str)
    p0-->>p17: semantics.get('attributes', {...})
    p0-->>p17: semantics.get('methods', {...})
    p0-->>p17: semantics.get('description')
    p0-->>p16: isinstance(attributes, Mapping)
    p0-->>p18: dict(attributes)
    p0-->>p16: isinstance(methods, Mapping)
    p0-->>p18: dict(methods)
    p1-->>p19: (…).get (src/llm_wiki_cli/services…y:merge_semantic_markdown)(heading)
    p7-->>p20: text.replace(…).replace('\r', '\n')
    p2-->>p21: normalize_markdown(…).splitlines (src/llm_wiki_cli/services…_sections.py:section_body)
    p4-->>p22: normalize_markdown(…).splitlines (src/llm_wiki_cli/services…s.py:replace_section_body)
    p5-->>p23: normalize_markdown(…).splitlines (src/llm_wiki_cli/services…y:table_description_cells)
    p6-->>p24: normalize_markdown(…).splitlines (src/llm_wiki_cli/services…e_table_description_cells)
    p7-->>p25: text.replace('\r\n', '\n')
```

> Call sequence diagram shows 30 of 112 interactions; 82 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 24 (19 omitted); unresolved 10 of 57 (47 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:section_body` | 9 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 12 | - | unresolved | 10 |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 12 | - | external | 6 |
| `src/llm_wiki_cli/services/markdown_sections.py:section_body` | 9 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:trim_blank_lines` | 31 | - | external | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:trim_blank_lines` | 31 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/section_ownership.py:merge_semantic_markdown` | 5 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:is_placeholder_description` | 37 | - | unresolved | 2 |
> Omission summary shows 8 of 24 groups; 16 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. merge_entity_semantics"]
    s2["2. semantics.get"]
    s3["3. semantics.get"]
    s4["4. semantics.get"]
    s5["5. merge_semantic_markdown"]
    s6["6. normalize_markdown"]
    s7["7. text.replace(…).replace"]
    s8["8. text.replace"]
    s9["9. section_body"]
    s10["10. normalize_markdown(…).splitlines (src/llm_wiki_cli/services…_sections.py:section_body)"]
    s11["11. normalize_markdown"]
    s12["12. section_bounds"]
    s1 -. "semantics.get('attributes', {...})" .-> s2
    s1 -. "semantics.get('methods', {...})" .-> s3
    s1 -. "semantics.get('description')" .-> s4
    s1 -->|"merge_semantic_markdown(existing, generated, (...), old_description=..., old_table_descriptions={...})"| s5
    s5 -->|"normalize_markdown(generated)"| s6
    s6 -. "text.replace(…).replace('\r', '\n')" .-> s7
    s6 -. "text.replace('\r\n', '\n')" .-> s8
    s5 -->|"section_body(existing, 'Description')"| s9
    s9 -. "normalize_markdown(…).splitlines (src/llm_wiki_cli/services…_sections.py:section_body)(data not statically known)" .-> s10
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
| `semantics.get` | - | - | - | - |
| `semantics.get` | - | - | - | - |
| `semantics.get` | - | - | - | - |
| `merge_semantic_markdown` | `existing: str`, `generated: str`, `table_headings: tuple[str, ...]`, `old_description: str \| None`, `old_table_descriptions: dict[str, dict[str, str]] \| None` | - | - | `SemanticMergeResult(...)` |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `section_body` | `markdown: str`, `heading: str` | - | - | `None`, `...` |
| `normalize_markdown(…).splitlines (src/llm_wiki_cli/services…_sections.py:section_body)` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `section_bounds` | `lines: list[str]`, `heading: str` | - | - | `(...)`, `None` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| merge_entity_semantics | semantics.get | 1191 | `semantics.get('attributes', {...})` |
| merge_entity_semantics | semantics.get | 1192 | `semantics.get('methods', {...})` |
| merge_entity_semantics | semantics.get | 1193 | `semantics.get('description')` |
| merge_entity_semantics | merge_semantic_markdown | 1194 | `merge_semantic_markdown(existing, generated, (...), old_description=..., old_table_descriptions={...})` |
| merge_semantic_markdown | normalize_markdown | 1155 | `normalize_markdown(generated)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 81 | `text.replace('\r\n', '\n')` |
| merge_semantic_markdown | section_body | 1157 | `section_body(existing, 'Description')` |
| section_body | normalize_markdown(…).splitlines (src/llm_wiki_cli/services…_sections.py:section_body) | 695 | `normalize_markdown(markdown).splitlines(data not statically known)` |
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
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| unresolved_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `section_body` | `normalize_markdown(markdown).splitlines` | 695 |
| step_limit | `merge_entity_semantics` | `first 12 steps` | 0 |

## Behavior

This flow starts at `merge_entity_semantics` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
