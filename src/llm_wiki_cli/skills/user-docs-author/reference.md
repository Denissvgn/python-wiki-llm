# user-docs-author reference

Use this reference after the main skill confirms that a full user-docs pass is needed. Keep the pass deterministic-first: commands establish evidence, the agent writes semantic prose, and validation decides what gets adjusted.

## Evidence Sources

| Evidence | Use for | Notes |
| --- | --- | --- |
| `llm-wiki sync --output-format json` or text output | Current generated structure, relinked guide pages, stale source detection | If sync rewrites generated pages, review the diff before authoring on top of it. |
| `llm-wiki lint --strict` | Broken links, orphan pages, unsafe wiki structure | Lint failures are blocking unless the finding is clearly unrelated and deferred with rationale. |
| `llm-wiki ci-check --format json` | Whole-wiki gate status | Use after authoring, not as a substitute for reading affected pages. |
| `llm-wiki site export --profile user` | User-site mirror generation and export metadata | Export output is disposable distribution output, not an authoring surface. |
| `llm-wiki site check --profile user` | Missing guide surface, default site name, placeholder primary docs, unsafe links | These issues seed the first adjustment worklist. |
| `llm-wiki site check --built-site-dir ... --link-mode http` | Hosted built-site link behavior | Use for GitHub Pages or hosted web routing. |
| `llm-wiki site check --built-site-dir ... --link-mode file` | Direct file handoff link behavior | Use after a file-friendly export/build path. |
| `index.md` and `.llm-wiki-surface.json` | Canonical page inventory and site profile scope | Start here before reading individual pages. |
| Generated `flows/`, `modules/`, `entities/`, `dependencies/`, `infrastructure/` pages | Product/workflow facts that guides may cite | Link to the page that supports each claim. |
| Source files | Last-resort confirmation for facts missing from wiki evidence | If source evidence is needed, prefer updating the wiki/source docs that should have carried it. |

## Page Contract

Author primarily in `guides/*.md`. Use existing human-owned semantic pages only when the wiki already has that convention. Do not edit generated blocks, generated diagrams, generated tables, generated front matter, exported site files, or builder output.

Each user-facing guide should contain:

- A short audience statement and prerequisite context.
- A plain-language task/workflow overview.
- A guided reading path with relative links to existing wiki evidence.
- A "first successful task" or "common next task" section when source evidence supports it.
- A "deferred-docs" section or sibling report entries for missing evidence, ambiguous behavior, or topics outside the pass.

Use a compact deferred-docs format:

```markdown
## Deferred Docs

| Topic | Missing evidence | Next evidence source |
| --- | --- | --- |
| <topic> | <what cannot be proven yet> | <wiki page, source file, issue, or owner to check> |
```

Do not invent facts to avoid a deferred-docs row. Deferred work is better than plausible but unsupported user guidance.

## Command Matrix

Use the project-specific paths when they differ from these examples.

| Stage | Command |
| --- | --- |
| Sync current wiki | `llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs auto` |
| Strict lint | `llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki` |
| Whole-wiki gate | `llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json` |
| User export | `llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user --format mkdocs --profile user --site-name <project> --front-matter --output-format json` |
| User check | `llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user --profile user --site-name <project> --output-format json` |
| Hosted built-link check | `llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user --built-site-dir _site --link-mode http --profile user --site-name <project> --output-format json` |
| File handoff built-link check | `llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user --built-site-dir _site --link-mode file --profile user --site-name <project> --output-format json` |

For a direct-file handoff, pair the file-mode check with `site export --profile user --file-friendly`. For hosted docs, prefer `--link-mode http` after the real builder succeeds. The shorthand for both built-site modes is `site check --built-site-dir <built> --link-mode http|file` after export/check and the real builder succeed.

## Adjustment Loop

1. Normalize validation output into a worklist: command, issue id/category, affected page, cited evidence, intended edit surface.
2. Discard anything outside semantic wiki prose unless the user explicitly requested source or generator changes.
3. Fix only validation-backed issues or evidence-backed clarity gaps.
4. Re-run the smallest deterministic command that reported the issue, then the full sync/lint/site-check set before completion.
5. Record unresolved items as deferred-docs entries with the missing evidence and next action.

`doc-review` output can feed this loop directly. Keep its classification vocabulary rather than inventing a parallel status scheme.

## Failure Modes

| Failure | What it means | Response |
| --- | --- | --- |
| `sync` rewrites generated pages | The wiki was stale before authoring | Review deterministic changes first; resume authoring only after lint is clean. |
| Missing `guides/` pages | User-profile docs have no human narrative layer | Create evidence-linked guide pages or defer with explicit missing evidence. |
| Default or generic site name | User profile lacks product identity | Use a real site name from repo evidence or ask the user. |
| Placeholder or bootstrap prose in primary docs | A generated/reference page is being promoted to user docs | Replace only human-owned prose with evidence-backed narrative, or defer if no evidence supports it. |
| Unsupported workflow claim | The agent cannot cite wiki/source evidence | Add deferred-docs; do not invent facts. |
| Builder unavailable | Deterministic export/check can run, but built-site validation cannot | Report export/check results and the missing builder; do not install toolchains without approval. |
| Built-link failure | Exported docs and built docs disagree for the chosen distribution mode | Fix links in semantic wiki pages or distribution settings, then re-run `site check --built-site-dir` with the relevant link mode. |
