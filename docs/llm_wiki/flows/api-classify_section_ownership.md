# classify_section_ownership

**Entry point:** `classify_section_ownership` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [section_ownership](../modules/section_ownership.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as classify_section_ownership
    participant p1 as _coerce_page_kind
    participant p2 as isinstance
    participant p3 as PageKind
    participant p4 as ValueError
    participant p5 as _top_level_policy
    participant p6 as casefold
    participant p7 as fullmatch
    participant p8 as match
    p0->>p1: _coerce_page_kind
    p1-->>p2: isinstance
    p1->>p3: PageKind
    p1-->>p4: ValueError
    p0->>p5: _top_level_policy
    p5-->>p6: casefold
    p5-->>p7: fullmatch
    p5-->>p8: match
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. classify_section_ownership"]
    s2["2. _coerce_page_kind"]
    s3["3. isinstance"]
    s4["4. PageKind"]
    s5["5. ValueError"]
    s6["6. _top_level_policy"]
    s7["7. casefold"]
    s8["8. fullmatch"]
    s9["9. match"]
    s1 -->|"_coerce_page_kind(page_kind)"| s2
    s2 -. "isinstance(page_kind, PageKind)" .-> s3
    s2 -->|"PageKind(page_kind)"| s4
    s2 -. "ValueError(...)" .-> s5
    s1 -->|"_top_level_policy(kind, section.title, occurrence, index_preserved=index_preserved)"| s6
    s6 -. "title.casefold(data not statically known)" .-> s7
    s6 -. "_LOG_DATE_HEADING_RE.fullmatch(title)" .-> s8
    s6 -. "_HTTP_OPERATION_HEADING_RE.match(title)" .-> s9
    click s1 "../modules/section_ownership.md"
    click s2 "../modules/section_ownership.md"
    click s4 "../modules/wiki_surface.md"
    click s6 "../modules/section_ownership.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `classify_section_ownership` | `page_kind: PageKind \| str`, `section: MarkdownSection`, `parent_ownership: SectionOwnership \| None`, `canonical_occurrence: int \| None`, `index_preserved: bool` | `PageKind`, `SectionOwnership`, `PageKind`, `SectionOwnership`, `SectionOwnership` | - | `SectionOwnership.SEMANTIC`, `SectionOwnership.GENERATED`, `parent_ownership`, `SectionOwnership.UNKNOWN`, `_top_level_policy(...)` |
| `_coerce_page_kind` | `page_kind: PageKind \| str` | `PageKind` | - | `page_kind`, `PageKind(...)` |
| `isinstance` | - | - | - | - |
| `PageKind` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `_top_level_policy` | `page_kind: PageKind`, `title: str`, `canonical_occurrence: int`, `index_preserved: bool` | `PageKind`, `SectionOwnership`, `PageKind`, `SectionOwnership`, `SectionOwnership`, `PageKind`, `_INDEX_GENERATED_HEADINGS`, `SectionOwnership` | - | `SectionOwnership.SEMANTIC`, `SectionOwnership.GENERATED`, `SectionOwnership.UNKNOWN`, `...`, `...`, `...`, `...`, `...` |
| `casefold` | - | - | - | - |
| `fullmatch` | - | - | - | - |
| `match` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| classify_section_ownership | _coerce_page_kind | 432 | `_coerce_page_kind(page_kind)` |
| _coerce_page_kind | isinstance | 266 | `isinstance(page_kind, PageKind)` |
| _coerce_page_kind | PageKind | 269 | `PageKind(page_kind)` |
| _coerce_page_kind | ValueError | 271 | `ValueError(...)` |
| classify_section_ownership | _top_level_policy | 442 | `_top_level_policy(kind, section.title, occurrence, index_preserved=index_preserved)` |
| _top_level_policy | casefold | 281 | `title.casefold(data not statically known)` |
| _top_level_policy | fullmatch | 286 | `_LOG_DATE_HEADING_RE.fullmatch(title)` |
| _top_level_policy | match | 384 | `_HTTP_OPERATION_HEADING_RE.match(title)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_coerce_page_kind` | `isinstance` | 266 |
| unresolved_call | `_coerce_page_kind` | `ValueError` | 271 |
| unresolved_call | `_top_level_policy` | `title.casefold` | 281 |
| unresolved_call | `_top_level_policy` | `_LOG_DATE_HEADING_RE.fullmatch` | 286 |
| unresolved_call | `_top_level_policy` | `_HTTP_OPERATION_HEADING_RE.match` | 384 |

## Behavior

This flow starts at `classify_section_ownership` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
