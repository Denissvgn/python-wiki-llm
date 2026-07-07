---
name: dep-audit
description: Triage LLM Wiki dependency diagnostics for cycles, undeclared dependencies, unused dependencies, visibility mismatches, and dependency-documentation drift. Use when lint, ci-check, review JSON, or a user report asks an agent to decide whether dependency warnings require source edits, manifest edits, wiki documentation, or an explicit deferral.
---

# dep-audit

Triage dependency diagnostics using existing `llm-wiki` outputs. This skill does not invent a new scanner. It turns dependency-cycle, undeclared-dependency, and unused-dependency diagnostics into a bounded action plan with source verification before any manifest or code edit.

See [reference.md](reference.md) for status labels, report rows, and edge cases.

## Preconditions

- The user asked to investigate dependency diagnostics, package visibility, or dependency hygiene.
- Source and wiki paths are selected. For external source roots, use `--allow-external-src` on source-reading commands and keep output/wiki paths guarded.
- No manifest edits without source evidence. A dependency warning alone is not enough to change package metadata.

## Steps

1. **Collect diagnostics.**

   ```bash
   llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json
   ```

   Save the JSON or profile output when the run is large. Include review JSON if the dependency finding came from `llm-wiki review` or a saved review report.

2. **Normalize each finding.** Classify every dependency-cycle, undeclared-dependency, and unused-dependency item as one of: valid dependency issue, documentation-only mismatch, expected/generated dependency, third-party/vendor noise, or needs human confirmation.

3. **Perform source verification.** Read the named source files, imports, and generated metadata before proposing changes. Confirm whether the dependency is runtime, test-only, optional, generated, plugin-provided, or stale documentation.

4. **Choose the smallest safe action.**

   - Fix source imports only when the code is truly wrong.
   - Edit manifests only when source evidence proves a missing or stale declaration.
   - Update wiki `dependencies.md` or `load-order.md` notes when the warning is intentional architecture.
   - Defer with rationale when evidence is ambiguous.

5. **Verify.** Re-run the focused command that produced the diagnostic, then run `llm-wiki ci-check` when wiki or dependency docs changed.

6. **Report.** Summarize findings by status, files inspected, actions taken, verification commands, and unresolved items. Do not hide warnings that were deferred.
