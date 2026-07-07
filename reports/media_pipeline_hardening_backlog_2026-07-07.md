# Media Pipeline Hardening Implementation Backlog

> For agentic workers: REQUIRED SUB-SKILL: Use
> `superpowers:executing-plans` to execute this backlog task-by-task. Update
> task status in this file as work lands, preserve unrelated worktree changes,
> and commit each completed implementation task as a scoped change unless the
> user explicitly asks for a different commit strategy.

**Goal:** Close the post-review media-pipeline defects and follow-up debt from `reports/adr_media_pipeline_hardening_2026-07-07.md` without reopening the already-shipped usage-docs media feature.

**Architecture:** Harden media parsing once in `wiki_media`, make lint/export policy consistent for every wiki-internal referenced media file, document warning-level policy gaps, then consolidate duplicate resolver and asset-scan logic after the correctness fixes land. Keep behavior additive or false-positive-reducing unless a task explicitly names a sanctioned output delta.

**Tech Stack:** Python 3.9+, stdlib-only parsing and path handling, argparse CLI, pytest, Ruff, Markdown report/docs artifacts, bundled skill Markdown, sibling wiki docs.

---

Date: 2026-07-07
Source ADR: `reports/adr_media_pipeline_hardening_2026-07-07.md`
Related ADR: `reports/adr_user_docs_usage_examples_2026-07-07.md`
Related backlog: `reports/user_docs_usage_examples_backlog_2026-07-07.md`
Status: Done
Owner: Unassigned
Task prefix: `UDH-` (Usage Docs media Hardening)

## Implementation Closeout

- Main implementation commit: `76a2eb6` (`feat: harden media pipeline`)
- Sibling wiki documentation commit: `6740448` (`docs: document media pipeline hardening`)
- Closure report: `reports/media_pipeline_hardening_closure_2026-07-07.md`
- Final review: initial final review found a built-site `data:` `srcset` false-positive gap and the missing closure report; both were addressed before closeout.
- Verification evidence: full gate passed with `1605 passed, 34 skipped` for `.venv/bin/pytest -q --ignore=tests/test_rust_extract.py`, plus clean compileall, Ruff, format-check, and diff checks.

## Source Context

The usage-docs media program shipped the first complete media layer: `assets/` surface registration, media lint categories, surface-index asset maps, static-export asset mirroring, built-site media validation, the `usage-examples` skill, and agent schema guidance. The feature commit `a78bfbc` shipped that layer. The blocker-fix commit `23fed29` fixed two release blockers:

- Plain markdown links to media are existence-checked as `media_link_broken`, count as referenced assets, and are mirrored by export when they resolve under `assets/`.
- Multi-line raw `<video>` embeds survive Docusaurus MDX escaping.

The ADR tracks the remaining 13 verified review findings. This backlog keeps the ADR's sequencing: correctness tracks first, small robustness and contract items next, then deduplication and efficiency cleanup.

## Findings Coverage

| Finding | Backlog task | Outcome |
| --- | --- | --- |
| F-01 Parenthesized markdown media targets truncated | UDH-001 | Shared balanced markdown target scanner covers images, plain media links, lint page links, and surface-index links. |
| F-02 Wiki-internal media outside `assets/` passes lint/check but is not mirrored | UDH-005 | Export mirrors every wiki-internal referenced media file and lint warns about convention drift. |
| F-03 Fenced media examples hard-fail lint | UDH-002 | Media collection ignores fenced code blocks. |
| F-04 Reference-style images invisible | UDH-003 | Same-page reference-style image definitions are collected and resolved. |
| F-05 Symlinked assets escaping wiki root silently disappear | UDH-007 | Escape is warning-visible as `media_symlink_escape`. |
| F-06 Titled internal-link surface-index behavior changed without acknowledgement | UDH-008 | Contract is pinned by regression test and CHANGELOG note. |
| F-07 `srcset` unparsed in wiki and built HTML | UDH-004 | Wiki and built-site scanners validate and mirror every local `srcset` candidate. |
| F-08 Non-media files under `assets/` invisible to orphan scan | UDH-006 | `assets/` scan covers all non-hidden files and warns on unrecognized asset types. |
| F-09 Built-site href/media resolver duplication | UDH-009 | Shared built-site parse-and-resolve helper with thin href/media callers. |
| F-10 Dead `_IGNORED_SCHEMES` policy in `wiki_media.local_link_path` | UDH-009 | Wiki-side local path policy is simplified and documented by tests. |
| F-11 Stale exported asset detection computed twice | UDH-010 | One stale-asset reducer feeds export operations and site-check warnings. |
| F-12 Lint media phase parses every page twice | UDH-011 | Media references are collected once per lint run and reused by the orphan reducer. |
| F-13 `_same_file_bytes` reads both files fully | UDH-012 | File comparison checks size first, then streams chunks. |

## Scope

In scope:

- Markdown and raw HTML media target parsing in `src/llm_wiki_cli/services/wiki_media.py`.
- Lint media diagnostics in `src/llm_wiki_cli/commands/lint_cmd.py`.
- Surface-index link and asset-count contracts in `src/llm_wiki_cli/services/wiki_surface_index.py`.
- Static-site export asset mirroring and stale-asset reporting in `src/llm_wiki_cli/services/site_export.py`.
- Built HTML validation in `src/llm_wiki_cli/services/site_html_check.py`.
- Public docs, bundled skill references, and sibling wiki docs for new warning categories and behavior deltas.

Out of scope:

