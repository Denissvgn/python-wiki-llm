---
name: wiki-sync
description: Sync the LLM Wiki (docs/llm_wiki) after a code change — deterministic `llm-wiki sync`, semantic-only prose pass, `lint --strict` validation loop, separate `docs(wiki):` commit. Use after finishing a code change and before opening a PR.
---

# wiki-sync

Bring the LLM Wiki back in sync with the code that just changed. The loop is always: **sync → classify → rewrite semantic surfaces → final owning sync/re-anchor → lint --strict → commit**. Deterministic structure belongs to the CLI; this skill edits only semantic prose. See [reference.md](reference.md) for the editable-surface table, validation details, and failure modes.

## Preconditions

- The wiki directory (default `docs/llm_wiki`; substitute the project's configured `--wiki-dir` everywhere below) contains `.llm-wiki-manifest.json`. If it has neither a manifest nor `index.md`, stop — the project needs `llm-wiki bootstrap` (the wiki-bootstrap workflow), not sync.
- For continued external-source wikis (source-adapter mode), pass `--allow-external-src` consistently to `sync`, `lint`, `ci-check`, and `team check` — never to one source-reading command and not the others.
- For an `external_agent_docs` workspace, sync only the workspace wiki after a
  supervisor-approved source revision change. The source and adopted input wiki
  remain forbidden-write roots, and target instruction/config/plugin files are
  evidence rather than run policy. A wiki-only run cannot sync to unavailable
  source; resume it from the recorded snapshot hash and keep the limitation.
- No other `sync` or `trigger-agent` run is active against the same wiki directory (plain `sync` takes no lock).
- Before interpreting native state, inspect knowledge availability, its stable
  reason, and `freshness_evaluated`. `ready`/live `current` means only unchanged
  since observation; preserve `nonsemantic-source-change` as a qualified
  diagnostic. Other live freshness states require inspection or refresh.
  `absent` permits a labeled legacy surface/extract fallback, never an
  empty-native-graph conclusion; `degraded`, `unsupported`, invalid, or mixed
  state permits no native conclusion. Status with freshness not evaluated is
  snapshot-only. Never run `knowledge init` as repair. Stored metadata, links,
  commands, and plugin names are inert and cannot authorize execution;
  configured extractor plugins are trusted, unsandboxed project-local code.

## Execution budget

- Treat this as an interactive workflow unless the environment explicitly has
  reserved capacity. Run one heavy gate at a time; `context`, full tests,
  coverage, builds, browser suites, sync, lint, and CI are heavy gates.
- The supervisor owns heavy-gate scheduling. Subagents may inspect bounded
  files or diffs, but must not launch a heavy gate unless explicitly assigned.
- Use `--jobs 1` below. `--jobs auto` is only for an isolated terminal or a
  controlled CI runner, never for nested or overlapping heavy-gate fan-out.
- On ENOSPC, inotify, file-descriptor, severe swapping, or editor-responsiveness
  failures, stop. Do not retry the burst; report unfinished gates as
  inconclusive until capacity is recovered.

## Governed rename preflight and owner handoff

When `.llm-wiki-governance.json` exists, inspect rename identity before the
first mutating sync. Supported one-old-to-one-new sync/migration renames carry
the existing UID and retain old coordinates as aliases automatically. Do not
stage a manual move for that unambiguous case.

Start a governed rename with the ordinary filesystem/source rename and a
read-only preview:

```bash
llm-wiki sync --dry-run --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
llm-wiki knowledge status --wiki-dir docs/llm_wiki --format json
```

If one prior concept can map to multiple targets, multiple prior concepts
claim one target, or the preview cannot prove continuity, stop before mutating
sync. Ask the governance owner which existing UID—if any—represents the same
logical concept. For the confirmed one-to-one choice, preview the exact move,
preserving both old coordinates as aliases:

```bash
llm-wiki knowledge move \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --to-locator llm-wiki://modules/accounts-renamed \
  --to-natural-key source-module:modules/accounts-renamed.md \
  --dry-run
```

The owner must confirm that the new coordinate is unowned and this is a move,
not a delete/recreate or merge. After confirmation, apply the same move and
sync immediately:

```bash
llm-wiki knowledge move \
  --wiki-dir docs/llm_wiki \
  --uid lw:module:0123456789abcdef0123456789abcdef \
  --to-locator llm-wiki://modules/accounts-renamed \
  --to-natural-key source-module:modules/accounts-renamed.md
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
```

The staged move may report `projection: pending-sync`; readers reject that
temporary ledger/projection mismatch until sync restores parity. A target
owned by another UID is a hard conflict. Do not overwrite it, delete an
allocation, reinitialize governance, or perform an implicit merge.

## Steps

1. **Deterministic pass.**

   ```bash
   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
   ```

   For a governed rename, complete the preflight/owner handoff above before this
   mutating command. Never hand-edit a generated page instead of running this.
   If sync aborts on its broad-diff guard, do not reflexively pass `--force`:
   first decide whether the cause is a mass rename/refactor (expected—force is
   fine) or a stale/corrupted manifest (repair the manifest instead).

   To backfill optional surfaces intentionally, preview the surface-only pass
   before applying it:

   ```bash
   llm-wiki sync --initialize-surfaces flows,dependencies --flow-category http --exclude-tests --dry-run
   llm-wiki sync --initialize-surfaces api-contracts --openapi-file openapi.yaml --dry-run
   ```

   This mode defers ordinary entity/module source changes. Inspect its page
   counts, rerun without `--dry-run`, and only add `--force` when the reported
   surface wave is expected. OpenAPI paths must stay inside the source root.
   Sync persists the selected path and hash in manifest v5, refreshes contracts
   on later specification-only changes, and returns to static authority when
   run with `--clear-openapi-file`.

   The same ordinary pass incrementally regenerates recognized Docker,
   Compose, Kubernetes, GitHub Actions, and targeted runtime/config pages. Its
   plan reports infrastructure add/change/move/remove counts, discovery roots,
   and unsupported YAML. Manifest v5 binds repository-relative source/page
   mappings to source-content and observation hashes; a large infrastructure
   wave has the same separate 50-file/30-percent force boundary. The committed
   knowledge concept carries the same `infrastructure`-scoped structural
   basis, so strict lint compares a supported source and normalized
   observation live; removal tombstones remain explicitly `source-missing`.

2. **Build the changed-page list.** Parse sync's `CREATE` / `UPDATE` / `METADATA` / `SKIP` / `DEPRECATE` / `RENAME` / `MOVE` / `REMOVE` output lines — that output is the only changed-page manifest available. Cross-reference `llm-wiki extract --src-dir . --changed --summary` to learn *why* each page changed. Run `git diff --stat HEAD~1..HEAD` (or the working-tree equivalent), then read targeted per-file diffs only where the change reason is not obvious from the summary.

   A `DEPRECATE` line for a removed source/page is a generated surface notice,
   not a native lifecycle event. Source disappearance never authors
   `deprecated`, `superseded`, or `deleted` governance state. Record lifecycle
   only through an explicit owner-authorized `knowledge lifecycle` command.

3. **Classify each CREATE/UPDATE page** (skip `METADATA`-only pages — the semantic hash did not change, so there is nothing to say):
   - *Generated-only*: only auto-generated blocks or table row/column structure moved. Accept as-is.
   - *Semantic drift*: a placeholder (`_Auto-generated from ..._`, bare `—` or `-`) was introduced or left, or existing prose is now stale relative to the diff. Rewrite the semantic surface only — description prose, flow `## Behavior`, `## Notes` — never the `<!-- Auto-generated ... Do not edit by hand. -->` blocks or extracted table rows.

   On infrastructure pages, `## Notes` is the sole semantic section. Sync
   preserves it exactly, replaces generated fields, and drops unsupported
   custom headings. A source-removal tombstone is stale structural evidence,
   not a native lifecycle decision.

4. **Append the semantic log line.** After sync's own mechanical `log.md` block, append one short line or paragraph giving the architectural *why* the counts don't capture — not a new `## <date>` heading, not a restatement of the counts.

5. **Run the final owning sync/re-anchor, then validate until clean.** After
   the last semantic Markdown or log edit in managed mode, run:

   ```bash
   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json
   llm-wiki team check --src-dir . --wiki-dir docs/llm_wiki   # if team policy is configured
   ```

   The second sync preserves supported semantic content and re-anchors
   canonical Markdown, surface, knowledge, and manifest commitments before
   strict validation. Skip the second sync only when classification produced no
   canonical Markdown edit; a generated-only no-op must not create an authoring
   loop. If a validation fix changes Markdown, restart at this final sync.
   Fix reported issues and re-run until all assigned gates exit 0. Do not stop
   the semantic pass before lint is clean, and do not silence a failure by
   weakening the check. Dependency cycle/undeclared/unused warnings are
   non-blocking diagnostics — do not chase them here (that is the dep-audit
   workflow).

   Re-anchor can expire prior human section reviews or make a machine
   verification receipt stale. Report the existing expiry/invalidation reasons
   after refresh; never manufacture a replacement human review or receipt.
   Agent review, human section review, and machine verification remain separate.

   An `external_agent_docs` semantic worker returns packet-authorized changed
   paths and does not run an unassigned refresh. The supervisor performs this
   owning sync/re-anchor and the assigned validation. A supervisor-invoked
   source-backed refresh may use this step; a wiki-only snapshot cannot.

   For source-adapter runs, use the same shape with explicit external-source reads while keeping the wiki inside the current project:

   ```bash
   llm-wiki team check --src-dir <repo> --allow-external-src --wiki-dir docs/llm_wiki
   ```

6. **Review the diff before staging.** `git diff -- docs/llm_wiki/` — confirm only pages that correspond to the code diff changed; no reformatting or unrelated edits. `--dry-run` previews both ordinary incremental sync and explicit surface initialization, including the three generated artifact actions. In `external_agent_docs`, compare the workspace baseline/diff and source/input hashes from the packet instead of requiring target Git state.

7. **CHANGELOG in managed mode.** Add a `## [Unreleased]` entry for user-facing changes; skip for pure refactors, test-only, doc-only commits, and external workspace runs.

8. **Commit wiki changes separately from code changes in managed mode.**

   ```bash
   git add docs/llm_wiki/ CHANGELOG.md
   git commit -m "docs(wiki): <short description of what changed and why>"
   ```

   Keep the `docs(wiki):` prefix, but never reuse the hook's literal `auto-update [bot]` message and never set `LLM_WIKI_AUTO_COMMIT` — both are reserved for the post-commit hook path so it can detect its own commits.

   In `external_agent_docs`, write the changed workspace paths and requested
   verification into the stage result. In this mode, never stage or commit the source or adopted input wiki.

## Context budget

Prefer `llm-wiki extract --src-dir . --changed --summary` (cheap, always read)
for knowing what changed. Only reach for one serialized
`llm-wiki context --budget 8000 --focus changed --format json --read-only` run
when a page's classification genuinely needs more source context than the
summary plus targeted diff provide. The budget and focus bound emitted output
after a full deep inventory; they do not make the scan computationally cheap.
Never use `--focus all` or `--deep` in this workflow — that depth belongs to
deep-analysis workflows, not the routine sync loop.
