---
name: wiki-sync
description: Sync the LLM Wiki (docs/llm_wiki) after a code change — deterministic `llm-wiki sync`, semantic-only prose pass, `lint --strict` validation loop, separate `docs(wiki):` commit. Use after finishing a code change and before opening a PR.
---

# wiki-sync

Bring the LLM Wiki back in sync with the code that just changed. The loop is always: **sync → classify → rewrite semantic surfaces → lint --strict → commit**. Deterministic structure belongs to the CLI; this skill edits only semantic prose. See [reference.md](reference.md) for the editable-surface table, validation details, and failure modes.

## Preconditions

- The wiki directory (default `docs/llm_wiki`; substitute the project's configured `--wiki-dir` everywhere below) contains `.llm-wiki-manifest.json`. If it has neither a manifest nor `index.md`, stop — the project needs `llm-wiki bootstrap` (the wiki-bootstrap workflow), not sync.
- For continued external-source wikis (source-adapter mode), pass `--allow-external-src` consistently to `sync`, `lint`, `ci-check`, and `team check` — never to one source-reading command and not the others.
- No other `sync` or `trigger-agent` run is active against the same wiki directory (plain `sync` takes no lock).

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

## Steps

1. **Deterministic pass.**

   ```bash
   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
   ```

   Never hand-edit a generated page instead of running this. If sync aborts on its broad-diff guard, do not reflexively pass `--force`: first decide whether the cause is a mass rename/refactor (expected — force is fine) or a stale/corrupted manifest (repair the manifest instead).

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

2. **Build the changed-page list.** Parse sync's `CREATE` / `UPDATE` / `METADATA` / `SKIP` / `DEPRECATE` / `RENAME` output lines — that output is the only changed-page manifest available. Cross-reference `llm-wiki extract --src-dir . --changed --summary` to learn *why* each page changed. Run `git diff --stat HEAD~1..HEAD` (or the working-tree equivalent), then read targeted per-file diffs only where the change reason is not obvious from the summary.

3. **Classify each CREATE/UPDATE page** (skip `METADATA`-only pages — the semantic hash did not change, so there is nothing to say):
   - *Generated-only*: only auto-generated blocks or table row/column structure moved. Accept as-is.
   - *Semantic drift*: a placeholder (`_Auto-generated from ..._`, bare `—` or `-`) was introduced or left, or existing prose is now stale relative to the diff. Rewrite the semantic surface only — description prose, flow `## Behavior`, `## Notes` — never the `<!-- Auto-generated ... Do not edit by hand. -->` blocks or extracted table rows.

4. **Append the semantic log line.** After sync's own mechanical `log.md` block, append one short line or paragraph giving the architectural *why* the counts don't capture — not a new `## <date>` heading, not a restatement of the counts.

5. **Validate until clean.**

   ```bash
   llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki team check --src-dir . --wiki-dir docs/llm_wiki   # if team policy is configured
   ```

   Fix reported issues and re-run until both exit 0. Do not stop the semantic pass before lint is clean, and do not silence a failure by weakening the check. Dependency cycle/undeclared/unused warnings are non-blocking diagnostics — do not chase them here (that is the dep-audit workflow).

   For source-adapter runs, use the same shape with explicit external-source reads while keeping the wiki inside the current project:

   ```bash
   llm-wiki team check --src-dir <repo> --allow-external-src --wiki-dir docs/llm_wiki
   ```

6. **Review the diff before staging.** `git diff -- docs/llm_wiki/` — confirm only pages that correspond to the code diff changed; no reformatting or unrelated edits. `--dry-run` previews both ordinary incremental sync and explicit surface initialization, including the three generated artifact actions.

7. **CHANGELOG.** Add a `## [Unreleased]` entry for user-facing changes; skip for pure refactors, test-only, or doc-only commits.

8. **Commit wiki changes separately from code changes.**

   ```bash
   git add docs/llm_wiki/ CHANGELOG.md
   git commit -m "docs(wiki): <short description of what changed and why>"
   ```

   Keep the `docs(wiki):` prefix, but never reuse the hook's literal `auto-update [bot]` message and never set `LLM_WIKI_AUTO_COMMIT` — both are reserved for the post-commit hook path so it can detect its own commits.

## Context budget

Prefer `llm-wiki extract --src-dir . --changed --summary` (cheap, always read)
for knowing what changed. Only reach for one serialized
`llm-wiki context --budget 8000 --focus changed --format json --read-only` run
when a page's classification genuinely needs more source context than the
summary plus targeted diff provide. The budget and focus bound emitted output
after a full deep inventory; they do not make the scan computationally cheap.
Never use `--focus all` or `--deep` in this workflow — that depth belongs to
deep-analysis workflows, not the routine sync loop.
