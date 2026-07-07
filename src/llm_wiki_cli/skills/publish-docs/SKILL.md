---
name: publish-docs
description: Wire LLM Wiki's static-site export into an actual publishable site — export (single-wiki or multi-wiki hub), validate with `site check`, run the real mkdocs/docusaurus builder when installed, and hand off a deploy step. Use when a user wants the wiki actually published as a browsable site, not just exported as Markdown; low LLM judgment, mostly a scripted convenience wrapper around existing deterministic commands.
---

# publish-docs

Turn `site export`'s Markdown mirror into an actually-buildable, optionally deployed site. The default export is a reference profile: complete generated coverage for agents and maintainers. Use `--profile user` only when a human documentation layer exists. The loop is: **export → check → detect and run the real builder if installed → validate built links for the selected distribution mode → hand off deploy**. Every step through `site check` is already deterministic and covered by existing commands; this skill's judgment calls are which profile matches the audience, which format matches the target host, which link mode matches the handoff, and whether to attempt the real build at all. See [reference.md](reference.md) for format/host pairings, builder detection, distribution modes, and the CI wiring pattern.

If user docs need captured examples before publishing, run `usage-examples` first; this skill only validates and publishes the resulting media-bearing site.

## Preconditions

- A current wiki (or several, for hub mode) already exists — run `wiki-sync`/`wiki-bootstrap` first if not; this skill does not generate wiki content.
- For `--profile user`, a non-default `--site-name` and at least one guide page under `guides/` already exist — run `onboarding-guide` first if only persona guides are missing, or `user-docs-author` first if the whole user-docs narrative layer needs to be filled from deterministic site evidence.
- The user has said where this is being published (GitHub Pages, an internal MkDocs/Docusaurus host, or "just give me a static mirror") — that choice picks the export `--format` and whether a real build step applies at all (`--format plain` has no corresponding builder).
- If a real builder (`mkdocs`, `npm`/docusaurus) will be invoked, confirm it is actually installed before attempting it — this skill fails closed and reports clearly rather than half-running a build.

## Steps

1. **Export.** Reference profile, single wiki:

   ```bash
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site \
     --format mkdocs --profile reference --front-matter --output-format json
   ```

   User profile, single wiki:

   ```bash
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site \
     --format mkdocs --profile user --site-name <project> \
     --front-matter --output-format json
   ```

   Multi-wiki hub (see the `doc-hub` skill first if hub aggregation itself, not just publishing, is the goal):

   ```bash
   llm-wiki site export --wiki-root sources/code_wikis --out-dir site \
     --format docusaurus --front-matter --output-format json
   ```

   Confirm `ok: true` and `issues: []` before proceeding — never build on top of a failed export.

2. **Check.** Reference profile:

   ```bash
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
     --profile reference --output-format json
   # or the matching --wiki-root form for hub mode
   ```

   User profile:

   ```bash
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
     --profile user --site-name <project> --output-format json
   ```

   Confirm `ok: true`, `0` issues. This is the last purely-deterministic gate; treat any failure here as a stop, not a warning to note and continue past.

3. **Detect whether the real builder is available, and run it only if so.**
   For `--format mkdocs`: check `mkdocs --version` (or the project's pinned dependency, e.g. in `requirements-docs.txt`/`pyproject.toml`).
   For `--format docusaurus`: check for `package.json` + `node_modules` in the target site directory, or that `npm`/`npx` resolves. If the builder isn't installed, say so explicitly and stop after step 2 — do not attempt to install a toolchain on the user's behalf without being asked.

   ```bash
   # mkdocs
   mkdocs build --strict -f site/mkdocs.yml
   # docusaurus (from the exported site directory, if it has its own package.json)
   npm run build
   ```

   Surface the real builder's own errors verbatim — this skill does not reinterpret mkdocs/docusaurus build failures, since `site check` already covers the checks `llm-wiki` itself can make.

4. **Validate built links for the selected distribution mode.** Hosted docs use HTTP routing:

   ```bash
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
     --built-site-dir _site --link-mode http --output-format json
   ```

   Direct-file handoffs use file-friendly export plus file-mode validation:

   ```bash
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-file \
     --format mkdocs --profile user --site-name <project> --file-friendly \
     --front-matter --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-file \
     --profile user --site-name <project> --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-file \
     --built-site-dir _site --link-mode file --output-format json
   ```

5. **Hand off the deploy step, don't perform it.** State the built output location and the deploy mechanism the user named (GitHub Pages action, `rsync` to an internal host, etc.) as a next step. Actually pushing to a hosting target, publishing a GitHub Pages branch, or deploying is a visible, hard-to-reverse action — confirm with the user before doing it, even if they asked for "publish-docs" broadly; "publish" the export pipeline is safe to run repeatedly, an actual deploy is not.

6. **CI wiring (optional).** If the user wants this as a CI step rather than an interactive run, wire export → check → build → built-link check into the existing CI workflow alongside `ci-check` (see [reference.md](reference.md) for the pattern) rather than creating a second, parallel docs-publishing pipeline.

## Context budget

This skill has almost no LLM judgment budget by design — every step is a deterministic command whose JSON/exit-code result is the only evidence needed. Do not read wiki page content as part of this workflow; that belongs to the skills that write or review it (`wiki-sync`, `doc-review`, `user-docs-author`).
