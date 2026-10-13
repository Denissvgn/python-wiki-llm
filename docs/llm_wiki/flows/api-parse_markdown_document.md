# parse_markdown_document

**Entry point:** `parse_markdown_document` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as parse_markdown_document
    participant p1 as _iter_structural_headings
    participant p2 as hash_json
    participant p3 as normalize_markdown
    participant p4 as _HeadingCandidate
    participant p5 as section_locator
    participant p6 as MarkdownSection
    participant p7 as sha256_bytes
    participant p8 as MarkdownSectionDocument
    participant p9 as _frontmatter_extent
    participant p10 as canonical_json_bytes
    participant p11 as _line_content
    participant p12 as _atx_heading
    participant p13 as canonical_json_text
    participant p14 as isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p15 as stack.pop
    participant p16 as TypeError
    participant p17 as ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p18 as list
    participant p19 as defaultdict
    participant p20 as candidates.append
    participant p21 as stack.append
    participant p22 as len (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p23 as utf8_prefix_lengths.append
    participant p24 as character.encode
    participant p25 as enumerate (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p26 as exact_text.encode
    participant p27 as sections.append
    p0->>p1: _iter_structural_headings
    p0->>p2: hash_json
    p0->>p3: normalize_markdown
    p0->>p4: _HeadingCandidate
    p0->>p5: section_locator
    p0->>p6: MarkdownSection
    p0->>p7: sha256_bytes
    p0->>p8: MarkdownSectionDocument
    p1->>p9: _frontmatter_extent
    p2->>p10: canonical_json_bytes
    p1->>p11: _line_content
    p1->>p12: _atx_heading
    p10->>p13: canonical_json_text
    p0-->>p14: isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(markdown, str)
    p0-->>p15: stack.pop
    p0-->>p16: TypeError('markdown must be a string')
    p0-->>p14: isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(page_locator, str)
    p0-->>p17: ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)('page_locator must be a non-empty string')
    p0-->>p18: list(_iter_structural_headings(...))
    p0-->>p19: defaultdict(int)
    p0-->>p20: candidates.append(_HeadingCandidate(...))
    p0-->>p21: stack.append(...)
    p0-->>p22: len (src/llm_wiki_cli/services…py:parse_markdown_document)(candidates)
    p0-->>p23: utf8_prefix_lengths.append(...)
    p0-->>p22: len (src/llm_wiki_cli/services…py:parse_markdown_document)(character.encode(...))
    p0-->>p24: character.encode('utf-8')
    p0-->>p25: enumerate (src/llm_wiki_cli/services…py:parse_markdown_document)(candidates)
    p0-->>p22: len (src/llm_wiki_cli/services…py:parse_markdown_document)(normalized)
    p0-->>p26: exact_text.encode('utf-8')
    p0-->>p27: sections.append(MarkdownSection(...))
```

> Call sequence diagram shows 30 of 85 interactions; 55 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 10 of 43 (33 omitted); unresolved 7 of 24 (17 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:normalize_markdown` | 6 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_iter_structural_headings` | 10 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 12 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 12 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_line_content` | 15 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 12 | - | external | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_iter_structural_headings` | 10 | - | external | 5 |
| `src/llm_wiki_cli/services/markdown_sections.py:_atx_heading` | 29 | - | unresolved | 3 |
> Omission summary shows 8 of 20 groups; 12 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. parse_markdown_document"]
    s2["2. isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)"]
    s3["3. TypeError"]
    s4["4. isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)"]
    s5["5. ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)"]
    s6["6. normalize_markdown"]
    s7["7. text.replace(…).replace"]
    s8["8. text.replace"]
    s9["9. list"]
    s10["10. _iter_structural_headings"]
    s11["11. markdown.splitlines"]
    s12["12. _frontmatter_extent"]
    s1 -. "isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(markdown, str)" .-> s2
    s1 -. "TypeError('markdown must be a string')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(page_locator, str)" .-> s4
    s1 -. "ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)('page_locator must be a non-empty string')" .-> s5
    s1 -->|"normalize_markdown(markdown)"| s6
    s6 -. "text.replace(…).replace('\r', '\n')" .-> s7
    s6 -. "text.replace('\r\n', '\n')" .-> s8
    s1 -. "list(_iter_structural_headings(...))" .-> s9
    s1 -->|"_iter_structural_headings(normalized)"| s10
    s10 -. "markdown.splitlines(keepends=True)" .-> s11
    s10 -->|"_frontmatter_extent(lines)"| s12
    b0["mutation stack.pop"]
    s1 -. "mutation stack.pop" .-> b0
    b1["mutation candidates.append"]
    s1 -. "mutation candidates.append" .-> b1
    b2["mutation stack.append"]
    s1 -. "mutation stack.append" .-> b2
    b3["mutation utf8_prefix_lengths.append"]
    s1 -. "mutation utf8_prefix_lengths.append" .-> b3
    b4["mutation sections.append"]
    s1 -. "mutation sections.append" .-> b4
    click s1 "../modules/markdown_sections.md"
    click s6 "../modules/markdown_sections.md"
    click s10 "../modules/markdown_sections.md"
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
| `markdown.splitlines` | - | - | - | - |
| `_frontmatter_extent` | `lines: list[str]` | - | - | `0`, `0`, `...`, `len(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| parse_markdown_document | isinstance (src/llm_wiki_cli/services…py:parse_markdown_document) | 325 | `isinstance(markdown, str)` |
| parse_markdown_document | TypeError | 326 | `TypeError('markdown must be a string')` |
| parse_markdown_document | isinstance (src/llm_wiki_cli/services…py:parse_markdown_document) | 327 | `isinstance(page_locator, str)` |
| parse_markdown_document | ValueError (src/llm_wiki_cli/services…py:parse_markdown_document) | 328 | `ValueError('page_locator must be a non-empty string')` |
| parse_markdown_document | normalize_markdown | 330 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 81 | `text.replace('\r\n', '\n')` |
| parse_markdown_document | list | 331 | `list(_iter_structural_headings(...))` |
| parse_markdown_document | _iter_structural_headings | 331 | `_iter_structural_headings(normalized)` |
| _iter_structural_headings | markdown.splitlines | 251 | `markdown.splitlines(keepends=True)` |
| _iter_structural_headings | _frontmatter_extent | 252 | `_frontmatter_extent(lines)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `stack.pop` | `parse_markdown_document` | 338 |
| mutation | `candidates.append` | `parse_markdown_document` | 350 |
| mutation | `stack.append` | `parse_markdown_document` | 362 |
| mutation | `utf8_prefix_lengths.append` | `parse_markdown_document` | 366 |
| mutation | `sections.append` | `parse_markdown_document` | 393 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `parse_markdown_document` | `isinstance` | 325 |
| external_call | `parse_markdown_document` | `TypeError` | 326 |
| external_call | `parse_markdown_document` | `isinstance` | 327 |
| external_call | `parse_markdown_document` | `ValueError` | 328 |
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| unresolved_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `_iter_structural_headings` | `markdown.splitlines` | 251 |
| step_limit | `parse_markdown_document` | `first 12 steps` | 0 |

## Behavior

This flow starts at `parse_markdown_document` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
