# Assistant Docsite User Documentation Improvement Backlog

> For agentic workers: REQUIRED SUB-SKILL: Use `superpowers:executing-plans`
> to execute this backlog task-by-task. Update task status in this file as work
> lands, preserve unrelated worktree changes, and commit each completed
> implementation task as a scoped change unless the user explicitly asks for a
> different commit strategy.

**Goal:** Turn the Assistant docsite dogfood findings into an implementation
backlog that makes static-site output navigable for the intended distribution
mode and creates a user-facing documentation profile distinct from the existing
agent/reference mirror.

**Architecture:** Keep the current generated wiki and static-site mirror as the
default reference profile. Add explicit distribution/link validation and a
separate human-docs profile on top of the existing `site export|check`,
`onboarding-guide`, `publish-docs`, and `doc-review` surfaces.

**Tech Stack:** Python 3.9+, argparse CLI, stdlib Markdown/HTML scanning,
MkDocs config generation, pytest, Ruff, bundled skill Markdown, generated wiki
surfaces, sibling wiki docs.

---

Date: 2026-07-05
Source ADR: `reports/assistant_docsite_user_docs_improvement_analysis_2026-07-05.md`
Status: Completed
Owner: Unassigned

## Scope

This backlog addresses the two concrete failures from the Assistant docsite
dogfood run:

- Built MkDocs links were valid for HTTP routing but fragile when the generated
  `_site/index.html` was opened directly from disk.
- The published root page read like a raw wiki bootstrap inventory instead of
  product documentation for people.

The existing reference mirror remains valuable for LLM agents and maintainers.
This backlog must not remove that behavior. New user-facing behavior should be
opt-in until the migration impact is known.

## Out Of Scope

- Editing `/mnt/data/projects/Assistant` source files or committed
  documentation. Assistant is a read-only dogfood target for this backlog.
- Deploying a generated site to a public host.
- Replacing every generated entity/module page with authored prose.
- Using an LLM quality score as the only gate for published documentation.
- Making Docusaurus a fully scaffolded app if the current output remains a
  metadata mirror.

## Delivery Rules

- Use the project virtual environment for every Python command:
  `.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/ruff`.
- Keep implementation portable across Windows, macOS, Ubuntu, and Python 3.9+.
- Preserve existing defaults unless a task explicitly introduces an opt-in flag
  or profile.
- Keep target repositories read-only. When using Assistant dogfood, generate
  output under a temporary runner or this repo's own report paths only.
- Keep source wiki pages as the source of truth. Static-site output is a derived
  distribution surface.
- Update `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki` separately when a
  task changes user-facing CLI behavior, bundled skill behavior, or published
  docs workflow guidance.
- For ignored `reports/` artifacts, verify ignore behavior with
  `git check-ignore -v` and stage intentionally with `git add -f` only when the
  user asks for a commit.

## Dependency Order

| ID | Title | Priority | Depends on | Type |
| --- | --- | --- | --- | --- |
| ADU-001 | Built HTML link validation | P0 | None | Code/tests |
| ADU-002 | File-friendly MkDocs export mode | P0 | ADU-001 | Code/tests/docs |
| ADU-003 | Human docs profile and generated-reference split | P0 | ADU-001 | Code/tests |
| ADU-004 | Human-profile quality gates | P0 | ADU-003 | Code/tests |
| ADU-005 | Human navigation grouping and noise policy | P1 | ADU-003, ADU-004 | Code/tests |
| ADU-006 | Skill contract updates for user docs | P1 | ADU-002, ADU-004 | Skills/docs/tests |
| ADU-007 | Assistant human-docs dogfood confirmation | P1 | ADU-001 through ADU-006 | Dogfood report |
| ADU-008 | Public docs, sibling wiki, and backlog closeout | P1 | ADU-001 through ADU-007 | Docs/report |

## File Map

Likely code touch points:

- `src/llm_wiki_cli/services/site_export.py`
- `src/llm_wiki_cli/commands/site_cmd.py`
- `src/llm_wiki_cli/cli.py`
- `src/llm_wiki_cli/services/wiki_surface.py`
- New focused helper if the implementation would keep `site_export.py` from
  growing further: `src/llm_wiki_cli/services/site_html_check.py`

