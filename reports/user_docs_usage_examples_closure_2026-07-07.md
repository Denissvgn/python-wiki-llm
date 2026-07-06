# User Docs Usage Examples Closure

Date: 2026-07-07
Status: Completed
Backlog: `reports/user_docs_usage_examples_backlog_2026-07-07.md`
ADR: `reports/adr_user_docs_usage_examples_2026-07-07.md`
Final review: `reports/user_docs_usage_examples_final_review_2026-07-07.md`

## Implemented Scope

- UDE-001: Added media parsing and lint categories for local image/video
  references, missing alt text, oversize warnings, and orphan assets.
- UDE-002: Added the semantic `assets/` surface contract and surface-index
  asset counts plus page-to-asset references.
- UDE-003: Added static-site asset mirroring, dry-run reporting, unchanged
  copy detection, hub aggregation, and stale exported-asset warnings.
- UDE-004: Added built HTML media validation for `<img>`, `<video>`, and
  `<source>` targets in both `http` and `file` link modes.
- UDE-005: Added a warning-level user-profile gate for primary docs with no
  usage-example media.
- UDE-006: Added the bundled `usage-examples` skill and package-data coverage.
- UDE-007: Updated generated schema guidance, README autonomous-agent
  instructions, and adjacent skill cross-references.
- UDE-008: Completed self dogfood in a disposable `/tmp` runner.
- UDE-009: Completed Assistant dogfood using a fresh `/tmp` runner and
  read-only `/mnt/data/projects/Assistant`.
- UDE-010: Updated README, CHANGELOG, sibling wiki pages, backlog evidence,
  this closure, and the final review report.

## Dogfood Summary

Self runner: `/tmp/llm-wiki-usage-examples-self-2026-07-07`

| Check | Result |
| --- | --- |
| `sync` | Passed |
| `lint --strict` | Passed |
| `ci-check` | Passed with 0 issues |
| User export/check | 5 export pages, 4 check pages, 0 issues, 0 warnings, 1 asset |
| Built-site checks | Passed in `http` and `file` modes |

The self run confirmed the 2 MB media warning default, idempotent unchanged
asset copies, and warning-level stale exported-asset behavior. Terminal
recording was deferred because `asciinema` and `agg` were unavailable.

Assistant runner:
`/tmp/llm-wiki-assistant-usage-examples-bootstrap-2026-07-07`

| Check | Result |
| --- | --- |
| Assistant status before/after | Clean |
| User hosted export/check | 996 export pages, 995 check pages, 0 issues, 497 warnings, 1 asset |
| Hosted built check | Passed in `http` mode |
| User file export/check | 996 export pages, 995 check pages, 0 issues, 497 warnings, 1 asset |
| File built check | Passed in `file` mode |

The Assistant counts match the 2026-07-05 ADU-007 baseline except for the new
intentional media asset. The 497 warnings are the existing non-failing
`generated_reference_placeholder` warnings.

## Verification

Passed:

```bash
.venv/bin/pytest tests/test_lint.py tests/test_wiki_surface.py tests/test_wiki_surface_index.py tests/test_sync.py -q -k "media or asset or surface or lint"
# 87 passed, 83 deselected

.venv/bin/pytest tests/test_site_export.py tests/test_cli.py -q
# 88 passed

.venv/bin/pytest tests/test_skills.py tests/test_package_metadata.py tests/test_schema.py tests/test_init.py -q
# 102 passed

.venv/bin/pytest -q --ignore=tests/test_rust_extract.py
# 1584 passed, 34 skipped

.venv/bin/python -m compileall src tests

.venv/bin/ruff check src tests
# All checks passed

.venv/bin/ruff format --check src tests
# 137 files already formatted

git diff --check

git -C /mnt/data/projects/llm-wiki/python-wiki-llm.wiki diff --check
```

Ignored report handling was verified with:

```bash
git check-ignore -v reports/usage_examples_self_dogfood_2026-07-07.md \
  reports/assistant_usage_examples_confirmation_2026-07-07.md \
  reports/user_docs_usage_examples_backlog_2026-07-07.md \
  reports/user_docs_usage_examples_closure_2026-07-07.md \
  reports/user_docs_usage_examples_final_review_2026-07-07.md
# .gitignore:15:reports/ for each path
```

## Residual Limitations

- Capture tooling remains environment-dependent. Missing `asciinema`/`agg` is
  recorded as a deferred capture row, not hidden.
- Stale exported assets are warning-level by design; this work does not add a
  destructive clean mode.
- Markdown media parsing intentionally stays close to the existing lightweight
  Markdown link parser. Complex Markdown edge cases are still best handled by
  authoring explicit, simple local asset links.
- This branch does not contain a committed `docs/llm_wiki` tree for this repo,
  so self dogfood used a disposable wiki and public docs landed in the sibling
  GitHub wiki checkout.

## Review

The final review found no blocking issues. The implementation keeps source
targets read-only during dogfood, treats generated output as derived, validates
media before and after static-site builds, and preserves existing reference
profile behavior.
