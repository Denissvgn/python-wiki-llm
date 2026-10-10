# observe_page_sections

**Entry point:** `observe_page_sections` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as observe_page_sections
    participant p1 as _coerce_page_kind
    participant p2 as parse_markdown_document
    participant p3 as len (src/llm_wiki_cli/services….py:observe_page_sections)
    participant p4 as _preamble_observation
    participant p5 as defaultdict (src/llm_wiki_cli/services….py:observe_page_sections)
    participant p6 as section.title.casefold
    participant p7 as ownership_by_locator.get
    participant p8 as classify_section_ownership
    participant p9 as _scoped_hashes
    participant p10 as observations.append
    participant p11 as SectionObservation
    participant p12 as tuple (src/llm_wiki_cli/services….py:observe_page_sections)
    participant p13 as PageSectionObservations
    participant p14 as sha256_bytes
    participant p15 as markdown.encode
    participant p16 as isinstance (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)
    participant p17 as isinstance (src/llm_wiki_cli/services…y:parse_markdown_document)
    participant p18 as mixed_table_projection
    participant p19 as PageKind
    participant p20 as TypeError
    participant p21 as preamble.encode
    participant p22 as _top_level_policy
    participant p23 as ValueError (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)
    participant p24 as ValueError (src/llm_wiki_cli/services…y:parse_markdown_document)
    participant p25 as normalize_markdown
    participant p26 as list (src/llm_wiki_cli/services…y:parse_markdown_document)
    p0->>p1: _coerce_page_kind
    p0->>p2: parse_markdown_document
    p0-->>p3: len (src/llm_wiki_cli/services….py:observe_page_sections)(document.normalized_markdown)
    p0->>p4: _preamble_observation
    p0-->>p5: defaultdict (src/llm_wiki_cli/services….py:observe_page_sections)(int)
    p0-->>p6: section.title.casefold
    p0-->>p7: ownership_by_locator.get(section.parent_locator)
    p0->>p8: classify_section_ownership
    p0->>p9: _scoped_hashes
    p0-->>p10: observations.append(SectionObservation(...))
    p0->>p11: SectionObservation
    p0-->>p12: tuple (src/llm_wiki_cli/services….py:observe_page_sections)(observations)
    p0->>p13: PageSectionObservations
    p0->>p14: sha256_bytes
    p0-->>p15: markdown.encode('utf-8')
    p1-->>p16: isinstance (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)(page_kind, PageKind)
    p2-->>p17: isinstance (src/llm_wiki_cli/services…y:parse_markdown_document)(markdown, str)
    p4->>p14: sha256_bytes
    p8->>p1: _coerce_page_kind
    p9->>p18: mixed_table_projection
    p1->>p19: PageKind
    p2-->>p20: TypeError('markdown must be a string')
    p4-->>p21: preamble.encode('utf-8')
    p8->>p22: _top_level_policy
    p1-->>p23: ValueError (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)(...)
    p2-->>p17: isinstance (src/llm_wiki_cli/services…y:parse_markdown_document)(page_locator, str)
    p4->>p11: SectionObservation
    p2-->>p24: ValueError (src/llm_wiki_cli/services…y:parse_markdown_document)('page_locator must be a non-empty string')
    p2->>p25: normalize_markdown
    p2-->>p26: list (src/llm_wiki_cli/services…y:parse_markdown_document)(_iter_structural_headings(...))
