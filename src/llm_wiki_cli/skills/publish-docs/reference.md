# publish-docs reference

Supporting detail for [SKILL.md](SKILL.md).

## Format/builder pairing

| `--format` | What export generates | Real builder | Ready to build as-is? |
|---|---|---|---|
| `mkdocs` | Markdown pages + a generated `mkdocs.yml` with registry-ordered navigation | `mkdocs build` | Yes — `mkdocs.yml` is self-contained; `mkdocs build` can run directly against `--out-dir`. |
| `docusaurus` | Markdown pages with Docusaurus front matter + generated `sidebars.json` | `npm run build` (or `npx docusaurus build`) inside an existing Docusaurus app | No — export does not generate `docusaurus.config.js` or `package.json`. The exported content is meant to be copied or symlinked into an existing Docusaurus app's `docs/` directory, with `sidebars.json` wired into that app's config. |
| `plain` | Plain Markdown mirror, optional front matter | None | It's already the deliverable — there is no build step; "publishing" it means hosting the Markdown (or a Markdown-rendering static host) directly. |

## Commands

```bash
# Hosted docs, single wiki, mkdocs reference profile
llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site \
  --format mkdocs --profile reference --front-matter --output-format json
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
  --profile reference --output-format json
mkdocs build --strict -f site/mkdocs.yml   # only if `mkdocs` is installed
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site \
  --built-site-dir _site --link-mode http --output-format json

# Human/user docs, direct-file handoff
llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-file \
  --format mkdocs --profile user --site-name <project> --file-friendly \
  --front-matter --output-format json
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-file \
  --profile user --site-name <project> --output-format json
mkdocs build --strict -f site-file/mkdocs.yml
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-file \
  --built-site-dir _site --link-mode file --output-format json

# Hub, docusaurus (requires an existing Docusaurus app to receive the output)
llm-wiki site export --wiki-root sources/code_wikis --out-dir site \
  --format docusaurus --front-matter --output-format json
llm-wiki site check --wiki-root sources/code_wikis --out-dir site --output-format json
# then, from the Docusaurus app root:
npm run build
```

## Distribution modes

Hosted docs use MkDocs' default directory URLs and validate the built site with `--link-mode http`. Direct handoff docs use `--file-friendly`, which emits `use_directory_urls: false`, and validate built HTML with `--link-mode file`. Pair the export mode and check mode deliberately; a site that is structurally valid for HTTP routing can still be a poor direct-file artifact.

The shorthand to remember is `site check --built-site-dir <built> --link-mode http|file` after the real builder has produced HTML.

User-profile publishing is stricter than reference publishing. Before `site export --profile user`, ensure `guides/` contains at least one page and pass a non-default `--site-name`; then run `site check --profile user` so missing guides, default site names, overlarge root indexes, and placeholder text are caught before build. If guides or narrative docs are missing beyond one persona page, run `user-docs-author` before publishing so deterministic evidence feeds the semantic user-docs pass.

## Builder detection (fail closed)

Before attempting a real build:

```bash
command -v mkdocs        # mkdocs format
command -v npm && command -v npx   # docusaurus format
```

If neither resolves, stop after `site check` and report explicitly: "export and validation passed; the real builder is not installed, so no build was attempted." Do not install a toolchain on the user's behalf without being asked — that is a dependency-install action, not a docs-publishing one.

## CI wiring pattern

Add export → check → build as a job step alongside the existing `ci-check` gate, not as a competing pipeline:

```yaml
- name: Export static site
  run: llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site --format mkdocs --output-format json
- name: Check static site
  run: llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site --output-format json
- name: Build site
  run: mkdocs build --strict -f site/mkdocs.yml
- name: Deploy
  # user's existing deploy action (GitHub Pages, internal host, etc.) — this
  # skill does not choose or configure a deploy target on its own
```

## Failure modes

| Symptom | Cause | Response |
|---|---|---|
| `site export`/`site check` fails | Stale or invalid wiki | Stop; run `wiki-sync` first — never build on top of a failed check. |
| `mkdocs build --strict` fails | A real MkDocs plugin/theme issue outside `llm-wiki`'s validation scope | Surface the builder's own error; `site check` already covers what `llm-wiki` can validate without the real tool. |
| Docusaurus build fails with "docs not found" | Exported output wasn't placed into an existing Docusaurus app's `docs/` directory | Confirm the target app structure before exporting; this format is not standalone-buildable. |
| User expects a deployed site after running this skill | Deploy is a separate, confirmed action (step 4 of the SKILL) | Don't deploy without an explicit ask — hand off the build output and the deploy mechanism instead. |

## Usage examples handoff

Run `usage-examples` before publishing when user docs need screenshots, recordings, or command-output examples. `publish-docs` validates the exported and built media targets but does not capture or attach examples itself.

## External documentation workspace

Enter only after supervisor verification of semantic readiness, user-doc exit
criteria, and the separately auditable review packet/result. Use the recorded
site name and distribution mode; an unverified/stale wiki limitation remains in
the final report and cannot become source-verified `publish_ready`. Export,
builder output, and checks stay under the workspace. Return deployment as an
explicit handoff and preserve source/input-wiki byte identity.
