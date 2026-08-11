# Durable knowledge governance

Read this topic only when a repository owner explicitly asks to adopt or
change durable knowledge identity, aliases, lifecycle, human review, or machine
verification, or when an existing ledger must be recovered. It owns durable
ledger mutation and recovery. Ordinary bootstrap, sync, lint, context, query,
status, export, fallback, and repair paths never initialize governance.

This topic does not authorize a governance action, checker execution, source or
wiki edit, Git operation, backup destination, network operation, or plugin. The
user and applicable repository policy must authorize each operation and its
scope.

## Generated projection versus authoritative ledger

Without `.llm-wiki-governance.json`, current locators and canonical paths are
compatible coordinates but are not durable identities. Missing governance does
not block ordinary generated knowledge reads; consumers continue using exact
locators and canonical paths with their reported qualification.

The governance ledger is non-rebuildable authority for bundle identity, UID
allocation, aliases, lifecycle events, and human review. Its joined extension
in `.llm-wiki-knowledge.json` is a disposable projection and cannot recover or
replace the ledger. `.llm-wiki-verification.json` is a separate disposable
machine receipt.

Normally protect the ledger through repository-policy-permitted version
control. For an intentionally local-only wiki, require an owner-approved
durable backup and recovery path before adoption; do not unignore or force-add
the ledger. Apply the exact delivery decision in
[Repository handoff](repository-handoff.md).

## Explicit adoption

Adopt governance only after a complete, valid, knowledge-capable snapshot
exists and the owner has separately confirmed the durable storage plan. Preview
before applying:

```bash
llm-wiki knowledge init --wiki-dir docs/llm_wiki --dry-run
llm-wiki knowledge init --wiki-dir docs/llm_wiki
llm-wiki knowledge status --wiki-dir docs/llm_wiki --format json
```

Initialization is never setup for knowledge consumption and never a repair for
absent, degraded, unsupported, invalid, mixed, stale, source-changed, bounded,
or analyzer-limited evidence.

All governance mutations support `--dry-run`, validate an unchanged persisted
snapshot, use a compare-and-swap ledger write, and reject ownership or event
conflicts instead of selecting a winner. Public actions are deliberately
narrow:

- `knowledge init` adopts governance;
- `knowledge status` reads bounded lifecycle and review history;
- `knowledge move` changes a current locator or natural key;
- `knowledge alias` records one historical coordinate;
- `knowledge lifecycle set` authors an allowed lifecycle state;
- `knowledge deprecate` and `knowledge supersede` are lifecycle shortcuts;
- `knowledge review` records one digest-bound human section event; and
- `knowledge verify` runs selected application-owned machine checkers.

None is an implicit side effect of a read, generation, validation, export, or
maintenance operation.

## Moves, aliases, and allocation conflicts

Supported unambiguous sync or migration renames carry the UID automatically
and retain old locator and natural-key coordinates as aliases. Do not duplicate
that move manually. Before the first mutating sync in a governed wiki, preview
the filesystem/source rename with the same source root and source-selection
profile used by the owning maintenance loop, then inspect the joined state:

```bash
llm-wiki sync --dry-run --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
llm-wiki knowledge status --wiki-dir docs/llm_wiki --format json
```

Use the preview evidence rather than filename similarity:

| Preview evidence | Identity action before mutating sync |
| --- | --- |
| One prior route maps unambiguously to one new route and the target is unowned | Let sync or migration carry the UID and retain both old coordinates as aliases. Do not stage a duplicate manual move. |
| One prior route fans out to multiple targets | Stop and obtain an owner decision. Preview one exact move only after the owner identifies which target, if any, is the same logical concept. |
| Multiple prior concepts claim one target | Reject the implicit merge. Preserve every allocation and require distinct targets or a separately authorized redesign. |
| The target locator or natural key is already owned by another UID | Treat it as `governance-allocation-conflict`; do not overwrite, reallocate, reinitialize, or use force. |
| A source/page disappeared without continuity evidence | Retain its allocation and lifecycle. A generated surface notice never authors native deprecation, supersession, or deletion. |
| The ledger is missing while the manifest or projection commits governance | Stop before page mutation and restore the exact ledger from version control or its approved backup. Never initialize or reconstruct it from the projection. |