Likely skill and docs touch points:

- `src/llm_wiki_cli/skills/publish-docs/SKILL.md`
- `src/llm_wiki_cli/skills/publish-docs/reference.md`
- `src/llm_wiki_cli/skills/onboarding-guide/SKILL.md`
- `src/llm_wiki_cli/skills/onboarding-guide/reference.md`
- `src/llm_wiki_cli/skills/doc-review/SKILL.md`
- `src/llm_wiki_cli/skills/doc-review/reference.md`
- `README.md`
- `src/llm_wiki_cli/services/schema.py`
- Sibling wiki command/workflow pages under
  `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki`

Likely test touch points:

- `tests/test_site_export.py`
- `tests/test_cli.py`
- `tests/test_skills.py`
- `tests/test_package_metadata.py`
- New focused tests if needed: `tests/test_site_html_check.py`

## Shared Verification Baseline

Run the focused verification named by each task. For code or CLI behavior
changes, also run:

```bash
.venv/bin/pytest tests/test_site_export.py tests/test_cli.py -q
.venv/bin/python -m compileall src tests
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
git diff --check
```

For skill or package-data changes, also run:

```bash
.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py -q
.venv/bin/python -m compileall src tests
git diff --check
```

For report-only dogfood or closeout tasks, run:

```bash
git diff --check -- reports/assistant_docsite_user_docs_confirmation_2026-07-05.md
git diff --check -- reports/assistant_docsite_user_docs_closure_2026-07-05.md
```

Run the command that matches the report changed by the active task.

## ADU-001 - Built HTML Link Validation

Priority: P0
Status: Completed
Depends on: None
Type: Code/tests

### Goal

Make `llm-wiki` able to validate links in built static-site HTML, with explicit
`http` and `file` distribution modes.

### Developer Context

`check_site_mirror()` currently validates the exported Markdown mirror: expected
pages exist, Markdown links resolve inside the mirror, front matter is well
formed, and front-matter ids are consistent. It does not parse the built
`_site/**/*.html` output.

The Assistant dogfood output exposed the gap. Links such as
`entities/ActionItem/` resolve under MkDocs HTTP routing because the real target
is `entities/ActionItem/index.html`. They are risky for a direct filesystem
handoff from `_site/index.html`, where browser behavior for directory-style
links is not a reliable product contract.

The implementation should avoid adding a heavyweight HTML dependency. A small
stdlib `html.parser.HTMLParser` subclass is enough to collect `href` values from
`a`, `link`, and related tags.

### Files

- Create or modify: `src/llm_wiki_cli/services/site_html_check.py`
- Modify: `src/llm_wiki_cli/services/site_export.py`
- Modify: `src/llm_wiki_cli/commands/site_cmd.py`
- Modify: `src/llm_wiki_cli/cli.py`
- Test: `tests/test_site_export.py`
- Test: `tests/test_cli.py`
- Optional focused test split: `tests/test_site_html_check.py`

### Tasks

- [x] Add a built-site HTML scanner that walks `*.html` under a caller-provided
  built site directory.
- [x] Collect internal `href` values while ignoring external schemes:
  `http:`, `https:`, `mailto:`, `tel:`, `data:`, and `javascript:`.
- [x] Preserve anchor handling: hash-only links stay on the current page, and
  `page.html#section` resolves the file target first.
- [x] Implement `link_mode="http"` resolution:
  - `foo/` resolves to `foo/index.html`.
  - `foo` resolves to `foo/index.html` or `foo.html`.
  - `foo.html` resolves to that exact file.
- [x] Implement `link_mode="file"` resolution:
  - `foo.html` resolves to that exact file.
  - `foo/index.html` resolves to that exact file.
  - `foo/` is reported as a `file_directory_url` issue even when
    `foo/index.html` exists, because it is not a direct-file-safe handoff link.
- [x] Report issues with categories that can be asserted in tests:
  `missing_built_html_target`, `unsafe_built_html_link`,
  `file_directory_url`, and `malformed_built_html_link`.
- [x] Add `llm-wiki site check --built-site-dir <path> --link-mode http|file`.
- [x] Keep the current Markdown mirror check behavior unchanged when
  `--built-site-dir` is omitted.