- General `broken_links` fence exclusion for all page links. UDH-002 changes media collection only. The broader page-link behavior predates the media pipeline and needs a separate decision.
- Inline-code-span exclusion for media references. Fenced code blocks are the supported false-positive fix for this backlog.
- Full symlinked asset-store support. UDH-007 makes escapes visible but keeps `resolve()` containment guards.
- Cross-page reference-definition resolution for `![alt][ref]`. UDH-003 supports same-page definitions only.
- Image/video content decoding, thumbnail generation, or new binary/media dependencies.
- Automatic deletion of stale exported assets.

## Delivery Rules

- Use the project virtual environment for every Python command: `.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/ruff`.
- Preserve Windows, macOS, Ubuntu, and Python 3.9+ compatibility. Use `Path`, POSIX-normalized wiki-relative strings, and no hardcoded platform separators.
- Preserve unrelated dirty files. Inspect `git status --short` before staging and stage only files that belong to the active task.
- Keep all new lint categories warning-level unless this backlog explicitly says an existing blocking category remains blocking.
- Keep wikis without `assets/` and without media references behaviorally unchanged. Sanctioned output deltas are F-01 parenthesis handling and F-03 fenced media exclusion, both reducing false positives.
- Keep source wiki pages and wiki-local files as the source of truth. Export output remains derived and must not delete source assets.
- Update `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki` separately when a task changes user-facing CLI behavior, lint category documentation, export behavior, or skill workflow guidance.
- For ignored `reports/` artifacts, verify ignore behavior with `git check-ignore -v` and stage intentionally with `git add -f` only when committing the report.

## Dependency Order

| ID | Title | Priority | Depends on | Type |
| --- | --- | --- | --- | --- |
| UDH-001 | Shared markdown target extraction and parenthesis fix | P0 | None | Code/tests |
| UDH-002 | Media fence exclusion | P0 | UDH-001 | Code/tests/docs |
| UDH-003 | Same-page reference-style image support | P0 | UDH-001 | Code/tests/docs |
| UDH-004 | `srcset` media validation and mirroring | P0 | UDH-001 | Code/tests/docs |
| UDH-005 | Mirror wiki-internal media outside `assets/` | P0 | UDH-001 | Code/tests/docs |
| UDH-006 | All-file `assets/` inventory and unrecognized-type warnings | P0 | UDH-001 | Code/tests/docs |
| UDH-007 | Symlink escape diagnostics | P1 | UDH-001, UDH-005 | Code/tests/docs |
| UDH-008 | Titled-link surface-index contract pin | P1 | None | Tests/docs |
| UDH-009 | Shared built-site resolver and wiki-side scheme cleanup | P2 | UDH-004 | Code/tests |
| UDH-010 | Single stale-exported-asset reducer | P2 | UDH-005, UDH-006 | Code/tests |
| UDH-011 | Single media collection path for lint and asset indexing | P2 | UDH-001 through UDH-006 | Code/tests |
| UDH-012 | Size-aware chunked asset file comparison | P2 | None | Code/tests |
| UDH-013 | Public docs, sibling wiki, and closeout review | P1 | UDH-001 through UDH-012 | Docs/report |

## File Map

Core code touch points:

- `src/llm_wiki_cli/services/wiki_media.py`
  - Current markdown regexes: `_MARKDOWN_IMAGE_RE`, `_MARKDOWN_PLAIN_LINK_RE`, `_MARKDOWN_TITLE_RE`.
  - Current raw HTML parser: `_HtmlMediaParser`.
  - Current policy helpers: `normalize_markdown_link_target`, `local_link_path`, `media_type_for_path`, `is_media_target`, `asset_relative_path`, `_asset_files`.
  - Current index helper: `build_asset_index`.
  - `src/llm_wiki_cli/commands/lint_cmd.py`
  - Current page-link regex: `LINK_RE`.
  - Current page index builder: `_build_page_index`.
  - Current checks: `_check_broken_links`, `_check_media_references`, `_content_by_relative_path`.
  - Current renderer groups for media categories near the diagnostic category lists.
- `src/llm_wiki_cli/services/wiki_surface_index.py`
  - Current link extraction: `_LINK_RE`, `_outgoing_internal_links`, `_resolve_internal_target`.
  - Current asset counts are sourced through `wiki_media.build_asset_index`.
- `src/llm_wiki_cli/services/site_export.py`
  - Current asset operations: `_record_asset_operations`, `_record_asset_copy_operation`, `_same_file_bytes`, `_stale_asset_warnings`, `_exported_asset_paths`.
  - Current markdown export iterator: `_iter_markdown_link_targets`, useful as the line-based fenced-code precedent.
- `src/llm_wiki_cli/services/site_html_check.py`
  - Current parser and duplicated checks: `_HrefParser`, `_check_href`, `_check_media_src`, `_candidate_targets`, `_IGNORED_SCHEMES`.

Public docs and skills:

- `README.md`
- `CHANGELOG.md`
- `src/llm_wiki_cli/skills/usage-examples/SKILL.md`
- `src/llm_wiki_cli/skills/usage-examples/reference.md`
- `src/llm_wiki_cli/skills/doc-review/SKILL.md`
- `src/llm_wiki_cli/skills/doc-review/reference.md`
- Sibling wiki checkout: `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki`

Likely tests:

- `tests/test_lint.py`
- `tests/test_site_export.py`
- `tests/test_wiki_surface_index.py`
- `tests/test_cli.py`
- `tests/test_skills.py`
- `tests/test_package_metadata.py`

## Shared Verification Baseline

Run the focused verification named by each task. For code or CLI behavior changes, also run:

```bash
.venv/bin/pytest tests/test_lint.py tests/test_site_export.py tests/test_cli.py -q
.venv/bin/python -m compileall src tests
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
git diff --check
```

For skill text or package-data changes, also run:

```bash
.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py -q
.venv/bin/python -m compileall src tests
git diff --check
```

For sibling wiki changes, also run:

```bash
git -C /mnt/data/projects/llm-wiki/python-wiki-llm.wiki diff --check
```

Full-suite gate before closeout:

```bash
.venv/bin/pytest -q --ignore=tests/test_rust_extract.py
```

## UDH-001 - Shared Markdown Target Extraction And Parenthesis Fix

Priority: P0
Status: Done
Depends on: None
Type: Code/tests
Track: 1
Findings: F-01

### Goal

Replace the non-greedy markdown target regex behavior with one shared local markdown target extractor that handles one practical level of balanced parentheses, angle-bracket targets, optional titles, and current local-link normalization.

### Developer Context

Today `wiki_media._MARKDOWN_IMAGE_RE`, `wiki_media._MARKDOWN_PLAIN_LINK_RE`, `lint_cmd.LINK_RE`, and `wiki_surface_index._LINK_RE` each try to capture markdown link targets with regexes shaped like `(.+?)`. A valid target such as `../assets/guides/tour/shot(1).png` is captured as `../assets/guides/tour/shot(1`, which creates three bad effects:

- `lint_cmd._check_broken_links` can report a blocking `broken_links` error for a media target that actually exists.
- `wiki_media.collect_media_references` misses the real media target, so the asset can be reported as `media_orphan`.
- `site_export._record_asset_operations` never sees the real reference through `build_asset_index`, so the asset is not mirrored.

The blocker fix added `_MARKDOWN_PLAIN_LINK_RE`, so the same bug now affects plain media links as well as image embeds. Patch all markdown-media and page-link consumers through the same extractor instead of editing each regex independently.

### Files

- Modify: `src/llm_wiki_cli/services/wiki_media.py`
- Modify: `src/llm_wiki_cli/commands/lint_cmd.py`
- Modify: `src/llm_wiki_cli/services/wiki_surface_index.py`
- Test: `tests/test_lint.py`
- Test: `tests/test_site_export.py`
- Test: `tests/test_wiki_surface_index.py`

### Implementation Tasks

- [x] Add a small result dataclass in `wiki_media.py`, for example `MarkdownLinkTarget`, with fields for `raw_target`, normalized `target`, `label`, `is_image`, and source span only if a later task needs spans.
- [x] Implement a scanner in `wiki_media.py` that walks markdown content and yields inline markdown links/images. It must accept: `![Shot](../assets/guides/tour/shot(1).png)`, `[Demo](../assets/guides/tour/demo(1).webm)`, `![Shot](<../assets/guides/tour/shot(2).png>)`, and titled links such as `![Shot](../assets/guides/tour/shot.png "Home")`.
- [x] Keep the supported parenthesis scope explicit: one nested balanced pair in a target is supported; angle-bracket targets are the escape hatch for more complex targets.
- [x] Update `collect_media_references` to consume the shared extractor for markdown images and plain markdown media links.
- [x] Update `lint_cmd._build_page_index` so `links_by_page` stores raw targets from the shared extractor instead of `LINK_RE.findall(content)`.
- [x] Update `wiki_surface_index._outgoing_internal_links` to use the shared extractor for ordinary internal markdown links. Mermaid click extraction remains separate.
- [x] Keep `wiki_media.normalize_markdown_link_target` as the canonical title and angle-bracket normalizer used by the scanner and existing callers.
- [x] Add regression tests for a present parenthesized image target: no `broken_links`, no `media_link_broken`, no `media_orphan`, and the asset appears in export output.
- [x] Add a plain markdown media-link regression for a present parenthesized `.webm` or `.mp4` target.
- [x] Add a surface-index regression proving a titled internal link with a parenthesized path still resolves to an outgoing internal edge when the page exists.

### Focused Verification

```bash
.venv/bin/pytest tests/test_lint.py::TestLintMediaReferences -q
.venv/bin/pytest tests/test_site_export.py -k "asset or media" -q
.venv/bin/pytest tests/test_wiki_surface_index.py -q
```

### Acceptance Criteria

- Valid parenthesized media targets are neither truncated nor misclassified as page links.
- Plain markdown links to parenthesized media targets are validated and mirrored the same way as markdown image embeds.
- Existing titled-link stripping behavior is preserved.
- Surface-index internal-link extraction no longer depends on a separate non-greedy markdown target regex.

## UDH-002 - Media Fence Exclusion

Priority: P0
Status: Done
Depends on: UDH-001
Type: Code/tests/docs
Track: 1
Findings: F-03

### Goal

Ignore fenced code blocks during media collection so documentation examples of `<img>`, `<video>`, markdown images, or plain media links do not produce media lint issues.

### Developer Context

`wiki_media.collect_media_references` currently scans the whole page content.
That means a fenced example such as:

````markdown
```html
<img src="assets/example.png" alt="example">
```
````

reports a blocking `media_link_broken` when `assets/example.png` does not exist. The export path already has a line-based fenced-code walk in `site_export.py` around `_iter_markdown_link_targets`; reuse that design, not a fragile regular expression. This task intentionally changes media lint only.
The existing general page-link `broken_links` behavior in fenced code remains out of scope.

### Files

