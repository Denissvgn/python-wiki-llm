# classify_section_ownership

**Entry point:** `classify_section_ownership` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [section_ownership](../modules/section_ownership.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as classify_section_ownership
    participant p1 as _coerce_page_kind
    participant p2 as _top_level_policy
    participant p3 as isinstance
    participant p4 as title.casefold
    participant p5 as PageKind
    participant p6 as _LOG_DATE_HEADING_RE.fullmatch
    participant p7 as ValueError
    participant p8 as _HTTP_OPERATION_HEADING_RE.match
    p0->>p1: _coerce_page_kind
    p0->>p2: _top_level_policy
    p1-->>p3: isinstance(page_kind, PageKind)
    p2-->>p4: title.casefold
    p1->>p5: PageKind
    p2-->>p6: _LOG_DATE_HEADING_RE.fullmatch(title)
    p1-->>p7: ValueError(...)
    p2-->>p8: _HTTP_OPERATION_HEADING_RE.match(title)
```

> Call sequence diagram shows 8 of 8 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 2 of 2 (0 omitted); unresolved 3 of 3 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 4; effect analysis evaluated: 2, partial: 1, unavailable: 1. Counts include steps omitted from the displayed trace.

Collector observations for 3 source steps with known totals: observed: 123, emitted: 39, omitted: 84. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `classify_section_ownership` | `available` | `evaluated` | `available` | `15` | `15` | `0` |
| `_coerce_page_kind` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `PageKind` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `ValueError` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_top_level_policy` | `available` | `partial` | `available` | `104` | `20` | `84` |
| `title.casefold` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_LOG_DATE_HEADING_RE.fullmatch` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_HTTP_OPERATION_HEADING_RE.match` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. classify_section_ownership"]
    s2["2. _coerce_page_kind"]
    s3["3. isinstance"]
    s4["4. PageKind"]
    s5["5. ValueError"]
    s6["6. _top_level_policy"]
    s7["7. title.casefold"]
    s8["8. _LOG_DATE_HEADING_RE.fullmatch"]
    s9["9. _HTTP_OPERATION_HEADING_RE.match"]
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
| `title.casefold` | - | - | - | - |
| `_LOG_DATE_HEADING_RE.fullmatch` | - | - | - | - |
| `_HTTP_OPERATION_HEADING_RE.match` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| classify_section_ownership | _coerce_page_kind | 435 | `_coerce_page_kind(page_kind)` |
| _coerce_page_kind | isinstance | 269 | `isinstance(page_kind, PageKind)` |
| _coerce_page_kind | PageKind | 272 | `PageKind(page_kind)` |
| _coerce_page_kind | ValueError | 274 | `ValueError(...)` |
| classify_section_ownership | _top_level_policy | 445 | `_top_level_policy(kind, section.title, occurrence, index_preserved=index_preserved)` |
| _top_level_policy | title.casefold | 284 | `title.casefold(data not statically known)` |
| _top_level_policy | _LOG_DATE_HEADING_RE.fullmatch | 289 | `_LOG_DATE_HEADING_RE.fullmatch(title)` |
| _top_level_policy | _HTTP_OPERATION_HEADING_RE.match | 387 | `_HTTP_OPERATION_HEADING_RE.match(title)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_coerce_page_kind` | `isinstance` | 269 |
| external_call | `_coerce_page_kind` | `ValueError` | 274 |
| unresolved_call | `_top_level_policy` | `title.casefold` | 284 |
| unresolved_call | `_top_level_policy` | `_LOG_DATE_HEADING_RE.fullmatch` | 289 |
| unresolved_call | `_top_level_policy` | `_HTTP_OPERATION_HEADING_RE.match` | 387 |

## Behavior

This flow starts at `classify_section_ownership` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
