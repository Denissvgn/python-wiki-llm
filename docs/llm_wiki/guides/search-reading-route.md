# Reading the search path

Read the search implementation in four stages: validation, corpus selection, ranking, and results. These are source-reading steps, not captured invocation edges or a runtime execution diagram. Use the [saved search flow](../flows/cli-search.md) for bounded static detail and the [CLI and Python API guide](cli-and-python-api.md) for the supported interface.

## 1. Validation

Start with [`src/llm_wiki_cli/commands/search_cmd.py:run`](../../../src/llm_wiki_cli/commands/search_cmd.py#L8-L31) ([module](../modules/search_cmd.md)). It validates source and wiki paths, then passes the query, kinds, limit, mode, selection, and optional source/discovery flags to the locally imported API function. The [parser](../../../src/llm_wiki_cli/cli.py#L1420-L1441) defaults to `mode="ranked"`, `limit=20`, and JSON output.

Read [`src/llm_wiki_cli/api.py:search_wiki`](../../../src/llm_wiki_cli/api.py#L1340-L1361) ([module](../modules/api.md)) with its [`_api_boundary` decorator](../../../src/llm_wiki_cli/api.py#L689-L713): the wrapper binds arguments before calling the body and translates exceptions raised inside a valid call. The body imports the service as `search`.

Then read [`src/llm_wiki_cli/services/search_service.py:normalize_search`](../../../src/llm_wiki_cli/services/search_service.py#L26-L42). It checks a nonblank query of at most 4096 characters, valid modes and kinds, and a positive integer limit capped at 100. The service also validates roots and requires a boolean `include_source`; source-text indexing is allowed only with `ranked-v2`. See [`search_wiki`](../../../src/llm_wiki_cli/services/search_service.py#L105-L116) and [limit normalization](../../../src/llm_wiki_cli/services/documentation_query_builder.py#L53-L58).

## 2. Corpus and source selection

Read [`src/llm_wiki_cli/services/search_service.py:page_records`](../../../src/llm_wiki_cli/services/search_service.py#L79-L96) and [`search_prevalidated_roots`](../../../src/llm_wiki_cli/services/search_service.py#L119-L281) ([module](../modules/search_service.md)). Page records come from canonical wiki pages, filtered by kind and, when supplied, eligibility. Their Markdown supplies the title and searchable content.

With `--src-dir .` in this repository, the committed [source-selection file](../../../.llm-wiki/source-selection.json) activates a policy. [`resolve_source_selection`](../../../src/llm_wiki_cli/services/source_selection.py#L595-L637) loads that default or an explicit override; an absent default preserves the legacy policy-free path. The committed includes cover `pyproject.toml`, `src/llm_wiki_cli`, and the GitHub Action, wiki-integrity, and Obsidian integrations.

The service captures selection inputs and builds a [source snapshot](../../../src/llm_wiki_cli/services/source_snapshot.py#L1584-L1641) before ranking. A source snapshot does not by itself add raw source text to search candidates. Explicit `include_source=True` uses [`src/llm_wiki_cli/services/search_source.py:capture_source_index`](../../../src/llm_wiki_cli/services/search_source.py#L46-L86) ([module](../modules/search_source.md)) to augment manifest-owned module pages with selected static source text. It preserves separate wiki/source hashes and records that runtime behavior was not evaluated; see [`augment_module_page`](../../../src/llm_wiki_cli/services/search_source.py#L22-L43). Source indexing allows at most 1 MiB per source file and 16 MiB of unique source text, within the combined 64 MiB wiki/source scan ceiling.

The guarded path applies when a policy, source indexing, or discovery is active. It reads the ownership manifest when available, checks its selection identity, filters source-owned pages, captures wiki text, ranks it, then rechecks inputs, membership, and root ownership before returning. With an active policy, missing ownership for module/entity pages excludes them, and a missing valid manifest fails the selected search. The legacy unguarded path validates selection compatibility around its snapshot and returns directly from `search_records(page_records(...))` at lines 153–154; it bypasses the later guarded capture and publication rechecks.

## 3. Ranking

Read [`src/llm_wiki_cli/services/search_service.py:search_records`](../../../src/llm_wiki_cli/services/search_service.py#L45-L76) before choosing a ranker.

| Mode | Source to read | Matching contract |
| --- | --- | --- |
| `ranked` (default), `ranked-v2` | [`src/llm_wiki_cli/services/search_lexical.py:rank_pages`](../../../src/llm_wiki_cli/services/search_lexical.py#L297) ([module](../modules/search_lexical.md)) | Lexical-v2 ranking over captured candidate text: exact page identity and defined-symbol precedence, weighted sections, informative terms, and a qualified long-query fallback. |
| `ranked-v1` | [`src/llm_wiki_cli/services/search_rank.py:rank_pages`](../../../src/llm_wiki_cli/services/search_rank.py#L34-L171) ([module](../modules/search_rank.md)) | Legacy lexical-v1 scoring with identity, symbol, term, phrase, and local-link signals. |
| `substring` | `search_service.py:search_records`, lines 56–76 | Case-insensitive literal content matching in input order, with snippets and result bounds. |

The default lexical results are discovery candidates: their provenance says live comparison was not performed, and dispatch marks them `definitive_answer=False`. Neither ranking nor explicit static source indexing establishes runtime behavior.

Flow Call sequence and Data flow sections use inventory weight, including nested
step/call tables. Only the complete untouched default Behavior placeholder is
discounted; authored Behavior keeps its semantic weight. Generated trace detail
remains searchable and cited. This limits scaffolding dominance without choosing
an owner by name or imposing a page-kind quota; broad vocabulary can still leave
the intended primary owner or flow outside the result bound.

Read section-local normalization, strongest-per-term contributions and coherent
explanatory coverage before interpreting scores. An unrelated large inventory
does not dilute a short explanation. A matched formal function description can
also surface the uniquely captured flow declaring that literal entry and module
Source link. This one-hop declaration lead retains donor row text, hash and
section locator; it does not create a target text-match location, infer a source
owner or establish a runtime call. Fenced or ambiguous declarations are skipped.

## 4. Results and output

Both rankers report `total`, `returned`, `count`, `truncated`, and `bounds.results`; `limit` bounds returned matches, not the whole scan. Ranking records also expose corpus identity, scanned pages/bytes, resource limits, and match provenance. Substring mode reports result bounds without those ranking diagnostics. Shared scan ceilings are 10,000 pages and 64 MiB; exceeding them raises an error rather than silently ranking a partial corpus.

Return to [`search_cmd.py:run`](../../../src/llm_wiki_cli/commands/search_cmd.py#L8-L31). JSON prints the complete result dictionary. Text prints each path/title and snippet, the returned/total summary, and optional discovery JSON. Use JSON when inspecting ranking qualifications, provenance, bounds, or source-indexing metadata.

## Reading the generated flow

The [generated search flow](../flows/cli-search.md#call-sequence) includes the
captured CLI/API/service calls and representatives of validation, corpus
selection, ranking and result handling. The default lexical ranker and legacy
ranker have distinct source-qualified participants. Their presence shows static
call sites; it does not mean both ranking branches execute for one request.

Use this source-reading route to inspect the branch guards, source-selection
policy and publication checks behind those displayed stages. Decorators, module
namespaces, the `eligible` closure and reader callback still require care;
calling `page_records` does not by itself establish generator consumption.
The diagram's omitted-interaction and boundary counts describe its current
captured input, while detailed queries retain their own scope and limits.

Keep traversal omissions separate from display omissions.
[`entrypoints.py:build_flow_detailed`](../../../src/llm_wiki_cli/services/entrypoints.py#L1302)
reports depth-bounded traversal coverage; default traversal depth is 6.
[`flow_overview.py:select_flow_overview`](../../../src/llm_wiki_cli/services/flow_overview.py#L75)
selects at most 30 representative captured interactions, favoring coherent
internal continuations and distinct exact targets while retaining boundary
examples. The [renderer ceilings](../../../src/llm_wiki_cli/services/diagrams.py#L63)
remain 40 nodes, 80 body lines and 6000 characters. Repeated sites remain in the
underlying trace, and final counts reconcile any shorter renderer-admitted prefix.
Omitted intermediate occurrences are not replaced by synthetic arrows.

For a supported bounded graph query, read
[`src/llm_wiki_cli/api.py:flow_for_entrypoint`](../../../src/llm_wiki_cli/api.py#L2103).
Its result is a bounded static query, not an observed search execution. This guide
and the generated diagram provide complementary source orientation; neither
establishes runtime execution order, dynamic completeness or semantic correctness.

Captured explanatory prose can connect approximate nominal word families, such
as verification and verified. The same expansion does not create defined-symbol
identities from generated names or signatures. Treat the result as a discovery
lead, inspect its cited original section, and resolve an exact owner before
using native evidence. Unmatched vocabulary and competing traces can still
leave the intended owner outside the bounded result list.