- [x] Include built-site issues and warnings in the existing text and JSON
  report shape rather than inventing a second console format.
- [x] Add tests showing an HTTP-style MkDocs directory URL passes in `http`
  mode and fails with `file_directory_url` in `file` mode.
- [x] Add tests showing `entities/User.html` passes in `file` mode.
- [x] Add tests showing unsafe traversal such as `../outside.html` is rejected.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py tests/test_cli.py -q
```

### Evidence

- Implemented `site_html_check.py` with HTTP/file built-HTML link modes and CLI
  flags `--built-site-dir` / `--link-mode`.
- Focused verification passed for `tests/test_site_export.py` and
  `tests/test_cli.py` during the code slice.
- Assistant dogfood built checks later passed with zero built-link issues in
  both `http` and `file` modes.

### Acceptance Criteria

- Existing `llm-wiki site check --wiki-dir ... --out-dir ...` behavior is
  unchanged for Markdown mirrors.
- A built site can be checked with `--built-site-dir`.
- HTTP mode accepts MkDocs directory URLs when matching `index.html` files exist.
- File mode rejects directory-style URLs and accepts direct `.html` links.
- JSON output exposes built-site link issues with stable categories.

## ADU-002 - File-Friendly MkDocs Export Mode

Priority: P0
Status: Completed
Depends on: ADU-001
Type: Code/tests/docs

### Goal

Allow callers to intentionally generate MkDocs configuration that produces
direct-file-friendly links.

### Developer Context

MkDocs defaults to directory URLs. That is usually right for hosted docs, but
the Assistant run was judged as a local handoff artifact. Users need an explicit
way to choose the distribution contract:

- HTTP-hosted site: directory URLs are acceptable.
- Direct-file/offline site: links should point to concrete `.html` files.

This task should not change the default MkDocs output. The safer migration path
is an opt-in flag.

### Files

- Modify: `src/llm_wiki_cli/services/site_export.py`
- Modify: `src/llm_wiki_cli/commands/site_cmd.py`
- Modify: `src/llm_wiki_cli/cli.py`
- Test: `tests/test_site_export.py`
- Test: `tests/test_cli.py`
- Update docs: `README.md`
- Update docs: `src/llm_wiki_cli/services/schema.py`
- Update sibling wiki static-site/command docs

### Tasks

- [x] Add a `file_friendly: bool = False` parameter to MkDocs export paths.
- [x] Add `llm-wiki site export --file-friendly` with help text that states it
  is intended for static sites opened directly from disk.
- [x] Reject `--file-friendly` unless `--format mkdocs` is selected, with a
  clear error message.
- [x] Emit `use_directory_urls: false` in generated `mkdocs.yml` when
  `--file-friendly` is set.
- [x] Apply the same setting to single-wiki MkDocs export and hub MkDocs export.
- [x] Include the selected distribution mode in the export report text and JSON,
  using a stable field such as `distribution_mode: "file"` or
  `distribution_mode: "http"`.
- [x] Update `render_report_text()` so the handoff says whether the output is
  intended for HTTP serving or direct-file browsing.
- [x] Add tests for the exact generated `mkdocs.yml` content with and without
  `use_directory_urls: false`.
- [x] Add a CLI test proving `--file-friendly --format mkdocs` is accepted.
- [x] Add a CLI test proving `--file-friendly --format plain` fails closed.
- [x] Add documentation examples that pair:
  - hosted docs with `site check --link-mode http`;
  - local handoff docs with `--file-friendly` and
    `site check --link-mode file`.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py tests/test_cli.py -q
git diff --check
```

### Evidence

- Implemented `site export --file-friendly` for MkDocs mirror and hub exports,
  including `distribution_mode: "file"`, `use_directory_urls: false`, and a
  generated MkDocs theme override for file-safe home links.
- Added CLI/config tests for supported MkDocs use and unsupported formats.
- Assistant file-friendly MkDocs output built with `mkdocs build --strict` and
  passed `site check --built-site-dir _site --link-mode file`.

### Acceptance Criteria

- Default MkDocs export remains byte-for-byte compatible except for any
  intentional report-field additions.
