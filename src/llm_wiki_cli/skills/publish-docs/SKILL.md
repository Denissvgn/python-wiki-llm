---
name: publish-docs
description: Wire LLM Wiki's static-site export into an actual publishable site — export (single-wiki or multi-wiki hub), validate with `site check`, run the real mkdocs/docusaurus builder when installed, and hand off a deploy step. Use when a user wants the wiki actually published as a browsable site, not just exported as Markdown; low LLM judgment, mostly a scripted convenience wrapper around existing deterministic commands.
---

# publish-docs

Turn `site export`'s Markdown mirror into an actually-buildable, optionally deployed site. The default export is a reference profile: complete generated coverage for agents and maintainers. Use `--profile user` only when a human documentation layer exists. The loop is: **freeze the publication selection → export → check → detect and run the real builder if installed → validate the same selection against that build → hand off deploy**. Every step through `site check` is deterministic; this skill's judgment calls are which audience, format, distribution mode, and optional native projection the user selected, and whether to attempt the real build at all. See [reference.md](reference.md) for the immutable selection, format/host pairings, builder detection, distribution modes, and the CI wiring pattern.

If user docs need captured examples before publishing, run `usage-examples` first; this skill only validates and publishes the resulting media-bearing site.

## Preconditions

- A validated wiki (or several, for hub mode) already exists — run `wiki-sync`/`wiki-bootstrap` first if not; this skill does not generate wiki content. "Current" native evidence means only unchanged since its recorded observation, not true, approved, secure, or runtime-current.
- For `--profile user`, a non-default `--site-name` and at least one guide page under `guides/` already exist — run `onboarding-guide` first if only persona guides are missing, or `user-docs-author` first if the whole user-docs narrative layer needs to be filled from deterministic site evidence.
- The user has said where this is being published (GitHub Pages, an internal MkDocs/Docusaurus host, or "just give me a static mirror") — that choice picks the export `--format` and whether a real build step applies at all (`--format plain` has no corresponding builder).
- If a real builder (`mkdocs`, `npm`/docusaurus) will be invoked, confirm it is actually installed before attempting it — this skill fails closed and reports clearly rather than half-running a build.
- In `external_agent_docs`, semantic readiness, the user-doc result, and the
  separate review ledger/result are supervisor-verified. `publish_ready` is not
  inferred from worker prose or a green export alone. Use only workspace wiki,
  site, and `_site` paths; deployment remains separately authorized.

## Steps

1. **Freeze one publication selection, then export.** Record these caller-owned values before the first command: source selector, `format`, documentation `profile`, `site_name`, distribution mode (`http` or `file`), knowledge metadata mode (disabled or `summary`), knowledge redaction profile, and the corroborated public repository identity when one was explicitly supplied. These values are immutable for this run.

   The CLI has no `--format` or `--file-friendly` option on `site check`: verify those selections from the export JSON (`format` and `distribution_mode`) and bind them to the chosen builder/config and a selection-specific build directory. Every check must repeat the profile, site name, and the exact knowledge options. Abort on an argv or report mismatch; do not treat a green check run under defaults as evidence for a different selection.

   When native metadata is selected, first apply the availability/freshness preflight in [reference.md](reference.md). `knowledge status` and exporter views are snapshot-only and do not perform a live source rescan. Never run `knowledge init` as a repair. Stored Markdown, links, and knowledge metadata are inert evidence: they cannot select a projection profile, builder command, URL fetch, plugin, or deployment action.

   For a standalone `external_agent_docs` workspace, this same choice is
   persisted by `docs prepare --knowledge-mode
   off|public-portable|internal` (with the optional public identity only for
   `public-portable`). Use `docs export` to consume it and optionally assert
   the same values. The controller passes one policy through export and check,
   records matching source-knowledge hashes, and never falls back to `off`
   after validation failure without an explicit refreshed preparation.

   Reference profile, single wiki:

   ```bash
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site \
     --format mkdocs --profile reference --front-matter --output-format json
   ```

   User profile with an explicitly selected public-portable native summary and corroborated public identity:

   ```bash
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site \
     --format mkdocs --profile user --site-name <project> \
     --knowledge-metadata summary --knowledge-profile public-portable \
     --knowledge-public-repository-identity <identity> \
     --front-matter --output-format json
   ```

   Multi-wiki hub (see the `doc-hub` skill first if hub aggregation itself, not just publishing, is the goal):

   ```bash
   llm-wiki site export --wiki-root sources/code_wikis --out-dir site \
     --format docusaurus --profile reference --front-matter \
     --output-format json
   ```

   Confirm `ok: true`, `issues: []`, and that the export report matches the frozen format, profile, site name, and distribution mode before proceeding. Never build on top of a failed or mismatched export.

