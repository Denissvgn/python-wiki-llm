# User Docs Usage Examples Implementation Backlog

> For agentic workers: REQUIRED SUB-SKILL: Use `superpowers:executing-plans`
> to execute this backlog task-by-task. Update task status in this file as work
> lands, preserve unrelated worktree changes, and commit each completed
> implementation task as a scoped change unless the user explicitly asks for a
> different commit strategy.

**Goal:** Give the user-docs pipeline a validated media layer — an agent-owned
`assets/` wiki surface, media-aware lint and site validation, asset mirroring
in static-site export, a `usage-examples` bundled skill that tells autonomous
agents how to capture and attach screenshots/recordings, and an instruction
surface external agents (`hermes`, `openclaw`, and similar) can consume.

**Architecture:** Keep the deterministic/semantic ownership split. Assets are
agent/human-owned binaries the CLI never generates or deletes; lint, site
export, and site check gain deterministic media validation; skills own
judgment and capture. Media policy: mirrored page-path layout
(`assets/<surface>/<page-stem>/<name>.<ext>`), poster-in-repo + external
video as the recommended hosting pattern, size warnings instead of hard git
policy.

**Tech Stack:** Python 3.9+, argparse CLI, stdlib-only runtime (no image
decoding — existence/size/extension/reference validation only), stdlib
`html.parser`, MkDocs/Docusaurus/plain export surfaces, pytest, Ruff, bundled
skill Markdown, sibling wiki docs.

---

Date: 2026-07-07
Source ADR: `reports/adr_user_docs_usage_examples_2026-07-07.md`
Status: Completed
Owner: Unassigned

## Scope

This backlog implements the five ADR tracks:

- Wiki media asset surface with lint categories and parser fixes (Track 1).
- Site export asset mirroring and built-site media validation (Track 2).
- `usage-examples` bundled skill with an agent-neutral capture contract
  (Track 3).
- Autonomous-agent instruction surface through the existing `init`/schema
  system (Track 4).
- Self-dogfood plus Assistant dogfood confirmation and closeout (Track 5).

## Out Of Scope

- Pixel-level or content validation of images and video (no Pillow/ffmpeg
  dependencies; validation stays existence/size/extension/reference based).
- Automatic staleness detection for captured media when product output
  changes; captions carry the flow identity so `doc-review`/`review` runs can
  flag affected guides, and that is the accepted mitigation.
- Installing capture tooling (playwright, asciinema, agg) from package code
  or skills; agents check availability and defer when missing.
- Git LFS integration or repository size policy enforcement beyond warnings.
- Turning Docusaurus export into a full application scaffold.
- Editing dogfood target repositories; Assistant remains read-only input.

## Delivery Rules

- Use the project virtual environment for every Python command:
  `.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/ruff`.
- Keep implementation portable across Windows, macOS, Ubuntu, and Python
  3.9+. Asset paths must use `Path` semantics, never hardcoded separators.
- Preserve existing defaults; every behavior change is opt-in, profile-scoped,
  or warning-level first. Existing lint/site-check output for wikis without
  an `assets/` directory must be unchanged.
- Keep source wiki pages and `assets/` as the source of truth. Static-site
  output is a derived distribution surface.
- Keep dogfood targets read-only. Generate dogfood output under a temporary
  runner or this repo's own report paths only.
- Update `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki` separately when a
  task changes user-facing CLI behavior, bundled skill behavior, or published
  docs workflow guidance.
- For ignored `reports/` artifacts, verify ignore behavior with
  `git check-ignore -v` and stage intentionally with `git add -f` only when
  the user asks for a commit.

## Dependency Order

| ID | Title | Priority | Depends on | Type |
| --- | --- | --- | --- | --- |
| UDE-001 | Media link parsing and lint categories | P0 | None | Code/tests |
| UDE-002 | Asset surface registration and index asset map | P0 | UDE-001 | Code/tests/docs |
| UDE-003 | Site export asset mirroring | P0 | UDE-002 | Code/tests |
| UDE-004 | Built-site media validation | P0 | UDE-003 | Code/tests |
| UDE-005 | User-profile usage-example warning gate | P1 | UDE-002 | Code/tests |
| UDE-006 | `usage-examples` bundled skill | P0 | UDE-002, UDE-003, UDE-005 | Skills/docs/tests |
| UDE-007 | Autonomous-agent instruction surface | P1 | UDE-006 | Code/docs/tests |
| UDE-008 | Self-dogfood: capture examples for this repo | P1 | UDE-001 through UDE-006 | Dogfood report |
| UDE-009 | Assistant dogfood confirmation | P1 | UDE-008 | Dogfood report |
| UDE-010 | Public docs, sibling wiki, and closeout | P1 | UDE-001 through UDE-009 | Docs/report |