- `--file-friendly --format mkdocs` emits `use_directory_urls: false`.
- `--file-friendly` is rejected for unsupported formats.
- Built HTML from the file-friendly MkDocs config passes ADU-001 file-mode link
  validation.
- README/schema/sibling wiki docs explain when to use HTTP mode versus file mode.

## ADU-003 - Human Docs Profile And Generated-Reference Split

Priority: P0
Status: Completed
Depends on: ADU-001
Type: Code/tests

### Goal

Add an opt-in human documentation profile that publishes a concise product
landing page and moves the exhaustive generated inventory out of the root index.

### Developer Context

The root problem is not that the reference index is invalid. It is doing the
wrong job for a human landing page. The current `index.md` generated by
`bootstrap` and `sync` is an exhaustive wiki surface inventory. For Assistant,
the generated site put hundreds of entity/module links in the reader's first
path and reported `Guides | 0`.

The default reference profile should preserve this behavior. The human profile
should be explicit and require a real site name so the output does not default
to `LLM Wiki`.

### Files

- Modify: `src/llm_wiki_cli/services/site_export.py`
- Modify: `src/llm_wiki_cli/commands/site_cmd.py`
- Modify: `src/llm_wiki_cli/cli.py`
- Test: `tests/test_site_export.py`
- Test: `tests/test_cli.py`

### Tasks

- [x] Add supported site profiles: `reference` and `user`.
- [x] Add `llm-wiki site export --profile reference|user`, defaulting to
  `reference`.
- [x] Add `llm-wiki site export --site-name <name>`.
- [x] Preserve today's output for `--profile reference`.
- [x] For `--profile user`, require `--site-name` to be non-empty and different
  from `LLM Wiki`.
- [x] For `--profile user`, export the source wiki's original `index.md` as
  `generated-reference.md`.
- [x] For `--profile user`, write a new root `index.md` with this stable shape:
  - H1 equal to the provided site name.
  - `## Overview` with one short paragraph explaining that the site combines
    curated guide pages with generated reference pages.
  - `## Start Here` linking to available `guides/*.md` pages first.
  - `## Core Workflows` linking to available `workflows/*.md` and the highest
    priority `flows/*.md` pages.
  - `## Architecture And Operations` linking to `dependencies.md`,
    `load-order.md`, and infrastructure pages when present.
  - `## Generated Reference` linking to `generated-reference.md`.
- [x] Keep the generated root index under 250 lines for the user profile.
- [x] Add front matter to the synthetic root index when the selected format
  would normally add front matter.
- [x] Do not attach canonical `llm_wiki` front matter to
  `generated-reference.md`, because it is a distribution artifact rather than a
  canonical wiki page.
- [x] Update MkDocs nav so the user profile begins with the human `index.md`
  and includes `generated-reference.md` after guide/workflow/architecture
  entries.
- [x] Add tests proving `reference` profile preserves the current root index and
  nav order.
- [x] Add tests proving `user` profile writes a short root index, writes
  `generated-reference.md`, and uses the provided site name.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py tests/test_cli.py -q
```

### Evidence

- Implemented `--profile user --site-name ...` while preserving
  `--profile reference` as the default behavior.
- User profile writes a human root `index.md` and moves the generated inventory
  to `generated-reference.md`.
- Assistant dogfood user root starts with `# Assistant`, has 71 lines, links to
  a guide, and links generated reference as a secondary section.

### Acceptance Criteria

- Existing callers see the reference profile by default.
- `--profile user --site-name Assistant` produces a root page titled
  `# Assistant`.
- The exhaustive generated inventory is no longer the human profile's root
  landing page.
- The original inventory remains available as `generated-reference.md`.
- `--profile user` fails closed when the site name is omitted or still
  `LLM Wiki`.

## ADU-004 - Human-Profile Quality Gates

Priority: P0
Status: Completed
Depends on: ADU-003
Type: Code/tests

### Goal

Make user-facing documentation quality checkable with deterministic gates that
catch the failures seen in the Assistant dogfood run.

### Developer Context

The previous site checks reported success because the output was structurally
valid. They did not care whether the landing page was useful, whether guides
existed, or whether primary pages exposed bootstrap placeholders.

This task should add deterministic checks, not subjective prose scoring. Keep
severity calibrated:

- Hard issues for defects in primary human docs.
- Warnings for generated-reference pages that still contain placeholders or
  low-confidence static-analysis content.
- No user-doc quality gates for the reference profile.

### Files

- Modify: `src/llm_wiki_cli/services/site_export.py`
- Modify: `src/llm_wiki_cli/commands/site_cmd.py`
- Modify: `src/llm_wiki_cli/cli.py`
- Test: `tests/test_site_export.py`
- Test: `tests/test_cli.py`

### Tasks

- [x] Add `llm-wiki site check --profile reference|user`, defaulting to
  `reference`.
- [x] Add `--site-name <name>` to `site check` for user-profile validation.
- [x] For `--profile reference`, preserve current check behavior except for
  built-site checks from ADU-001 when explicitly requested.
- [x] For `--profile user`, hard-fail if root `index.md` is missing.
- [x] For `--profile user`, hard-fail if root `index.md` exceeds 250 lines.
- [x] For `--profile user`, hard-fail if root `index.md` has more than 80
  Markdown links.
- [x] For `--profile user`, hard-fail if there are no `guides/*.md` pages.
- [x] For `--profile user`, hard-fail if the site name is missing or equals
  `LLM Wiki`.
- [x] For `--profile user`, hard-fail if primary human docs contain any of
  these phrases:
  - `Replace this placeholder`
  - `_Auto-generated from`
  - `data not statically known`
  - raw TypeScript/JSDoc starts such as `/**`
- [x] Treat root `index.md` and `guides/*.md` as primary human docs.
- [x] Treat `generated-reference.md`, `entities/*.md`, `modules/*.md`, and
  generated flow pages as generated reference docs unless ADU-005 promotes a
  page into primary nav.
- [x] Report generated-reference placeholder hits as warnings with the category
  `generated_reference_placeholder`.
- [x] Add tests for each quality category:
  `human_index_too_long`, `human_index_too_many_links`,
  `missing_user_guides`, `default_user_site_name`,
  `published_placeholder`, and `generated_reference_placeholder`.
- [x] Add JSON/text report rendering coverage so users can see whether a
  finding is an issue or warning.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py tests/test_cli.py -q
```

### Evidence

- Added deterministic user-profile gates for default site names, missing guide
  surfaces, oversized human indexes, excessive links, and placeholder text in
  primary human docs.
- Generated-reference placeholder text is reported as non-failing
  `generated_reference_placeholder` warnings.
- Assistant dogfood user-profile checks passed with zero issues; 497
  generated-reference placeholder warnings remained non-failing.

### Acceptance Criteria

- Reference-profile checks remain compatible with existing tests.
- User-profile checks fail on the exact quality failures seen in the Assistant
  run.
- Placeholder text in primary human docs is a hard issue.
- Placeholder text in generated reference docs is reported and visible.
- Reports explain what file and category triggered each finding.

## ADU-005 - Human Navigation Grouping And Noise Policy

Priority: P1
Status: Completed
Depends on: ADU-003, ADU-004
Type: Code/tests

### Goal

Group human-profile navigation by reader intent and de-emphasize test/mock/raw
reference pages.

### Developer Context

The current registry order is correct for a canonical wiki surface:

1. root index,
2. log,
3. entities,
4. modules,
5. workflows,
6. guides,
7. flows,
8. infrastructure,
9. dependencies,
10. load order.

That order is poor as the first navigation a human sees. The Assistant ADR
suggested product-domain groups such as live meeting runtime, post-meeting
memory, model/tool integration, host integration, operations, and generated
reference. A generic implementation should start with stable groups and allow
domain heuristics to improve over time.

### Files

- Modify: `src/llm_wiki_cli/services/site_export.py`
- Modify: `src/llm_wiki_cli/services/wiki_surface.py` only if shared metadata
  belongs in the registry.
- Test: `tests/test_site_export.py`
- Optional focused helper: `src/llm_wiki_cli/services/site_navigation.py`

### Tasks

- [x] Add a user-profile nav builder separate from the reference-profile nav
  builder.
- [x] Keep reference-profile MkDocs and Docusaurus nav unchanged.
- [x] For the user profile, group nav as:
  - `Start Here`: root index and guides.
  - `Core Workflows`: workflows and high-confidence flows.
  - `Architecture And Operations`: infrastructure pages, dependencies, and
    load order.
  - `Generated Reference`: generated reference index, entities, modules, and
    lower-confidence flows.
  - `Test And Fixture Reference`: pages whose source path indicates tests,
    fixtures, mocks, or fake implementations.
- [x] Use `.llm-wiki-surface.json` `source_path` values when available to
  classify test/fixture/mock pages.
- [x] Treat source paths containing `/tests/`, `\\tests\\`, `/fixtures/`,
  `\\fixtures\\`, `test_`, `_test`, `/mocks/`, `\\mocks\\`, `/fake`, or
  `\\fake` as test/fixture reference pages.
- [x] Treat flow pages whose `## Behavior` contains `Replace this placeholder`
  as lower-confidence generated reference pages.