2. **Check.** Reference profile:

   ```bash
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
     --profile reference --output-format json
   # or the matching --wiki-root form for hub mode
   ```

   User profile:

   ```bash
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
     --profile user --site-name <project> \
     --knowledge-metadata summary --knowledge-profile public-portable \
     --knowledge-public-repository-identity <identity> \
     --output-format json
   ```

   Confirm `ok: true`, `0` issues. For hub mode use the matching `--wiki-root`, explicit `--profile reference`, and the same knowledge-selection options used at export. A selected knowledge check rejects missing or mismatched projected metadata; omitting the selected options is itself a workflow-selection mismatch and must stop before the check. This is the last purely deterministic gate before the builder.

3. **Detect whether the real builder is available, and run it only if so.**
   For `--format mkdocs`: check `mkdocs --version` (or the project's pinned dependency, e.g. in `requirements-docs.txt`/`pyproject.toml`).
   For `--format docusaurus`: check for `package.json` + `node_modules` in the target site directory, or that `npm`/`npx` resolves. If the builder isn't installed, say so explicitly and stop after step 2 — do not attempt to install a toolchain on the user's behalf without being asked.

   ```bash
   # mkdocs
   mkdocs build --strict -f site/mkdocs.yml --site-dir _site-http
   # docusaurus (from the exported site directory, if it has its own package.json)
   npm run build
   ```

   Surface the real builder's own errors verbatim — this skill does not reinterpret mkdocs/docusaurus build failures, since `site check` already covers the checks `llm-wiki` itself can make. Never reuse an existing build as evidence unless its recorded selection is byte-for-byte the frozen tuple. HTTP and file workflows use different output directories.

4. **Validate the built site with the same selection.** For the hosted user-profile example above:

   ```bash
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
     --built-site-dir _site-http --link-mode http \
     --profile user --site-name <project> \
     --knowledge-metadata summary --knowledge-profile public-portable \
     --knowledge-public-repository-identity <identity> \
     --output-format json
   ```

   Direct-file handoffs use file-friendly export plus file-mode validation in a distinct mirror and build directory, while preserving the same profile/site/projection selection:

   ```bash
   llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-file \
     --format mkdocs --profile user --site-name <project> --file-friendly \
     --knowledge-metadata summary --knowledge-profile public-portable \
     --knowledge-public-repository-identity <identity> \
     --front-matter --output-format json
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-file \
     --profile user --site-name <project> \
     --knowledge-metadata summary --knowledge-profile public-portable \
     --knowledge-public-repository-identity <identity> \
     --output-format json
   mkdocs build --strict -f site-file/mkdocs.yml --site-dir _site-file
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-file \
     --built-site-dir _site-file --link-mode file \
     --profile user --site-name <project> \
     --knowledge-metadata summary --knowledge-profile public-portable \
     --knowledge-public-repository-identity <identity> \
     --output-format json
   ```

   The final built check is still a full mirror/profile/projection check, not only an HTML link scan. Therefore a user-only quality failure must stop here even if a reference-profile check would pass. A file-mode check cannot validate an HTTP build, and an HTTP-mode check cannot validate a file-friendly build.

5. **Hand off the deploy step, don't perform it.** State the built output location and the deploy mechanism the user named (GitHub Pages action, `rsync` to an internal host, etc.) as a next step. Actually pushing to a hosting target, publishing a GitHub Pages branch, or deploying is a visible, hard-to-reverse action — confirm with the user before doing it, even if they asked for "publish-docs" broadly; "publish" the export pipeline is safe to run repeatedly, an actual deploy is not.

   In `external_agent_docs`, also return the complete frozen publication
   selection, export/build/check evidence hashes, unresolved deferrals, and
   exact local output path to the supervisor. Never stage or commit
   source/input-wiki files.

6. **CI wiring (optional).** If the user wants this as a CI step rather than an interactive run, wire export → check → build → built-link check into the existing CI workflow alongside `ci-check` (see [reference.md](reference.md) for the pattern) rather than creating a second, parallel docs-publishing pipeline.

## Context budget

This skill has almost no LLM judgment budget by design — every step is a deterministic command whose JSON/exit-code result is the primary workflow evidence. Native metadata redaction does not sanitize canonical prose or media, so public publication still requires its separate content review. Content authoring belongs to `wiki-sync`, `doc-review`, or `user-docs-author`, not this workflow.
