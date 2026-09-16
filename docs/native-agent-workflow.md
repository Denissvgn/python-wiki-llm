# Native coding workflow

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

## Declare evidence requirements

```python
from llm_wiki_cli import api

request = {
    "schema_version": "llm-wiki-task-request/v1",
    "text": "Inspect the configured retry count.",
    "kind": "bug-diagnosis",
    "requirements": [
        {"id": "retry-contract", "facet": "source-contract",
         "selector": "retry.py:retry"}
    ],
}
result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
if result.ok:
    payload = api.validate_task_context(result.rendered, request)
    print(payload["coverage"])
```

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

## Counting and MCP delivery

The v3 MCP tool requires `protocol: "llm-wiki-context/v3"` and `changes`, which
accepts explicit paths, a base/head range, or staged changes. Use
`{"mode": "paths", "paths": []}` for no supplied changes. Old MCP context tools and
resource URIs retain their response shapes.

V3 and task tools return one canonical text block without a structured copy of
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