## File Map

Likely code touch points:

- `src/llm_wiki_cli/commands/lint_cmd.py`
- `src/llm_wiki_cli/services/wiki_surface.py`
- `src/llm_wiki_cli/services/wiki_surface_index.py`
- `src/llm_wiki_cli/services/site_export.py`
- `src/llm_wiki_cli/services/site_html_check.py`
- `src/llm_wiki_cli/services/schema.py`
- `src/llm_wiki_cli/commands/site_cmd.py`
- `src/llm_wiki_cli/commands/init_cmd.py`
- `src/llm_wiki_cli/cli.py`
- `src/llm_wiki_cli/config.py`
- New focused helper if `site_export.py` would keep growing:
  `src/llm_wiki_cli/services/site_assets.py`

Likely skill and docs touch points:

- New: `src/llm_wiki_cli/skills/usage-examples/SKILL.md`
- New: `src/llm_wiki_cli/skills/usage-examples/reference.md`
- `src/llm_wiki_cli/skills/user-docs-author/SKILL.md` and `reference.md`
- `src/llm_wiki_cli/skills/publish-docs/SKILL.md` and `reference.md`
- `src/llm_wiki_cli/skills/doc-review/SKILL.md` and `reference.md`
- `src/llm_wiki_cli/skills/onboarding-guide/SKILL.md` and `reference.md`
- `README.md`
- Sibling wiki command/workflow pages under
  `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki`

Likely test touch points:

- `tests/test_lint.py` (or the module that covers lint categories)
- `tests/test_site_export.py`
- `tests/test_cli.py`
- `tests/test_skills.py`
- `tests/test_package_metadata.py`
- New focused tests if the helper module is created:
  `tests/test_site_assets.py`

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

Full-suite note: exclude `tests/test_rust_extract.py` unless the Rust helper
cache is prepared (known environmental failures; see
`reports/assistant_docsite_user_docs_closure_2026-07-05.md` for the split-run
pattern).

## UDE-001 - Media Link Parsing And Lint Categories

Priority: P0
Status: Completed
Depends on: None
Type: Code/tests

### Goal

Make lint media-aware: classify image/video references distinctly from page
links, fix the two known parser defects, and pin the sync ownership
invariant for `assets/`.

### Developer Context

`_check_broken_links` (`lint_cmd.py:570`) already resolves every local link
target — image or page — via `_local_link_path` (`lint_cmd.py:177`) and bare
`Path.exists()`. A missing asset therefore already reports, but under the
generic `broken_links` category. Two verified defects: a markdown link title
(`![alt](x.png "Title")`) stays inside the `LINK_RE` capture and
false-positives the existence check, and raw `<img>`/`<video>` HTML embeds
are invisible to `LINK_RE`.

Ownership safety is verified but unpinned: the only deletions in the
sync/bootstrap/export path are the rename-cleanup unlinks at
`sync_cmd.py:962,982`, hard-scoped to `entities/*.md` and `modules/*.md`.

Media formats in scope: `png`, `jpg`/`jpeg`, `webp`, `gif`, `svg` as images;
`mp4`/`webm` as opaque video files. No image decoding — extension and file
metadata only.

### Files

- Modify: `src/llm_wiki_cli/commands/lint_cmd.py`
- Test: the lint test module (extend existing lint category tests)

### Tasks

- [x] Strip an optional trailing markdown title (`"..."` or `'...'` after
  whitespace) from captured link targets before resolution, for both page and
  media links.
- [x] Classify a link as media by target extension; report missing media
  targets as `media_link_broken` instead of `broken_links` (blocking, same
  severity as today — reclassify, never double-report).
- [x] Scan wiki pages for raw `<img src=...>` and `<video src=...>` /
  `<source src=...>` embeds with a small stdlib parser or focused regex, and
  run the same existence check on local `src` targets.