```

> Call sequence diagram shows 30 of 174 interactions; 144 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 10 of 67 (57 omitted); unresolved 5 of 61 (56 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:normalize_markdown` | 11 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:parse_markdown_document` | 6 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 6 |
| `src/llm_wiki_cli/services/markdown_sections.py:_iter_structural_headings` | 15 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:_iter_structural_headings` | 15 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 17 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 17 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_line_content` | 20 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 17 | - | external | 2 |
> Omission summary shows 8 of 38 groups; 30 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. observe_page_sections"]
    s2["2. _coerce_page_kind"]
    s3["3. isinstance (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)"]
    s4["4. PageKind"]
    s5["5. ValueError (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)"]
    s6["6. parse_markdown_document"]
    s7["7. isinstance (src/llm_wiki_cli/services…y:parse_markdown_document)"]
    s8["8. TypeError"]
    s9["9. isinstance (src/llm_wiki_cli/services…y:parse_markdown_document)"]
    s10["10. ValueError (src/llm_wiki_cli/services…y:parse_markdown_document)"]
    s11["11. normalize_markdown"]
    s12["12. text.replace(…).replace"]
    s1 -->|"_coerce_page_kind(page_kind)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)(page_kind, PageKind)" .-> s3
    s2 -->|"PageKind(page_kind)"| s4
    s2 -. "ValueError (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)(...)" .-> s5
    s1 -->|"parse_markdown_document(markdown, page_locator)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…y:parse_markdown_document)(markdown, str)" .-> s7
    s6 -. "TypeError('markdown must be a string')" .-> s8
    s6 -. "isinstance (src/llm_wiki_cli/services…y:parse_markdown_document)(page_locator, str)" .-> s9
    s6 -. "ValueError (src/llm_wiki_cli/services…y:parse_markdown_document)('page_locator must be a non-empty string')" .-> s10
    s6 -->|"normalize_markdown(markdown)"| s11
    s11 -. "text.replace(…).replace('\r', '\n')" .-> s12
    b0["mutation observations.append"]
    s1 -. "mutation observations.append" .-> b0
    b1["mutation stack.pop"]
    s6 -. "mutation stack.pop" .-> b1
    b2["mutation candidates.append"]
    s6 -. "mutation candidates.append" .-> b2
    b3["mutation stack.append"]
    s6 -. "mutation stack.append" .-> b3
    b4["mutation utf8_prefix_lengths.append"]
    s6 -. "mutation utf8_prefix_lengths.append" .-> b4
    b5["mutation sections.append"]
    s6 -. "mutation sections.append" .-> b5
    click s1 "../modules/section_ownership.md"
    click s2 "../modules/section_ownership.md"
    click s4 "../modules/wiki_surface.md"
    click s6 "../modules/markdown_sections.md"
    click s11 "../modules/markdown_sections.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `observe_page_sections` | `markdown: str`, `page_locator: str`, `page_kind: PageKind \| str`, `index_preserved: bool` | - | `canonical_occurrences[...]`, `ownership_by_locator[...]` | `PageSectionObservations(...)` |
| `_coerce_page_kind` | `page_kind: PageKind \| str` | `PageKind` | - | `page_kind`, `PageKind(...)` |
| `isinstance (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)` | - | - | - | - |
| `PageKind` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…ship.py:_coerce_page_kind)` | - | - | - | - |
| `parse_markdown_document` | `markdown: str`, `page_locator: str` | `SECTION_ORDER_DOMAIN` | `occurrences[...]` | `MarkdownSectionDocument(...)` |
| `isinstance (src/llm_wiki_cli/services…y:parse_markdown_document)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…y:parse_markdown_document)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…y:parse_markdown_document)` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| observe_page_sections | _coerce_page_kind | 543 | `_coerce_page_kind(page_kind)` |
| _coerce_page_kind | isinstance (src/llm_wiki_cli/services…ship.py:_coerce_page_kind) | 266 | `isinstance(page_kind, PageKind)` |
| _coerce_page_kind | PageKind | 269 | `PageKind(page_kind)` |
| _coerce_page_kind | ValueError (src/llm_wiki_cli/services…ship.py:_coerce_page_kind) | 271 | `ValueError(...)` |
| observe_page_sections | parse_markdown_document | 544 | `parse_markdown_document(markdown, page_locator)` |
| parse_markdown_document | isinstance (src/llm_wiki_cli/services…y:parse_markdown_document) | 325 | `isinstance(markdown, str)` |
| parse_markdown_document | TypeError | 326 | `TypeError('markdown must be a string')` |
| parse_markdown_document | isinstance (src/llm_wiki_cli/services…y:parse_markdown_document) | 327 | `isinstance(page_locator, str)` |
| parse_markdown_document | ValueError (src/llm_wiki_cli/services…y:parse_markdown_document) | 328 | `ValueError('page_locator must be a non-empty string')` |
| parse_markdown_document | normalize_markdown | 330 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `observations.append` | `observe_page_sections` | 575 |
| mutation | `stack.pop` | `parse_markdown_document` | 338 |
| mutation | `candidates.append` | `parse_markdown_document` | 350 |
| mutation | `stack.append` | `parse_markdown_document` | 362 |
| mutation | `utf8_prefix_lengths.append` | `parse_markdown_document` | 366 |
| mutation | `sections.append` | `parse_markdown_document` | 393 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_coerce_page_kind` | `isinstance` | 266 |
| external_call | `_coerce_page_kind` | `ValueError` | 271 |
| external_call | `parse_markdown_document` | `isinstance` | 325 |
| external_call | `parse_markdown_document` | `TypeError` | 326 |
| external_call | `parse_markdown_document` | `isinstance` | 327 |
| external_call | `parse_markdown_document` | `ValueError` | 328 |
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| step_limit | `observe_page_sections` | `first 12 steps` | 0 |

## Behavior

This flow starts at `observe_page_sections` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