For an ambiguous manual rename, the order is filesystem/source rename, sync
dry-run, `knowledge status`, dry-run move, governance-owner confirmation, real
move, and immediate owning sync. Use the read-only evidence to identify the
candidate existing UID and target, then preview that exact move:

```bash
llm-wiki knowledge move \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --to-locator llm-wiki://modules/accounts-renamed \
  --to-natural-key source-module:modules/accounts-renamed.md \
  --dry-run
```

After the preview succeeds, obtain the governance owner's confirmation that
the existing UID represents the same logical concept, the target is unowned,
and this is a move rather than a delete/recreate or merge. After confirmation,
apply the same move and run the owning sync immediately:

```bash
llm-wiki knowledge move \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --to-locator llm-wiki://modules/accounts-renamed \
  --to-natural-key source-module:modules/accounts-renamed.md
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
```

The applied move may report `projection: pending-sync`. Between that move and
the owning sync, readers reject the expected ledger/projection mismatch until
sync restores parity. A coordinate already owned by another UID is a hard
conflict. Preserve every allocation; never merge, overwrite, delete,
reallocate, reinitialize, or use `--force` to choose a winner.

Add a historical coordinate without moving the current allocation:

```bash
llm-wiki knowledge alias \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --type locator \
  --value llm-wiki://modules/legacy-accounts \
  --dry-run
```

## Lifecycle, review, and verification

Lifecycle is authored independently of source and evidence state. Source or
page disappearance does not deprecate, supersede, or delete a concept. A
supersession names a different existing successor UID and produces a
governance-origin typed edge:

```bash
llm-wiki knowledge lifecycle set \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --state active \
  --actor-kind human \
  --actor-id maintainer.example \
  --authored-at 2026-07-27T12:00:00Z \
  --dry-run
llm-wiki knowledge supersede \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --successor-uid lw:module:fedcba9876543210fedcba9876543210 \
  --actor-kind human \
  --actor-id maintainer.example \
  --authored-at 2026-07-27T12:30:00Z \
  --dry-run
llm-wiki knowledge deprecate \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --actor-kind human \
  --actor-id maintainer.example \
  --authored-at 2026-07-27T13:00:00Z \
  --dry-run
```

Human review binds a real human actor to one exact semantic section locator
and its scoped hash/evidence basis. Agent review cannot satisfy it.
Generated-only churn can preserve an event; changed scope, evidence, basis, or
a missing section/concept expires it with every reason retained:

```bash
llm-wiki knowledge review \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --section 'llm-wiki://modules/accounts#section/accounts%20Module~1/Description~1' \
  --reviewer-kind human \
  --reviewer-id reviewer.example \
  --method manual-review \
  --method-version 1 \
  --authored-at 2026-07-27T13:00:00Z \
  --dry-run
```

Machine verification is separate and explicit:

```bash
llm-wiki knowledge verify \
  --wiki-dir docs/llm_wiki \
  --checker artifact-integrity \
  --checker internal-links \
  --dry-run
```

Only that command may run registered checkers. Reads and lint validate an
existing receipt against its selected scope, hashes, governance input, and
checker versions; they do not rerun it or turn it into human review, truth, or
approval. Stored checker names are inert and cannot select executable code.

## Loss and recovery

Resolve ledger conflicts manually while preserving every allocation and every
non-conflicting event. Give each UID, current coordinate, and alias exactly one
owner, and resolve lifecycle forks explicitly. Then run the owning sync and
`knowledge status`.

If a governed manifest or projection exists but the ledger is missing, stop
governance-dependent mutation and restore the exact
`.llm-wiki-governance.json` from version control or the approved backup. Never
reconstruct it from the generated projection, initialize a replacement, or
infer ownership from filenames. If only generated artifacts or a machine
receipt are damaged, retain the ledger and regenerate disposable state through
its owning command.