- Modify: `src/llm_wiki_cli/services/wiki_media.py`
- Test: `tests/test_lint.py`
- Docs: `README.md`
- Sibling wiki docs if lint behavior pages enumerate media checking behavior.

### Implementation Tasks

- [x] Add a helper in `wiki_media.py`, for example `strip_fenced_code_blocks(content: str) -> str`, that preserves line count while replacing fenced content with blank lines.
- [x] Support common Markdown fences opened with at least three backticks or at least three tildes, with optional language text after the opener.
- [x] Call the helper before markdown and raw HTML media collection inside `collect_media_references`.
- [x] Add a lint test where fenced raw `<img src="assets/example.png">` does not report `media_link_broken`.
- [x] Add a lint test where fenced markdown `![Shot](assets/example.png)` and `[Demo](assets/demo.webm)` do not count as media references or orphan suppressors.
- [x] Add a lint test proving an unfenced media reference immediately before or after the fenced block is still validated.
- [x] Document the behavior delta in `README.md`: media lint ignores fenced examples; general page-link lint is unchanged.

### Focused Verification

```bash
.venv/bin/pytest tests/test_lint.py::TestLintMediaReferences -q
git diff --check -- README.md tests/test_lint.py src/llm_wiki_cli/services/wiki_media.py
```

### Acceptance Criteria

- Fenced media examples do not create `media_link_broken`, `media_missing_alt_text`, `media_oversize`, or orphan-reference effects.
- Unfenced media references are unchanged.
- The README notes the media-only fence behavior so the lint output delta is visible to users.

## UDH-003 - Same-Page Reference-Style Image Support

Priority: P0
Status: Done
Depends on: UDH-001
Type: Code/tests/docs
Track: 1
Findings: F-04

### Goal

Collect same-page reference-style image embeds so `![alt][ref]` and `![alt][]` participate in media lint, export mirroring, and asset indexing.

### Developer Context

Current media parsing only sees inline markdown image syntax and raw HTML `src` attributes. A page containing:

```markdown
![Screenshot][home]

[home]: ../assets/guides/tour/home.png "Home"
```

does not validate the file, does not count the asset as referenced, and does not mirror the asset during export. Keep the scope intentionally narrow: same-page definitions only. Do not implement cross-page definitions or broad CommonMark shortcut semantics beyond the two ADR-approved forms.

### Files

- Modify: `src/llm_wiki_cli/services/wiki_media.py`
- Test: `tests/test_lint.py`
- Test: `tests/test_site_export.py`
- Test: `tests/test_wiki_surface_index.py`
- Docs: `README.md`

### Implementation Tasks

- [x] Add a same-page reference-definition collector in `wiki_media.py` for lines shaped as `[label]: target` with optional single- or double-quoted title text.
- [x] Normalize reference labels case-insensitively and collapse internal whitespace for lookup.
- [x] Resolve `![Alt][label]` by looking up `label`.
- [x] Resolve collapsed image references `![Alt][]` by looking up the alt text as the label.
- [x] Keep unresolved reference-style images invisible to media checks rather than converting them to page-link errors.
- [x] Ensure targets flow through `local_link_path`, `media_type_for_path`, alt-text handling, and oversize checks exactly like inline markdown images.
- [x] Add lint tests for present, missing, and collapsed reference-style image targets.
- [x] Add export and surface-index tests proving reference-style image targets are included in `build_asset_index` and export mirroring.
- [x] Document same-page reference-style image support in the README media section.

### Focused Verification

```bash
.venv/bin/pytest tests/test_lint.py::TestLintMediaReferences -q
.venv/bin/pytest tests/test_site_export.py -k "asset or media" -q
.venv/bin/pytest tests/test_wiki_surface_index.py -q
```

### Acceptance Criteria

- Same-page reference-style image targets are validated, counted, and mirrored.
- Missing reference-style media targets report `media_link_broken`.
- Existing inline markdown and raw HTML media behavior is unchanged.
- Unsupported cross-page or unresolved definitions are documented as out of scope and do not create new blocking behavior.

## UDH-004 - `srcset` Media Validation And Mirroring

Priority: P0
Status: Done
Depends on: UDH-001
Type: Code/tests/docs
Track: 1
Findings: F-07

### Goal

Parse local `srcset` candidates in wiki raw HTML and built HTML so responsive media is validated, mirrored, traversal-checked, and counted consistently.

### Developer Context

Current wiki parsing reads only `src` from raw `<img>`, `<video>`, and `<source>` tags. Current built-site parsing also reads only `src`. A local responsive image such as:

```html
<img src="assets/fallback.png" srcset="assets/small.png 1x, assets/large.png 2x">
```

can therefore bypass wiki-side validation and export mirroring for `small.png` and `large.png`. A traversal candidate inside `srcset` also avoids built-site unsafe-link handling. Each candidate URL must use the same local-target policy as `src`.

### Files

- Modify: `src/llm_wiki_cli/services/wiki_media.py`
- Modify: `src/llm_wiki_cli/services/site_html_check.py`
- Test: `tests/test_lint.py`
- Test: `tests/test_site_export.py`
- Docs: `README.md`
- Skill docs: `src/llm_wiki_cli/skills/usage-examples/reference.md` if the supported-media syntax list is updated.

### Implementation Tasks