- [x] Add `media_missing_alt_text` (warning) for markdown image embeds with
  empty alt text and `<img>` embeds without an `alt` attribute.
- [x] Add `media_oversize` (warning) for referenced assets above a
  configurable cap; default 2 MB, overridable via an existing-style lint
  option. Tune the default in UDE-008 if dogfood shows it is wrong.
- [x] Keep `_check_orphan_pages` and all page-only checks operating on `*.md`
  pages exactly as today; asset files must not become orphan-page reports.
- [x] Add a regression test that a populated `assets/` tree survives `sync`
  untouched (pin the `sync_cmd.py:962,982` scoping invariant).
- [x] Add tests: valid asset reference passes; missing asset reports
  `media_link_broken`; titled image link resolves; raw `<img>` with missing
  target reports; oversize and missing-alt warnings are non-blocking; a wiki
  with no `assets/` directory produces byte-identical lint output to today.

### Focused Verification

```bash
.venv/bin/pytest tests/ -q -k "lint"
```

### Evidence

- Added `src/llm_wiki_cli/services/wiki_media.py` for Markdown and raw HTML
  media parsing, title stripping, local-path normalization, media type
  classification, and asset indexing.
- Updated `lint_cmd.py` and `cli.py` with media-specific lint categories:
  `media_link_broken`, `media_missing_alt_text`, `media_oversize`, and
  `media_orphan`, plus `--media-size-warn-bytes`.
- Added focused coverage in `tests/test_lint.py`, including raw HTML media,
  Markdown title stripping, oversize warnings, orphan assets, and CLI default
  handling.

### Acceptance Criteria

- Missing media targets report under `media_link_broken`, not
  `broken_links`, with no duplicate reports.
- Titled image links no longer false-positive.
- Raw HTML `img`/`video` embeds are validated for local targets.
- `sync` cannot delete anything under `assets/`, proven by test.
- Wikis without assets produce unchanged lint output.

## UDE-002 - Asset Surface Registration And Index Asset Map

Priority: P0
Status: Completed
Depends on: UDE-001
Type: Code/tests/docs

### Goal

Register `assets/` as a canonical agent-owned surface with a deterministic
page-to-asset map in the machine-readable surface index.

### Developer Context

The surface registry and `.llm-wiki-surface.json`
(`wiki_surface.py` / `wiki_surface_index.py`) currently describe Markdown
pages plus the manifest artifacts. Agents need a deterministic way to query
"which pages have examples, which assets are unreferenced" without globbing.

Layout decision (ADR resolved question 3): assets mirror the owning page's
wiki-relative path — `assets/guides/getting-started/<name>.<ext>` for
`guides/getting-started.md`. Page stems are only unique per surface
directory, so flat naming can collide.

### Files

- Modify: `src/llm_wiki_cli/services/wiki_surface.py`
- Modify: `src/llm_wiki_cli/services/wiki_surface_index.py`
- Modify: `src/llm_wiki_cli/commands/lint_cmd.py` (orphan-asset check reads
  the reference map)
- Modify docs: `README.md` (surface taxonomy table gains the `assets/` row)
- Test: surface-index and lint test modules

### Tasks

- [x] Add `assets/` to the canonical surface taxonomy as an agent-owned,
  never-generated surface; document the mirrored page-path layout.
- [x] Record asset counts and a page-to-asset reference map (from UDE-001
  parsing) in `.llm-wiki-surface.json`; keys are wiki-relative POSIX-style
  paths for cross-platform stability.
- [x] Add `media_orphan` (warning) for asset files referenced by no page.
  Scope decision (ADR remaining item): scan all of `assets/` so misplaced
  files are visible, but report the expected mirrored location when the stem
  matches a known page.
- [x] Keep the surface JSON schema versioned/compatible: additive fields
  only; wikis without assets emit empty counts, not new required structure.
- [x] Add tests: asset map content, orphan warning, empty-assets
  compatibility, POSIX path normalization on Windows-style input.

### Focused Verification

```bash
.venv/bin/pytest tests/ -q -k "surface or lint"
```

### Evidence

- Added the semantic, agent-owned `assets/` surface contract via
  `wiki_surface.asset_surface()`.
- Updated `wiki_surface_index.py` so `.llm-wiki-surface.json` includes
  top-level asset counts and a page-to-asset reference map.
