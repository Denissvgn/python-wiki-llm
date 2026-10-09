# Ordinary documentation review

Source synchronization refreshes generated structure and preserves authored
prose. It does not approve that prose. Ordinary maintenance records keep the
sections that still need review across synchronization and restarts.

This is useful when source implementation changes but the generated declaration
structure stays the same. Supported Python executable syntax observations can
identify that drift. An unchanged scoped syntax digest does not establish
unchanged dependencies or runtime behavior, and unavailable evidence remains
explicitly unavailable.

## Adopt review tracking

Start with a coherent wiki produced by bootstrap or sync. Adopt maintenance
explicitly and retain its recovery directory outside both the source directory
and the wiki:

```bash
llm-wiki maintenance adopt --src-dir src --wiki-dir docs/llm_wiki \
  --recovery-dir ../wiki-maintenance-recovery
llm-wiki maintenance status --src-dir src --wiki-dir docs/llm_wiki
llm-wiki queue --src-dir src --wiki-dir docs/llm_wiki
```

The queue is advisory. Its JSON `qualification.ordinary_review_custody` reports
`availability`, `durable_owner_available` and `live_evaluation_performed`.
Partial, unadopted or unavailable custody does not establish completed review.
Even a ready status or an empty queue proves neither source/prose correctness nor
ordinary-review completion. Inspect the affected source and prose, then use the
exact status and acknowledgment route below for adopted records.

Adoption starts existing tracked prose as unreviewed. It preserves generated
Markdown and existing human governance. The immutable
`.llm-wiki-maintenance-adoption.json` marker and the manifest's typed maintenance
state belong together. Keep those files, the committed projections and any
indexed catalog objects intact. Flat maintenance manifests use version 7;
indexed maintenance manifests use version 8. Unadopted wikis retain their
existing format. Use `--manifest-format indexed-v8` when explicitly adopting an
indexed maintenance owner.

## Review and acknowledge an exact section

Status identifies records by a stable ID and an exact page/section target. It
shows recorded review history separately from effective current review needs.
Review the source and authored semantic section; preserve generated regions.
After editing prose, run sync to re-anchor the native snapshot before
acknowledgment:

```bash
llm-wiki sync --src-dir src --wiki-dir docs/llm_wiki
llm-wiki maintenance status --src-dir src --wiki-dir docs/llm_wiki \
  --record-id RECORD_UUID --format json > review.json
```

The returned `state_hash` commits the captured authority. The selected record's
`expected_basis` binds the current source, executable syntax, documentation,
producer and exact prose/target. If it is null or status says `requires_sync`,
acknowledgment is unavailable. Resolve the stated gap and capture status again.

Keep captured status and basis files outside both actual source and wiki roots.
Save that exact basis object to `basis.json`, then acknowledge it with an
explicit actor:

```bash
jq '.records[0].expected_basis' review.json > basis.json
llm-wiki maintenance acknowledge --src-dir src --wiki-dir docs/llm_wiki \
  --record-id RECORD_UUID --expected-state-hash STATE_HASH \
  --basis-file basis.json --actor-kind agent --actor-id documentation-agent
```

Use the actual record ID and state hash from `review.json`. A source/prose/state
change after capture rejects stale acknowledgment. Repeating the same successful
acknowledgment with the same actor and reviewed basis is idempotent. Later
relevant edits reopen review. Reviewing one section does not acknowledge another
section sharing its source.

An ordinary `agent` or `human` actor records operational review. It grants no
human governance approval and cannot reactivate an expired human review.
Deleted targets and ambiguous moves remain pending with their retained identity
and candidate targets; acknowledgment does not guess a replacement owner.

`maintenance status --snapshot` reports historical recorded review only. It does
not claim that an acknowledgment still matches current source or prose. Output
is bounded; select an exact record to obtain its current basis when the broader
listing is truncated. Read-only status, context, inspection and MCP calls do not
acknowledge work.

## Python and MCP

The supported Python operations share the command behavior:

```python
from llm_wiki_cli import api

status = api.get_maintenance_status("src", "docs/llm_wiki", record_id=record_id)
record = status["records"][0]
api.acknowledge_maintenance(
    "src", "docs/llm_wiki",
    record_id=record["record_id"],
    expected_state_hash=status["state_hash"],
    expected_basis=record["expected_basis"],
    actor_kind="agent",
    actor_id="documentation-agent",
)
```

Check that `expected_basis` is available before calling. Adoption and recovery
are `api.adopt_maintenance` and `api.recover_maintenance`. MCP exposes
`get_maintenance_status` and the existing `get_maintenance_queue` as read-only
tools. Explicit local CLI/Python operations perform adoption, acknowledgment and
recovery.

## Recover complete authority

A missing/corrupt owner or mismatched marker requires a verified complete
snapshot. Ordinary repair never rebuilds history from the latest projection.
Restore only the expected adoption identity:

```bash
llm-wiki maintenance recover --wiki-dir docs/llm_wiki \
  --recovery-dir ../wiki-maintenance-recovery/committed \
  --expected-adoption-id ADOPTION_UUID
```

Use the actual directory containing a retained complete recovery snapshot.
Recovery refuses newer committed work and edits outside its eligible preimage.
`--allow-prepared-adoption` is an explicit retry of an interrupted prepared
adoption and requires its original source basis via `--src-dir`.
`--allow-captured-preimage` restores an explicitly selected captured preimage
that may contain authored bytes not yet anchored by native projections. Its
result reports `requires_sync: true` and `prose_basis_validated: false`; run sync
before using it for current review or acknowledgment. Recovery does not assert
runtime/source currentness.

Standalone single-file knowledge export is unavailable after maintenance
adoption because it omits authoritative history. Preserve a complete authority
bundle instead. There is no automatic downgrade or de-adoption.

[Command reference](cli-reference.md) · [Wiki guide](wiki-guide.md) ·
[Native knowledge reads](native-knowledge.md)