- [x] Add a small, deterministic scoring helper for flow pages:
  substantive behavior prose first, then workflows, then remaining flows by
  canonical path.
- [x] Apply grouped nav to MkDocs config in the user profile.
- [x] Apply grouped sidebar categories to Docusaurus output in the user profile
  if Docusaurus profile support remains in scope for ADU-003.
- [x] Add tests with source-index metadata proving test pages are grouped under
  `Test And Fixture Reference`.
- [x] Add tests proving placeholder flow pages are not promoted into
  `Core Workflows`.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py -q
```

### Evidence

- Implemented grouped user-profile MkDocs and Docusaurus navigation with
  Start Here, Core Workflows, Architecture And Operations, Generated Reference,
  and Test And Fixture Reference sections.
- Test/fixture pages are classified from surface metadata and placeholder-heavy
  flows are demoted out of primary human navigation.
- Focused site export tests cover the grouping and noise policy.

### Acceptance Criteria

- User-profile navigation starts with human entry points, not entities/modules.
- Test, fixture, mock, and fake pages are still available but separated from
  primary product navigation.
- Flow pages with placeholder behavior are not promoted as core workflows.
- Reference-profile navigation is unchanged.

## ADU-006 - Skill Contract Updates For User Docs

Priority: P1
Status: Completed
Depends on: ADU-002, ADU-004
Type: Skills/docs/tests

### Goal

Align bundled skills with the new distinction between reference docs,
user-facing docs, and distribution mode.

### Developer Context

The current skills already encode useful boundaries:

- `wiki-bootstrap` creates the generated wiki/reference surface.
- `onboarding-guide` writes persona-scoped guide pages into `guides/`.
- `publish-docs` exports and checks a deterministic static-site mirror.
- `doc-review` is the right place to evaluate documentation defects.

The Assistant run failed partly because those boundaries were not explicit
enough in the publish handoff. `publish-docs` sounded like it produced a
complete user docs site, but it actually published the reference mirror.

### Files

- Modify: `src/llm_wiki_cli/skills/publish-docs/SKILL.md`
- Modify: `src/llm_wiki_cli/skills/publish-docs/reference.md`
- Modify: `src/llm_wiki_cli/skills/onboarding-guide/SKILL.md`
- Modify: `src/llm_wiki_cli/skills/onboarding-guide/reference.md`
- Modify: `src/llm_wiki_cli/skills/doc-review/SKILL.md`
- Modify: `src/llm_wiki_cli/skills/doc-review/reference.md`
- Modify: `src/llm_wiki_cli/skills/wiki-bootstrap/SKILL.md`
- Test: `tests/test_skills.py`
- Test: `tests/test_package_metadata.py`

### Tasks

- [x] Update `publish-docs` to state that default export is a reference
  profile.
- [x] Add a `publish-docs` user-profile path:
  - require current wiki,
  - require a non-default `--site-name`,
  - require at least one guide page,
  - run `site export --profile user`,
  - run `site check --profile user`,
  - run built-site link validation with the selected `--link-mode`.
- [x] Update `publish-docs` reference material so hosted docs use HTTP mode and
  direct handoff docs use `--file-friendly` plus file-mode validation.
- [x] Update `onboarding-guide` to say it is the prerequisite narrative layer
  for `publish-docs --profile user`.
- [x] Update `onboarding-guide` persona defaults for product documentation:
  contributor, operator, reviewer, and product/user reader when the repo exposes
  user-facing workflows.
- [x] Update `doc-review` to classify:
  - broken distribution-mode link,
  - missing human landing page,
  - missing guide surface,
  - bootstrap placeholder in primary docs,
  - raw generated inventory used as root landing page.
- [x] Update `wiki-bootstrap` to say its default output is reference-oriented
  and should be followed by `onboarding-guide` plus user-profile publishing for
  user docs.
- [x] Add `tests/test_skills.py` assertions for the new command flags and
  contract phrases.
- [x] Keep package-data tests passing; add new package-data assertions only if a
  new skill file is created.

### Focused Verification

```bash
.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py -q
```

### Evidence

- Updated `wiki-bootstrap`, `onboarding-guide`, `doc-review`, and
  `publish-docs` bundled skill contracts and references to distinguish
  reference mirrors from user documentation publishing.
- Added skill tests for the new user-profile, file-friendly, and built-link
  validation contract language.
- Focused verification passed for `tests/test_skills.py` and
  `tests/test_package_metadata.py` with 64 tests.

### Acceptance Criteria

- Skill text no longer implies the reference mirror is complete user docs.
- `publish-docs` instructs agents to choose HTTP versus file distribution mode.
- `publish-docs --profile user` guidance requires guides and non-default site
  name.
- `doc-review` can consume the quality categories introduced by ADU-004.
- Skill package tests protect the new contracts.

## ADU-007 - Assistant Human-Docs Dogfood Confirmation

Priority: P1
Status: Completed
Depends on: ADU-001 through ADU-006
Type: Dogfood report

### Goal

Rerun the Assistant docsite workflow in a temporary workspace and prove the new
user-docs path addresses the original failures without mutating Assistant.

### Developer Context

The original evidence came from `/mnt/data/projects/Assistant` and preserved
artifacts under `/tmp/llm-wiki-assistant-docsite-37vp6W`. Future confirmation
should not rely on that temp directory still existing. It should generate a
fresh runner, keep Assistant read-only, and save a durable report in this repo.

The dogfood should validate both contracts:

- Reference profile remains complete and structurally valid.
- User profile has a human landing page, guide pages, quality checks, and
  distribution-mode-safe links.

### Files

- Create report:
  `reports/assistant_docsite_user_docs_confirmation_2026-07-05.md`
- Optional opt-in test:
  `tests/test_assistant_docsite_user_docs_pilot.py`
- Modify docs or backlog status only after the run has evidence.

### Tasks

- [x] Create a fresh runner with `mktemp -d /tmp/llm-wiki-assistant-user-docs-XXXXXXXX`.
- [x] Run Assistant bootstrap from the runner, reading Assistant as an external
  source and writing wiki output only inside the runner.
- [x] If guide pages do not exist after bootstrap, run the updated
  `onboarding-guide` workflow against the runner wiki, not the Assistant repo.
- [x] Export the reference profile and run existing mirror checks to prove
  backward compatibility.
- [x] Export the user profile with `--site-name Assistant`.
- [x] Build MkDocs with hosted defaults and run built-site link validation in
  `http` mode.
- [x] Export/build the file-friendly MkDocs variant and run built-site link
  validation in `file` mode.
- [x] Confirm the user-profile root `index.md`:
  - starts with `# Assistant`,
  - is under 250 lines,
  - links to at least one guide page,
  - links to generated reference as a secondary section,
  - does not start with `# LLM Wiki Index`.
