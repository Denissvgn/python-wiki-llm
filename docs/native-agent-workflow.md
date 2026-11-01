# Native coding workflow

Initialized projects receive a default development procedure through their
managed agent instructions: define acceptance criteria, gather scoped evidence,
inspect source, make bounded changes, verify independently, refresh affected
knowledge, and preserve a qualified handoff. The managed
`wiki-reference/references/development-workflow.md` topic owns that procedure;
expanded instructions retain it when skills are disabled or unavailable.
Package installation ships the reference; `llm-wiki init` establishes the
project instructions, and `llm-wiki upgrade` refreshes them after a package update.

The library selects current data and workflow contracts. Normal task and compact
view requests omit version fields. Bootstrap creates compressed packed knowledge
and indexed ordinary maintenance ownership; project upgrade brings valid older
snapshots forward with recovery preimages. Review starts pending and never
implies human approval. Readers never migrate or repair data.

Canonical delivery stays the default. Compact delivery, session reuse and source
indexing remain explicit behavior choices with their own bounds and costs. MCP
session tools are available by default; opening a session is still explicit.
Workflow profiles, human governance, application execution and Git actions keep
their existing authorization requirements. Older explicit contracts remain
available for integrations that require compatibility.

An explicit task request gathers qualified source and wiki evidence. The provider
reads and reports; your coding host decides what to include, edit, execute and
publish.

## Install the workflow in another project

Run the following commands from the target project's root, using its own
Python 3.11+ virtual environment at `.venv/`. Package installation supplies the
CLI and bundled workflow; initialization writes the project-specific agent
instructions and wiki scaffold.

For a released package that includes the default development workflow:

```bash
.venv/bin/pip install agent-wiki-cli
.venv/bin/llm-wiki init --agent generic
```

To use a source checkout, including changes that have not been published,
install that checkout instead. Replace the quoted path with its absolute
location; keep running commands from the target project:

```bash
.venv/bin/pip install "/absolute/path/python-wiki-llm"
.venv/bin/llm-wiki init --agent generic
```

Choose the agent's instruction format with `--agent`:

| Agent target | Project instruction file | Managed reference directory |
|---|---|---|
| `generic` | `AGENTS.md` | `.llm-wiki/skills/wiki-reference/` |
| `claude` | `CLAUDE.md` | `.claude/skills/wiki-reference/` |
| `cursor` | `.cursorrules` | `.llm-wiki/skills/wiki-reference/` |
| `copilot` | `.github/copilot-instructions.md` | `.llm-wiki/skills/wiki-reference/` |
| `aider` | `.aider.conf.yml` | `.llm-wiki/skills/wiki-reference/` |
| `opencode` | `.opencode/instructions.md` | `.llm-wiki/skills/wiki-reference/` |

Use `generic` for Codex or another agent that reads `AGENTS.md`. Initialization
preserves existing user instructions outside the managed block and installs
`references/development-workflow.md` within the managed reference directory.
Start a new agent session, or reload its project instructions, so it reads the
workflow. The default procedure is available without separately installing the
optional `native-coding` skill.

The default wiki scaffold is `docs/llm_wiki/`. To choose another location, pass
`--wiki-dir .wiki` to initialization and keep that same path in subsequent
commands. Initialization creates the scaffold; bootstrap populates the wiki
from the project's sources:

```bash
.venv/bin/llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki
```

