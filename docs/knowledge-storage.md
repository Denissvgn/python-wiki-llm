# Knowledge storage

Native knowledge supports the original JSON file (`v1`), indexed JSON objects
(`sharded-v2`), or indexed ZIP packs (`packed-v3` and `packed-v4`). Existing wikis keep their
format. New wikis use v1 unless you select another format.

Sharded storage keeps a small `.llm-wiki-knowledge.json` root and JSON objects in
`.llm-wiki-knowledge/objects/`. Commit the root, referenced objects, surface index
and sync manifest together. A normal checkout needs neither Git LFS nor a rebuild
to read that snapshot.

Markdown and `.llm-wiki-governance.json` remain the authority for authored content,
stable identity and review history. Storage migration preserves them.

## Choose a format for a large repository

| Format | Use it when |
|---|---|
| `sharded-v2` | You want bounded JSON files that ordinary text tools can inspect. |
| `packed-v3` | You want fewer checked-out files while Git handles repository compression. |
| `packed-v3-deflate` | You also want compressed files in the working directory. |
| `packed-v4` | You want finer routing and smaller writes, with more data packs than v3. |
| `packed-v4-deflate` | You want that finer layout with individually compressed members. |

Both packed profiles contain the same logical knowledge. `packed-v3` uses
uncompressed ZIP members (`ZIP_STORED`); `packed-v3-deflate` compresses members
individually. Packs grow toward 4 MiB and have an 8 MiB hard ceiling, including
archive headers. Large collections split into additional packs. An individual
record that cannot fit is reported before publication.

The opt-in v4 `local-v1` profile targets 1 MiB data packs, with the same 8 MiB
hard ceiling. Its locator leaves contain at most 24 rows. Small index pages
share content-addressed containers of at most 1 MiB under
`.llm-wiki-knowledge/index-pages/`; readers fetch committed page ranges directly.
This avoids a separate file for every small locator page. Full audits verify
every container and its exact page membership. Selected reads verify only the
pages and members they consume. A record may exceed the pack target while
remaining within the hard ceiling.

The root stays at `.llm-wiki-knowledge.json`. Packed data lives in
`.llm-wiki-knowledge/packs/`, with bounded routing files in
`.llm-wiki-knowledge/pack-index/`. Commit all referenced files and companion
artifacts together. Readers access selected members directly; no extraction,
external database, network service or Git LFS is required.

Git normally displays ZIP changes as binary changes. Use the logical inspection
and comparison commands below to review the underlying records. Compression
savings and update costs depend on the data and the breadth of each change.

## Adopt packed storage

Upgrade every reader and writer to support `llm-wiki-knowledge/v3` before adoption.
Migration accepts either an existing v1 wiki or an adopted v2 wiki:

```sh
llm-wiki knowledge migrate --wiki-dir docs/llm_wiki --to packed-v3 --dry-run
llm-wiki knowledge migrate --wiki-dir docs/llm_wiki --to packed-v3
```

Use `--to packed-v3-deflate` to select compressed members explicitly. On projects
without Git, supply a recovery directory outside the wiki. You can return to
indexed JSON through `--to sharded-v2`; recovery and v1 export also remain
available. Migration preserves a verified recovery snapshot and does not remove
old generated files. Preview and apply `prune-storage` after a successful
migration to remove obsolete objects and packs.

Generation can adopt either packed profile directly:

```sh
llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki --knowledge-format packed-v3
llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --knowledge-format packed-v3-deflate
```

Subsequent owning writes preserve the chosen profile. A missing or invalid packed
root requires recovery or an explicitly selected rebuild format.

For finer routing, upgrade all readers and writers to support
`llm-wiki-knowledge/v4`, then adopt it explicitly:

```sh
llm-wiki knowledge migrate --wiki-dir docs/llm_wiki --to packed-v4-deflate --dry-run
llm-wiki knowledge migrate --wiki-dir docs/llm_wiki --to packed-v4-deflate
```

