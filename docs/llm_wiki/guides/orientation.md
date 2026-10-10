# Orientation

LLM Wiki provides qualified source and documentation evidence for a declared
coding task. Use it when you need exact declarations, linked documentation,
static callers or explicit gaps that another developer or agent can revisit.
For a tiny change in one function, reading that source directly can be simpler
and cheaper. The coding host owns edits, behavioral verification and publication.

Start with [making a change](making-a-change.md),
[investigating symptoms](investigating-symptoms.md), or
[maintaining documentation](maintaining-documentation.md). The generated module
and entity lists are reference catalogs, not a recommended reading order.
Installation and first-use setup remain in [Getting Started](getting-started.md).

## Follow the source path

The [CLI dispatcher](../modules/cli.md), at
`src/llm_wiki_cli/cli.py:main`, selects the command adapter. Task reads reach the
[supported API](../modules/api.md), at
`src/llm_wiki_cli/api.py:build_task_context`, and the
[scoped task reader](../modules/task_context_v2.md), at
`src/llm_wiki_cli/services/task_context_v2.py:build_scoped_task_read`.
The [extraction coordinator](../modules/extraction_service.md), at
`src/llm_wiki_cli/services/extraction_service.py:get_inventory_result`, supplies
captured static inventory. Native reads additionally validate the committed
wiki inputs they consume.

Built-in Python analysis parses source without importing the application.
Prepared helpers are separate prerequisites; project-local plugins are trusted
executable code. A read does not install helpers, bootstrap a wiki, migrate
storage or run the target application's behavior. Keep your actual source root,
[source selection](source-selection-and-configuration.md) and permissions.

## Start without a wiki

In a new example workspace, save this as `src/app.py`:

```python
def limit(value: int = 3) -> int:
    return value
```

Save `source-task.json` outside `src`:

```json
{
  "schema_version": "llm-wiki-task-request/v2",
  "kind": "contract-change",
  "requirements": [
    {"id": "contract", "facet": "source-contract", "selector": "app.py:limit"}
  ],
  "options": {"knowledge_mode": "off", "budget_tokens": 32000}
}
```

```bash
llm-wiki task-context --request source-task.json --src-dir src --wiki-dir wiki
```

The explicit `wiki` path may be absent. The selector is relative to `src`;
`app.py:limit` identifies this declaration. `off` disables native selection;
`auto` is not the same no-wiki route. Check the installed `task-context --help`
for the interfaces you intend to use. The read does not create the example file.

The same request is available through Python:

```python
import json
from pathlib import Path
from llm_wiki_cli import api

request = json.loads(Path("source-task.json").read_text(encoding="utf-8"))
result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
if result.ok:
    payload = api.validate_task_context(result.rendered, request)
    print(payload["coverage"])
```

Read coverage and omissions before acting. A `behavior` requirement remains a
host-verification gap; emitted evidence does not mean the task is solved.

## When the task needs native documentation

A task-v2 native requirement needs explicitly supported sharded or packed
knowledge storage. An existing flat wiki can still support its full readers,
but selected native task reads reject it. Keep required native evidence required;
use the [storage and recovery route](investigating-symptoms.md#native-storage-is-unavailable)
with authorization instead of silently switching the request off.

`snapshot` reads committed documentation without live source proof. A selected
read qualifies the source it actually captures and the native records it
consumes. Neither implies whole-store validation, correct prose or runtime
completeness. Read availability, reasons, bounds and each live-comparison flag.
The [selected storage reader](../modules/knowledge_storage_access.md), at
`src/llm_wiki_cli/services/knowledge_storage_access.py:_capture_slice`, owns that
consumed scope.

## Read flow diagrams as overviews

[Entry-point flow assembly](../modules/entrypoints.md), at
`src/llm_wiki_cli/services/entrypoints.py:build_flow_detailed`, records a static
trace with depth coverage. The [page renderer](../modules/bootstrap_runtime.md),
at `src/llm_wiki_cli/services/bootstrap_runtime.py:_generate_flow_md`, presents
up to 30 interactions within its existing diagram ceilings. Presentation order
is not runtime execution order. Display omissions, external/unresolved boundary
omissions and upstream depth omissions have different denominators.

The [search command overview](../flows/cli-search.md) retains an unresolved
`search_wiki` boundary. That saved diagram alone does not establish the current
ranking path or runtime behavior. Follow the [search reading route](search-reading-route.md)
through validation, corpus selection, ranking and results. Those four stages are
source-reviewed navigation, not resolved captured invocation edges.

Start at [`search_service.py:search_records`](../../../src/llm_wiki_cli/services/search_service.py#L45-L76)
([module](../modules/search_service.md)), then choose the implementation for the mode:

| Mode | Ranking source |
| --- | --- |
| Omitted mode, `ranked`, `ranked-v2` | [`search_lexical.py:rank_pages`](../../../src/llm_wiki_cli/services/search_lexical.py#L94-L216) ([module](../modules/search_lexical.md)): lexical-v2. |
| `ranked-v1` | [`search_rank.py:rank_pages`](../../../src/llm_wiki_cli/services/search_rank.py#L34-L171) ([module](../modules/search_rank.md)): legacy lexical-v1. |
| `substring` | `search_records`, lines 56–76: case-insensitive literal content matching in input order. |

A source snapshot does not itself index raw source text. Explicit source-text
indexing requires `include_source=True` with `mode="ranked-v2"`, or CLI
`--include-source --mode ranked-v2`; it augments selected, manifest-owned module
candidates with static source text. It does not evaluate runtime behavior.
See [`search_wiki`](../../../src/llm_wiki_cli/services/search_service.py#L105-L116)
and [`capture_source_index`](../../../src/llm_wiki_cli/services/search_source.py#L46-L86).

Policy, source indexing or discovery activates the guarded capture path, which
rechecks captured inputs, page membership and root ownership before returning.
The policy-free path without indexing or discovery returns directly after its
snapshot and selection-compatibility checks; it does not run those later guarded
publication rechecks. Read both branches of
[`search_prevalidated_roots`](../../../src/llm_wiki_cli/services/search_service.py#L119-L281).

The saved flow reports 30 displayed of 114 captured static interactions and 84
display omissions. These are historical saved counts. A whole-source capture
attempt timed out after 600 seconds; a current full trace and its omission
counts remain unavailable. Use the source reading route for orientation without
assuming that it repairs generated trace coverage.

[`api.flow_for_entrypoint`](../../../src/llm_wiki_cli/api.py#L2103-L2136) provides a
bounded static step query. Inspect its outer response bounds and any supplied
traversal/depth coverage separately; the default query does not promise versioned
inner coverage. Source links and additional exact queries can fill a specific
evidence gap, without establishing runtime execution.
