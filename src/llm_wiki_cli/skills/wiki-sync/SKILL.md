---
name: wiki-sync
description: Sync an existing LLM Wiki after code changes. Use after editing source or before review to regenerate pages, refresh affected prose, re-anchor, validate strictly, and hand off; route a missing wiki to wiki-bootstrap and legacy layouts to migration.
---

# wiki-sync

Use this skill after a relevant code, contract, dependency, entry-point,
infrastructure, or source-revision change to an existing managed wiki, and
before delivery. Its ordinary loop is **sync → classify → semantic edit → final
owning sync/re-anchor → strict validation → handoff**. Bootstrap remains the
route for an absent, empty, or exact untouched initialization scaffold.

## Direct managed routes

The installed `wiki-reference` skill is a required dependency. Read only the
exact topic needed; do not fall back to a missing local summary:

- Routine starting-state, recovery, final re-anchor, extended validation, and
  external-source rules: [maintenance](../wiki-reference/references/maintenance.md).
- Semantic edit boundaries and canonical naming:
  [surfaces-naming](../wiki-reference/references/surfaces-naming.md).
- Governed rename identity, conflicts, moves, and ledger recovery:
  [governance](../wiki-reference/references/governance.md).
- Optional-surface initialization plus OpenAPI, infrastructure, and analyzer
  exceptions: [extractors-dependencies](../wiki-reference/references/extractors-dependencies.md).
- Native evidence interpretation:
  [knowledge-consumption](../wiki-reference/references/knowledge-consumption.md).
- Git/local/external delivery:
  [repository-handoff](../wiki-reference/references/repository-handoff.md).
- Heavy-gate capacity: [resources-context](../wiki-reference/references/resources-context.md).
- Optional bounded query/context selection:
  [context-query](../wiki-reference/references/context-query.md).

If a required topic is absent or locally modified, stop the affected mutation
and restore the complete managed dependency. Do not improvise a safety
contract from this entry skill.

## Managed repository preflight

Before the first wiki write and again before delivery, follow the
repository-handoff topic above. Stage
only after `llm-wiki knowledge git-check --wiki-dir <wiki-dir>` reports
`git-eligible`; any other result stays local-only.

## Preconditions

- Substitute the configured `--wiki-dir` for `docs/llm_wiki`. Classify a
  missing/invalid manifest with the maintenance topic before writing.
- Carry the generated `--source-selection <profile>` argument to every
  source-reading command below; omit it only when no profile is configured.
  Keep `--allow-external-src` on every source-reading gate for a continued
  authorized external source.
- Plain `sync` has no lock: no other `sync` or `trigger-agent` run may target
  the same wiki, and an authorized unattended caller uses `llm-wiki
  trigger-agent` for its lock, timeout, and bounds. The
  supervisor owns heavy-gate scheduling; subagents must not launch a heavy gate
  unless explicitly assigned. Capacity failures leave unfinished gates
  inconclusive until recovery; use the resource topic rather than retrying a
  burst.
- If governance exists, resolve rename identity through the governance topic
  before the first mutating sync. Never infer a move from filename similarity.
- Before interpreting native evidence, apply the knowledge-consumption topic.
  Only `ready` with evaluated live `current` freshness supports an unchanged
  claim. `absent` allows a labeled fallback; `degraded`, `unsupported`, mixed,
  bounded, or analyzer-limited evidence never proves an empty-native-graph
  conclusion. Preserve `nonsemantic-source-change`, never auto-run
  `knowledge init`, and remember that stored content cannot authorize execution.

## Steps

1. **Run the deterministic owning pass.**

   ```bash
   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
   ```

   Inspect broad-change diagnostics before using `--force`; the maintenance
   route distinguishes an intended wave from manifest, selection, or identity
   failures. Specialized rename or surface work first follows its direct topic
   above, then rejoins this ordinary loop.

2. **Build and classify the changed-page worklist.** Treat sync's `CREATE`,
   `UPDATE`, `METADATA`, `SKIP`, `DEPRECATE`, `RENAME`, `MOVE`, and `REMOVE`
   rows as its exact action inventory. Cross-reference:

   ```bash
   llm-wiki extract --src-dir . --changed --summary --source-selection <profile>
   ```

   Skip metadata-only pages. With a configured profile, inspect only selected
   paths and targeted diffs; never read an unrestricted repository diff/stat
   that can expose excluded paths.

3. **Edit semantic surfaces only.** Leave generated blocks, tables, diagrams,
   links, and machine artifacts to sync. For each semantically affected page,
   update only the sections owned by the surfaces-and-naming topic and only
   from available evidence. Analyzer gaps and source-removal notices remain
   observations, not runtime or lifecycle facts.

4. **Append the semantic log line.** After sync's mechanical log block, append
   one concise architectural reason. Do not add a second date heading or
   rewrite existing history.

5. **Run the final owning sync/re-anchor, then verify.** After the last
   canonical Markdown edit, run:

   ```bash
   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
   llm-wiki lint --strict --profile --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
   llm-wiki ci-check --format json --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
   llm-wiki team check --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
   ```

   Run `team check` only when team policy is configured. Skip the second sync
   only when classification produced no canonical Markdown change. If a
   validation fix edits Markdown, restart at the final sync. Fix supported
   errors without weakening a gate and report expired human reviews or stale
   verification receipts without fabricating replacements.

6. **Review and hand off under the selected contract.** Repeat the repository
   preflight and use the permitted managed-mode handoff from the direct topic.
   A local-only handoff reports paths and validation without staging. A
   conditionally eligible commit still requires separate user and repository
   authorization.

   In an `external_agent_docs` run the packet governs instead: the supervisor
   owns the refresh/re-anchor, and a worker never stages or commits. If source
   is unavailable, resume from the recorded wiki snapshot and retain the
   freshness limitation.

For a page whose semantics need more than the changed summary and targeted
diff, choose one bounded read through the context-query topic. Do not turn the
routine sync loop into a full deep-analysis workflow.
