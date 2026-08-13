# user-docs-author reference

## Contents

- [Evidence Sources](#evidence-sources)
- [Page Contract](#page-contract)
- [Command Matrix](#command-matrix)
- [External documentation workspace](#external-documentation-workspace)
- [Adjustment Loop](#adjustment-loop)
- [Failure Modes](#failure-modes)
- [Usage examples handoff](#usage-examples-handoff)

Use this reference after the main skill confirms that a full user-docs pass is needed. Keep the pass deterministic-first: commands establish evidence, the agent writes semantic prose, and validation decides what gets adjusted.

## Evidence Sources

| Evidence | Use for | Notes |
| --- | --- | --- |
| `llm-wiki sync` text output | Current generated structure, relinked guide pages, stale source detection | `sync` has no JSON output flag. If it rewrites generated pages, review the diff before authoring on top of it. |
| `llm-wiki lint --strict` | Broken links, orphan pages, unsafe wiki structure | Lint failures are blocking unless the finding is clearly unrelated and deferred with rationale. |
| `llm-wiki ci-check --format json` | Whole-wiki gate status | Use after authoring, not as a substitute for reading affected pages. |
| `llm-wiki site export --profile user` | User-site mirror generation and export metadata | Export output is disposable distribution output, not an authoring surface. |
| `llm-wiki site check --profile user` | Missing guide surface, default site name, placeholder primary docs, unsafe links | These issues seed the first adjustment worklist. |
| `llm-wiki site check --built-site-dir ... --link-mode http` | Hosted built-site link behavior | Use for GitHub Pages or hosted web routing. |
| `llm-wiki site check --built-site-dir ... --link-mode file` | Direct file handoff link behavior | Use after a file-friendly export/build path. |
| `index.md` and `.llm-wiki-surface.json` | Canonical page inventory and site profile scope | Start here before reading individual pages. |
| Generated `flows/`, `modules/`, `entities/`, and `dependencies/` pages | Product/workflow facts that guides may cite | Link to the page that supports each claim. |
| Generated `infrastructure/` pages | Bounded source-bound observations with semantic `## Notes` | Bootstrap creates the initial observation and sync regenerates it incrementally. Treat it as current structural evidence only when its recorded basis matches a live freshness evaluation; recent sync alone is not assurance. Confirm operational claims from current raw source or a fresh dedicated extraction, and never copy secrets, private endpoints, or sensitive host details into guide prose. |
| Source files | Last-resort confirmation for facts missing from wiki evidence | If source evidence is needed, prefer updating the wiki/source docs that should have carried it. |

For structured `external_agent_docs` results, `claims_evidence_pages` remains
the compatible page-level citation list. Optional
`llm-wiki-documentation-claim-evidence/v1` records qualify selected claims with
the current exact UID/locator, optional section locator, structural evidence,
freshness, lifecycle/section review, and explicit query/analyzer bounds. Use
`safe_evidence_link` for a publishable canonical page or fragment;
`internal_evidence_ref`, when needed, stays under
`.llm-wiki-docs/evidence/`. The supervisor preflights structure before refresh,
then recomputes every native field live/read-only only for a verified-current
source-bound run; other runs reconcile against the snapshot with freshness
unevaluated. It rejects stale or fabricated records.

## Page Contract

Author primarily in `guides/*.md`. Use existing human-owned semantic pages only when the wiki already has that convention. Do not edit generated blocks, generated diagrams, generated tables, generated front matter, `.llm-wiki-manifest.json`, `.llm-wiki-surface.json`, `.llm-wiki-knowledge.json`, exported site files, or builder output.

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
| Sync current wiki | `llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs 1` |
| Strict lint | `llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki` |
| Whole-wiki gate | `llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json` |
| Hosted user export | `llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user-http --format mkdocs --profile user --site-name <project> --front-matter --output-format json` |
| Hosted user check | `llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-http --format mkdocs --link-mode http --profile user --site-name <project> --output-format json` |
| Hosted built-link check | `llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-http --format mkdocs --built-site-dir _site-user-http --link-mode http --profile user --site-name <project> --output-format json` |
| Direct-file export | `llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site-user-file --format mkdocs --profile user --site-name <project> --file-friendly --front-matter --output-format json` |
| Direct-file check | `llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-file --format mkdocs --link-mode file --profile user --site-name <project> --output-format json` |
| File handoff built-link check | `llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site-user-file --format mkdocs --built-site-dir _site-user-file --link-mode file --profile user --site-name <project> --output-format json` |

For a direct-file handoff, the complete order is file-friendly export to
`site-user-file`, matching user-profile check, real MkDocs build into
`_site-user-file`, then file-mode built-link check. Hosted output uses
`site-user-http` and `_site-user-http`. Changing policy in a receipted mirror
fails before writes, and reusing either mode's mirror/build for the other is
invalid evidence.

Each export writes `.llm-wiki-site-selection.json` and the non-sensitive
`llm-wiki-site-selection.json` marker. Mirror checks require the complete
matching receipt. MkDocs carries the marker to the built root; built checks
reject a missing, stale, or mismatched marker. Legacy output therefore needs a
fresh export and build.

Freeze one native publication row and apply its suffix unchanged to the mirror
export, mirror check, and built-site check:

| Policy | Site command suffix | Standalone docs policy |
| --- | --- | --- |
| `off` | Omit all knowledge options. | `docs prepare --knowledge-mode off`; this is also the explicit fallback after an enriched failure. |
| `public-portable` | `--knowledge-metadata summary --knowledge-profile public-portable`, plus the exact corroborated `--knowledge-public-repository-identity` only when selected. | `docs prepare --knowledge-mode public-portable` with the matching optional identity; `docs export` may assert both values. |
| `internal` | `--knowledge-metadata summary --knowledge-profile internal`; use only for an explicitly authorized internal publication target. | `docs prepare --knowledge-mode internal`; `docs export --knowledge-mode internal` may assert it. |

Standalone export loads a snapshot-only native read view, preserves freshness
as not evaluated, and records the same source-knowledge hash for export and
check. Projection failure or a changed hash stops the run; it never silently
retries without enrichment. Public projection redaction is metadata-only, so
review canonical prose and media independently.

## External documentation workspace

- Enter only when `llm-wiki-documentation-semantic-readiness/v1` records
  `ready_for_user_docs: true` and supervisor verification agrees.
- Use the packet's recorded project purpose, audiences, per-audience jobs, site
  name, source availability, and freshness. Do not conduct a second intake.
- A grounded imported enrichment can satisfy work as `reused`; unverified or
  stale important claims become deferred-docs items and stay out of primary
  pages.
- Wiki-only runs read the workspace snapshot and linked wiki evidence. They do
  not invent source claims or silently upgrade freshness.
- Write only semantic workspace-wiki pages and the assigned result. Export and
  `_site` remain derived; source and input wiki remain byte-identical.
- Use optional `claim_evidence` only for claims that benefit from exact
  concept/section qualification. Keep legacy page citations, never copy raw
  relationship evidence into a public link, and let the supervisor recompute
  identity, freshness, lifecycle/review, and all bounds.

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

## Usage examples handoff

When guides are evidence-backed and lint/site-check clean, use `usage-examples` for screenshots, recordings, captions, mirrored asset paths, and media validation. Keep this skill focused on prose and checker-driven adjustment.
