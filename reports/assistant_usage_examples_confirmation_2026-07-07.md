# Assistant Usage Examples Confirmation

Date: 2026-07-07
Status: Passed
Runner: `/tmp/llm-wiki-assistant-usage-examples-bootstrap-2026-07-07`
Read-only target: `/mnt/data/projects/Assistant`

## Summary

The Assistant dogfood followed the ADU-007 pattern: fresh `/tmp` runner,
read-only Assistant source, runner-local guide media, user-profile export, and
built-site validation in both link modes. The real Assistant checkout was clean
before and after the run.

## Commands

```bash
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

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/mkdocs build --strict -f site-user/mkdocs.yml

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-user \
  --built-site-dir _site \
  --link-mode http \
  --profile user \
  --site-name Assistant \
  --output-format json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site export \
  --wiki-dir wiki-external \
  --out-dir site-user-file \
  --format mkdocs \
  --profile user \
  --site-name Assistant \
  --file-friendly \
  --front-matter \
  --output-format json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-user-file \
  --profile user \
  --site-name Assistant \
  --output-format json

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/mkdocs build --strict -f site-user-file/mkdocs.yml

/mnt/data/projects/llm-wiki/python-wiki-llm/.venv/bin/python -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-user-file \
  --built-site-dir _site \
  --link-mode file \
  --profile user \
  --site-name Assistant \
  --output-format json
```

## Runner-Local Usage Asset

- Guide: `wiki-external/guides/assistant-usage-examples.md`
- Asset: `wiki-external/assets/guides/assistant-usage-examples/live-controls.svg`
- Hosted export target:
  `site-user/assets/guides/assistant-usage-examples/live-controls.svg`
- File-friendly export target:
  `site-user-file/assets/guides/assistant-usage-examples/live-controls.svg`

The asset uses alt text, a caption, and a deferred-capture table. No Assistant
source or committed docs were edited.

## Results

| Step | Pages | Issues | Warnings | Assets | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| User hosted export | 996 | 0 | 0 | 1 | Asset copied |
| User hosted source check | 995 | 0 | 497 | 0 | Warnings are `generated_reference_placeholder` |
| User hosted built check | 995 | 0 | 497 | 0 | `link_mode=http`, media target validated |
| User file export | 996 | 0 | 0 | 1 | Asset copied |
| User file source check | 995 | 0 | 497 | 0 | Warnings are `generated_reference_placeholder` |
| User file built check | 995 | 0 | 497 | 0 | `link_mode=file`, media target validated |

## Baseline Comparison

Compared with `reports/assistant_docsite_user_docs_confirmation_2026-07-05.md`:

- Page counts match the ADU-007 baseline: 996 user export pages and 995 check
  pages.
- Issue counts match the baseline: 0 issues in source and built checks.
- Warning counts match the baseline: 497 non-failing
  `generated_reference_placeholder` warnings.
- New delta: each user export copies one runner-local media asset.

An initial attempt to use the committed Assistant wiki copy found stale
generated-reference links and an oversized root page. The official confirmation
therefore used a fresh bootstrap, matching the ADU-007 pattern.

## Capture Blockers

| Capture | Status | Reason |
| --- | --- | --- |
| Runtime Assistant UI screenshot | Deferred | The run validates wiki media in isolation and does not start Assistant services. |
| Terminal recording | Deferred | `asciinema` and `agg` are unavailable in this environment. |

## Target Status

`git -C /mnt/data/projects/Assistant status --porcelain` produced no output
after the run.