- [x] Confirm no primary human docs contain `Replace this placeholder`.
- [x] Record exact commands, runner path, page counts, guide count, quality
  issues/warnings, and built-link issue counts in the report.
- [x] Keep any generated site artifacts in the runner or `/tmp`; do not copy
  them into this repository unless the user asks for fixtures.

### Focused Verification

Use `.venv/bin/python` from this repo even when running from the temp runner:

```bash
RUNNER=$(mktemp -d /tmp/llm-wiki-assistant-user-docs-XXXXXXXX)
cd "$RUNNER"
/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli bootstrap \
  --src-dir /mnt/data/projects/Assistant \
  --wiki-dir wiki-external \
  --source-adapter \
  --allow-external-src \
  --format json
/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site export \
  --wiki-dir wiki-external \
  --out-dir site-user \
  --format mkdocs \
  --profile user \
  --site-name Assistant \
  --front-matter \
  --output-format json
/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-user \
  --profile user \
  --site-name Assistant \
  --output-format json
```

After building with MkDocs, also run the ADU-001 built-site checks in both
distribution modes that match the generated configs.

### Acceptance Criteria

- Assistant remains unmodified.
- Reference profile still passes structural checks.
- User profile passes human-profile quality gates.
- File-friendly built output has zero file-mode link issues.
- Hosted/default built output has zero HTTP-mode link issues.
- The durable report records evidence for the original broken-link and bad-index
  complaints.

