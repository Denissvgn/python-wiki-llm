# Assistant Docsite User Documentation Closure

Date: 2026-07-05
Status: Completed
Backlog: `reports/assistant_docsite_user_docs_improvement_backlog_2026-07-05.md`
Confirmation: `reports/assistant_docsite_user_docs_confirmation_2026-07-05.md`

## Implemented Scope

- ADU-001: Added built HTML link validation with explicit `http` and `file`
  modes, stable issue categories, JSON/text report integration, and CLI flags
  `site check --built-site-dir` / `--link-mode`.
- ADU-002: Added MkDocs `--file-friendly` export mode, distribution-mode
  reporting, hub support, and a generated MkDocs override for direct-file-safe
  home links.
- ADU-003: Added opt-in `--profile user --site-name ...`, a concise human root
  page, and `generated-reference.md` for the raw generated inventory.
- ADU-004: Added user-profile quality gates for default names, missing guides,
  oversized indexes, excessive links, and primary-doc placeholders.
- ADU-005: Added user-profile navigation grouping and noise separation for
  guide, workflow, operations, generated reference, and test/fixture surfaces.
- ADU-006: Updated bundled `wiki-bootstrap`, `onboarding-guide`, `doc-review`,
  and `publish-docs` skill contracts.
- ADU-007: Completed fresh Assistant dogfood confirmation in `/tmp`.
- ADU-008: Updated README, schema guidance, sibling wiki docs, backlog status,
  and this closure record.

## Assistant Dogfood

Fresh runner: `/tmp/llm-wiki-assistant-user-docs-fkd7ZSQO`

| Check | Result |
| --- | --- |
| Assistant repo status | Clean |
| Reference export/check | 995 pages, 0 issues, 0 warnings |
| User hosted export/check | 996 export pages, 0 issues |
| Hosted built-link check | 0 issues in `http` mode |
| File-friendly export/check | 996 export pages, 0 issues |
| File built-link check | 0 issues in `file` mode |
| Human root page | `# Assistant`, 71 lines, guide link, generated reference secondary |

The remaining 497 warnings are non-failing
`generated_reference_placeholder` warnings in generated reference pages, not
primary human docs.

## Verification

Passed:

```bash
.venv/bin/pytest tests/test_site_export.py tests/test_cli.py tests/test_skills.py tests/test_package_metadata.py -q
# 142 passed

.venv/bin/python -m compileall src tests

.venv/bin/ruff check src tests
# All checks passed

.venv/bin/ruff format --check src tests
# 136 files already formatted

.venv/bin/python -m llm_wiki_cli.cli prepare-extractors --language rust
# rust: already_current

.venv/bin/pytest -q --ignore=tests/test_rust_extract.py
# 1558 passed, 34 skipped

LLM_WIKI_CACHE_DIR=/mnt/data/projects/llm-wiki/python-wiki-llm/.git \
  .venv/bin/pytest tests/test_rust_extract.py -q
# 42 passed

git diff --check
git -C /mnt/data/projects/llm-wiki/python-wiki-llm.wiki diff --check
```

The final broad suite is split intentionally: Rust extractor tests need the
prepared helper cache, while cache-resolution tests must run with the default
environment to verify local `.git` cache behavior.

## Project Review

No blocking findings were found in the final review. The implementation keeps
reference-profile defaults compatible, scopes user-facing behavior behind
explicit flags, validates output paths for built HTML links, and preserves the
Assistant target as read-only dogfood input.

Residual limitations:

- User-profile prose is still a deterministic scaffold. High-quality product
  docs still depend on authored guide pages.
- Generated reference pages can still contain low-confidence placeholder text;
  this is now visible as warnings instead of hidden behind a passing check.
- Docusaurus remains a content/sidebars export surface; this work did not turn
  it into a full Docusaurus application scaffold.