The same values are accepted by `bootstrap --knowledge-format` and
`sync --knowledge-format`. V3 remains available with its original layout.

## Keep manifest reads small

Manifest v6 stores artifact commitments and small generation policy in
`.llm-wiki-manifest.json`. Large source, evidence and page-mapping fields live in
bounded catalogs under `.llm-wiki-manifest/objects/`. The commit root and every
catalog have a 64 KiB ceiling. Large policy values also use committed catalogs;
reading them still counts against the request's byte budget.

Upgrade every reader and writer to support manifest v6, then adopt it explicitly:

```sh
llm-wiki knowledge migrate --wiki-dir docs/llm_wiki --to indexed-v6 --dry-run
llm-wiki knowledge migrate --wiki-dir docs/llm_wiki --to indexed-v6
```

This setting is independent of the knowledge pack profile. Full readers recover
all manifest entries; selected queries read the commit header and policy.
Generation, governance and review writes preserve adoption and publish the
manifest last. Commit its referenced catalogs alongside the other artifacts.
Older manifest writers reject version 6. A conflicted v6 root requires restoring
one complete committed root before sync can rebuild it.

Unchanged packed members and compatible compressed bytes can be reused during
generation. Global logical hashing and complete validation still run where
required. Compression profile changes explicitly invalidate compressed reuse.

## Review logical changes

Inspect records independently of their physical storage format:

```sh
llm-wiki knowledge inspect-storage --wiki-dir docs/llm_wiki --limit 100
llm-wiki knowledge diff-storage --wiki-dir docs/llm_wiki \
  --against-wiki ../before/docs/llm_wiki --limit 100
```

The comparison takes another complete wiki snapshot, such as one in a separate
Git worktree. Both commands validate the committed inputs and emit JSON with
logical record identities, hashes and available values. `--max-bytes` bounds the
output; omitted records or values are counted explicitly. A storage-only
migration produces no logical differences.

For a bounded selected read, supply a selector explicitly:

```sh
llm-wiki knowledge inspect-storage --wiki-dir docs/llm_wiki \
  --selector page:modules/app.md --limit 10
```

This mode reports `selected-records-and-policy`; unread records and companion
authority remain unverified. Without a selector, inspection validates the full
snapshot even when `--limit` is small.

## Adopt sharded storage

Use a provider that supports `llm-wiki-knowledge/v2` for every application that
reads or writes the wiki. Older writers must be upgraded before adoption.

Preview an existing wiki:

```sh
llm-wiki knowledge migrate --wiki-dir docs/llm_wiki --to sharded-v2 --dry-run
```

Apply the migration:

```sh
llm-wiki knowledge migrate --wiki-dir docs/llm_wiki --to sharded-v2
```

In a Git repository, the recovery copy defaults to Git's metadata directory.
For a project without Git, provide an empty recovery directory outside the wiki:

```sh
llm-wiki knowledge migrate --wiki-dir wiki --to sharded-v2 --recovery-dir ../wiki-recovery
```

The command validates the original snapshot, preserves its recovery bytes and
compares the reconstructed knowledge before committing the new format. Repeating
an unchanged migration makes no artifact changes. A read never migrates a wiki.

You can also select the format during generation:

```sh
llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki --knowledge-format sharded-v2
llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --knowledge-format sharded-v2
```

Subsequent sync, governance and review updates preserve the adopted format when
the option is omitted.

## Inspect size and integrity

```sh
llm-wiki knowledge storage-check --wiki-dir docs/llm_wiki
llm-wiki knowledge storage-check --wiki-dir docs/llm_wiki --full
```

Quick reporting inspects sizes and identifies pointer-only LFS files. It does
not claim that the complete snapshot is valid. `--full` validates all referenced
objects, native records, routing and current Markdown; it also identifies
unreferenced objects. Both commands return JSON and use a nonzero exit status for
failed checks.

`storage-check --stream` audits every referenced storage object, native record
shape, logical commitment, reference and routing membership using private spill
files. It reports `complete-storage-and-routing`. Surface/Markdown/governance
authority and complete native projection parity require `--full`.

