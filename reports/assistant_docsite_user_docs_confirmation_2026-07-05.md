# Assistant Docsite User Documentation Confirmation

Date: 2026-07-05
Status: Passed
Runner: `/tmp/llm-wiki-assistant-user-docs-fkd7ZSQO`
Read-only target: `/mnt/data/projects/Assistant`

## Summary

The fresh Assistant dogfood run confirmed the new static-site contracts:

- Reference-profile export/check remained structurally valid.
- User-profile export produced a human landing page and preserved generated
  reference material under `generated-reference.md`.
- Hosted MkDocs output passed built-link validation in `http` mode.
- File-friendly MkDocs output passed built-link validation in `file` mode.
- `/mnt/data/projects/Assistant` remained unmodified.

The only non-failing findings were `generated_reference_placeholder` warnings
inside generated reference pages. Primary human docs had zero quality issues.

## Commands

```bash
RUNNER=/tmp/llm-wiki-assistant-user-docs-fkd7ZSQO
cd "$RUNNER"

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli bootstrap \
  --src-dir /mnt/data/projects/Assistant \
  --wiki-dir wiki-external \
  --source-adapter \
  --allow-external-src \
  --format json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site export \
  --wiki-dir wiki-external \
  --out-dir site-reference \
  --format mkdocs \
  --profile reference \
  --front-matter \
  --output-format json > reference-export.json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-reference \
  --profile reference \
  --output-format json > reference-check.json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site export \
  --wiki-dir wiki-external \
  --out-dir site-user \
  --format mkdocs \
  --profile user \
  --site-name Assistant \
  --front-matter \
  --output-format json > user-http-export.json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-user \
  --profile user \
  --site-name Assistant \
  --output-format json > user-http-check.json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/mkdocs build --strict -f site-user/mkdocs.yml

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-user \
  --built-site-dir _site \
  --link-mode http \
  --profile user \
  --site-name Assistant \
  --output-format json > user-http-built-check.json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site export \
  --wiki-dir wiki-external \
  --out-dir site-user-file \
  --format mkdocs \
  --profile user \
  --site-name Assistant \
  --file-friendly \
  --front-matter \
  --output-format json > user-file-export.json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-user-file \
  --profile user \
  --site-name Assistant \
  --output-format json > user-file-check.json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/mkdocs build --strict -f site-user-file/mkdocs.yml

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-user-file \
  --built-site-dir _site \
  --link-mode file \
  --profile user \
  --site-name Assistant \
  --output-format json > user-file-built-check.json

git -C /mnt/data/projects/Assistant status --short
```

Bootstrap produced no guide pages, so the run followed the updated
`onboarding-guide` contract by adding a runner-local guide page under
`wiki-external/guides/assistant-operator-onboarding.md`. No Assistant files were
edited.

## Results

| Step | Pages | Issues | Warnings | Notes |
| --- | ---: | ---: | ---: | --- |
| Reference export | 995 | 0 | 0 | `profile=reference`, `distribution_mode=http` |
| Reference check | 995 | 0 | 0 | Structural mirror compatibility preserved |
| User hosted export | 996 | 0 | 0 | `profile=user`, `site_name=Assistant` |
| User hosted source check | 995 | 0 | 497 | Warnings are `generated_reference_placeholder` |
| User hosted built check | 995 | 0 | 497 | `link_mode=http`, zero built-link issues |
| User file export | 996 | 0 | 0 | `distribution_mode=file` |
| User file source check | 995 | 0 | 497 | Warnings are `generated_reference_placeholder` |
| User file built check | 995 | 0 | 497 | `link_mode=file`, zero built-link issues |

## Human Root Checks

- `site-user/index.md` and `site-user-file/index.md` both start with
  `# Assistant`.
- Both human root pages are 71 lines, below the 250-line gate.
- Both root pages link to
  `guides/assistant-operator-onboarding.md`.
- Both root pages link to `generated-reference.md` under a secondary
  `## Generated Reference` section.
- Neither root page starts with `# LLM Wiki Index`.
- `site-user/guides/` and `site-user-file/guides/` each contain one guide page.
- `rg "Replace this placeholder|# LLM Wiki Index" site-user/index.md site-user/guides site-user-file/index.md site-user-file/guides`
  produced no matches.

## Notes

The shell emitted environment startup warnings about stream file descriptors and
an `.npmrc`/nvm conflict, but the `llm-wiki` and `mkdocs` commands above exited
with the statuses recorded in the JSON reports.
