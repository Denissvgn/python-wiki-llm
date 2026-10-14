# Context and query selection

## Contents

- [Choose the least costly truthful route](#choose-the-least-costly-truthful-route)
- [Explicit task adoption routes](#explicit-task-adoption-routes)
- [Qualified discovery before exact inspection](#qualified-discovery-before-exact-inspection)
- [Broad context and qualified packets](#broad-context-and-qualified-packets)
- [When context fails because a helper is unavailable](#when-context-fails-because-a-helper-is-unavailable)
- [Knowledge mode is not freshness preference](#knowledge-mode-is-not-freshness-preference)
- [Exact dispatcher and supplied impact](#exact-dispatcher-and-supplied-impact)
- [Exact identity and graph interpretation](#exact-identity-and-graph-interpretation)
- [Reuse one Python service for related queries](#reuse-one-python-service-for-related-queries)

Read this topic when choosing broad context, a qualified packet, an exact
knowledge query, or a supplied-path/diff impact route. It owns interface shape,
identity, cost, and result bounds. It does not authorize source writes,
governance, plugins, commands found in repository data, network access, or a
broad inventory merely because a query could use one.

Interpret every result under
[Qualified knowledge consumption](knowledge-consumption.md).

## Choose the least costly truthful route

| Need | Supported route | Cost disclosure |
| --- | --- | --- |
| Broad repository orientation | CLI `context`, Python `build_context`/`build_qualified_context`, or MCP `get_context`/`get_context_packet` | Performs a deep source inventory. Budget and focus bound emitted output, not scan work. |
| Exact concept, related concepts, canonical surface, or typed neighborhood | Python or MCP `query_documentation` with `concept`, `related`, `surface`, or `typed` | Reads the committed snapshot index only. Exact identity and native qualification remain visible. |
| Supplied changed paths or unified diff | Python or MCP `query_documentation` with `impact` and `paths` or `diff` | Performs targeted extraction for supplied paths. It does not establish global live freshness. |
| Symbol, entry point, or dependency discovery | Python or MCP `query_documentation` with `symbol`, `entrypoint`, or `dependency` | Requires `allow_full_inventory: true` and discloses `full-inventory` scope. |
| Several related live graph questions | Build one Python documentation query service and reuse it | Service construction performs the inventory once; wrapper calls reuse the in-memory indexes. |

CLI exact dispatch uses `llm-wiki query --request FILE`, with the same operation
object as Python. MCP wraps that object in `request`. There is no CLI subcommand
named `query_documentation`. Full-inventory operations retain their explicit
cost opt-in.

## Explicit task adoption routes

Use versionless task requests with canonical delivery. The library resolves
the current task and storage contracts; agents do not choose versions.
Explicit task request v1 retains its full native-validation behavior;
legacy context calls retain their own response contracts. A task result and a
broad context packet are different envelopes. Read coverage and gaps before
treating either as sufficient for the declared task.

Use the source-only route only when no requirement needs native concepts,
semantic sections or relationships. Save this as `source-task.json` outside the
selected source tree, replacing the coordinate with a real declaration relative
to it:

```json
{
  "requirements": [
    {"id": "contract", "facet": "source-contract", "selector": "app.py:limit"}
  ],
  "options": {"knowledge_mode": "off", "budget_tokens": 32000}
}
```

```bash
llm-wiki task-context --request source-task.json --src-dir src --wiki-dir wiki
```

`wiki` may be absent. `off` disables native reads; `auto` is not the same no-wiki
route. Keep the user's actual roots, selection and permissions. The read does
not create example source, install helpers or execute target code.

A native requirement needs current supported native knowledge. New authorized
bootstrap selects current storage and ordinary maintenance ownership. Existing
projects use authorized upgrade after a package update; the library retains
recovery copies and chooses compatible current formats:

```bash
llm-wiki upgrade --wiki-dir wiki
llm-wiki knowledge storage-check --wiki-dir wiki --full
llm-wiki doctor --capabilities --src-dir src --wiki-dir wiki --format json
```

Then request exact native evidence with `knowledge_mode: "required"`, for example
`{"id":"concept","facet":"concept","selector":"llm-wiki://modules/app"}`.
`read_scope: "snapshot"` reports committed evidence without live source proof;
use explicit source requirements with selected reads when needed. Missing,
corrupt, unsupported or bounded native evidence remains a gap or failure. Never
rewrite the requirements or switch native mode off to claim success. All readers
and writers must support the current format. A read never migrates or syncs.

Upgrade reports recovery locations. For an interrupted storage migration,
use the reported matching storage preimage; ownership adoption has its separate
complete recovery record. Never combine unrelated recovery snapshots:

```bash
llm-wiki knowledge recover-storage --wiki-dir wiki --recovery-dir storage-recovery --dry-run
llm-wiki knowledge recover-storage --wiki-dir wiki --recovery-dir storage-recovery
```

Recovery refuses unrelated root edits, changed Markdown authority and newer
committed work. A refused snapshot is not authority to force replacement.

Storage adoption and ordinary maintenance adoption are separate. An existing
`.llm-wiki-maintenance-adoption.json` marker with missing/corrupt owner requires
complete authority recovery through the [maintenance route](maintenance.md),
before manifestless seeding. `indexed-v8` requires an adopted owner and does not
shard flat knowledge.

Canonical delivery stays default. Optional compact CLI delivery adds
`--view compact --view-budget-tokens N --canonical-output FILE`; both canonical
receipt and optional `--output FILE` must be outside source/wiki and disjoint
from request/profile/tokenizer/selection inputs and each other. For source root
`.` that means outside the entire root. Choose a positive explicit budget; a
compact minimum can still fail to fit. No 1,000-token fit or fixed saving is
promised. Canonical failure produces no receipt; compact-only cannot-fit returns
its counted diagnostic and preserves a valid canonical receipt when available.

The current compact view is self-contained readable JSON with complete
selected facts, citations, coverage, gaps and limitations. Use the same explicit
view budget and disjoint canonical receipt path. Python/session `view_options`
omit version fields; validation/expansion remain bound to the
original canonical text and request. The readable body may exceed compact-v1's
encoded size. Its budget still covers emitted view text rather than host framing.
MCP retains identity/base/state and validation qualifications in its smaller v2
envelope; `include_metadata: true` returns full telemetry. V1 and Python session
metadata retain their existing shape. Count setup, transport and any necessary
follow-up messages; never infer a universal fit or saving.

Python uses `build_compact_task_context(..., view_options={"budget_tokens": N})`, then validates/expands
against that exact request and canonical text. Session `read_compact` and MCP
`read_compact_context_session` return compact presentation; explicit
`canonical_receipt(request_id, result_id)` or MCP `get_task_context_receipt`
returns exact retained canonical evidence separately. Missing/closed/expired
custody requires a fresh read. Historical receipt identity is not currentness;
current lookup revalidates. Include one representation deliberately, count
metadata/framing/follow-ups separately, and do not assume the host hides metadata.

Sessions are an explicit host choice, with cold task reads available for the
same evidence features. Reuse requires request-time validation of source bytes,
selection, wiki authority and producer configuration; events only invalidate
state. Save or defer unsaved buffers. Change of workspace, closure or lost
receipt custody requires a fresh read. No continuous freshness or general
speedup is established by opening a session.

## Qualified discovery before exact inspection

Ranked search keeps exact page and declaration identities ahead of approximate
matches and reports reasons and corpus bounds. The default `ranked` mode and
explicit `ranked-v2` mode use `ranking_version: "llm-wiki-search/lexical-v2"`.
`--mode ranked-v1` retains the earlier policy; `--mode substring` keeps literal matching. Search results remain
candidates, including relaxed matches and source snippets.

Choose source augmentation explicitly when source text is needed for discovery:

```bash
llm-wiki search "retry failure" --src-dir src --wiki-dir wiki --include-source
```

It requires a valid committed manifest and indexes only mapped module sources
inside the captured selection. Source capture, hashing and rechecks add work;
snippets do not prove runtime behavior. A bounded read cannot widen selection
automatically or install helpers to satisfy a query.

Choose owner/section qualification explicitly:

```bash
llm-wiki search "retry failure" --src-dir src --wiki-dir wiki --discovery qualified-v1
```

The additional `discovery` groups only returned candidates by validated owner
and retains distinct narrative sections, omissions and bounds. Recorded source
and review state does not establish live freshness or current approval. Missing
native storage or a valid unsupported layout captured within bounds leaves an
unavailable qualification; inconsistent authority or exceeded capture/output
bounds fails the read. Neither outcome authorizes adoption.

Select a returned exact `path`, then call
`api.inspect_concept(path, src_dir="src", wiki_dir="wiki", live=False)`.
Continue with its locator only when it resolves one concept. Preserve missing,
ambiguous and unavailable outcomes; do not substitute another fuzzy hit.
When review status is decisive, read the exact record with
`api.get_maintenance_status(..., record_id=record_id, live=False)` and request a
live comparison separately when needed. Selected task context carries its own
maintenance scope and can report current review unavailable.

## Broad context and qualified packets

For broad repository work, run one serialized read and reuse its selection:

```bash
llm-wiki context --budget 8000 --src-dir . --wiki-dir docs/llm_wiki --format packet --focus changed --knowledge-mode auto --read-only
```

`--format json` and `--format markdown` return a context response. CLI
`--format packet`, Python `build_qualified_context`, and MCP
`get_context_packet` return the full canonical Qualified Context Packet, which
binds normalized request, source basis, wiki/knowledge basis, response,
policies, and packet identity. Python `build_context` and MCP `get_context`
return a response, not a packet. `query_documentation` returns a bounded query
result, not either context envelope.

`--budget` bounds emitted token content. `--focus changed` prioritizes files
from the last Git commit, gives their import neighbors slimmer detail, and
keeps other files names-only; `--focus all` gives equal priority. Neither
option limits inventory work. A broad packet captures one coordinated
source/wiki/knowledge read and rechecks the immutable anchors before return.

Native selection has independent bounds for concepts, pages, and
relationships (normally 20 concepts, 20 pages, and 40 relationships), plus
separate source-file bounds. A packet or knowledge envelope is capped at the
documented serialized ceiling; a size fallback is an explicit limitation, not
silent omission.

Source selection reports exact candidate and returned counts under
`bounds.files`. Its `truncated` flag means at least one file was omitted. The
top-level context `truncated` flag is broader: it can also mean a returned
file's detail was downgraded to fit the token budget.

## When context fails because a helper is unavailable

Treat a missing or stale extractor helper as a recoverable setup prerequisite,
not as an empty context result. Follow
[helper recovery](extractors-dependencies.md#recover-a-failed-context-or-extraction-command).
When setup is already authorized, run the error's preparation command separately
and retry the original read once, preserving its source selection, helper
cache, and `--read-only` option. Preparation can write or download; the read-only
command itself never performs it.

If setup cannot proceed, disclose the failed command and limitation, then
continue with targeted source/wiki evidence. Do not regenerate the wiki or
claim the prescribed context command succeeded.

## Knowledge mode is not freshness preference

Explicit knowledge mode has exactly three values:

- `off` disables native selection and returns a disabled disclosure;
- `auto` selects ready qualified native evidence or returns an explicit
  validated fallback; and
- `required` returns the selected evidence or fails with a stable structured
  reason, fallback evidence, and recovery boundary.

Omitting knowledge mode preserves the legacy v1 response. An explicit mode
uses the v2 contract. `prefer_fresh` is independent: under budget pressure it
can prefer live-current sources only inside an existing relevance tier. It
never enables knowledge, crosses relevance tiers, filters stale/unknown
material, or changes truth. `off` plus `prefer_fresh: true` is accepted and
reports that the ranking was not applied because selection was disabled.

A direct v2 raw request is:

```json
{
  "protocol": "llm-wiki-context/v2",
  "budget_tokens": 8000,
  "focus": ["changed", "neighbors"],
  "format": "json",
  "filters": {},
  "prefer_fresh": false,
  "knowledge_mode": "auto"
}
```

The compatibility v1 request does not accept `knowledge_mode`. It can refine
concepts by freshness, evidence, and typed relationship fields only when a
`surface` or `symbol` filter is present:

```json
{
  "protocol": "llm-wiki-context/v1",
  "budget_tokens": 8000,
  "focus": ["changed", "neighbors"],
  "format": "json",
  "filters": {
    "surface": "entities",
    "freshness": "source-changed",
    "evidence": "present",
    "relationship_kind": "calls",
    "relationship_origin": "extracted",
    "relationship_resolution": "resolved",
    "relationship_direction": "incoming"
  }
}
```

Freshness accepts `current`, `nonsemantic-source-change`, `unknown`,
`source-changed`, `source-missing`, or `basis-incompatible`. Evidence accepts
`present`, `missing`, `invalid`, `unknown`, or `not-applicable`. Relationship
origin accepts `extracted`, `inferred`, `markdown`, or `governance`;
resolution accepts `resolved`, `ambiguous`, `external`, or `unresolved`; and
direction accepts `incoming`, `outgoing`, or `both`. A kind is a core kind or a
qualified plugin kind such as `vendor.plugin/relationship`.

Refinements run before response limiting. Exact counts live at
`knowledge_selection.unfiltered_total`, `.filtered_total`, `.returned`, and
`.truncated`. Without an explicit freshness filter, stale and unknown
references remain eligible. Knowledge enrichment does not change source-file
priority or consume the source-file token budget.

Knowledge-aware page references may carry compact lifecycle, section-review,
and machine-verification summaries. Ordinary context limits review data to
state counts, truncation, and stable reason codes, and limits verification to
receipt state and check counts. Reviewer/event detail, receipt scope IDs,
diagnostics, evidence payloads, and hashes remain outside ordinary context.

## Exact dispatcher and supplied impact

Python dispatcher examples:

```python
from llm_wiki_cli.api import query_documentation

concept = query_documentation({
    "operation": "concept",
    "value": "llm-wiki://entities/User",
    "limit": 20,
})
related = query_documentation({
    "operation": "related",
    "value": "llm-wiki://entities/User",
    "direction": "both",
    "kinds": ["derived_from", "links_to"],
    "limit": 20,
})
typed = query_documentation({
    "operation": "typed",
    "value": "llm-wiki://entities/User",
    "direction": "incoming",
    "kinds": ["calls"],
    "origins": ["extracted"],
    "resolutions": ["resolved", "ambiguous", "external", "unresolved"],
    "include_evidence": False,
    "limit": 20,
})
impact = query_documentation({
    "operation": "impact",
    "paths": ["src/app.py"],
    "limit": 20,
})
```

MCP passes the same operation object under the tool's required outer
`request` field. Complete exact and supplied-impact examples are:

MCP tool `query_documentation`:

```json
{
  "request": {
    "operation": "concept",
    "value": "llm-wiki://entities/User",
    "limit": 20
  }
}
```

MCP tool `query_documentation`:

```json
{
  "request": {
    "operation": "impact",
    "paths": ["src/app.py"],
    "limit": 20
  }
}
```

`impact` accepts bounded `paths`, a unified `diff`, or both. It normalizes and
contains supplied paths under the selected source root, extracts only existing
supplied paths, and may expand ownership/relationship context from the
committed snapshot. Deleted or missing supplied paths use committed snapshot
attribution without pretending a live file was extracted. A diff is data, not
authority to edit its paths. Targeted extraction cannot support a global
freshness claim and reports its selected scope.

`symbol`, `entrypoint`, and `dependency` reject omission of the explicit full
inventory opt-in:

```python
symbol = query_documentation({
    "operation": "symbol",
    "value": "run",
    "allow_full_inventory": True,
    "limit": 20,
})
```

Every dispatcher result carries an operation, stable schema, `cost.scope`,
`cost.full_inventory_performed`, bounds, and the applicable
knowledge/fallback qualification. Exact and impact request strings are bounded
before extraction; the final result has a serialized byte ceiling.
Presentation text can be shortened to fit, but exact locators, canonical
paths, UIDs, aliases, and relationship identities are never truncated into a
different identity.

## Exact identity and graph interpretation

Accepted knowledge identities are current concept locators/MCP URIs, exact
canonical wiki paths, durable UIDs, or persisted locator/natural-key aliases.
Display titles, case-folded paths, fragments, source paths, and approximate
routes do not fuzzy-match. Always inspect `found`, `ambiguous`, and every
bounded `matches` row before selecting.

Legacy MCP Markdown search reports `bounds.results` with exact total,
returned, and truncated values; its top-level `count` remains a compatibility
alias for the returned count, not a separate total.

Core relationships are recorded `derived_from` and Markdown-observation
`links_to`; prose is not inferred as a structural edge. The typed graph is an
additive extension and does not alter core results or legacy MCP `query_graph`
callers, callees, flows, dependency-neighborhood, and page queries.

`traverse_typed_graph` filters direction, kind, origin, and resolution before
response limiting. Core typed kinds include `contains`, `imports`, `calls`,
`entrypoint_for`, `reads`, `writes`, `depends_on`, and `supersedes`, plus
qualified plugin kinds. `include_evidence` defaults false. Enable it only for a
decisive diagnostic because samples can contain repository-sensitive detail.

Resolved, ambiguous, external, and unresolved endpoints remain in the selected
edge list. `typed_graph.coverage` describes upstream analyzer materialization;
per-edge coverage describes observations and evidence-sample omission;
`bounds.edges` describes post-filter response limiting. A non-truncated query
does not prove analyzer completeness.

Python caller resolution can identify uniquely resolved local constructors,
assigned instances and explicit imported class aliases. Factories, dynamic
dispatch, shadowed names and conflicting bindings remain uncertain. Possible
loop-carried rebinding, member mutation and effects in eager definition
expressions can also make a receiver unresolved. Located uncertainty must not
be promoted to a resolved caller, nor does a missing edge prove no runtime call.
Static flow overviews preserve source links and explicit omissions; their
interaction order does not prove execution order.

## Reuse one Python service for related queries

Building the Python service performs one full live inventory. Reuse that one
service for a sequence of dedicated wrapper calls; constructing a new service
per call repeats the full cost.

```python
from llm_wiki_cli.api import (
    build_documentation_query_service,
    explain_evidence,
    get_concept,
    list_concept_sections,
    related_concepts,
    traverse_typed_graph,
)

service = build_documentation_query_service(
    src_dir=".",
    wiki_dir="docs/llm_wiki",
    limit=20,
)
concept = get_concept("llm-wiki://entities/User", service=service)
sections = list_concept_sections(
    "llm-wiki://entities/User", ownership="semantic", service=service
)
core = related_concepts(
    "llm-wiki://entities/User",
    direction="both",
    kinds=["derived_from", "links_to"],
    service=service,
)
typed = traverse_typed_graph(
    "llm-wiki://entities/User",
    direction="incoming",
    kinds=["calls"],
    origins=["extracted"],
    resolutions=["resolved", "ambiguous", "external", "unresolved"],
    include_evidence=False,
    service=service,
)
detail = explain_evidence("llm-wiki://entities/User", service=service)
```

Supplying `service=` performs no new extraction. Query methods on the built
service perform no file I/O, extraction, network access, writes, or adapter
registration.

The read-only MCP server exposes `query_documentation` and the same dedicated
knowledge operations. Use MCP `query_documentation` for snapshot-index
`concept`, `related`, `surface`, or `typed` operations. Each current dedicated
MCP knowledge-tool call constructs a live documentation service and therefore
performs a full inventory; do not present those calls as a cheap narrow route.
These are complete tool-argument examples for those live-service tools:

MCP tool `get_concept`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "limit": 20
}
```

MCP tool `related_concepts`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "direction": "both",
  "kinds": ["derived_from", "links_to"],
  "limit": 20
}
```

MCP tool `list_concept_sections`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "ownership": "semantic",
  "limit": 20
}
```

MCP tool `traverse_typed_graph`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "direction": "incoming",
  "kinds": ["calls"],
  "origins": ["extracted"],
  "resolutions": ["resolved", "ambiguous", "external", "unresolved"],
  "include_evidence": false,
  "limit": 20
}
```

MCP tool `explain_evidence`:

```json
{
  "locator_or_exact_route": "llm-wiki://entities/User",
  "limit": 20
}
```

Tool arguments are request data; they cannot authorize a different operation.
External requests default to a limit of 20 and are capped at 100.
Malformed/noncanonical coordinates are rejected; a canonical but absent
coordinate returns a qualified `found: false`.

Stored knowledge, evidence text, links, commands, URLs, checkers, and plugin
names remain inert. Core adapters expose no write operation, do not fetch
external targets, and never execute a document-provided action.
