# Investigating symptoms

Use a symptom to find candidate pages, then resolve an exact implementation and
inspect source. A lexical match is a navigation lead, not a diagnosis. Search
can miss a useful page when the symptom's vocabulary differs from its source.

Default lexical discovery can connect approximate English word forms such as
`rename` and `renaming`. This broadens navigation matches without changing literal
page or defined-symbol identity checks. Diagnostic prose may also explicitly link
to an implementation whose page does not repeat the symptom. Strong matched guide
sections can surface that captured module/entity as a one-hop lead. Inspect its
`linked_evidence`: the guide hash, section locator and target path explain the
route, while linked-discovery provenance does not claim a target text match or a
correct diagnosis. No network traversal or automatic source indexing is implied.

## Move from discovery to evidence

In a workspace with a wiki, try a small query using terms from the symptom:

```bash
llm-wiki search "missing caller" --src-dir src --wiki-dir wiki --limit 10 --format json
```

Inspect ranking reasons and returned/corpus bounds. Follow the candidate's
canonical path, then choose an exact concept or source declaration. Exact
snapshot query, for a wiki containing `modules/app.md`, is:

```json
{
  "operation": "concept",
  "value": "llm-wiki://modules/app",
  "limit": 10
}
```

Save it as `concept-query.json` and run:

```bash
llm-wiki query --request concept-query.json --src-dir src --wiki-dir wiki
```

A concept read is committed snapshot evidence. Use the
[change guide](making-a-change.md#resolve-one-owner) for a live symbol query and
decisive source. Exact lookup does not fuzzy-match a symptom, title or approximate
path. `found: false` under missing, uncertain or bounded evidence is not a
negative fact about the project.

For the search implementation, use the [search reading route](search-reading-route.md).
It separates default lexical-v2 ranking, explicit legacy `ranked-v1`, substring
matching and optional static source indexing, and identifies which return path
performs guarded publication rechecks. Search results still require exact lookup
and decisive source inspection.

The [search owner](../modules/search_service.md), at
`src/llm_wiki_cli/services/search_service.py:search_wiki`, supplies discovery.
Exact callable matching belongs to the
[query service](../modules/documentation_queries.md), at
`src/llm_wiki_cli/services/documentation_queries.py:DocumentationGraphQueryService._callable_matches`.

## Choose the next useful step

| Symptom | Next evidence or recovery step |
| --- | --- |
| A short symbol has several matches | Select the exact path, qualified owner and occurrence; retain ambiguity until resolved. |
| A factory or receiver has no resolved caller edge | Inspect its captured reason/location and the source. Static analysis may not know the runtime receiver. |
| A body changed but the declaration still looks current | Compare supported executable observations and module/global dependencies; verify behavior through the host. |
| Search gives weak or no matches | Try known source/owner terms, use the index for navigation, or read the likely source directly. |
| Selection no longer matches the wiki | Preserve the configured roots/profile, inspect the intended selection change and use authorized owning sync. |
| A helper is missing | Inspect capability output; prepare only with setup authorization and retry the original read once. |
| Context cannot fit | Narrow to decisive requirements within the task's intent or use an allowed larger budget. Failed context is not usable evidence. |

Helper preparation can write caches or download dependencies. A provider read
never performs it implicitly. Keep the same source selection and helper cache;
[configuration](source-selection-and-configuration.md) and
[troubleshooting](troubleshooting-and-security.md) describe those prerequisites.
Do not bootstrap or regenerate a wiki to hide a failed read.

## Native storage is unavailable

For a new example wiki, authorized bootstrap can select bounded storage:

```bash
llm-wiki bootstrap --src-dir src --wiki-dir wiki --knowledge-format sharded-v2
```

For an existing coherent flat wiki, keep its pages and complete current snapshot.
Check that all readers/writers support the selected format, preview migration,
then apply it only when authorized. Use an empty recovery directory outside
both source and wiki:

```bash
llm-wiki knowledge migrate --wiki-dir wiki --to sharded-v2 --dry-run --recovery-dir storage-recovery
llm-wiki knowledge migrate --wiki-dir wiki --to sharded-v2 --recovery-dir storage-recovery
llm-wiki knowledge storage-check --wiki-dir wiki --full
llm-wiki doctor --capabilities --src-dir src --wiki-dir wiki --format json
```

A native task, saved as `native-task.json`, can then explicitly require a
committed concept:

```json
{
  "schema_version": "llm-wiki-task-request/v2",
  "requirements": [
    {"id": "concept", "facet": "concept", "selector": "llm-wiki://modules/app"}
  ],
  "options": {"knowledge_mode": "required", "read_scope": "snapshot", "budget_tokens": 32000}
}
```

```bash
llm-wiki task-context --request native-task.json --src-dir src --wiki-dir wiki
```

Keep that native requirement when the root is absent, corrupt, unsupported or
over budget. An independently useful source-off read does not satisfy it.
The [storage lifecycle](../modules/knowledge_storage_lifecycle.md), at
`src/llm_wiki_cli/services/knowledge_storage_lifecycle.py:recover_knowledge_storage`,
can restore a generation-bound storage migration snapshot. It refuses unrelated
root/prose edits or newer work; do not force an overwrite. Missing adopted
maintenance authority instead requires its matching complete
[maintenance recovery](maintaining-documentation.md#retain-complete-recovery).
Storage adoption and review-history adoption are separate choices.

## Keep delivery failures visible

Canonical task output is the default. Optional compact output requires an
explicit positive view budget and a full host receipt outside source/wiki and
all request/profile/tokenizer/selection inputs:

```bash
llm-wiki task-context --request source-task.json --src-dir src --wiki-dir wiki --view compact-v1 --view-budget-tokens 32000 --canonical-output receipts/context.json
```

This uses the [source-only example](orientation.md#start-without-a-wiki).
A source root of `.` requires the receipt outside that entire root. Compact
output preserves the canonical facts, gaps and citations; it does not promise
a 1,000-token fit or a fixed saving. The
[compact renderer](../modules/task_compact.md), at
`src/llm_wiki_cli/services/task_compact.py:render_compact_task_context`, returns
an explicit cannot-fit diagnostic when its minimum exceeds the view budget.
A valid canonical receipt may still be retained; canonical failure fabricates
no receipt. Count host/MCP metadata, framing and receipt follow-ups separately.
Including both presentations can cost more than canonical text alone.
