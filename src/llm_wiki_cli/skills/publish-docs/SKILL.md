---
name: publish-docs
description: Build and hand off a publishable site from one validated wiki or a hub already exported by `doc-hub`. Use for builder detection, build/check, and deploy handoff; never aggregate hub sources or deploy without confirmation.
---

# publish-docs

Turn one validated wiki, or the checked mirror returned by `doc-hub`, into an actually-buildable, optionally deployed site. This skill owns **single-wiki publication export, builder detection, the real build, built-site validation, and deploy handoff**. `doc-hub` exclusively owns multi-wiki source selection, aggregation, hub export, and the first hub check. The default export is a reference profile for a single wiki; use `--profile user` only when a human documentation layer exists. The loop is: **freeze or accept the exact publication selection → export a single wiki or verify the handed-off hub → run the real builder when installed → validate the same selection against that build → hand off deploy**. See [reference.md](reference.md) for the immutable selection, format/host pairings, builder detection, distribution modes, and CI wiring.

If user docs need captured examples before publishing, run `usage-examples` first; this skill only validates and publishes the resulting media-bearing site.

## Preconditions

- A validated single wiki or a complete checked-mirror handoff from `doc-hub`
  already exists. Use
  `wiki-bootstrap` only when the target is absent or is the exact untouched
  `llm-wiki init` scaffold. Route every other target through `wiki-sync` or
  `llm-wiki migrate --dry-run`; bootstrap is never an existing-wiki repair
  path. This skill does not generate wiki content or aggregate hub sources.
  "Current" native evidence
  means only unchanged since its recorded observation, not true, approved,
  secure, or runtime-current.
- For `--profile user`, a non-default `--site-name` and at least one guide page under `guides/` already exist — run `onboarding-guide` first if only persona guides are missing, or `user-docs-author` first if the whole user-docs narrative layer needs to be filled from deterministic site evidence.
- The user has said where this is being published (GitHub Pages, an internal MkDocs/Docusaurus host, or "just give me a static mirror") — that choice picks the export `--format` and whether a real build step applies at all (`--format plain` has no corresponding builder).
- If a real builder (`mkdocs`, `npm`/docusaurus) will be invoked, confirm it is actually installed before attempting it — this skill fails closed and reports clearly rather than half-running a build.
- In `external_agent_docs`, semantic readiness, the user-doc result, and the
  separate review ledger/result are supervisor-verified. `publish_ready` is not
  inferred from worker prose or a green export alone. Use only workspace wiki,
  site, and `_site` paths; deployment remains separately authorized.

## Steps

1. **Freeze one publication selection; export only a single wiki.** Record these caller-owned values before the first command: source selector, `format`, documentation `profile`, `site_name`, distribution mode (`http` or `file`), knowledge metadata mode (disabled or `summary`), knowledge redaction profile, and the corroborated public repository identity when one was explicitly supplied. These values are immutable for this run. For hub mode, accept the exact tuple and checked output from `doc-hub`; do not select sources or run `site export --wiki-root` here.

   Export records the immutable policy in
   `.llm-wiki-site-selection.json` and writes the non-sensitive
   `llm-wiki-site-selection.json` build marker. Every check must repeat
   `--format`, profile, site name, distribution mode (for a built check), and
   the exact knowledge options. Abort on a receipt, argv, or report mismatch;
   do not treat a green check under defaults as evidence for another
   selection. Changing policy in a receipted output directory is rejected
   before writes, so use a distinct output directory. Same-policy regeneration
   retains the selection identity and records a new content-specific export
   identity.

   When native metadata is selected, follow the complete contract at
   `.claude/skills/wiki-reference/references/knowledge-consumption.md` for
   Claude or `.llm-wiki/skills/wiki-reference/references/knowledge-consumption.md`
   for another configured agent. Apply the projection/receipt boundary at
   `.claude/skills/wiki-reference/references/publishing.md` or
   `.llm-wiki/skills/wiki-reference/references/publishing.md`. Schedule
   export/check/build through
   `.claude/skills/wiki-reference/references/resources-context.md` or
   `.llm-wiki/skills/wiki-reference/references/resources-context.md`. Carry
   every limitation unchanged, never initialize governance for publication,
   and serialize heavy gates when capacity is unknown; the supervisor owns
   fan-out.

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

   Multi-wiki hub: require `doc-hub` to have exported and checked this exact
   selection. Accept its checked mirror, receipt, and immutable selection
   without exporting again; step 2 performs the one publication-owned recheck.

   Confirm `ok: true`, `issues: []`, and that a single-wiki export or hub
   handoff names the frozen format, profile, site name, distribution mode,
   source set, and optional knowledge selection. Never build on failed or
   mismatched evidence.

