# Knowledge storage

Native knowledge can use the original JSON file (`v1`) or an explicitly adopted
indexed format (`sharded-v2`). Existing wikis keep their format. New wikis use v1
unless you select another format.

Sharded storage keeps a small `.llm-wiki-knowledge.json` root and JSON objects in
`.llm-wiki-knowledge/objects/`. Commit the root, referenced objects, surface index
and sync manifest together. A normal checkout needs neither Git LFS nor a rebuild
to read that snapshot.

Markdown and `.llm-wiki-governance.json` remain the authority for authored content,
stable identity and review history. Storage migration preserves them.

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

For selected native concepts or semantic sections, use an adopted v2 wiki and
`knowledge_mode: "auto"` or `"required"`. `read_scope: "snapshot"` skips live
source extraction. Required mode requires the selected native inputs; it does
not establish source freshness or semantic correctness.

A task v2 result reports its validated storage scope, consumed inputs, actual
storage bytes including final rechecks, and unverified records. It carries no
legacy packet claiming whole-artifact validity. Missing input, corruption or a
read limit cannot turn into a complete graph or a satisfied requirement.

Sessions revalidate consumed objects and source inputs before reuse. Delta v2
binds the exact v2 base and result; v1 and v2 deltas cannot be interchanged.
