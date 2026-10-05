# Maintaining documentation

Refresh generated evidence and review affected prose as separate steps. Sync
preserves supported authored content; it does not make that content accurate or
approved. A queue or worklist proposes work and never applies its recommendations.

## Complete the owning loop

Use the repository's actual roots and source-selection profile throughout. For
this repository, with maintenance authorized, preview and run:

```bash
llm-wiki sync --dry-run --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection .llm-wiki/source-selection.json
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection .llm-wiki/source-selection.json
```

Read each reported affected path. Sync owns generated tables, inventories,
diagrams, links and native commitments. Inspect source before surgically editing
supported semantic sections: descriptions, table descriptions and flow Behavior.
Guides and custom index navigation are authored content. Preserve unrelated
pages, generated regions and existing source selection.

After the last canonical Markdown edit, run the same owning sync again before
validation:

```bash
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection .llm-wiki/source-selection.json
llm-wiki lint --strict --profile --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection .llm-wiki/source-selection.json
llm-wiki ci-check --no-report --format json --report-schema v4 --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection .llm-wiki/source-selection.json
llm-wiki knowledge storage-check --wiki-dir docs/llm_wiki --full
```

Run heavy gates serially. Run the configured team gate only when team policy
exists. `ci-check` normally writes a report; this example explicitly chooses
console output with `--no-report`. Review warnings as well as blocking errors.
If a repair edits Markdown, re-anchor with the same sync before validating again.
A failed or unfinished gate leaves maintenance incomplete. Repository rules
still determine whether the wiki may be committed or published.

The [sync adapter](../modules/sync_cmd.md), at
`src/llm_wiki_cli/commands/sync_cmd.py:run`, owns the refresh. The
[semantic worklist](../modules/documentation_worklist.md), at
`src/llm_wiki_cli/services/documentation_worklist.py:build_documentation_worklist`,
prioritizes evidence-backed documentation needs; deferred items remain visible.
It does not establish that unknown or unreviewed prose is complete.

## Optional durable ordinary review

Ordinary maintenance adoption keeps pending work and reviewed source/prose
bindings across sync and restart. It is optional and independent of storage
format and human governance. Do not adopt it merely to make a read succeed.
For a separate coherent example wiki, adoption is an explicit write:

```bash
llm-wiki maintenance adopt --src-dir src --wiki-dir wiki --recovery-dir maintenance-recovery
llm-wiki maintenance status --src-dir src --wiki-dir wiki --format json
```

Keep the recovery directory outside source/wiki. Adoption starts tracked prose
unreviewed and discloses unsupported/untracked coverage. Empty or bounded
records do not mean all documentation is current.

Review an exact record's source and semantic target. After prose edits, sync to
re-anchor the native snapshot and capture status again. Use the actual record
ID and `state_hash`; retain its exact non-null `expected_basis` as `basis.json`:

```bash
llm-wiki maintenance status --src-dir src --wiki-dir wiki --record-id RECORD_UUID --format json
llm-wiki maintenance acknowledge --src-dir src --wiki-dir wiki --record-id RECORD_UUID --expected-state-hash STATE_HASH --basis-file basis.json --actor-kind agent --actor-id documentation-agent
```

Replace the placeholders with that captured record's values. A null basis,
`requires_sync`, later source/prose/state changes or unresolved ownership prevents
current acknowledgment. One record does not acknowledge another section.
Deleted targets and ambiguous moves retain pending work and candidate targets;
never guess an identity from a similar name.

The [maintenance authority](../modules/maintenance_service.md), at
`src/llm_wiki_cli/services/maintenance_service.py:get_maintenance_status_authority`,
and [read-only status projection](../modules/maintenance_status.md), at
`src/llm_wiki_cli/services/maintenance_status.py:build_maintenance_status`,
separate recorded history from effective live needs. Snapshot or selected-header
views remain partial, with no revived current acknowledgment. An ordinary agent
or human actor is not a human governance approval and cannot reactivate an
expired governance review. MCP exposes read-only status and queue, not adoption
or acknowledgment writes.

## Retain complete recovery

The immutable `.llm-wiki-maintenance-adoption.json` marker belongs with its
matching manifest state, projections and referenced objects. A missing/corrupt
adopted owner must be recovered before sync, bootstrap or manifestless seeding.
Current pages cannot reconstruct historical authority.

For adoption using the example directory above, restore the actual retained
complete snapshot and adoption identity:

```bash
llm-wiki maintenance recover --wiki-dir wiki --recovery-dir maintenance-recovery/committed --expected-adoption-id ADOPTION_UUID
```

Use the actual ID, never an invented replacement. Recovery refuses newer
committed work and ineligible preimages. Explicit captured-preimage recovery can
restore authored bytes not yet anchored by native projections; its result
requires owning sync before current review. Storage migration recovery is a
different operation, and a single knowledge export is not a complete adopted
authority bundle. Preserve the repository's chosen storage format and authored
regions throughout.
