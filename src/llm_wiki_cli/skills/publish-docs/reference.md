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
# Single wiki, mkdocs
llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site \
  --format mkdocs --front-matter --output-format json
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site --output-format json
mkdocs build --strict -f site/mkdocs.yml   # only if `mkdocs` is installed

# Hub, docusaurus (requires an existing Docusaurus app to receive the output)
llm-wiki site export --wiki-root sources/code_wikis --out-dir site \
  --format docusaurus --front-matter --output-format json
llm-wiki site check --wiki-root sources/code_wikis --out-dir site --output-format json
# then, from the Docusaurus app root:
npm run build
```

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
