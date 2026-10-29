# parse_markdown_sections

**Entry point:** `parse_markdown_sections` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as parse_markdown_sections
    participant p1 as parse_markdown_document
    participant p2 as _iter_structural_headings
    participant p3 as hash_json
    participant p4 as _markdown_lines
    participant p5 as _frontmatter_extent
    participant p6 as canonical_json_bytes
    participant p7 as normalize_markdown
    participant p8 as _HeadingCandidate
    participant p9 as section_locator
    participant p10 as MarkdownSection
    participant p11 as sha256_bytes
    participant p12 as MarkdownSectionDocument
    participant p13 as _line_content
    participant p14 as _atx_heading
    participant p15 as canonical_json_text
    participant p16 as isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p17 as stack.pop
    participant p18 as TypeError
    participant p19 as ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p20 as list
    participant p21 as defaultdict
    participant p22 as candidates.append
    participant p23 as stack.append
    participant p24 as len (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p25 as utf8_prefix_lengths.append
    participant p26 as character.encode
    participant p27 as enumerate (src/llm_wiki_cli/services…py:parse_markdown_document)
    p0->>p1: parse_markdown_document
    p1->>p2: _iter_structural_headings
    p1->>p3: hash_json
    p2->>p4: _markdown_lines
    p2->>p5: _frontmatter_extent
    p3->>p6: canonical_json_bytes
    p1->>p7: normalize_markdown
    p1->>p8: _HeadingCandidate
    p1->>p9: section_locator
    p1->>p10: MarkdownSection
    p1->>p11: sha256_bytes
    p1->>p12: MarkdownSectionDocument
    p2->>p13: _line_content
    p2->>p14: _atx_heading
    p6->>p15: canonical_json_text
    p1-->>p16: isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(markdown, str)
    p1-->>p17: stack.pop
    p1-->>p18: TypeError('markdown must be a string')
    p1-->>p16: isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(page_locator, str)
    p1-->>p19: ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)('page_locator must be a non-empty string')
    p1-->>p20: list(_iter_structural_headings(...))
    p1-->>p21: defaultdict(int)
    p1-->>p22: candidates.append(_HeadingCandidate(...))
    p1-->>p23: stack.append(...)
    p1-->>p24: len (src/llm_wiki_cli/services…py:parse_markdown_document)(candidates)
    p1-->>p25: utf8_prefix_lengths.append(...)
    p1-->>p24: len (src/llm_wiki_cli/services…py:parse_markdown_document)(character.encode(...))
    p1-->>p26: character.encode('utf-8')
    p1-->>p27: enumerate (src/llm_wiki_cli/services…py:parse_markdown_document)(candidates)
    p1-->>p24: len (src/llm_wiki_cli/services…py:parse_markdown_document)(normalized)
```

> Call sequence diagram shows 30 of 89 interactions; 59 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 10 of 44 (34 omitted); unresolved 5 of 23 (18 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:normalize_markdown` | 7 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_markdown_lines` | 12 | - | external | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:_markdown_lines` | 12 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_line_content` | 15 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 17 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 17 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 17 | - | external | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_iter_structural_headings` | 11 | - | external | 5 |
> Omission summary shows 8 of 22 groups; 14 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. parse_markdown_sections"]
    s2["2. parse_markdown_document"]
    s3["3. isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)"]
    s4["4. TypeError"]
    s5["5. isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)"]
    s6["6. ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)"]
    s7["7. normalize_markdown"]
    s8["8. text.replace(…).replace"]
    s9["9. text.replace"]
    s10["10. list"]
    s11["11. _iter_structural_headings"]
    s12["12. _markdown_lines"]
    s1 -->|"parse_markdown_document(markdown, page_locator)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(markdown, str)" .-> s3
    s2 -. "TypeError('markdown must be a string')" .-> s4
    s2 -. "isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(page_locator, str)" .-> s5
    s2 -. "ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)('page_locator must be a non-empty string')" .-> s6
    s2 -->|"normalize_markdown(markdown)"| s7
    s7 -. "text.replace(…).replace('\r', '\n')" .-> s8
    s7 -. "text.replace('\r\n', '\n')" .-> s9
    s2 -. "list(_iter_structural_headings(...))" .-> s10
    s2 -->|"_iter_structural_headings(normalized)"| s11
    s11 -->|"_markdown_lines(markdown, keepends=True)"| s12
    b0["mutation stack.pop"]
    s2 -. "mutation stack.pop" .-> b0
    b1["mutation candidates.append"]
    s2 -. "mutation candidates.append" .-> b1
    b2["mutation stack.append"]
    s2 -. "mutation stack.append" .-> b2
    b3["mutation utf8_prefix_lengths.append"]
    s2 -. "mutation utf8_prefix_lengths.append" .-> b3
    b4["mutation sections.append"]
    s2 -. "mutation sections.append" .-> b4
    click s1 "../modules/markdown_sections.md"
    click s2 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
    click s11 "../modules/markdown_sections.md"
    click s12 "../modules/markdown_sections.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `parse_markdown_sections` | `markdown: str`, `page_locator: str` | - | - | `...` |
| `parse_markdown_document` | `markdown: str`, `page_locator: str` | `SECTION_ORDER_DOMAIN` | `occurrences[...]` | `MarkdownSectionDocument(...)` |
| `isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `list` | - | - | - | - |
| `_iter_structural_headings` | `markdown: str` | - | - | - |
| `_markdown_lines` | `markdown: str`, `keepends: bool` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| parse_markdown_sections | parse_markdown_document | 465 | `parse_markdown_document(markdown, page_locator)` |
| parse_markdown_document | isinstance (src/llm_wiki_cli/services…py:parse_markdown_document) | 333 | `isinstance(markdown, str)` |
| parse_markdown_document | TypeError | 334 | `TypeError('markdown must be a string')` |
| parse_markdown_document | isinstance (src/llm_wiki_cli/services…py:parse_markdown_document) | 335 | `isinstance(page_locator, str)` |
| parse_markdown_document | ValueError (src/llm_wiki_cli/services…py:parse_markdown_document) | 336 | `ValueError('page_locator must be a non-empty string')` |
| parse_markdown_document | normalize_markdown | 338 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 82 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 82 | `text.replace('\r\n', '\n')` |
| parse_markdown_document | list | 339 | `list(_iter_structural_headings(...))` |
| parse_markdown_document | _iter_structural_headings | 339 | `_iter_structural_headings(normalized)` |
| _iter_structural_headings | _markdown_lines | 259 | `_markdown_lines(markdown, keepends=True)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `stack.pop` | `parse_markdown_document` | 346 |
| mutation | `candidates.append` | `parse_markdown_document` | 358 |
| mutation | `stack.append` | `parse_markdown_document` | 370 |
| mutation | `utf8_prefix_lengths.append` | `parse_markdown_document` | 374 |
| mutation | `sections.append` | `parse_markdown_document` | 401 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `parse_markdown_document` | `isinstance` | 333 |
| external_call | `parse_markdown_document` | `TypeError` | 334 |
| external_call | `parse_markdown_document` | `isinstance` | 335 |
| external_call | `parse_markdown_document` | `ValueError` | 336 |
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 82 |
| unresolved_call | `normalize_markdown` | `text.replace` | 82 |
| step_limit | `parse_markdown_sections` | `first 12 steps` | 0 |

## Behavior

This flow starts at `parse_markdown_sections` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