Use the actual source root and configured source selection. For languages that
need extractor helpers, install the relevant toolchain and explicitly prepare
the helpers with `init --prepare-extractors` or
`llm-wiki prepare-extractors --src-dir .`; see
[helper setup](cli-reference.md#prepare-extractors). Source-only task evidence
can be used before bootstrap, following the [source-only route](#source-only-task-without-a-wiki).

### Use the inline fallback

For an agent or project that needs instructions in a single file, skip the
managed reference installation:

```bash
.venv/bin/llm-wiki init --agent generic --no-skills
```

This writes expanded, self-contained instructions, including the development
procedure, into the selected agent instruction file. It records the preference
for later initialization and upgrades. An existing reference directory is
preserved, and read-only context interfaces remain available. Initialization
and upgrade also use expanded instructions when the managed reference is
unavailable or cannot be verified current.

### Upgrade an initialized project

Update the package in the target project's environment, then refresh its
managed instructions from that project's root:

```bash
.venv/bin/pip install --upgrade agent-wiki-cli
.venv/bin/llm-wiki upgrade
```

For a source checkout, replace the package update command with
`.venv/bin/pip install --upgrade "/absolute/path/python-wiki-llm"`. Package
updates alone do not refresh project instructions or migrate project data. For a custom wiki location,
use `.venv/bin/llm-wiki upgrade --wiki-dir .wiki`.

Upgrade selects current storage formats and workflow contracts automatically.
It preserves authored Markdown and existing governance, retains complete recovery
preimages and prints their locations. Preserve those copies until the upgraded
project is accepted. Damaged or unsupported authority requires recovery rather
than automatic reseeding. Use `--src-dir src` when the source root is `src`, and
carry the configured helper cache and source selection through setup.

Upgrade retains the configured agent, source-selection preference and skills
preference unless explicitly overridden. It refreshes the managed instruction
block, reference topics and missing scaffold structure while preserving user
instructions outside the managed block and existing wiki prose. When references
are enabled, expected managed topic files are replaced even if edited locally;
keep project-specific rules outside that tree or back up edits before upgrading.
Conflicting or unsafe entries are preserved and reported. See the
[managed skills lifecycle](cli-reference.md#skills) for recovery details.

To change the instruction format, use `upgrade --agent claude` or another
supported target. To change the skills preference explicitly:

```bash
.venv/bin/llm-wiki upgrade --no-skills
.venv/bin/llm-wiki upgrade --skills
```

The first command selects inline instructions; the second restores managed
references and compact routing when verification succeeds. Choose the command
for your desired mode, then reload the agent's project instructions.

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
queue is advisory and never applies recommendations. Read its
`qualification.ordinary_review_custody` availability, owner and live-evaluation
fields before relying on ordinary-review history. Partial, unadopted or
unavailable custody remains a gap. Even a ready status or an empty queue does
not establish source/prose correctness or review completion; inspect the exact
source and prose and follow [ordinary review tracking](maintenance.md) when needed.

Ranked search weights informative terms and semantic sections, keeps exact page
and declaration matches before fuzzy candidates, and labels relaxed matches for
longer queries. The default `ranked` mode and explicit `ranked-v2` mode use
`ranking_version: "llm-wiki-search/lexical-v2"`. `--mode ranked-v1` retains
the earlier ranking policy;
`--mode substring` performs literal text matching. All results remain discovery
candidates and require exact inspection before a coding decision.

Source text indexing is an explicit read and cost choice:

```bash
llm-wiki search "retry failure" --src-dir src --wiki-dir wiki --include-source
```

It requires a valid committed manifest and indexes only its mapped module sources
inside the captured selection. Source snapshot validation and source-byte
rechecks have separate costs; snippets can include static code or error-message text without proving
runtime behavior. Narrow the selection when the declared indexing bounds cannot
fit. Reads never execute the application, install helpers or migrate storage.

To connect a symptom query to exact inspection, request qualified discovery:

```bash
llm-wiki search "retry failure" --src-dir src --wiki-dir wiki --discovery qualified-v1
```

The additional `discovery` response groups the returned candidates by validated
owner and retains each page and distinct narrative section. Groups cover only
the returned results; section omissions and limits remain explicit. Recorded
source and review information describes the captured state. It does not establish
live freshness, runtime behavior, semantic correctness or current approval.
Pending and contradictory prose remain visible as separate evidence.

Select a candidate explicitly, then pass its exact `path` to
`api.inspect_concept(path, src_dir="src", wiki_dir="wiki", live=False)`.
Continue with the resolved locator only when that response identifies one
concept. Missing, ambiguous or unavailable outcomes require investigation;
another fuzzy result cannot replace the selected identity automatically.
Use the resolved exact source, concept and section anchors in the native task
request below. Its compact view preserves unresolved requirements and bounds.

Qualified discovery uses bounded selected native reads where supported.
A wiki without committed native storage, or a valid unsupported layout within
the capture bounds, leaves
an explicit unavailable qualification and does not authorize adoption or
migration. Exceeding capture or output bounds aborts the read, as does missing
or inconsistent committed authority. Plain Markdown
pages can still be read by exact path. Discovery's recorded pending review is a
separate capture: selected task context reports its own maintenance scope and
may leave current review state unavailable. When review status is decisive,
re-read the corresponding record with `api.get_maintenance_status(...,
record_id=record_id, live=False)`; request a live status separately when an
actual current comparison is needed.

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

<a id="native-task-with-explicit-storage-adoption"></a>

## Native task with current storage

Choose this route when a requirement needs committed concepts, semantic
sections or typed relationships. Authorized bootstrap selects current bounded
storage without a format argument:

```bash
llm-wiki bootstrap --src-dir src --wiki-dir wiki
```

For an existing project, update the package in every reader/writer environment,
then run the authorized project upgrade with its actual roots:

```bash
llm-wiki upgrade --src-dir src --wiki-dir wiki
llm-wiki knowledge storage-check --wiki-dir wiki --full
llm-wiki doctor --capabilities --src-dir src --wiki-dir wiki --format json
```

Upgrade chooses current formats and reports complete recovery locations. An
explicit compatibility-format migration remains available through
[knowledge storage](knowledge-storage.md). Missing, damaged or unsupported
committed authority requires recovery; a failed read never authorizes migration.

Save this native snapshot request as `native-task.json`:

```json
{
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

Current bootstrap and upgrade also establish pending
[ordinary review tracking](maintenance.md), separate from human governance. A
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

Python method callers can resolve through uniquely justified local constructors,
assigned constructor instances and explicit imported class aliases. Factories,
shadowed/conflicting bindings, receiver mutations and uncertain loop or exception
paths stay located unresolved evidence. Captured module, class and receiver
namespace mutations can invalidate a target. Resolution uses lexical scope and
captured evaluation order, including conditional and short-circuit expressions.
Inspect exact source before relying on
a candidate; neither a missing edge nor a non-truncated response proves runtime
completeness.

Source bytes, recorded declaration structure and captured Python executable
syntax are separate observations. A body or default edit can change executable
syntax while an unrelated declaration remains unchanged. Matching syntax does
not prove behavior, dependency stability or authored prose correctness. Other
languages and legacy artifacts may lack executable comparison evidence. The
legacy `nonsemantic-source-change` value means “Source changed; recorded
structure unchanged; behavior not evaluated.” Review tracking requires its own
explicit adoption; an untracked review state does not mean approval.

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
llm-wiki task-context --request source-task.json --src-dir src --wiki-dir wiki --view compact --view-budget-tokens 32000 --canonical-output receipts/source-context.json
```

The compact view goes to stdout. Add `--output views/source-context.json` for a
separate view file. A source root of `.` requires both artifacts outside that
entire root; choose destinations accordingly. Redirected paths and overlaps
are rejected. A canonical receipt is host custody, not permission to include
both representations in the model prompt.

```python
view_options = {"budget_tokens": 32000}
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

The budgeted MCP tool uses the current context contract when `protocol` is
omitted. It requires `changes`, which accepts explicit paths, a base/head range,
or staged changes. Use
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

MCP sessions are available by default; `--disable-sessions` removes their tools. Handles belong to that server and its
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