- [x] Add a `split_srcset_candidates(value: str) -> list[str]` helper in `wiki_media.py` or a new shared media utility if importing from `site_html_check.py` would create a dependency cycle.
- [x] Split candidates on commas, trim whitespace, and take the first whitespace-delimited token from each candidate as the URL.
- [x] Treat empty candidates as ignored.
- [x] Keep data URLs and remote URLs ignored through existing scheme handling.
- [x] Extend `_HtmlMediaParser` in `wiki_media.py` to collect `srcset` candidates from `img` and `source` tags. Each candidate becomes a `MediaReference` with source value `html_srcset`.
- [x] Extend `_HrefParser` in `site_html_check.py` to collect `srcset` candidates from `img` and `source` tags.
- [x] Run built-site `srcset` candidates through the same category behavior as media `src`: missing files report `missing_built_media_target`, traversal reports `unsafe_built_html_link`, malformed values report `malformed_built_html_link`.
- [x] Add lint tests for present and missing wiki `srcset` candidates.
- [x] Add export tests proving referenced `srcset` assets are copied.
- [x] Add built-site check tests for missing `srcset`, external `srcset`, and traversal `srcset`.
- [x] Document `srcset` validation and mirroring support in the README.

### Focused Verification

```bash
.venv/bin/pytest tests/test_lint.py::TestLintMediaReferences -q
.venv/bin/pytest tests/test_site_export.py -k "srcset or built_site or media" -q
```

### Acceptance Criteria

- Wiki `srcset` candidates are validated, counted as referenced assets, and mirrored during export.
- Built HTML `srcset` candidates are checked for missing targets and traversal using the same issue categories as media `src`.
- Remote and data `srcset` candidates remain ignored.
- Existing `src` media behavior is unchanged.

## UDH-005 - Mirror Wiki-Internal Media Outside `assets/`

Priority: P0
Status: Done
Depends on: UDH-001
Type: Code/tests/docs
Track: 2
Findings: F-02

### Goal

Close the lint-green/export-broken window by mirroring every referenced media file that resolves inside the wiki root, while warning when the file does not follow the `assets/` convention.

### Developer Context

`wiki_media.asset_relative_path` currently returns `None` when a referenced media file resolves inside the wiki but the wiki-relative path does not start with `assets/`. That makes `guides/foo.md` with `![pic](pic.png)` pass lint when `guides/pic.png` exists, but `site_export._record_asset_operations` never copies it. The ADR decision is that export should copy what pages reference.
The `assets/` convention remains a warning-level hygiene policy, not a mirror precondition.

The new `media_outside_assets` warning starts per page, not per reference, to avoid high-noise output. The warning should name sorted offending targets and the mirrored export locations.

### Files

- Modify: `src/llm_wiki_cli/services/wiki_media.py`
- Modify: `src/llm_wiki_cli/commands/lint_cmd.py`
- Modify: `src/llm_wiki_cli/services/site_export.py`
- Test: `tests/test_lint.py`
- Test: `tests/test_site_export.py`
- Docs: `README.md`
- Skill docs: `src/llm_wiki_cli/skills/usage-examples/reference.md`
- Skill docs: `src/llm_wiki_cli/skills/doc-review/reference.md`

### Implementation Tasks

- [x] Add a helper in `wiki_media.py` that resolves a `MediaReference` to a wiki-relative path for any file contained by the wiki root, not only `assets/` paths.
- [x] Keep `asset_relative_path` or replace it with a clearer helper name only if all call sites are updated in the same task.
- [x] Preserve containment: paths resolving outside the wiki root are not mirrored.
- [x] Update `build_asset_index` so referenced media outside `assets/` appears in `referenced` and `by_page`.
- [x] Update `site_export._record_asset_operations` so `guides/pic.png` copies to `<out>/guides/pic.png` and hub export copies it under the source namespace.
- [x] Add `media_outside_assets` as a non-blocking lint diagnostic in `lint_cmd._check_media_references`.
- [x] Emit one `media_outside_assets` warning per page, with a deterministic sorted target list in the message and the page path in `path`.
- [x] Add lint tests for inside-wiki outside-assets media: no blocking issue, one warning per page, and no warning for canonical `assets/` references.
- [x] Add export tests for single-wiki and hub export copying outside-assets referenced media.
- [x] Update docs and skill category tables so agents know the warning means "move into `assets/` when practical; export still works."

### Focused Verification

```bash
.venv/bin/pytest tests/test_lint.py::TestLintMediaReferences -q
.venv/bin/pytest tests/test_site_export.py -k "asset or hub or media" -q
.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py -q
```

### Acceptance Criteria

- Referenced wiki-internal media outside `assets/` is copied during export.
- The lint warning is non-blocking and emitted at page granularity.
- Referenced outside-assets media no longer appears as an unmirrored lint-green/site-check-late failure.
- Existing `assets/` convention remains documented and preferred.

## UDH-006 - All-File `assets/` Inventory And Unrecognized-Type Warnings

Priority: P0
Status: Done
Depends on: UDH-001
Type: Code/tests/docs
Track: 2
Findings: F-08

### Goal

Make the `assets/` inventory cover every non-hidden file under `assets/`, not only recognized media extensions, and warn on unrecognized asset types without breaking adopters.

### Developer Context

`wiki_media._asset_files` currently skips any file whose suffix is not in the image/video allowlist. That conflicts with the original usage-docs decision to scan all of `assets/` so misplaced or unsupported files do not disappear from lint and the surface index. The new policy is:

- Recognized media files keep existing `media_orphan` behavior when unreferenced.
- Non-hidden, non-media files under `assets/` report `asset_unrecognized_type` as a warning.
- Dotfiles and `README.md`-style companion files are excluded from the warning.
- Surface-index asset counts gain an additive `other` bucket under `counts.assets.by_media_type`.

### Files

