# github action: action.yml

**Path:** `integrations/github-action/action.yml`
**Format:** `github_action`

Structural summary only; templates, expressions and referenced files are not evaluated. Read the source for complete configuration.

## Inputs

- `comparison-policy`
- `wiki-dir`
- `src-dir`
- `source-selection`
- `strict`
- `fail-on`
- `report-schema`
- `evidence-id`

## Outputs

- `status`
- `exit-code`

## Runtime

- `composite`

## Steps

- `Validate scalar inputs`
- `Set up Python 3.13`
- `Install the dashboard package`
- `Reserve dashboard paths`
- `Plan dashboard extractor helpers`
- `Install the locked TypeScript and JavaScript extractor toolchain`
- `Install the locked Go extractor toolchain`
- `Install the locked Rust extractor toolchain`
- `Install the locked Haskell extractor toolchain`
- `Prepare dashboard extractor helpers`
- `Build knowledge health report`
- `Publish diagnostic dashboard and apply threshold`
- `Upload fixed doctor dashboard evidence`

## Action references

- `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1`
- `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`

## Notes

This composite action plans the selected extractor helpers, prepares the locked toolchains, builds the doctor dashboard and applies the configured health threshold. The summary exposes interface and step names; validation scripts, environment settings and complete threshold behavior require the action source.
