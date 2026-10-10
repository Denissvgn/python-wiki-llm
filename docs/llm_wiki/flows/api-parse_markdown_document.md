# parse_markdown_document

**Entry point:** `parse_markdown_document` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as parse_markdown_document
    participant p1 as isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p2 as TypeError
    participant p3 as ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p4 as normalize_markdown
    participant p5 as list
    participant p6 as _iter_structural_headings
    participant p7 as defaultdict
    participant p8 as stack.pop
    participant p9 as candidates.append
    participant p10 as _HeadingCandidate
    participant p11 as stack.append
    participant p12 as len (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p13 as utf8_prefix_lengths.append
    participant p14 as character.encode
    participant p15 as enumerate (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p16 as section_locator
    participant p17 as exact_text.encode
    participant p18 as sections.append
    participant p19 as MarkdownSection
    participant p20 as sha256_bytes
    participant p21 as children[…].append
    participant p22 as replace
    participant p23 as tuple (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p24 as normalized.encode
    p0-->>p1: isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(markdown, str)
    p0-->>p2: TypeError('markdown must be a string')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(page_locator, str)
    p0-->>p3: ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)('page_locator must be a non-empty string')
    p0->>p4: normalize_markdown
    p0-->>p5: list(_iter_structural_headings(...))
    p0->>p6: _iter_structural_headings
    p0-->>p7: defaultdict(int)
    p0-->>p8: stack.pop
    p0-->>p9: candidates.append(_HeadingCandidate(...))
    p0->>p10: _HeadingCandidate
    p0-->>p11: stack.append(...)
    p0-->>p12: len (src/llm_wiki_cli/services…py:parse_markdown_document)(candidates)
    p0-->>p13: utf8_prefix_lengths.append(...)
    p0-->>p12: len (src/llm_wiki_cli/services…py:parse_markdown_document)(character.encode(...))
    p0-->>p14: character.encode('utf-8')
    p0-->>p15: enumerate (src/llm_wiki_cli/services…py:parse_markdown_document)(candidates)
    p0-->>p12: len (src/llm_wiki_cli/services…py:parse_markdown_document)(normalized)
    p0->>p16: section_locator
    p0->>p16: section_locator
    p0-->>p17: exact_text.encode('utf-8')
    p0-->>p18: sections.append(MarkdownSection(...))
    p0->>p19: MarkdownSection
    p0->>p20: sha256_bytes
    p0-->>p7: defaultdict(list)
    p0-->>p21: children[…].append(section.locator)
    p0-->>p22: replace(section, child_locators=tuple(...))
    p0-->>p23: tuple (src/llm_wiki_cli/services…py:parse_markdown_document)(children[...])
    p0-->>p5: list(section.child_locators)
    p0-->>p24: normalized.encode('utf-8')
```

> Call sequence diagram shows 30 of 85 interactions; 55 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 14 of 43 (29 omitted); unresolved 9 of 24 (15 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:normalize_markdown` | 6 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_iter_structural_headings` | 10 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:_iter_structural_headings` | 10 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 12 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 12 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_line_content` | 15 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:_frontmatter_extent` | 12 | - | external | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_iter_structural_headings` | 10 | - | external | 5 |
> Omission summary shows 8 of 21 groups; 13 further groups are not expanded here. Counts above include all omitted interactions.
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
