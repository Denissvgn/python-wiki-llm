# mixed_table_projection

**Entry point:** `mixed_table_projection` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as mixed_table_projection
    participant p1 as normalize_markdown
    participant p2 as normalized.splitlines
    participant p3 as normalized.endswith
    participant p4 as description_table_cells
    participant p5 as list
    participant p6 as format_table_row
    participant p7 as is_placeholder_description
    participant p8 as semantic_by_key.items
    participant p9 as semantic_cells.sort
    participant p10 as str(…).casefold
    participant p11 as str
    participant p12 as MixedTableProjection
    participant p13 as hash_json
    participant p14 as text.replace(…).replace
    participant p15 as normalize_markdown(…).splitlines
    participant p16 as ' | '.join
    participant p17 as value.strip
    participant p18 as sha256_bytes
    participant p19 as text.replace
    participant p20 as _AUTO_GENERATED_RE.match
    participant p21 as canonical_json_bytes
    participant p22 as enumerate
    participant p23 as split_table_row
    participant p24 as headers.index
    participant p25 as len (src/llm_wiki_cli/services…py:description_table_cells)
    p0->>p1: normalize_markdown
    p0-->>p2: normalized.splitlines
    p0-->>p3: normalized.endswith('\n')
    p0->>p4: description_table_cells
    p0-->>p5: list(lines)
    p0-->>p5: list(cell.cells)
    p0->>p6: format_table_row
    p0->>p7: is_placeholder_description
    p0-->>p8: semantic_by_key.items
    p0-->>p9: semantic_cells.sort(key=...)
    p0-->>p10: str(…).casefold
    p0-->>p11: str(item[...])
    p0-->>p11: str(item[...])
    p0-->>p11: str(item[...])
    p0->>p12: MixedTableProjection
    p0->>p13: hash_json
    p0->>p13: hash_json
    p1-->>p14: text.replace(…).replace('\r', '\n')
    p4-->>p15: normalize_markdown(…).splitlines
    p6-->>p16: ' | '.join(cells)
    p7-->>p17: value.strip
    p13->>p18: sha256_bytes
    p1-->>p19: text.replace('\r\n', '\n')
    p4->>p1: normalize_markdown
    p7-->>p20: _AUTO_GENERATED_RE.match(stripped)
    p13->>p21: canonical_json_bytes
    p4-->>p22: enumerate(lines)
    p4->>p23: split_table_row
    p4-->>p24: headers.index('Description')
    p4-->>p25: len (src/llm_wiki_cli/services…py:description_table_cells)(lines)
```

> Call sequence diagram shows 30 of 71 interactions; 41 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 21 (14 omitted); unresolved 12 of 33 (21 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 11 | - | unresolved | 12 |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 11 | - | external | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:description_table_cells` | 7 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 5 |
| `src/llm_wiki_cli/services/markdown_sections.py:is_table_separator` | 29 | - | external | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:is_table_separator` | 29 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:description_table_cells` | 7 | - | external | 6 |
| `src/llm_wiki_cli/services/markdown_sections.py:semantic_table_key` | 39 | - | external | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:semantic_table_key` | 39 | - | unresolved | 4 |
> Omission summary shows 8 of 14 groups; 6 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. mixed_table_projection"]
    s2["2. normalize_markdown"]
    s3["3. text.replace(…).replace"]
    s4["4. text.replace"]
    s5["5. normalized.splitlines"]
    s6["6. normalized.endswith"]
    s7["7. description_table_cells"]
    s8["8. normalize_markdown(…).splitlines"]
    s9["9. normalize_markdown"]
    s10["10. enumerate"]
    s11["11. split_table_row"]
    s12["12. line.strip"]
    s1 -->|"normalize_markdown(section_markdown)"| s2
    s2 -. "text.replace(…).replace('\r', '\n')" .-> s3
    s2 -. "text.replace('\r\n', '\n')" .-> s4
    s1 -. "normalized.splitlines(data not statically known)" .-> s5
    s1 -. "normalized.endswith('\n')" .-> s6
    s1 -->|"description_table_cells(normalized)"| s7
    s7 -. "normalize_markdown(…).splitlines(data not statically known)" .-> s8
    s7 -->|"normalize_markdown(markdown)"| s9
    s7 -. "enumerate(lines)" .-> s10
    s7 -->|"split_table_row(line)"| s11
    s11 -. "line.strip(data not statically known)" .-> s12
    b0["mutation semantic_cells.sort"]
    s1 -. "mutation semantic_cells.sort" .-> b0
    b1["mutation cells.append"]
    s7 -. "mutation cells.append" .-> b1
    b2["mutation current.extend"]
    s11 -. "mutation current.extend" .-> b2
    b3["mutation current.append"]
    s11 -. "mutation current.append" .-> b3
    b4["mutation cells.append"]
    s11 -. "mutation cells.append" .-> b4
    b5["mutation current.append"]
    s11 -. "mutation current.append" .-> b5
    b6["mutation cells.append"]
    s11 -. "mutation cells.append" .-> b6
    click s1 "../modules/markdown_sections.md"
    click s2 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
    click s9 "../modules/markdown_sections.md"
    click s11 "../modules/markdown_sections.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `mixed_table_projection` | `section_markdown: str` | `MIXED_TABLE_DOMAIN`, `MIXED_TABLE_DOMAIN` | `row[...]`, `structural_lines[...]`, `semantic_by_key[...]` | `MixedTableProjection(...)` |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `normalized.splitlines` | - | - | - | - |
| `normalized.endswith` | - | - | - | - |
| `description_table_cells` | `markdown: str` | - | `occurrences[...]` | `tuple(...)`, `(...)` |
| `normalize_markdown(…).splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `enumerate` | - | - | - | - |
| `split_table_row` | `line: str` | - | - | `[...]`, `cells` |
| `line.strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| mixed_table_projection | normalize_markdown | 605 | `normalize_markdown(section_markdown)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 81 | `text.replace('\r\n', '\n')` |
| mixed_table_projection | normalized.splitlines | 606 | `normalized.splitlines(data not statically known)` |
| mixed_table_projection | normalized.endswith | 607 | `normalized.endswith('\n')` |
| mixed_table_projection | description_table_cells | 608 | `description_table_cells(normalized)` |
| description_table_cells | normalize_markdown(…).splitlines | 558 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| description_table_cells | normalize_markdown | 558 | `normalize_markdown(markdown)` |
| description_table_cells | enumerate | 559 | `enumerate(lines)` |
| description_table_cells | split_table_row | 560 | `split_table_row(line)` |
| split_table_row | line.strip | 467 | `line.strip(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `semantic_cells.sort` | `mixed_table_projection` | 629 |
| mutation | `cells.append` | `description_table_cells` | 581 |
| mutation | `current.extend` | `split_table_row` | 478 |
| mutation | `current.append` | `split_table_row` | 486 |
| mutation | `cells.append` | `split_table_row` | 494 |
| mutation | `current.append` | `split_table_row` | 497 |
| mutation | `cells.append` | `split_table_row` | 499 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| unresolved_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `mixed_table_projection` | `normalized.splitlines` | 606 |
| unresolved_call | `mixed_table_projection` | `normalized.endswith` | 607 |
| unresolved_call | `description_table_cells` | `normalize_markdown(markdown).splitlines` | 558 |
| external_call | `description_table_cells` | `enumerate` | 559 |
| unresolved_call | `split_table_row` | `line.strip` | 467 |
| step_limit | `mixed_table_projection` | `first 12 steps` | 0 |

## Behavior

This flow starts at `mixed_table_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
