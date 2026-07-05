---
name: user-docs-author
description: Run a deterministic-first user docs authoring pass for an existing LLM Wiki - collect current llm-wiki sync/lint/site evidence, write only evidence-backed semantic guide prose, export/check the user site profile, and loop on validation-backed issues. Use when a project needs a fuller human user-docs layer before `site export --profile user`; do not use it to add a new llm-wiki command or to call an LLM from package code.
---

# user-docs-author

Build a user-facing documentation layer on top of a current LLM Wiki without weakening the reproducible core. The loop is: **deterministic evidence first -> LLM-authored semantic guide/docs pass -> deterministic site export/check/build -> LLM adjustment loop from checker output**. This is a skill-only workflow: `llm-wiki` commands produce evidence and validation, while the agent owns judgment, prose, and deferred-docs decisions. See [reference.md](reference.md) for the evidence map, page templates, command matrix, adjustment loop, and failure modes.

## Preconditions

- A maintained wiki exists and its source root is known. If not, run `wiki-bootstrap`; if the wiki is stale, run `wiki-sync` before authoring.
- The wiki directory is writable. The source repository may be read-only; use existing `--allow-external-src` patterns only where the deterministic command already supports them.
- The user-facing audience and site name are known or can be inferred from repository evidence. If inferred, state the assumption in the run report.
- No core-package LLM calls are added. This skill uses the current agent session for authoring and adjustment.

## Steps

1. **Establish the deterministic baseline.** Start from current command output, not from memory or guesses.

   ```bash
   llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs auto
   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user \
     --format mkdocs --profile user --site-name <project> \
     --front-matter --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
     --profile user --site-name <project> --output-format json
   ```

   Treat `site check --profile user` failures such as missing guide surface, placeholder primary docs, or default site naming as the authoring worklist. Do not work around failed evidence by editing exported static-site files.

2. **Collect only the evidence needed for the user-docs pass.** Read `index.md`, existing `guides/*.md`, generated flow/module/entity pages that the guide will link to, `.llm-wiki-surface.json` or equivalent site/check JSON, and source files only when linked wiki evidence is insufficient. Use the tables in [reference.md](reference.md) to decide which surfaces answer which claim.

3. **Author semantic wiki prose only.** Prefer `guides/*.md`; update other human-owned wiki prose only when the repo already uses it for narrative docs. This is a semantic wiki prose only pass: Do not edit generated blocks. Do not edit static-site output. Do not invent facts. Every factual product/workflow claim must link to existing wiki/source evidence. If evidence is weak, add a deferred-docs item with the missing source/evidence instead of filling the gap.

4. **Re-link and validate the wiki.**

   ```bash
   llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs auto
   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json
   ```

   Fix only issues that are backed by deterministic output or by evidence you can cite.

5. **Export, build, and check the user site.**

   ```bash
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user \
     --format mkdocs --profile user --site-name <project> \
     --front-matter --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
     --profile user --site-name <project> --output-format json
   # If a real builder is installed:
   mkdocs build --strict -f site-user/mkdocs.yml
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
     --built-site-dir _site --link-mode http \
     --profile user --site-name <project> --output-format json
   # For direct-file handoff, re-export file-friendly and validate file links:
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user \
     --built-site-dir _site --link-mode file \
     --profile user --site-name <project> --output-format json
   ```

6. **Run the adjustment loop from checker output.** Feed `lint`, `ci-check`, `site check`, builder output, and `doc-review` findings back into the same evidence-first loop. Fix validation-backed issues; defer weak or ambiguous findings with enough context for the next pass. Never adjust prose only because it "sounds better" if the change cannot be tied to user-docs clarity, cited evidence, or a reported validation issue.

## Context Budget

Start with deterministic JSON/text reports, `index.md`, and the pages that are linked from existing guides or user-profile warnings. Read source files only to confirm claims not already present in wiki evidence. Do not re-run extraction unless `sync` or `lint` shows the wiki is structurally stale; stale structure is `wiki-sync` work before this skill resumes.
