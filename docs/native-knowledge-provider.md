# Integrating native knowledge

Install `agent-wiki-cli` in your application's environment and use
`llm_wiki_cli.api` for native reads. `llm_wiki_cli.api_types` defines their
structured return types. The wheel and source distribution include inline
annotations with the standard `py.typed` marker. Nested extractor or versioned
wire records deliberately use `Any` where the narrower shape belongs to that
separate contract; annotations do not replace runtime validation.

The native consumer compatibility contract covers these public modules and
their documented exports. Importing another service module does not make it
part of this contract. Extension and documentation-controller interfaces have
their own guides. See the Python
[typing distribution specification](https://typing.python.org/en/latest/spec/distributing.html#packaging-type-information)
for how installed annotations are discovered.

## Choose a read operation

| Public operation | Scope and result | Writes |
|---|---|---|
| `bootstrap_wiki(source_root, wiki_root)` | Creates initial deterministic Markdown and native projections; always uses source-adapter behavior | Explicit wiki creation; no agent setup |
| `extract_source(..., deep=True, read_only=True)` | Source inventory with declared extraction scope | No implicit preparation or source edits |
| `inspect_concept(..., live=False)` | One exact concept, typed edges, sections and coverage from a committed snapshot | None |
| `inspect_concept(..., live=True)` | The same bounded result with one live full source capture and final input checks | None |
| `get_knowledge_coverage(..., live=False)` | Eligibility counts; freshness is unevaluated | None |
| `get_knowledge_coverage(..., live=True)` | Eligibility, actual comparisons and modeled freshness | None |
| `build_documentation_query_service(...)` | Captures a live full inventory for several queries within one operation | Read-only by default |
| `get_concept`, `related_concepts`, `list_concept_sections`, `traverse_typed_graph`, `explain_evidence` | Reuse `service=` or construct a live service; preserve each result's qualifiers | Read-only by default |
| `query_documentation(request)` | Exact snapshot queries, supplied-path impact, or explicitly authorized full inventory | None |
| `build_context`, `build_qualified_context` | Bounded source context or a canonical qualified packet | Read-only by default |
| `validate_context_packet`, `compare_context_packet_basis` | Offline structural validation or supplied-basis comparison | None; no live-currentness claim |
| `reconcile_context_packet` | New read against caller-designated roots | None; does not refresh projections |

Only a new live read can evaluate currentness. Reusing a service retains its
captured scope; rebuild it for later work. `required` knowledge mode requires
ready native knowledge, not a positive live-currentness verdict. A successful
unavailable/fallback response is different from a ready model with no matching
concept. Check availability before interpreting `found=False`.

```python
from llm_wiki_cli import api

result = api.inspect_concept(
    "llm-wiki://entities/Item",
    src_dir="src",
    wiki_dir="wiki",
    live=True,
    helper_cache_dir=".cache",
)
assert result["schema_version"] == api.NATIVE_INSPECTION_SCHEMA_VERSION
coverage = result["coverage"]
assert coverage["schema_version"] == api.KNOWLEDGE_COVERAGE_SCHEMA_VERSION
```

Keep availability, source observation, review, verification, analyzer coverage,
and response truncation separate. `current` means the captured observation is
unchanged, not that prose or runtime behavior is correct. Intentionally
unmodeled concepts are not stale concepts. Missing bases remain in the modeled
population. See [native scopes and result bounds](native-knowledge.md#python-api).

## Workspace and process boundaries

The working directory is the allowed workspace boundary. Relative source and
wiki paths are resolved there. An absolute wiki path must remain within that
boundary. `allow_external_src=True` authorizes an external **source** root; it
does not authorize arbitrary wiki roots or weaken symlink containment.

The headless `bootstrap_wiki` writer also requires non-overlapping source and
wiki roots. With a whole-repository source input, place its initial wiki beside
that input in the consumer workspace. With `src/` as the input, a sibling
`wiki/` is suitable. Existing read operations can consume a conventional wiki
inside a repository; this does not relax the headless writer's source protection.

A process can read two projects under a common trusted workspace without
changing its working directory. Pass explicit roots for every operation:

```python
from pathlib import Path
from llm_wiki_cli import api

workspace = Path.cwd()
results = {
    project: api.get_knowledge_coverage(
        src_dir=str(workspace / project / "src"),
        wiki_dir=str(workspace / project / "wiki"),
        live=False,
    )
    for project in ("project-a", "project-b")
}
```

For unrelated workspace roots, launch a separate process with the consumer
project as `cwd`. Do not temporarily change process-wide cwd in a threaded
host. This CLI recipe returns the same coverage contract:

```python
import json
from pathlib import Path
import subprocess
import sys

project = Path("/work/consumer-project")
completed = subprocess.run(
    [sys.executable, "-I", "-m", "llm_wiki_cli.cli", "knowledge", "coverage",
     "--wiki-dir", "wiki", "--format", "json"],
    cwd=project, capture_output=True, text=True, check=True,
)
coverage = json.loads(completed.stdout)
```

Use separate mutable inventory-cache directories for separate projects.
Prepared language helpers may share an explicitly selected, trusted cache.
`--cache-dir BASE` during preparation and `--helper-cache-dir BASE` during reads
refer to the same **base**: helper storage is placed in `BASE/llm-wiki-extractors`.
Prepare dependencies explicitly before a read; unavailable helpers produce an
actionable failure instead of an empty successful inventory.

## Dependencies and optional adoption

The base library requires Python 3.10+ and its declared parsing dependencies.
It does not require an agent configuration, MCP, tokenizers, model-provider
SDKs, or the provider repository's own wiki. Install `[mcp]` for the advertised
stdio or local HTTP server, and `[tokens]` only for exact token counting with a
caller-supplied local tokenizer. External language helpers require their
documented runtimes and explicit preparation.

The [downstream tutorial](../examples/native-knowledge/README.md) demonstrates
bootstrap, qualified reads, source drift, authored follow-up and sync without
agent setup. Add managed agent instructions, durable governance, scoped review
or Site/Obsidian export only when your integration needs them. Existing user
prose and rules remain consumer-owned. Snapshot readers do not initialize or
repair those optional components.
Export writers also enforce a managed wiki's recorded source-selection
boundary. Carry the consumer's source root and profile into an Obsidian export,
even when enriched export uses the committed snapshot without extracting source.

## Producer and reader compatibility

Static scope matters when judging whether a response answers the task:

| Language | Useful boundary |
|---|---|
| Python | Declared signatures, members and supported static model metadata; TypedDict key presence is separate from nullability. Runtime validators and dynamic imports are not executed. |
| TypeScript/JavaScript | Top-level class/interface/type declarations and supported exports; nested namespace members and dynamic initialization can require direct source inspection. A union with `undefined` does not itself make a property optional. |
| Go | Package declarations, receiver identity and supported call observations; function-valued hooks do not imply a statically resolved target. |
| Rust | Parsed declarations and impl associations; `cfg`/feature-dependent declarations do not prove which implementation is active at runtime. An omitted return-type field represents no explicit annotation. |
| Haskell | Module/import/signature and type-oriented declaration inventory; constructor payloads and runtime behavior require additional source evidence. CPP needs an explicitly preprocessed snapshot, with that snapshot's scope and coordinates. |

| Input | Reader behavior |
|---|---|
| Omitted knowledge mode / context v1 | Retains qualified packet v1 behavior |
| Explicit `off`, `auto`, `required` / context v2 | Uses qualified packet v2; no implicit v1 reinterpretation |
| Context v3 accounting envelope | Contains an existing qualified v2 packet; outer accounting is a separate contract |
| Validated surface-only legacy wiki | Explicit absent native knowledge; supported fallback remains available |
| Supported committed native schema | Snapshot reads validate commitments; live reads separately compare the producer/source basis |
| Supported schema from a different producer basis | Snapshot qualification remains distinct from live compatibility; do not assume `current` |
| Unsupported schema or broken commitments | Explicit unsupported/degraded result where a safe fallback exists, otherwise a structured integrity failure |

The inspection and coverage schemas are separate from packet v1/v2 and the
closed aggregate summary. Their public constants are exported by `api`.
Preserve omitted-mode behavior when upgrading an existing consumer; use
explicit `auto` in a native integration that permits fallback.

Upgrade through the owning command: run `sync` with the recorded source
selection and prepared helpers, review its Markdown changes, and rebuild
handoffs. `--rebuild-knowledge` explicitly forces a new projection. Do not edit
generated projection hashes to make incompatible inputs appear current.
Consumers must compare a packet's embedded normalized request with their own
intent before relying on reconciliation. See [qualified packets](qualified-context-packets.md).

## Errors and authority

Catch `api.LlmWikiApiError` or its `InvalidRequestError`, `WorkspaceStateError`
and `ArtifactIntegrityError` subclasses. Native semantic failures expose safe
codes and field details; validated wiki-relative recovery paths may be present.
Raw chained causes are for local debugging. Ordinary Python argument binding,
CLI usage errors and MCP argument-schema errors retain their native boundaries.
See the [native error contract](native-knowledge.md#native-query-failures).

Read-only native queries and packets use built-in source adapters and do not
execute the target application or its project-local plugins. Their static
observations do not establish runtime behavior, authenticated review, or
secret-free publication. The consumer owns decisions to share prose, metadata
and source content or to apply a blocking policy to advisory drift.