- Modify: `src/llm_wiki_cli/services/wiki_media.py`
- Modify: `src/llm_wiki_cli/commands/lint_cmd.py`
- Modify: `src/llm_wiki_cli/services/wiki_surface_index.py`
- Test: `tests/test_lint.py`
- Test: `tests/test_wiki_surface_index.py`
- Docs: `README.md`
- Skill docs: `src/llm_wiki_cli/skills/usage-examples/reference.md`
- Skill docs: `src/llm_wiki_cli/skills/doc-review/reference.md`

### Implementation Tasks

- [x] Update `_asset_files` to return every non-hidden file under `assets/`.
- [x] Exclude dotfiles and files under hidden directories by checking path parts that start with `.`.
- [x] Exclude `README.md` and `README.*` companion files from `asset_unrecognized_type`.
- [x] Keep unreferenced recognized media files reporting `media_orphan`.
- [x] Add `asset_unrecognized_type` warning diagnostics for unrecognized non-hidden files under `assets/`.
- [x] Add `other` to the `by_media_type` counts returned by `build_asset_index`.
- [x] Ensure `.llm-wiki-surface.json` changes are additive: existing `image` and `video` keys remain present, and `other` is added.
- [x] Add lint tests for an unreferenced `.png`, an unrecognized `.txt`, a `README.md`, and a dotfile under `assets/`.
- [x] Add surface-index tests for `other` counts and stable path ordering.
- [x] Update docs and skill tables for the new `asset_unrecognized_type` category.

### Focused Verification

```bash
.venv/bin/pytest tests/test_lint.py::TestLintMediaReferences -q
.venv/bin/pytest tests/test_wiki_surface_index.py -q
.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py -q
```

### Acceptance Criteria

- All relevant files under `assets/` are visible to lint and the surface index.
- Recognized media orphan behavior is preserved.
- Unrecognized asset types warn without blocking.
- Existing surface-index consumers can keep reading `image` and `video`, and may opt into the new `other` count.

## UDH-007 - Symlink Escape Diagnostics

Priority: P1
Status: Done
Depends on: UDH-001, UDH-005
Type: Code/tests/docs
Track: 3
Findings: F-05

### Goal

Make symlinked media references that escape the wiki root visible as warnings instead of silently dropping them from indexing and export.

### Developer Context

The current media path flow resolves a target and then uses `relative_to` the resolved wiki root. That is the correct traversal guard, but it silently drops the reference when the unresolved path appears to be inside the wiki while the resolved path escapes through a symlink. Full symlinked asset-store support is deferred. This task only exposes the limitation.

### Files

- Modify: `src/llm_wiki_cli/services/wiki_media.py`
- Modify: `src/llm_wiki_cli/commands/lint_cmd.py`
- Test: `tests/test_lint.py`
- Docs: `README.md`
- Sibling wiki docs if troubleshooting pages discuss media asset storage.

### Implementation Tasks

- [x] Add a helper in `wiki_media.py` that can distinguish an unresolved target path under the wiki root from a resolved target path outside it.
- [x] In lint media checking, emit `media_symlink_escape` as a warning when that condition is detected.
- [x] Keep the existing containment guard: escaped targets are not mirrored and do not count as referenced assets.
- [x] Add a symlink-aware test using `pytest.importorskip` or platform-safe skip logic when the platform cannot create symlinks.
- [x] Test that normal `..` traversal outside the wiki remains blocking or ignored according to existing behavior; this warning is for symlink escapes, not ordinary missing paths.
- [x] Document the limitation: symlinked asset stores are not mirrored; vendor files into the wiki or mount them inside the wiki root.

### Focused Verification

```bash
.venv/bin/pytest tests/test_lint.py::TestLintMediaReferences -q
git diff --check -- src/llm_wiki_cli/services/wiki_media.py src/llm_wiki_cli/commands/lint_cmd.py README.md tests/test_lint.py
```

### Acceptance Criteria

- Symlink escapes under media paths produce a non-blocking `media_symlink_escape` diagnostic.
- Escaping targets are not exported.
- Tests are portable and skip cleanly on platforms without symlink privileges.
- Docs explain the current limitation and supported workaround.

## UDH-008 - Titled-Link Surface-Index Contract Pin

Priority: P1
Status: Done
Depends on: None
Type: Tests/docs
Track: 4
Findings: F-06

### Goal

Treat titled internal-link resolution in the surface index as an intentional fix by pinning it with a regression test and documenting it in the changelog.

### Developer Context

The shared normalizer changed surface-index behavior for titled markdown links. An asset-free wiki containing:

```markdown
[Setup](guides/setup.md "Setup guide")
```

now resolves an outgoing internal edge where the old output did not. The ADR decides this is desirable. There is no code change unless the regression test exposes drift.

### Files

- Test: `tests/test_wiki_surface_index.py`
- Docs: `CHANGELOG.md`

### Implementation Tasks

- [x] Add a regression test in `tests/test_wiki_surface_index.py` that builds a small wiki with a titled internal link and asserts the outgoing internal edge points to the target page.
- [x] Keep the fixture asset-free so the test proves the contract change is independent of the media pipeline.
- [x] Add a `Fixed` changelog note: internal links with markdown titles now resolve in the surface index.
- [x] Do not change production code unless the new test fails.

### Focused Verification

```bash
.venv/bin/pytest tests/test_wiki_surface_index.py -q
git diff --check -- tests/test_wiki_surface_index.py CHANGELOG.md
```

### Acceptance Criteria

- Surface-index titled-link behavior is explicitly tested.
- The changelog acknowledges the contract change.
- No unrelated surface-index JSON changes are introduced.