The streaming mode limits each expanded record to 1 MiB, each alias group to
8 MiB, each spill index to 16 MiB of charged key metadata, and each spill file to
2 GiB of writes. Merge batches use 1 MiB and at most 32 input handles. Decoder
caches are bounded separately; process memory also includes decoded JSON and
the bounded physical routing tables. Exceeding a limit produces an explicit
failure. Private files are removed when the operation ends or is cancelled.

To include the size policy in an existing report, use `ci-check --storage-check`.
Optional `--storage-git-base` and `--storage-git-head` add the explicit Git range
check to that same report. Neither command installs hooks or changes Git state.

The sharded root is limited to 256 KiB, with an 8 MiB ceiling per object. Objects
normally use smaller targets to keep selected reads bounded. An oversized record
is reported explicitly; its evidence is never silently truncated. Companion
surface/manifest files remain subject to size checks and caller read budgets.

## Check the commits you intend to push

Specify both ends of the outgoing range; no upstream or default branch is inferred:

```sh
llm-wiki knowledge storage-check --wiki-dir docs/llm_wiki \
  --git-base origin/main --git-head HEAD
```

The range check examines Git blob sizes, including intermediate versions deleted
from the latest tree. It warns above 50 MiB and fails at 95 MiB, leaving room below
GitHub's 100 MiB limit. It reports object IDs and sizes, performs no fetch or push,
and rejects incomplete or partial-clone object databases. These limits apply to
uncompressed Git objects. [GitHub's file-size guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

Splitting the current file does not remove an oversized blob from outgoing
history. Preserve a recovery reference, identify the commits containing it, and
correct the unpushed commits or migrate those blobs to LFS. The appropriate
amend/rebase/filter operation depends on the branch history. This tool never
rewrites history or installs a Git hook. [GitHub's LFS migration guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/moving-a-file-in-your-repository-to-git-large-file-storage).

Git LFS is an optional alternative for an existing large file. Collaborators and
automation must hydrate its content before native readers can use it. LFS does
not reduce local parsing work, and changed versions consume storage as complete
files. [GitHub's LFS accounting](https://docs.github.com/en/billing/concepts/product-billing/git-lfs).

## Recover, export or clean up

Restore the verified snapshot of an interrupted migration:

```sh
llm-wiki knowledge recover-storage --wiki-dir wiki --recovery-dir ../wiki-recovery --dry-run
llm-wiki knowledge recover-storage --wiki-dir wiki --recovery-dir ../wiki-recovery
```

Recovery refuses to overwrite an unrelated newer root or changed authored
content. It restores exact previous artifacts; an old oversized file still needs
push-history remediation.

Export a complete v1 file for an older consumer without changing the active wiki:

```sh
llm-wiki knowledge export-storage --wiki-dir wiki --to v1 --output ../knowledge-v1.json
```

Exports exceeding the 95 MiB policy fail without writing a partial file.

Preview and explicitly remove recognized, unreferenced objects:

```sh
llm-wiki knowledge prune-storage --wiki-dir wiki
llm-wiki knowledge prune-storage --wiki-dir wiki --apply
```

Cleanup requires a valid current generation. It preserves referenced objects,
unrecognized files and busy files. Review and commit the resulting changes using
your normal Git workflow.

To apply exactly the reviewed candidates, save a bounded plan outside the wiki:

```sh
llm-wiki knowledge prune-storage --wiki-dir wiki --save-plan cleanup.json
llm-wiki knowledge prune-storage --wiki-dir wiki --plan cleanup.json --apply
```

Plans bind the current generation, wiki location and candidate bytes. Apply
rechecks reachability and preimages; changed candidates or a moved wiki require a
new plan. `--max-bytes` bounds orphan bytes inspected and reports retained work
when the budget is exhausted. Applying a saved plan inspects its named candidates.

Cleanup verifies recovery copies before deleting anything. `--recovery-dir`
selects their location outside the wiki. Otherwise recovery uses Git metadata,
or a sibling `.llm-wiki-storage-recovery` directory for a non-Git wiki. Identical
preimages share recovery objects; recovery records and unknown files are retained.
The result identifies the recovery manifest. Preview or restore its absent files:

```sh
llm-wiki knowledge restore-pruned --wiki-dir wiki --recovery-manifest PATH
llm-wiki knowledge restore-pruned --wiki-dir wiki --recovery-manifest PATH --apply
```

This restores owned preimages without changing the active root, authored content
or differing existing files. Recovery bytes, obsolete generation bytes and Git
history are separate storage costs; cleanup does not compact Git history.

## Request scoped task context

Use `llm-wiki-task-request/v2` to opt into selected native storage reads. The
Python API, `task-context` CLI and task/session MCP tools accept this version.
Existing task v1 requests retain their full-validation behavior.

```json
{
  "schema_version": "llm-wiki-task-request/v2",
  "requirements": [
    {"id": "contract", "facet": "source-contract", "selector": "app.py:limit"}
  ],
  "options": {"knowledge_mode": "off"}
}
```

For selected native concepts or semantic sections, use an adopted v2, v3 or v4 wiki and
`knowledge_mode: "auto"` or `"required"`. `read_scope: "snapshot"` skips live
source extraction. Required mode requires the selected native inputs; it does
not establish source freshness or semantic correctness.

A task v2 result reports its validated storage scope, consumed inputs, actual
storage bytes including final rechecks, and unverified records. It carries no
legacy packet claiming whole-artifact validity. Missing input, corruption or a
read limit cannot turn into a complete graph or a satisfied requirement.

Sessions revalidate consumed objects and source inputs before reuse. Delta v2
binds the exact v2 base and result; v1 and v2 deltas cannot be interchanged.

Packed reads use the versioned `llm-wiki-task-storage/v2` receipt. It records
consumed file ranges and reports `archive_validation_scope: selected-members`.
Unconsumed members and archive metadata remain unverified until a full audit.
Sessions recheck the consumed ranges and pack identities before reuse. Actual
routing, range and final recheck bytes count against the caller's read budget;
compressed members also have bounded expansion. Broad requests can still exceed
that budget, including when surface, manifest or governance companions grow.

### Select only needed collections and compact the proof

Task v2 can explicitly request the version-3 storage receipt:

```json
{
  "schema_version": "llm-wiki-task-request/v2",
  "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
  "storage_options": {
    "selection": "required-facets-v1",
    "receipt": "compact-v1"
  },
  "requirements": [
    {"id": "concept", "facet": "concept", "selector": "modules/app.md"}
  ]
}
```

`required-facets-v1` selects concepts and adds edges or sections when the requested
facets need them. Its scope is `selected-committed-collections`; other collections
remain explicitly unverified. `all-collections-v1` retains the broader selection.
`compact-v1` uses a file table and compact range rows while retaining every hash,
coordinate, size and work count. `expanded-v1` keeps named fields. V4 storage uses
the version-3 receipt even without these options so metadata-page ranges are
distinguished from archive members.

Compact digests use canonical base64url encodings of the same SHA-256 bytes.
Repeated whole-file commitments can refer to their file-table entry; expansion
restores their full `sha256:` form.

`api.validate_task_context` validates either representation against its request.
`api.expand_task_storage_receipt(result["storage"])` reconstructs a compact proof
for inspection; expansion alone does not establish authenticity or freshness.
The Python, CLI and MCP task/session interfaces use the same canonical result.
Receipt layout and selection affect request/result and delta bindings. Output
accounting measures emitted UTF-8 text; disk compression is a separate measure.

Guarded reads reuse at most 128 handles per phase and reopen names for final
validation. Explicit storage options enable exact-adjacency range batching for
rechecks, with no speculative extra bytes. Every consumed byte remains charged.
Sessions may share immutable input bytes within one workspace, while each entry
retains and revalidates its own dependencies. Mutable provider installations
continue to require complete producer validation.