### Evidence

- Fresh runner: `/tmp/llm-wiki-assistant-user-docs-fkd7ZSQO`.
- Assistant repo remained clean before and after dogfood.
- Reference export/check passed with 995 pages, zero issues, and zero warnings.
- Hosted user export/build/check passed; built HTTP link validation had zero
  issues and 497 non-failing generated-reference warnings.
- File-friendly user export/build/check passed; built file-mode link validation
  had zero issues and 497 non-failing generated-reference warnings.
- Durable report: `reports/assistant_docsite_user_docs_confirmation_2026-07-05.md`.

## ADU-008 - Public Docs, Sibling Wiki, And Backlog Closeout

Priority: P1
Status: Completed
Depends on: ADU-001 through ADU-007
Type: Docs/report

### Goal

Close the backlog with public documentation, sibling wiki updates, and a clear
completion record.

### Developer Context

This repo treats docs and wiki updates as part of done for user-facing CLI and
skill behavior. The implementation should not leave behavior discoverable only
from tests or skill internals.

### Files

- Modify: `README.md`
- Modify: `src/llm_wiki_cli/services/schema.py`
- Modify: this backlog file
- Create or update: `reports/assistant_docsite_user_docs_closure_2026-07-05.md`
- Modify sibling wiki pages under
  `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki`

### Tasks

- [x] Update README command examples for:
  - `site export --profile reference`,
  - `site export --profile user --site-name ...`,
  - `site export --file-friendly`,
  - `site check --built-site-dir ... --link-mode http|file`.
- [x] Update schema/tool guidance so agents understand that static-site output
  is derived and profile-specific.
- [x] Update sibling wiki command reference and static-site distribution docs
  with the same examples.
- [x] Mark completed backlog tasks with status and evidence blocks.
- [x] Write a closure report summarizing:
  - implemented tasks,
  - verification commands,
  - Assistant dogfood results,
  - remaining known limitations,
  - any skipped broad verification and why.
- [x] Keep main repo and sibling wiki commits separate if this task is committed
  later.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py tests/test_cli.py tests/test_skills.py tests/test_package_metadata.py -q
.venv/bin/python -m compileall src tests
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
git diff --check
git -C /mnt/data/projects/llm-wiki/python-wiki-llm.wiki diff --check
```

### Acceptance Criteria

- README and generated schema guidance describe reference versus user profiles.
- Sibling wiki docs match the implemented command surface.
- Backlog status and closure report contain concrete verification evidence.
- Main repo and sibling wiki changes are reviewable as separate diffs.

### Evidence

- Updated `README.md`, `src/llm_wiki_cli/services/schema.py`, and sibling wiki
  `Command-Reference.md` / `Static-Site-Distribution.md` with profile,
  file-friendly, and built-link validation examples.
- Added closure report:
  `reports/assistant_docsite_user_docs_closure_2026-07-05.md`.
- Final focused verification and project review are recorded in the closure
  report.

## Backlog Completion Criteria

This backlog is complete when:

- Existing reference-profile static-site export behavior remains compatible.
- Built HTML link validation exists and covers both HTTP and direct-file modes.
- File-friendly MkDocs export is available and documented.
- User-profile export produces a concise human root page and separates generated
  reference inventory.
- User-profile quality gates catch missing guides, default site names, bloated
  indexes, and placeholder text in primary docs.
- Human-profile navigation no longer starts with raw entities/modules.
- Bundled skills clearly distinguish reference generation from user
  documentation publishing.
- A fresh Assistant dogfood report proves the original issues are addressed.
- User-facing docs and sibling wiki pages reflect the final behavior.
