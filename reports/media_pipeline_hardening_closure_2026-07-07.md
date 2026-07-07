# Media Pipeline Hardening Closure

Date: 2026-07-07

Backlog: `reports/media_pipeline_hardening_backlog_2026-07-07.md`

ADR: `reports/adr_media_pipeline_hardening_2026-07-07.md`

## Commits

- Main implementation: `76a2eb6` (`feat: harden media pipeline`)
- Sibling wiki docs: `6740448` (`docs: document media pipeline hardening`)
- Closure artifact: committed after the implementation and wiki commits so it can record their hashes.

## Completed Tasks

- `UDH-001`: Added shared Markdown link/image target scanning for balanced parenthesized targets and routed media collection, lint page links, site mirror link validation, and surface-index links through it where applicable.
- `UDH-002`: Media collection now strips fenced code blocks while preserving line count.
- `UDH-003`: Same-page reference-style images are collected, normalized, validated, indexed, and exported.
- `UDH-004`: Wiki raw HTML and built HTML now validate local `srcset` candidates; the parser preserves `data:` candidates as ignored external values instead of splitting payload commas.
- `UDH-005`: Export mirrors every referenced media file that resolves inside the wiki root, including page-local media outside `assets/`; lint emits warning-level `media_outside_assets`.
- `UDH-006`: `assets/` inventory covers all non-hidden files, adds the surface-index `other` bucket, preserves `media_orphan` for media files, and warns on unrecognized non-hidden asset files.
- `UDH-007`: Symlinked media paths that look wiki-local but resolve outside the wiki root produce warning-level `media_symlink_escape` and remain unmirrored.
- `UDH-008`: Surface-index titled-link behavior is pinned; safe parenthesized page ids now participate in registered surfaces.
- `UDH-009`: Built-site href/media checks share parse, decode, scheme, containment, and missing-target resolution; wiki-side local link extraction now explicitly ignores any scheme.
- `UDH-010`: Stale exported media detection uses one reducer for export operations and site-check warnings.
- `UDH-011`: Lint collects media references once per page and reuses that map for per-reference diagnostics and asset-index reduction.
- `UDH-012`: Asset byte comparison checks size first and compares equal-size files in chunks.
- `UDH-013`: README, CHANGELOG, bundled skills, sibling wiki pages, backlog status, final review, and this closure artifact were updated.

## Changed Diagnostics

- Existing hard issue preserved: `media_link_broken`.
- Existing warning diagnostics preserved: `media_missing_alt_text`, `media_oversize`, `media_orphan`, `missing_built_media_target`, `user_docs_missing_examples`, and `stale_asset`.
- New warning diagnostics: `media_outside_assets`, `asset_unrecognized_type`, and `media_symlink_escape`.
- Surface-index asset counts now include additive `counts.assets.by_media_type.other`.

## Verification Evidence

- `.venv/bin/pytest tests/test_lint.py::TestLintMediaLinks tests/test_site_export.py tests/test_wiki_surface_index.py tests/test_cli.py -q` -> `116 passed`
- `.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py -q` -> `71 passed`
- `.venv/bin/pytest tests/test_site_export.py::test_check_built_site_html_validates_srcset_candidates -q` -> `1 passed` after the final review fix
- `.venv/bin/python -m compileall src tests` -> exit `0`
- `.venv/bin/ruff check src tests` -> `All checks passed!`
- `.venv/bin/ruff format --check src tests` -> `137 files already formatted`
- `.venv/bin/pytest -q --ignore=tests/test_rust_extract.py` -> `1605 passed, 34 skipped`
- `git diff --check` -> exit `0`
- `git -C /mnt/data/projects/llm-wiki/python-wiki-llm.wiki diff --check` -> exit `0`

## Final Review

The final read-only review found two blockers:

- Built-site `data:` `srcset` payloads were split on the comma and could produce a false `missing_built_media_target` for the payload token. Fixed by adding a built-site regression and replacing the naive splitter with a URL-token scanner.
- The closure report was missing after the backlog had been marked done. Fixed by writing this report and intentionally force-adding it because `reports/` is ignored.

No additional blocking issue was reported in the sibling wiki diff. A residual non-blocking containment question remains for direct relative media paths that resolve outside the wiki root without symlinks; that behavior was outside `UDH-007`, which only made symlink escapes warning-visible.

## Deferred Scope

- General `broken_links` fence exclusion remains out of scope.
- Inline-code-span media exclusion remains out of scope.
- Cross-page reference-definition resolution remains out of scope.
- Full support for symlinked asset stores remains deferred; vendor or mount media inside the wiki root.
- Automatic deletion of stale exported assets remains out of scope.
