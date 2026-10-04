# Native coding workflow

Use a provider whose CLI and Python API expose the task request, storage and
optional delivery interfaces you select. Check `llm-wiki task-context --help`
and `llm-wiki knowledge migrate --help` in each environment; a version number
alone does not establish support for every format.

For large native snapshots, [knowledge storage](knowledge-storage.md) describes
explicit sharded or packed storage adoption and task request v2 with selected validation.
Task request v1 retains its existing full-validation behavior.

An explicit task request gathers qualified source and wiki evidence. The provider
reads and reports; your coding host decides what to include, edit, execute and
publish. Existing context calls retain their defaults.

## Choose an interface

| Operation | Python API | CLI | MCP |
|---|---|---|---|
| Ranked discovery | `search_wiki` | `search` | `search_wiki` |
| Advisory maintenance | `build_maintenance_queue` | `queue` | `get_maintenance_queue` |
| Exact query | `query_documentation` | `query --request FILE` | `query_documentation` |
| Complete output budget | `build_budgeted_context` | `context --request FILE` | `build_budgeted_context` |
| Task evidence | `build_task_context` | `task-context --request FILE` | `build_task_context` |
| Validated reuse | `open_context_session` | — | `open_context_session`, `read_context_session`, `hint_context_session`, `close_context_session` |

Search discovery preserves ranking reasons and corpus bounds. Exact queries use
the existing [native query contract](native-knowledge-provider.md). A maintenance
queue is advisory and never applies recommendations.

## Source-only task without a wiki

Choose this route when the task needs source evidence. It requires neither
bootstrap nor a wiki. In a new example workspace, create `src/app.py`:

```python
def limit(value: int = 3) -> int:
    return value
```

Save this request as `source-task.json` outside `src`:

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

Here `wiki` is an explicit in-project path that may be absent. `off` disables
native selection; `auto` is not the same no-wiki recipe. Selectors are relative
to `src`, so the declaration is `app.py:limit`, not `src/app.py:limit`.
The Python route produces and validates the same canonical evidence:

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

Use your actual source root, configured selection and exact declaration instead
of the example paths. Reads do not create the source file, install helpers or
run the target project. One direct source read can be simpler for a tiny task.

## Native task with explicit storage adoption

Choose this route when a requirement needs committed concepts, semantic
sections or typed relationships. For a new wiki, explicitly select bounded
storage during authorized bootstrap:

```bash
llm-wiki bootstrap --src-dir src --wiki-dir wiki --knowledge-format sharded-v2
```

For an existing flat wiki, keep its current pages and complete snapshot. A task
v2 native read requires sharded or packed knowledge storage; a flat rejection
does not authorize migration.

For a captured valid flat model, the task CLI returns exit 2 with
`error.details.reason: "flat-native-adoption-required"` and an authorized
migration-preview next action. This identifies the storage prerequisite; it
does not audit the complete snapshot. Unknown or damaged roots receive no
adoption hint. Migration validates companion authority before applying.

With migration authorized, preview and apply it using an empty recovery directory
outside both `src` and `wiki`:

```bash
llm-wiki knowledge migrate --wiki-dir wiki --to sharded-v2 --dry-run --recovery-dir storage-recovery
llm-wiki knowledge migrate --wiki-dir wiki --to sharded-v2 --recovery-dir storage-recovery
llm-wiki knowledge storage-check --wiki-dir wiki --full
llm-wiki knowledge inspect-storage --wiki-dir wiki --selector page:modules/app.md --limit 10
llm-wiki doctor --capabilities --src-dir src --wiki-dir wiki --format json
```

Dry-run does not write a recovery snapshot. Apply retains the prior snapshot;
`storage-check --full` audits the result. Capability output can identify helper
or producer prerequisites; resolve those only with setup authorization. Upgrade
all readers and writers to support the selected schema before adoption.

Save this native snapshot request as `native-task.json`:

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

This is committed snapshot evidence. It does not establish live source
currentness, prose approval or runtime behavior. Use `read_scope: "selected"`
and explicit source requirements when live source evidence is needed. Keep
native requirements and `required` mode when a native read fails; never turn
them into an `off` success. Missing, corrupt or unsupported roots require a
qualified failure and an authorized complete recovery, not hidden bootstrap.
For a failed storage migration, restore its retained complete snapshot:

```bash
llm-wiki knowledge recover-storage --wiki-dir wiki --recovery-dir storage-recovery --dry-run
llm-wiki knowledge recover-storage --wiki-dir wiki --recovery-dir storage-recovery
```