2. **Check.** Reference profile:

   ```bash
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
     --format mkdocs --link-mode http --profile reference --output-format json
   # or the matching --wiki-root form for hub mode
   ```

   User profile:

   ```bash
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
     --format mkdocs --link-mode http --profile user --site-name <project> \
     --knowledge-metadata summary --knowledge-profile public-portable \
     --knowledge-public-repository-identity <identity> \
     --output-format json
   ```

   Checked hub handoff:

   ```bash
   llm-wiki site check --wiki-root sources/code_wikis --out-dir site \
     --format docusaurus --link-mode http --profile reference \
     --output-format json
   ```

   Confirm `ok: true`, `0` issues. For hub mode this is the publication-owned
   recheck of the exact `doc-hub` handoff: use matching `--wiki-root`, explicit
   `--profile reference`, and the same knowledge-selection options. A selected
   knowledge check rejects missing or mismatched projected metadata; omitting
   selected options must stop before the builder.

3. **Detect whether the real builder is available, and run it only if so.**
   For `--format mkdocs`: check `mkdocs --version` (or the project's pinned dependency, e.g. in `requirements-docs.txt`/`pyproject.toml`).
   For `--format docusaurus`: check for `package.json` + `node_modules` in the target site directory, or that `npm`/`npx` resolves. If the builder isn't installed, say so explicitly and stop after step 2 — do not attempt to install a toolchain on the user's behalf without being asked.

   ```bash
   # mkdocs
   mkdocs build --strict -f site/mkdocs.yml --site-dir _site-http
   # docusaurus (after placing the export in an existing app's docs directory)
   npm run build
   cp site/llm-wiki-site-selection.json build/llm-wiki-site-selection.json
   ```

   Surface the real builder's own errors verbatim — this skill does not reinterpret mkdocs/docusaurus build failures, since `site check` already covers the checks `llm-wiki` itself can make. Never reuse an existing build as evidence unless its recorded selection is byte-for-byte the frozen tuple. HTTP and file workflows use different output directories.

   MkDocs carries the marker from its `docs_dir: .` into the built root
   automatically. Docusaurus and custom builders must copy the marker into the
   built root as shown; a build without the exact marker is not checkable
   evidence.

4. **Validate the built site with the same selection.** For the hosted user-profile example above:

   ```bash
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
     --format mkdocs --built-site-dir _site-http --link-mode http \
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
     --format mkdocs --link-mode file --profile user --site-name <project> \
     --knowledge-metadata summary --knowledge-profile public-portable \
     --knowledge-public-repository-identity <identity> \
     --output-format json
   mkdocs build --strict -f site-file/mkdocs.yml --site-dir _site-file
   llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-file \
     --format mkdocs --built-site-dir _site-file --link-mode file \
     --profile user --site-name <project> \
     --knowledge-metadata summary --knowledge-profile public-portable \
     --knowledge-public-repository-identity <identity> \
     --output-format json
   ```

   The final built check is still a full receipt/mirror/profile/projection
   check, not only an HTML link scan. It requires the matching marker at the
   built root, so a stale build or cross-mode build is rejected even when its
   links happen to work. A user-only quality failure must stop here even if a
   reference-profile check would pass.

5. **Hand off the deploy step, don't perform it.** State the built output location and the deploy mechanism the user named (GitHub Pages action, `rsync` to an internal host, etc.) as a next step. Actually pushing to a hosting target, publishing a GitHub Pages branch, or deploying is a visible, hard-to-reverse action — confirm with the user before doing it, even if they asked for "publish-docs" broadly; "publish" the export pipeline is safe to run repeatedly, an actual deploy is not.

   In `external_agent_docs`, also return the complete frozen publication
   selection, export/build/check evidence hashes, unresolved deferrals, and
   exact local output path to the supervisor. Never stage or commit
   source/input-wiki files.

6. **CI wiring (optional).** If the user wants this as a CI step rather than an interactive run, wire export → check → build → built-link check into the existing CI workflow alongside `ci-check` (see [reference.md](reference.md) for the pattern) rather than creating a second, parallel docs-publishing pipeline.

## Context budget

This skill has almost no LLM judgment budget by design — every step is a deterministic command whose JSON/exit-code result is the primary workflow evidence. Native metadata redaction does not sanitize canonical prose or media, so public publication still requires its separate content review. Content authoring belongs to `wiki-sync`, `doc-review`, or `user-docs-author`, not this workflow.

## Ownership compatibility

All `llm-wiki site` CLI forms remain supported. Existing callers that used
this skill to begin a multi-wiki export should run `doc-hub` for aggregation,
export, and the first check, then resume here with the returned checked mirror
and immutable selection. Single-wiki export/build behavior is unchanged.