## UDH-009 - Shared Built-Site Resolver And Wiki-Side Scheme Cleanup

Priority: P2
Status: Done
Depends on: UDH-004
Type: Code/tests
Track: 5
Findings: F-09, F-10

### Goal

Remove duplicate built-site href/media resolver logic and delete the dead scheme-policy branch in `wiki_media.local_link_path`.

### Developer Context

`site_html_check._check_href` and `_check_media_src` duplicate most of the same parse, scheme, NUL, unquote, containment, and missing-target handling.
They differ in candidate resolution and issue category for missing targets.
At the same time, `wiki_media.local_link_path` has a dead `_IGNORED_SCHEMES` membership branch because the following `if parsed.scheme` already rejects every scheme. The live behavior is:

- Built-site checks have an ignored-schemes policy for external links/media.
- Wiki-side local path extraction treats any scheme as external/ignored.

Keep that behavior and make it explicit with tests.

### Files

- Modify: `src/llm_wiki_cli/services/site_html_check.py`
- Modify: `src/llm_wiki_cli/services/wiki_media.py`
- Test: `tests/test_site_export.py`
- Test: `tests/test_lint.py`

### Implementation Tasks

- [x] Introduce an internal helper in `site_html_check.py`, for example `_resolve_local_html_target(...)`, that performs shared parse, NUL, scheme/netloc, unquote, and containment checks.
- [x] Keep href and media callers thin: href supplies link-mode candidate generation and `missing_built_html_target`; media supplies direct-file candidate generation and `missing_built_media_target`.
- [x] Keep href-only file-mode directory URL behavior in the href path.
- [x] Keep external `http`, `https`, `mailto`, `tel`, `data`, and `javascript` ignored in built-site checks.
- [x] In `wiki_media.local_link_path`, replace the dead ignored-schemes branch with the explicit rule `if parsed.netloc or parsed.scheme: return None`.
- [x] Delete `wiki_media._IGNORED_SCHEMES` if no live code needs it.
- [x] Add tests proving wiki-side `http:`, `data:`, `mailto:`, and an unknown scheme are all ignored as non-local targets.
- [x] Add built-site tests proving href and media still differ only in their intended missing-target categories.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py -k "built_site or html or media" -q
.venv/bin/pytest tests/test_lint.py::TestLintMediaReferences -q
```

### Acceptance Criteria

- Built-site href/media handling has one shared parse-and-containment path.
- Existing built-site issue categories remain stable.
- Wiki-side local-link scheme behavior is unchanged but no longer represented by a dead ignored-schemes constant.

## UDH-010 - Single Stale-Exported-Asset Reducer

Priority: P2
Status: Done
Depends on: UDH-005, UDH-006
Type: Code/tests
Track: 5
Findings: F-11

### Goal

Compute stale exported assets once and reuse that result for export operations and site-check warnings.

### Developer Context

`site_export._record_asset_operations` computes referenced assets from `build_asset_index(wiki, page_contents)` and appends `stale_asset` operations. `site_export._stale_asset_warnings` builds a new asset index with `build_asset_index(wiki)`, which re-reads every wiki page. The duplicate work also makes it easy for export operations and check warnings to drift.

The consolidation should keep the source-side read in `check_site_mirror`.
The ADR open question is about code shape, not removing source validation.

### Files

- Modify: `src/llm_wiki_cli/services/site_export.py`
- Modify: `src/llm_wiki_cli/services/wiki_media.py` only if
  `build_asset_index` gains a reusable precomputed-reference parameter in this task instead of UDH-011.
- Test: `tests/test_site_export.py`

### Implementation Tasks

- [x] Add `_stale_exported_assets(referenced: set[str], out: Path) -> list[str]` in `site_export.py`.
- [x] Call it from `_record_asset_operations` using the referenced set already computed for asset copying.
- [x] Call it from `_stale_asset_warnings` using source references collected once for that check path.
- [x] Keep action/category strings stable: export operations use `stale_asset`; check warnings use category `stale_asset`.
- [x] Add a regression test proving export operations and check warnings report the same stale asset set for the same source/out directory.
- [x] Add a regression test proving the stale set includes only exported media paths that are no longer referenced and excludes current referenced assets.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py -k "stale_asset or asset" -q
```

### Acceptance Criteria

- The stale asset set is computed by one helper.
- Export operation output and site-check warning output stay semantically aligned.
- Source-side validation behavior remains present.

## UDH-011 - Single Media Collection Path For Lint And Asset Indexing

Priority: P2
Status: Done
Depends on: UDH-001 through UDH-006
Type: Code/tests
Track: 5
Findings: F-12

### Goal

Avoid parsing every page twice during lint by collecting media references once per lint run and reusing the collection for reference checks and orphan reduction.

### Developer Context

`lint_cmd._check_media_references` currently calls `wiki_media.collect_media_references` per page for broken/missing-alt/oversize checks, then calls `wiki_media.build_asset_index` with copied page content. `build_asset_index` parses the same pages again. The goal is a small API adjustment, not a broad architecture rewrite.

### Files

- Modify: `src/llm_wiki_cli/services/wiki_media.py`
- Modify: `src/llm_wiki_cli/commands/lint_cmd.py`
- Test: `tests/test_lint.py`
- Test: `tests/test_wiki_surface_index.py`
- Test: `tests/test_site_export.py`

### Implementation Tasks

- [x] Add a helper in `wiki_media.py`, for example
  `collect_media_references_by_page(wiki_dir, content_by_page)`, that returns a deterministic mapping of page-relative paths to `MediaReference` lists.