Storage recovery is bound to the original or target migration generation. It
refuses unrelated root edits, changed Markdown authority or newer committed
work. Restore an authorized matching complete snapshot when that eligibility
check fails; do not force a replacement.

Storage adoption is separate from optional
[ordinary review tracking](maintenance.md). A
`.llm-wiki-maintenance-adoption.json` marker requires its matching maintenance
owner. Restore missing or corrupt adopted authority through the complete
[maintenance recovery route](maintenance.md#recover-complete-authority) before
sync; manifestless seeding cannot reconstruct its history. `indexed-v8`
requires that adopted owner and changes manifest storage, not flat knowledge
storage. Neither kind of adoption happens during a read.

For an owner adopted with a retained `maintenance-recovery` directory, use its
actual adoption ID and complete committed snapshot:

```bash
llm-wiki maintenance recover --wiki-dir wiki --recovery-dir maintenance-recovery/committed --expected-adoption-id ADOPTION_UUID
```

Replace `ADOPTION_UUID` with the retained marker's actual ID. A storage-migration
recovery copy is not a substitute for this matching complete maintenance bundle.

## Interpret evidence requirements

Task kinds are `orientation`, `bug-diagnosis`, `contract-change` and `refactor`.
Anchors have a `kind` (`source`, `symbol`, `wiki` or `concept`) and a `value`.
Source selectors are portable relative paths. Declaration coordinates may include
an exact owner and occurrence, such as `retry.py:Client.retry#2`. An unqualified
name can remain ambiguous. An optional `task_ref` is a host label, separate from
the provider's content identity.

Requirements declare `id`, `facet`, `selector` and optionally `criterion`
(`present` or `complete`). Supported facets are `source-contract`, `callers`,
`callees`, `concept`, `semantic-section`, `typed-relationships`, `entrypoint` and
`dependency`. A `behavior` requirement reports that host verification is needed.
Static observations cannot establish complete runtime behavior or prove the
absence of callers. Coverage concerns emitted evidence; it does not mean the task
is solved or that prose is correct.

Results preserve a captured basis, citations, qualifiers and every requirement's
gap. Follow-ups contain bounded selectors and reasons for the host to consider.
JSON serialization keeps unclosed source Markdown fences inside their data fields.

## Explicit profiles and work limits

Use `api.load_workflow_profile(FILE)` or pass a `WorkflowProfile`/profile mapping.
The profile schema is `llm-wiki-workflow-profile/v1` with a `settings` object.
Profiles are never discovered automatically. The bundled `native-coding` skill
includes a starting profile; adopt it explicitly with the existing skills lifecycle.

Defaults use native `auto` mode, freshness preference, selected source reads,
estimated counting, 32,000 output tokens, 64 captured inputs, 8 MiB each of source
and wiki inputs, four read rounds and four follow-up proposals. A trusted
`WorkflowPolicy` constrains scopes and limits. Request `options` can choose
per-call settings within those ceilings. Neither profiles nor task text can
change roots, load tokenizer paths, prepare helpers, enable plugins or execute
commands. Source selection and helper configuration remain host arguments.

`snapshot` reads wiki evidence without extracting source. `selected` captures
explicit source coordinates and relevant selection/package/infrastructure inputs.
`full-inventory` requires permission from the host policy and an explicit request.
An empty selection never expands into a full scan. Questions outside the permitted
scope return a gap and a proposed next read.

Request text is limited to 16 KiB, coordinates to 4 KiB, and anchors/requirements
to 100 each. CLI JSON input is limited to 1 MiB and rejects duplicate keys,
unknown fields, unsupported versions and coerced values. CLI input errors exit 2;
workspace errors exit 1; a minimum context that cannot fit exits 3 with no partial
context. Input byte limits apply per capture; validation rereads and parser work
are separate costs.

Source directory discovery is capped at `max(4096, 128 × max_files)` entries,
up to 100,000; wiki discovery is capped at 10,000 entries. Excessive discovery returns an explicit work-limit gap before
source extraction. A narrower source root or an allowed higher limit can help.

Native `required` mode requires availability. It does not require a positive
currentness verdict. Freshness preference does not enable native mode or approve
semantic content.

## Optional compact delivery

Canonical output remains the default. Compact delivery is an explicit
presentation of the same validated facts, gaps, citations and qualifiers.
Save the full canonical receipt outside the source and wiki trees and away
from the request, profile, tokenizer and selection files:

```bash
llm-wiki task-context --request source-task.json --src-dir src --wiki-dir wiki --view compact-v1 --view-budget-tokens 32000 --canonical-output receipts/source-context.json
```

The compact view goes to stdout. Add `--output views/source-context.json` for a
separate view file. A source root of `.` requires both artifacts outside that
entire root; choose destinations accordingly. Redirected paths and overlaps
are rejected. A canonical receipt is host custody, not permission to include
both representations in the model prompt.

```python
view_options = {"schema_version": "llm-wiki-task-view-request/v1", "budget_tokens": 32000}
view = api.build_compact_task_context(
    request, view_options=view_options, src_dir="src", wiki_dir="wiki"
)
if view.ok:
    api.validate_compact_task_context(view.rendered, view.canonical_text, request, view_options=view_options)
    facts = api.expand_compact_task_context(view.rendered, view.canonical_text, request, view_options=view_options)
```

Compact output may still exceed a small budget; there is no promised 1,000-token
fit or fixed percentage saving. If the compact minimum cannot fit, CLI exits 3
with its counted diagnostic, writes the valid canonical receipt when available,
and leaves the view output untouched. If canonical evidence cannot fit, no
receipt is fabricated. Estimated counts remain estimates.

Sessions support explicit `read_compact(..., view_options=...)` and exact
`canonical_receipt(request_id, result_id)` lookup. Configured MCP sessions expose
`read_compact_context_session` and `get_task_context_receipt`. The compact tool
returns view text plus bounded metadata; receipt lookup returns canonical text
separately. Lost, expired or closed custody needs a fresh read. Historical
receipts bind captured bytes; `current=True` requires current revalidation.
Metadata visibility depends on the host. Fetching a receipt and including it
with the compact view can cost more than canonical output alone.

## Counting and MCP delivery

The v3 MCP tool requires `protocol: "llm-wiki-context/v3"` and `changes`, which
accepts explicit paths, a base/head range, or staged changes. Use
`{"mode": "paths", "paths": []}` for no supplied changes. Old MCP context tools and
resource URIs retain their response shapes.

Canonical v3 and task tools return one canonical text block without a structured copy of
the context. Include that text once. Exact counting requires a trusted Python
counter or an explicitly configured server `--tokenizer FILE`; tool input cannot
choose the tokenizer file. Estimated counts remain labeled estimates. Accounting
covers canonical context text, including its accounting fields. MCP and host
framing, session metadata and model-side framing are separate costs.

## Optional sessions and resume

```python
with api.open_context_session(src_dir="src", wiki_dir="wiki") as session:
    first = session.read(request)
    again = session.read(request, if_result_id=first.result_id)
    # Unchanged requires current input validation.
```

Sessions default to eight entries, 16 MiB retained state and a five-minute expiry.
They serialize calls within one instance, return detached data, and bind to their
creating workspace. Changed roots or working directories require a new session.
Close sessions at disconnect or cancellation. Set `reuse=False`, use zero entries,
or use `build_task_context` for cold reads with the same feature coverage.

Source membership and bytes, ignore/selection inputs, wiki artifacts, producer
configuration and Git metadata are rechecked. Events only invalidate state;
lost events cannot authorize reuse. Unsaved buffers require save/defer handling.
Helper-backed captures use cold reads when a complete bounded producer check is
unavailable. No continuous freshness or general speedup is promised.

Session metadata reports reuse, validation work, elapsed time and retained memory
outside the portable task identity. Embedded task work describes its originating
read. Optional deltas require an exact retained base; use
`api.apply_task_delta(base_text, delta, request)` to reconstruct and validate the
full canonical context. Missing bases fall back to a full result. Wrong and
out-of-order bases are rejected. Whole-value array replacement preserves deletions
and changed qualifiers.

MCP sessions require `--enable-sessions`. Handles belong to that server and its
configured workspace. Full responses carry canonical context in text and separate
session metadata in structured content. Delta text is a delta envelope; embedded
accounting describes reconstructed context. Session delivery counters describe
the transmitted context or delta. Reconnect with a fresh session and validate
saved context before reuse.

For a persisted handoff, `api.reconcile_task_context(saved_text, request, ...)`
returns one fresh scoped context together with the input-basis comparison and
the existing packet reconciliation facets. A matching basis and semantic approval
are separate results. Legacy packet reconciliation keeps its existing read scope.

See the [downstream coding example](../examples/native-workflow/README.md) for a
host-owned edit, behavior check, durable explanation and resumed handoff. This
workflow remains opt-in; comparative model benefit has not been established.