- Added sync/surface/index tests proving assets are indexed and left
  agent-owned.

### Acceptance Criteria

- `.llm-wiki-surface.json` exposes asset counts and page-to-asset references.
- `media_orphan` warnings identify unreferenced assets without blocking.
- Existing surface-index consumers see only additive changes.
- README taxonomy documents the new surface and layout rule.

## UDE-003 - Site Export Asset Mirroring

Priority: P0
Status: Completed
Depends on: UDE-002
Type: Code/tests

### Goal

Make `site export` carry referenced assets into the out-dir for all formats
so image/video links survive in exported and built sites.

### Developer Context

Page collection is `root.rglob("*.md")` (`site_export.py:1483`); assets are
never copied today, so any embed exports broken. `site_export.py` grew ~715
lines in the ADU program — if mirroring logic is more than a thin walk+copy,
put it in a new `services/site_assets.py` following the `site_html_check.py`
precedent.

Side finding from the ADR: `site export` never deletes from the out-dir, so
stale assets accumulate across exports. Decision for this task: report, do
not delete — emit a `stale_asset` operation line for out-dir asset files no
longer referenced; an opt-in cleanup flag can come later if dogfood shows
accumulation is a real problem.

### Files

- Modify: `src/llm_wiki_cli/services/site_export.py`
- Possibly create: `src/llm_wiki_cli/services/site_assets.py`
- Test: `tests/test_site_export.py`
- Possibly create: `tests/test_site_assets.py`

### Tasks

- [x] Copy assets referenced by exported pages (per the UDE-002 map) into the
  out-dir preserving wiki-relative paths, for mkdocs, docusaurus, and plain
  formats, single-wiki and hub export.
- [x] Leave relative `![...](...)` targets unchanged in exported Markdown so
  preserved paths keep resolving.
- [x] Verify MDX escaping for Docusaurus leaves markdown image syntax and
  allowed raw `<img>`/`<video>` embeds intact; add regression tests.
- [x] Add an asset operations section to the export report (text and JSON):
  copied count, skipped count, `stale_asset` entries for previously exported
  assets no longer referenced. No deletions.
- [x] Copy only referenced assets by default (orphans stay wiki-side); note
  the behavior in the report when orphans were skipped.
- [x] Add tests: assets copied per format, hub export, unchanged links,
  stale-asset reporting, no-assets wikis produce byte-identical exports to
  today.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py tests/test_cli.py -q
```

### Evidence

- Updated `site_export.py` to copy referenced assets into single-wiki and hub
  exports, with `asset_count` and `asset_operations` reported separately from
  page operations.
- Added dry-run, idempotent unchanged-copy, hub namespacing, and stale exported
  asset warning behavior.
- Covered the behavior in `tests/test_site_export.py`.

### Acceptance Criteria

- Exported sites contain every referenced asset at its mirrored path in all
  three formats.
- Export report accounts for asset operations with stable fields.
- Exports of wikis without assets are unchanged.
- No out-dir deletions are introduced.

## UDE-004 - Built-Site Media Validation

Priority: P0
Status: Completed
Depends on: UDE-003
Type: Code/tests

### Goal

Validate `<img>`/`<video>` targets in built HTML in both link modes, closing
the verified gap that only `href` attributes are checked.

### Developer Context

`site_html_check.py` collects only `href` values (`site_html_check.py:30`).
Extend the same `html.parser` subclass to collect `src` from `img`, `video`,
and `source` tags, reusing the existing resolution and issue-shape machinery.
`_IGNORED_SCHEMES` (http/https/mailto/tel/data/javascript) stays authoritative
— externally hosted video is explicitly out of validation scope, which is
what makes the poster-in-repo + external-video pattern safe.

Media targets are concrete files in both modes; directory-style resolution
does not apply to them.

### Files

- Modify: `src/llm_wiki_cli/services/site_html_check.py`
- Modify: `src/llm_wiki_cli/services/site_export.py` (report integration)
- Test: `tests/test_site_export.py` or `tests/test_site_html_check.py`

### Tasks

- [x] Collect `src` attributes from `img`, `video`, and `source` tags in the
  built-HTML scanner.
- [x] Resolve media targets as exact files in both `http` and `file` modes;
  report missing targets as `missing_built_media_target` and malformed values
  under the existing malformed category.
- [x] Keep `_IGNORED_SCHEMES` handling identical for media; add a test that
  an external `https://` video URL is ignored in both modes.