- [x] Allow `build_asset_index` to accept precollected references while keeping the existing `content_by_page` path for current callers.
- [x] Update `lint_cmd._check_media_references` to collect references once and reuse them for per-reference diagnostics and orphan/index reduction.
- [x] Remove the unnecessary defensive `dict(content_by_page)` copy from `build_asset_index` when the caller passes a mapping that is only iterated.
- [x] Keep output ordering stable by sorting page keys and asset paths exactly as today.
- [x] Add a focused test with monkeypatched collection counting or a small spy helper proving lint media collection is not called twice per page.
- [x] Re-run existing asset-map and export tests to prove the optional precollected path does not change JSON or export output.

### Focused Verification

```bash
.venv/bin/pytest tests/test_lint.py::TestLintMediaReferences -q
.venv/bin/pytest tests/test_wiki_surface_index.py -q
.venv/bin/pytest tests/test_site_export.py -k "asset or media" -q
```

### Acceptance Criteria

- Lint parses media references once per page for the media phase.
- Asset-index output remains stable except for intentional changes from earlier tasks in this backlog.
- Public callers of `build_asset_index` remain source-compatible.

## UDH-012 - Size-Aware Chunked Asset File Comparison

Priority: P2
Status: Done
Depends on: None
Type: Code/tests
Track: 5
Findings: F-13

### Goal

Make export copy skipping avoid reading both files fully when file sizes differ and avoid loading large equal-size files into memory at once.

### Developer Context

`site_export._same_file_bytes` currently does:

```python
return left.read_bytes() == right.read_bytes()
```

That is simple but inefficient for media files. The replacement should be portable, dependency-free, and keep the same fallback behavior: return `False` if either file cannot be read or statted.

### Files

- Modify: `src/llm_wiki_cli/services/site_export.py`
- Test: `tests/test_site_export.py`

### Implementation Tasks

- [x] Update `_same_file_bytes` to compare `left.stat().st_size` and `right.stat().st_size` first.
- [x] Return `False` immediately when sizes differ.
- [x] When sizes match, open both files in binary mode and compare fixed-size chunks, for example 64 KiB.
- [x] Return `False` on `OSError`, matching the current conservative behavior.
- [x] Add a test proving different-size files return `False`.
- [x] Add a test proving same-size different-content files return `False`.
- [x] Add a test proving same-content files return `True` and export reports `unchanged` for an existing identical asset.

### Focused Verification

```bash
.venv/bin/pytest tests/test_site_export.py -k "same_file_bytes or unchanged or asset" -q
```

### Acceptance Criteria

- Size mismatch avoids full file reads.
- Equal-size comparison is chunked.
- Export operation semantics remain `copy`, `would_copy`, or `unchanged` as before.

## UDH-013 - Public Docs, Sibling Wiki, And Closeout Review

Priority: P1
Status: Done
Depends on: UDH-001 through UDH-012
Type: Docs/report
Track: Cross-cutting
Findings: F-01 through F-13

### Goal

Finish the media hardening program with public documentation, sibling wiki updates, verification evidence, and a review artifact that records what changed and what remains deferred.

### Developer Context

Several tasks above introduce visible behavior: fewer false positives for parenthesized and fenced media examples, new warning categories, `srcset` support, outside-`assets/` mirroring, all-file asset inventory, symlink escape warnings, and built-site resolver consolidation. The closeout must make those changes discoverable and leave a durable implementation record.

### Files

- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `src/llm_wiki_cli/skills/usage-examples/SKILL.md`
- Modify: `src/llm_wiki_cli/skills/usage-examples/reference.md`
- Modify: `src/llm_wiki_cli/skills/doc-review/SKILL.md`
- Modify: `src/llm_wiki_cli/skills/doc-review/reference.md`
- Modify: sibling wiki pages under `/mnt/data/projects/llm-wiki/python-wiki-llm.wiki`
- Create: `reports/media_pipeline_hardening_closure_2026-07-07.md`

### Implementation Tasks

- [x] Update README media-lint and site-export sections for the final behavior of this backlog.
- [x] Update CHANGELOG with user-facing fixes and warning categories.
- [x] Update `usage-examples` skill category tables for `media_outside_assets`, `asset_unrecognized_type`, and `media_symlink_escape`.
- [x] Update `doc-review` media-backed docs guidance for the same categories.
- [x] Update sibling wiki troubleshooting/export pages to match README behavior.
- [x] Write `reports/media_pipeline_hardening_closure_2026-07-07.md` with: completed tasks, commit hashes, changed diagnostics, verification commands, and deferred items.
- [x] In this backlog file, mark completed tasks and add implementation commit hashes as each task lands.
- [x] Run the full verification gate and record exact command outcomes in the closure report.
- [x] Keep main-repo and sibling-wiki commits separate.

### Focused Verification

```bash
.venv/bin/pytest tests/test_lint.py tests/test_site_export.py tests/test_cli.py -q
.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py -q
.venv/bin/python -m compileall src tests
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
git diff --check
git -C /mnt/data/projects/llm-wiki/python-wiki-llm.wiki diff --check
.venv/bin/pytest -q --ignore=tests/test_rust_extract.py
```

### Acceptance Criteria

- README, CHANGELOG, bundled skills, and sibling wiki describe the final behavior.
- Closure report includes task mapping, verification evidence, and deferred open questions.
- Main repo and sibling wiki commits are separate.
- Full verification gate passes or any environmental blocker is documented with exact command output and a mitigation.
