# Usage Examples Self Dogfood

Date: 2026-07-07
Status: Passed with documented capture deferrals
Runner: `/tmp/llm-wiki-usage-examples-self-2026-07-07`

## Scope

This run exercised the new `usage-examples` workflow against a disposable wiki
for this repository's CLI flows. The branch does not contain an in-repo
`docs/llm_wiki` tree, so the run used a minimal runner-local wiki with a real
`src/sample.py`, guide page, mirrored asset, static export, and built-site
fixture. Public docs are covered in the sibling wiki closeout.

## Skill Contract

The shipped `usage-examples` skill was followed for the media path, alt text,
captioning, command-output example, validation loop, and honest deferral rows.

Deviations:

- Real terminal recording was deferred because both `asciinema` and `agg` were
  unavailable in this environment.
- The wiki lived under `/tmp` because this branch has no committed
  `docs/llm_wiki` tree.

## Runner Content

- Guide: `docs/llm_wiki/guides/site-export.md`
- Asset: `docs/llm_wiki/assets/guides/site-export/skills-list.svg`
- Built media target: `_site/assets/guides/site-export/skills-list.svg`
- Example command output: `skills list --format json` included the new
  `usage-examples` bundled skill and its `SKILL.md`/`reference.md` files.

## Validation

| Check | Result |
| --- | --- |
| `sync --src-dir src --wiki-dir docs/llm_wiki --jobs auto` | Passed |
| `lint --strict --src-dir src --wiki-dir docs/llm_wiki` | Passed after removing an invented stale flow page |
| `ci-check --src-dir src --wiki-dir docs/llm_wiki --format text` | Passed with 0 issues |
| `site export --profile user` | 5 pages, 0 issues, 0 warnings, 1 asset |
| `site check --profile user` | 4 pages, 0 issues, 0 warnings |
| `site check --built-site-dir _site --link-mode http` | 4 pages, 0 issues, 0 warnings |
| `site check --built-site-dir _site --link-mode file` | 4 pages, 0 issues, 0 warnings |

The initial strict lint failure was a useful skill-contract check: the guide
referenced a flow page that did not correspond to a real detected workflow.
The final guide references a real module page instead.

## Default Tuning

- Mirrored paths were ergonomic enough for authored examples:
  `assets/guides/site-export/skills-list.svg` maps directly to the guide stem.
- The 2 MB default `media_oversize` threshold fits this run. The SVG asset is
  small, and no lower default was justified by the dogfood.
- Warning noise was zero in the final self-run.
- Consecutive exports are idempotent. The second export reported the asset
  operation as `unchanged`.
- Stale exported assets remain a warning-level check by design. This run did
  not justify adding an opt-in clean mode.

## Deferred Rows

| Capture | Status | Reason |
| --- | --- | --- |
| Terminal recording | Deferred | `asciinema` and `agg` were unavailable. |
| Real in-repo docs update | Deferred to UDE-010 | This branch has no `docs/llm_wiki`; public docs are maintained in the sibling wiki. |

## Follow-ups

No code follow-ups were filed from this dogfood run. The only runtime defect
found was the omitted CLI default for `--media-size-warn-bytes`; it was fixed
in-place with a regression test before this report was written.