- [x] Reject traversal outside the built-site dir for media the same way
  hrefs are rejected today.
- [x] Integrate media issues into the existing text/JSON report shape; no new
  console format.
- [x] Add tests: valid built `<img src>` passes both modes; missing media
  file fails with `missing_built_media_target`; `../outside.png` rejected;
  built sites without media produce unchanged reports.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py tests/test_cli.py -q
```

### Evidence

- Extended `site_html_check.py` to parse built HTML media sources from `<img>`,
  `<video>`, and `<source>` tags.
- Added stable issue handling for missing, unsafe, malformed, and traversal
  media targets in both `http` and `file` link modes.
- Added built-site media validation tests in `tests/test_site_export.py`.

### Acceptance Criteria

- Built-site checks validate media `src` targets in `http` and `file` modes.
- External schemes remain ignored by policy.
- Issue categories are stable and test-asserted.
- Reports for media-free sites are unchanged.

## UDE-005 - User-Profile Usage-Example Warning Gate

Priority: P1
Status: Completed
Depends on: UDE-002
Type: Code/tests

### Goal

Nudge — without blocking — user-profile docs that contain no usage-example
media in their primary human pages.

### Developer Context

`_check_user_profile_quality` (`site_export.py:1512-1571`) already returns
failing issues and non-failing warnings separately; the
`generated_reference_placeholder` precedent showed warnings scale without
blocking (497 non-failing warnings in the Assistant dogfood). ADR resolved
question 4 chose a gate warning over a doc-review-only rule so CI consumers
see the signal; `doc-review` inherits it from checker output anyway.

The warning must not fire for projects where media makes no sense (pure
libraries), which is exactly why it is a warning and scoped to primary human
docs (root page and `guides/`), not generated reference pages.

### Files

- Modify: `src/llm_wiki_cli/services/site_export.py`
- Test: `tests/test_site_export.py`

### Tasks

- [x] Add a `user_docs_missing_examples` warning (non-failing) when no
  primary human doc (user-profile root page or any `guides/*.md`) references
  at least one media asset.
- [x] Emit at most one warning per export, naming the guide surface, not one
  per page — keep the noise level below the placeholder precedent.
- [x] Do not evaluate the check outside `--profile user`.
- [x] Add tests: warning fires for a guides-without-media user export; does
  not fire when any primary doc embeds media; never fires for the reference
  profile; never turns into a failing issue.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py -q
```

### Evidence

- Extended user-profile checks to emit a warning when primary human docs have
  no usage media examples.
- Kept the gate warning-level so generated-reference placeholder warnings and
  usage-example absence do not block structurally valid sites.
- Added regression coverage in `tests/test_site_export.py`.

### Acceptance Criteria

- User-profile exports without example media warn once, clearly, without
  failing.
- Reference-profile behavior is unchanged.
- `doc-review` can consume the warning from existing JSON output unchanged.

## UDE-006 - `usage-examples` Bundled Skill

Priority: P0
Status: Completed
Depends on: UDE-002, UDE-003, UDE-005
Type: Skills/docs/tests

### Goal

Ship the agent-neutral capture contract as a bundled skill, with small
cross-reference updates in the adjacent docs skills.

### Developer Context

Follow the established contract style (`user-docs-author` is the closest
sibling: preconditions, numbered loop, context budget, reference.md with
evidence map / command matrix / failure modes). The core discipline from the
ADR: **examples are evidence, not decoration** — a capture is only valid if
it demonstrates a flow a guide already documents with cited wiki evidence;
never stage a screenshot of unclaimed behavior, never document behavior from
a screenshot without wiki/source evidence.

Tooling is agent-provided and availability-gated: real command output in
fenced blocks first, `asciinema`+`agg` (or equivalent) for terminal motion,
`playwright` or the agent's browser tooling for web UI, video only when the
platform records. The package and skills never install tooling.

### Files

- Create: `src/llm_wiki_cli/skills/usage-examples/SKILL.md`
- Create: `src/llm_wiki_cli/skills/usage-examples/reference.md`
- Modify: `src/llm_wiki_cli/skills/user-docs-author/SKILL.md`, `reference.md`
- Modify: `src/llm_wiki_cli/skills/publish-docs/SKILL.md`, `reference.md`
- Modify: `src/llm_wiki_cli/skills/doc-review/SKILL.md`, `reference.md`
- Modify: `src/llm_wiki_cli/skills/onboarding-guide/SKILL.md`, `reference.md`
- Modify: `pyproject.toml` (package data, if enumerated per skill)
- Test: `tests/test_skills.py`
- Test: `tests/test_package_metadata.py`

### Tasks

- [x] Write `SKILL.md`: frontmatter description with clear use/don't-use
  boundaries; preconditions (maintained wiki, lint clean, authored guides
  exist — `user-docs-author` first otherwise; capture tooling checked, never
  installed); the seven-step loop from the ADR (worklist from evidence →
  capture in a disposable dir against read-only source → attach under
  `assets/<surface>/<page-stem>/` with alt text and a caption naming the
  exact command/flow and linking the evidence page → validate → adjust →
  defer honestly → run report); context budget section.
- [x] Write `reference.md`: capture tooling matrix with availability checks
  and text-first rule; media format policy (`png`/`jpg`/`webp`/`gif`/`svg`;
  poster-in-repo + external video recommended, in-repo `mp4`/`webm`
  size-warned); redaction rules (secrets, real user data, machine-specific
  paths); deferred-docs table extended with a `capture blocker` column;
  command matrix covering lint media categories and
  `site export/check --profile user` including built-site media checks;
  failure modes table.
- [x] Update the four adjacent skills with one-line cross-references to
  `usage-examples` (ADU-006 style), not duplicated instructions.
- [x] Register the skill in packaging so `llm-wiki skills list|export|install`
  ship it; extend the metadata/skills tests accordingly.
- [x] Add `tests/test_skills.py` assertions for the new skill's frontmatter
  contract, required sections, and the command examples' flag validity.

### Focused Verification

```bash
.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py -q
```

### Evidence

- Added bundled `src/llm_wiki_cli/skills/usage-examples/SKILL.md` and
  `reference.md`.
- Added package-data coverage in `pyproject.toml` and tests asserting skill
  list/install/export behavior.
- The self dogfood `skills list --format json` output included
  `usage-examples` with both expected files.

### Acceptance Criteria

- `llm-wiki skills list` includes `usage-examples`; export/install ship it.
- The skill text enforces evidence-linked captures, mirrored asset paths,
  redaction, deferral, and the no-install rule.
- Adjacent skills reference the new skill without contract duplication.

## UDE-007 - Autonomous-Agent Instruction Surface

Priority: P1
Status: Completed
Depends on: UDE-006
Type: Code/docs/tests

### Goal

Make the docs pipeline consumable by non-Claude autonomous agents through
the existing `init`/schema system, with README pointing at the two
consumption paths.

### Developer Context

`llm-wiki init --agent <name>` already writes per-agent constraint files via
`SCHEMA_FILENAMES` (`services/schema.py:21`: `CLAUDE.md`, `.cursorrules`,
`.github/copilot-instructions.md`, `.aider.conf.yml`,
`.opencode/instructions.md`, `generic` -> `AGENTS.md`), and
`replace_skill_block` refreshes skill guidance blocks in those files. Agents
without a dedicated entry (`hermes`, `openclaw`, ...) use the
`generic`/`AGENTS.md` target. Named registrations in `CLI_AGENTS`
(`config.py:79`) / `SCHEMA_FILENAMES` are two-line follow-ups deferred until
a real adopter asks — do not add speculative entries in this task.

### Files

- Modify: `src/llm_wiki_cli/services/schema.py`
- Modify: `src/llm_wiki_cli/commands/init_cmd.py` (only if the section needs
  init-time wiring beyond schema content)
- Modify docs: `README.md`
- Test: the schema/init test module and `tests/test_cli.py`

### Tasks

- [x] Add a docs-workflow section to the generated schema content: available
  bundled skills, invocation order (`wiki-bootstrap` -> `wiki-sync` ->
  `user-docs-author` -> `usage-examples` -> `publish-docs`), and the hard
  rules — semantic prose only, generated blocks are CLI-owned, source targets
  read-only, no toolchain installs, validation loop before commit, wiki
  commits separate from code commits.
- [x] Ensure the section renders for every `SCHEMA_FILENAMES` target,
  including `generic`/`AGENTS.md`, and stays stable under
  `replace_skill_block` refresh (idempotent re-runs).
- [x] Verify (and assert in tests) that bundled skill text contains no
  Claude-only tool assumptions — commands must be runnable from any
  shell-capable agent.
- [x] Add a "For autonomous agents" README section naming the two consumption
  paths: `init --agent generic` for instructions and `skills export --dest`
  for the skill files.
- [x] Add tests: generated `AGENTS.md` contains the docs-workflow section;
  re-running init/refresh does not duplicate it.

### Focused Verification

```bash
.venv/bin/pytest tests/test_cli.py tests/test_skills.py -q
```

### Evidence

- Updated schema guidance to include the user-docs workflow order:
  `wiki-bootstrap -> wiki-sync -> user-docs-author -> usage-examples ->
  publish-docs`.
- Added autonomous-agent README guidance for `init --agent generic` and
  `skills export --dest`.
- Cross-linked `usage-examples` from adjacent bundled skills and added tests in
  `tests/test_schema.py`, `tests/test_init.py`, and
  `tests/test_package_metadata.py`.

### Acceptance Criteria

- `init --agent generic` produces an `AGENTS.md` that a non-Claude agent can
  follow to run the full docs pipeline including example capture.
- Schema refresh is idempotent.
- README documents both consumption paths.
- No speculative agent registrations are added.

## UDE-008 - Self-Dogfood: Capture Examples For This Repo

Priority: P1
Status: Completed
Depends on: UDE-001 through UDE-006
Type: Dogfood report

### Goal

Run the full `usage-examples` workflow against this repository's own wiki and
guides, producing real terminal captures and a run report, and tune the
defaults the ADR left open.

### Developer Context

`llm-wiki` CLI flows are ideal terminal-capture targets (bootstrap, sync,
lint, site export/check). This is the first real exercise of the mirrored
asset layout, the lint categories, and the size cap. ADR remaining items to
settle here with evidence: the `media_oversize` default (proposed 2 MB), and
whether stale-asset accumulation in the out-dir warrants an opt-in clean.

### Files

- New report: `reports/usage_examples_self_dogfood_2026-XX-XX.md` (use the
  actual run date)
- Wiki changes under `docs/llm_wiki/guides/` and `docs/llm_wiki/assets/`

### Tasks

- [x] Follow the shipped `usage-examples` SKILL.md verbatim; deviations are
  findings, not silent adaptations.
- [x] Capture at least: one fenced real-output example, one terminal
  recording (if `asciinema`+`agg` or equivalent is available; otherwise a
  deferred-docs row with the capture blocker), attached to existing guide
  pages with evidence-linked captions.
- [x] Run the full validation chain: `lint --strict`, `ci-check`,
  `site export/check --profile user`, built-site checks in both link modes
  when a builder is available.
- [x] Record findings on: mirrored-path ergonomics, size-cap fit,
  warning noise, stale-asset behavior across two consecutive exports.
- [x] File follow-up tasks (or amend defaults in-place if trivially small)
  for anything the dogfood contradicts.

### Focused Verification

```bash
git diff --check -- reports/
.venv/bin/python -m llm_wiki_cli.cli lint --strict --src-dir . --wiki-dir docs/llm_wiki
```

### Evidence

- Added `reports/usage_examples_self_dogfood_2026-07-07.md`.
- Disposable runner `/tmp/llm-wiki-usage-examples-self-2026-07-07` passed
  `sync`, `lint --strict`, `ci-check`, `site export/check --profile user`, and
  built-site media checks in `http` and `file` modes.
- Dogfood confirmed the 2 MB media warning default and idempotent unchanged
  asset copies; terminal recording was deferred because `asciinema` and `agg`
  were unavailable.

### Acceptance Criteria

- This repo's user-profile site ships at least one validated usage example.
- The run report documents skill-contract friction and default tuning
  decisions with command output.
- All validation gates pass or failures are explained with deferred items.

## UDE-009 - Assistant Dogfood Confirmation

Priority: P1
Status: Completed
Depends on: UDE-008
Type: Dogfood report

### Goal

Confirm the media pipeline against the established external target with the
ADU-007 pattern: read-only source, fresh `/tmp` runner, both link modes.

### Developer Context

Mirror `reports/assistant_docsite_user_docs_confirmation_2026-07-05.md`. The
Assistant target at `/mnt/data/projects/Assistant` stays read-only; captures
that require *running* Assistant are only in scope if the runner environment
supports it — otherwise exercise the media pipeline with the wiki-side assets
authored in the runner copy of the wiki, and record the capture blockers as
deferred rows. The point of this task is pipeline confirmation (assets
mirror, checks pass in both modes), not maximal capture coverage.

### Files

- New report: `reports/assistant_usage_examples_confirmation_2026-XX-XX.md`

### Tasks

- [x] Fresh runner under `/tmp` (or scratchpad); Assistant repo untouched,
  verified clean before and after.
- [x] Author/attach at least one asset-backed example in the runner wiki;
  export and check with `--profile user` plus built-site media checks in
  `http` and `file` modes.
- [x] Compare warning/issue counts against the 2026-07-05 baseline run and
  explain deltas.
- [x] Record capture blockers honestly; no staged screenshots of flows the
  runner cannot execute.

### Focused Verification

```bash
git diff --check -- reports/
git -C /mnt/data/projects/Assistant status --porcelain
```

### Evidence

- Added `reports/assistant_usage_examples_confirmation_2026-07-07.md`.
- Fresh runner
  `/tmp/llm-wiki-assistant-usage-examples-bootstrap-2026-07-07` bootstrapped
  from read-only `/mnt/data/projects/Assistant`, attached one runner-local
  media asset, exported hosted and file-friendly user sites, built both with
  MkDocs, and passed built-site media checks in `http` and `file` modes.
- Assistant remained clean before and after; counts matched the 2026-07-05
  baseline except for the intentional one copied usage asset.

### Acceptance Criteria

- Assistant repo is untouched.
- Media-bearing user export passes export/check and built-site validation in
  both link modes, or failures are triaged in the report.
- Report explains every delta from the ADU-007 baseline.

## UDE-010 - Public Docs, Sibling Wiki, And Closeout

Priority: P1
Status: Completed
Depends on: UDE-001 through UDE-009
Type: Docs/report

### Goal

Land the user-facing documentation for the new behavior and close the
backlog with a confirmation trail.

### Files

- Modify: `README.md` (surface taxonomy, media validation, autonomous-agents
  section final pass)
- Modify: `CHANGELOG.md`
- Sibling wiki pages under `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki`
- This backlog file (status flips)
- New report: `reports/user_docs_usage_examples_closure_2026-XX-XX.md`

### Tasks

- [x] Final README pass: `assets/` surface, media lint categories, export
  mirroring, built-site media checks, `usage-examples` skill, autonomous
  agent paths.
- [x] CHANGELOG entry per house convention.
- [x] Update sibling wiki command/workflow/skill pages for every user-facing
  change in UDE-001..007.
- [x] Flip all task statuses in this file with evidence lines filled.
- [x] Write the closure report: implemented scope, dogfood summaries,
  verification transcript, residual limitations (media staleness remains
  undetected by design; capture-tooling variance).

### Focused Verification

```bash
.venv/bin/pytest -q --ignore=tests/test_rust_extract.py
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
git diff --check
git -C /mnt/data/projects/llm-wiki/python-wiki-llm.wiki diff --check
```

### Evidence

- Updated README, CHANGELOG, and sibling wiki pages:
  `Static-Site-Distribution.md`, `Linting-and-Troubleshooting.md`,
  `Command-Reference.md`, `Agent-Support.md`, and `Plugins-and-Skills.md`.
- Added closure report
  `reports/user_docs_usage_examples_closure_2026-07-07.md` and final review
  `reports/user_docs_usage_examples_final_review_2026-07-07.md`.
- Verification passed: focused suites, full suite minus
  `tests/test_rust_extract.py`, `compileall`, Ruff check/format, main
  `git diff --check`, and sibling wiki `diff --check`.

### Acceptance Criteria

- All UDE tasks are Completed with evidence, or explicitly deferred with
  rationale recorded in the closure report.
- README/CHANGELOG/sibling wiki reflect the shipped behavior.
- The full suite (minus the known Rust-extract environmental split) passes.
