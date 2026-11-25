---
name: dep-audit
description: Triage LLM Wiki dependency diagnostics such as import cycles, undeclared or unused dependencies, visibility mismatches, and documentation drift. Use when lint, CI, or a review reports a dependency warning that needs an evidence-backed source, manifest, documentation, or deferral decision.
---

# dep-audit

Triage dependency diagnostics using existing `llm-wiki` outputs. This skill does not invent a new scanner. It turns dependency-cycle, undeclared-dependency, and unused-dependency diagnostics into a bounded action plan with source verification before any manifest or code edit.

See [reference.md](reference.md) for status labels, report rows, and edge cases.

## Managed repository preflight

Before the first wiki write and again before delivery, follow
[repository-handoff](../wiki-reference/references/repository-handoff.md). Stage
only after `llm-wiki knowledge git-check --wiki-dir <wiki-dir>` reports
`git-eligible`; any other result stays local-only.

## Preconditions

- The user asked to investigate dependency diagnostics, package visibility, or dependency hygiene.
- Source and wiki paths are selected. For external source roots, use `--allow-external-src` on source-reading commands and keep output/wiki paths guarded.
- Carry `--source-selection <profile>` on every source-reading command when a
  profile is configured or discovered; omit the option only when none exists,
  and never widen a configured selection.
- No manifest edits without source evidence. A dependency warning alone is not enough to change package metadata.
- Native knowledge: interpret every result through
  [knowledge-consumption](../wiki-reference/references/knowledge-consumption.md).
  Only `ready` with live `current` freshness supports an unchanged claim, and
  an unavailable or bounded `found: false` is never a negative fact.

## Steps

1. **Collect diagnostics.**

   ```bash
   llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json --source-selection <profile>
   ```

   Save the JSON or profile output when the run is large. Include review JSON if the dependency finding came from `llm-wiki review` or a saved review report.

2. **Normalize each finding.** Classify every dependency-cycle, undeclared-dependency, and unused-dependency item as one of: valid dependency issue, documentation-only mismatch, expected/generated dependency, third-party/vendor noise, or needs human confirmation.

3. **Perform source verification.** Read the named source files, imports, and generated metadata before proposing changes. Confirm whether the dependency is runtime, test-only, optional, generated, plugin-provided, or stale documentation.

4. **Choose the smallest safe action.**

   - Fix source imports only when the code is truly wrong.
   - Edit manifests only when source evidence proves a missing or stale declaration.
   - Update wiki `dependencies.md` or `load-order.md` notes when the warning is intentional architecture.
   - Defer with rationale when evidence is ambiguous.

5. **Re-anchor wiki edits, then verify.** If the audit changed canonical wiki
   Markdown such as `dependencies.md` or `load-order.md` notes, run the owning
   refresh after the last edit and before strict validation:

   ```bash
   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
   llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki --source-selection <profile>
   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json --source-selection <profile>
   ```

   The sync preserves supported semantic notes and re-anchors Markdown,
   surface, knowledge, and manifest commitments. If the audit wrote only its
   report outside the wiki, this refresh is unnecessary. A generated-only run
   with no Markdown edit does not repeat sync. Any later Markdown fix restarts
   this sequence. After refresh, report expired human section reviews and stale
   machine-verification receipts with their existing reasons; do not fabricate
   replacements.

6. **Report.** Summarize findings by status, files inspected, actions taken, verification commands, and unresolved items. Do not hide warnings that were deferred.
