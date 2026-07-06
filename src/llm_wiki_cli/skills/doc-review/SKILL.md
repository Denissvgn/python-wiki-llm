---
name: doc-review
description: Triage documentation review findings and apply wiki/source-doc follow-through from review JSON, branch diffs, patch reviews, lint reports, or sync diagnostics. Use when an agent needs to decide whether documentation feedback is valid, update wiki prose safely, run validation, and report unresolved findings without hiding them.
---

# doc-review

Triage documentation review findings and apply the smallest safe follow-up. This skill starts from review JSON, branch/diff workflow evidence, lint/sync diagnostics, or a user's review comments. It verifies each issue against source truth before editing wiki or source documentation.

See [reference.md](reference.md) for input shapes, status labels, and report format.

## Preconditions

- The user supplied review findings, a patch/branch to review, or saved review JSON.
- The target wiki path and source root are known.
- Generated wiki blocks remain protected. Edit semantic prose only unless the user explicitly asks for a generator/code change.

## Steps

1. **Collect review inputs.**

   - For a branch/diff workflow, inspect the changed source and wiki files with `git diff` or the review artifact the user supplied.
   - For a report workflow, load the saved review JSON and preserve finding IDs in your report.
   - Use `llm-wiki sync` or `llm-wiki lint --strict --profile` when the review is about stale generated wiki content.

2. **Validate each finding.** Classify it as valid documentation defect, stale generated content, source-code truth mismatch, duplicate finding, out-of-scope request, or needs human confirmation.

   For published user-docs reviews, also classify broken distribution-mode link, missing human landing page, missing guide surface, bootstrap placeholder in primary docs, and raw generated inventory used as root landing page. Map deterministic checker categories such as `published_placeholder` and `generated_reference_placeholder` to those review classes before editing. When findings require a broader user-docs rewrite rather than one review fix, hand the checker output to the `user-docs-author` adjustment loop.
   For media-backed docs, map `media_link_broken`, `media_missing_alt_text`,
   `media_oversize`, `media_orphan`, `missing_built_media_target`, and
   `user_docs_missing_examples` into the same review vocabulary; if capture
   work is needed, hand it to `usage-examples`.

3. **Apply follow-through.**

   - Run deterministic `llm-wiki sync` for source-driven wiki drift.
   - Edit only semantic wiki prose for wording, rationale, or review-context fixes.
   - Update source docs only when source comments/docstrings are the truth surface being reviewed.
   - Record every unresolved finding with rationale.

4. **Verify.**

   ```bash
   llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json
   ```

5. **Report.** List fixed, duplicate, false-positive, deferred, and unresolved finding IDs with evidence and verification commands. Do not close the review loop if an unresolved finding is hidden from the summary.
