# Follow a source change through qualified knowledge

The question is small: **does the Item documentation still describe the
recorded structure after adding a currency?** You will see when to inspect
source, when to refresh a handoff, and what an unchanged observation can tell
you. The client uses the supported Python API from a separate consumer project.
It does not import the application, install agent instructions, or call a model.

Copy this tutorial's `project/` contents into a fresh directory. Install this
checkout into a `.venv` there, following [working from source](../../docs/wiki-guide.md#working-from-source),
and activate it so `llm-wiki` uses that environment. Keep the tutorial and
installed package at the same revision: the inspection and coverage APIs are
additions to this checkout. On Windows use `.venv\Scripts\python.exe` where
the commands below use `.venv/bin/python`.

## Prepare and inspect

```sh
.venv/bin/python client.py prepare
.venv/bin/python client.py inspect
llm-wiki knowledge coverage --src-dir src --wiki-dir wiki --live
llm-wiki ci-check --src-dir src --wiki-dir wiki --knowledge-drift-report --format json --no-report --no-cache --no-plugins
```

Read `src/catalog.py`: `Item.price_cents` is an integer. The generated
`wiki/entities/Item.md` records that attribute. The inspection reports
`freshness.state: current` and a live comparison. Coverage reports **two modeled
concepts compared**: Item and the catalog module. Navigation, log and dependency
pages are intentionally unmodeled; their count is not a defect count.
Current means the recorded structural observation is unchanged. It does not
approve prose, currency rules, or runtime behavior.

## Capture a handoff

```sh
llm-wiki context --src-dir src --wiki-dir wiki --request expected-request.json --format packet --output output/context.packet.json --read-only
.venv/bin/python client.py check-packet output/context.packet.json
```

The request selects Python context with a 4,000-token inner budget and explicit
native mode `auto`. Packet bytes include additional qualification metadata.
The client validates canonical bytes, compares the embedded normalized request
with its own `expected-request.json`, then reconciles against live inputs.
Offline validation reports freshness **unevaluated**. Reconciliation reports
current bindings here; that result does not approve the packet's prose.
A different valid request is rejected before reconciliation.

## Change and diagnose

```sh
.venv/bin/python client.py change
.venv/bin/python client.py inspect
llm-wiki ci-check --src-dir src --wiki-dir wiki --knowledge-drift-report --format json --no-report --no-cache --no-plugins
.venv/bin/python client.py check-packet output/context.packet.json
```

The controlled edit adds `currency: str = "EUR"` to Item. Open the source and
compare it with the still-recorded Attributes table. Item reports
`source-changed`; the catalog module reports `nonsemantic-source-change`
because its recorded module observation is unchanged even though source bytes
changed. That is not a runtime-equivalence claim.

**The `ci-check` command now exits 1** because its ordinary sync-manifest check
detects the unrefreshed source. Removing `--knowledge-drift-report` gives the
same exit status. Native drift adds warning diagnostics and does not create an
additional blocking gate. The clean check above succeeds with that option.
Review Item's change; an unmodeled page does not need a fabricated freshness model.

The old handoff still validates offline but no longer reconciles as current.
Refresh the handoff before reusing it as current context. The inspection's
`decision` explains why a source/prose review is the next useful step.

## Review and synchronize

```sh
.venv/bin/python client.py follow-up
llm-wiki sync --src-dir src --wiki-dir wiki --no-plugins
.venv/bin/python client.py inspect
llm-wiki ci-check --src-dir src --wiki-dir wiki --knowledge-drift-report --format json --no-report --no-cache --no-plugins
llm-wiki context --src-dir src --wiki-dir wiki --request expected-request.json --format packet --output output/context.packet.json --read-only
.venv/bin/python client.py check-packet output/context.packet.json
```

First read `src/catalog.py`. The follow-up command adds a small authored note
to Item's Description: currency is explicit and prices remain integer minor
units. Synchronization updates the Attributes table and preserves that note.
The next live inspection reports current structural observations and the CI
check succeeds with drift reporting enabled; the new
handoff's bindings reconcile. Review the resulting Markdown yourself.

## Read with limited knowledge

```sh
.venv/bin/python client.py inspect --snapshot
.venv/bin/python client.py unavailable
```

Snapshot inspection does no source extraction and explicitly leaves freshness
unevaluated. Use it for navigation, then request a live read or open source
before making a currentness claim. The second command uses a missing wiki with
mode `auto`: native availability is absent and source context remains available.
It does not create that wiki. Mode `required` would instead require ready native
knowledge.

Optional durable UIDs and scoped reviews can be added with
[knowledge governance](../../docs/native-knowledge.md). They are unnecessary
for this loop. See [packet semantics](../../docs/qualified-context-packets.md)
and [native read scopes and limits](../../docs/native-knowledge.md#python-api)
when integrating the same workflow into another application.
