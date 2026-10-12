# search_lexical Module

**Path:** `src/llm_wiki_cli/services/search_lexical.py`

## Description

Pure informative lexical discovery; matches never establish source truth.

Discovery tokens use approximate ASCII English word families across captured
text, titles, paths and queries. Literal normalized page identities and actual
defined-symbol checks remain separate and retain precedence. The configuration
identity changes when this matching policy changes; original Markdown spans,
content hashes and section locators continue to describe captured text.

Strong non-identity guide matches can surface one-hop implementation leads from
explicit local links in matched semantic sections. Only uniquely captured
module/entity destinations qualify; fenced examples, external paths, escaping
paths and inventory sections do not supply such evidence. These leads retain
the donor page hash and section locator. A link-only result reports linked
discovery and does not fabricate a target text-match location. Source-augmented
records preserve separate original-wiki and indexed-text hashes. No recursive
lookup, source indexing, execution or truth judgment follows from a link.

Bounded ASCII nominal families are added from captured explanatory sections and
formal definition-table Description cells. For example, normalization can help
discovery for normalizing, and verification for verified. Generated names and
signatures retain their original tokens; defined symbols, paths, URIs and page
identities keep literal precedence. The prose-family configuration identity
records this treatment separately from the unchanged legacy ranker.

These extra discovery tokens do not rewrite indexed Markdown or its content
hash. Returned section locations still cite the original normalized text, and
lexical leads retain their no-live-comparison qualification. The bounded family
rules do not establish semantic equivalence, source correctness or general
language comprehension.

Flow Call sequence and Data flow sections, including nested step/call tables,
receive inventory weight. The complete untouched default Behavior placeholder
also receives inventory weight; authored additions keep the semantic weight.
Other page kinds keep their existing section treatment. Trace text stays
searchable with its original citations and scan bounds. This is a lexical
weighting rule, without source-owner inference, kind quotas or native fact claims.
The configuration identity records this treatment independently of the
compatible lexical-v2 result shape and unchanged legacy modes.

Frequency normalization uses each captured section's length. Each term contributes
its strongest section value, and coherent explanatory coverage receives the
existing semantic weight. A large unrelated inventory no longer dilutes a short
explanation; distributing common words across more sections cannot multiply their
contribution. Whole-page title/path signals and literal identity tiers remain
separate from this section-local treatment.

A matching formal Functions Description row can supply a one-hop lead to a
uniquely captured flow whose preamble explicitly declares that literal entry
symbol and a local Source link to the module. At least two query terms and 45%
weighted coverage must match the row; bounded nominal families apply to that
description comparison in either direction. Duplicate definitions/declarations,
fenced examples, external or escaping links and guide tables do not qualify.
These leads retain the donor section, row text and captured hash, plus the target
hash. A link-only result has no invented target match location. The declaration
is a lexical association, without a runtime call or source-correctness claim.

## Imports

| Source | Symbols |
|--------|---------|
| `.markdown_sections` | `parse_markdown_document`, `semantic_table_key`, `split_table_row` |
| `.search_rank` | `MAX_SEARCH_BYTES`, `MAX_SEARCH_PAGES`, `_STOP_WORDS`, `_WORDS` |
| `.wiki_media` | `mask_fenced_code_blocks` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `collections.abc` | `Mapping` |
| `copy` | `deepcopy` |
| `hashlib` | `hashlib` |
| `math` | `math` |
| `posixpath` | `posixpath` |
| `re` | `re` |
| `unicodedata` | `unicodedata` |
| `urllib.parse` | `unquote`, `urlsplit` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/markdown_sections.py"]
    n1["src/llm_wiki_cli/services/search_lexical.py"]
    n2["src/llm_wiki_cli/services/search_rank.py"]
    n3["src/llm_wiki_cli/services/search_service.py"]
    n4["src/llm_wiki_cli/services/wiki_media.py"]
    n1 --> n0
    n1 --> n2
    n1 --> n4
    n3 --> n1
    n3 --> n2
    click n0 "../modules/markdown_sections.md"
    click n1 "../modules/search_lexical.md"
    click n2 "../modules/search_rank.md"
    click n3 "../modules/search_service.md"
    click n4 "../modules/wiki_media.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [search_service](../modules/search_service.md) |
| Outbound | [markdown_sections](../modules/markdown_sections.md) |
| Outbound | [search_rank](../modules/search_rank.md) |
| Outbound | [wiki_media](../modules/wiki_media.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_normal` | `(text)` | — | — |
| `_word_form` | `(word)` | — | Approximate English word families for discovery, never identity matching. |
| `_tokens` | `(text)` | — | — |
| `_prose_aliases` | `(text)` | — | Bounded nominal families in explanatory text, never identifier aliases. |
| `_fields` | `(page)` | — | Disjoint captured spans; child sections do not multiply parent evidence. |
| `_identity_tier` | `(page, needle, definitions)` | — | — |
| `_linked_candidates` | `(documents, strict, terms)` | — | One-hop leads from matched diagnostic prose, never source correctness. |
| `_function_descriptions` | `(document)` | — | Read literal formal rows, preserving their original section citations. |
| `_entry_candidates` | `(documents, strict, terms, weights, average_length)` | — | One-hop lexical leads from formal descriptions to explicitly declared flows. |
| `rank_pages` | `(pages, query: str, *, limit = 20, max_pages = MAX_SEARCH_PAGES, max_bytes = MAX_SEARCH_BYTES) -> dict` | — | Rank only supplied captured text within honest, fail-closed work bounds. |