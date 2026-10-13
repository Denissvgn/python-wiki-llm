# github action: action.yml

**Path:** `integrations/wiki-integrity/action.yml`
**Format:** `github_action`

Structural summary only; templates, expressions and referenced files are not evaluated. Read the source for complete configuration.

## Inputs

- `comparison-policy`
- `maintenance-candidate-sha`
- `maintenance-identity`
- `maintenance-source-archive`
- `report-schema`
- `wiki-dir`
- `src-dir`
- `impact-base`
- `impact-head`

## Runtime

- `composite`

## Steps

- `Set up Python 3.13`
- `Install the action package`
- `Bind runner-temporary wiki paths`
- `Plan the automatically selected extractor helpers`
- `Bind the exact extractor-helper cache identity`
- `Restore the exact prepared extractor-helper cache`
- `Install the locked TypeScript and JavaScript extractor toolchain`
- `Install the locked Go extractor toolchain`
- `Install the locked Rust extractor toolchain`
- `Install the locked Haskell extractor toolchain`
- `Record selected locked extractor toolchain versions`
- `Prepare the automatically selected extractor helpers`
- `Validate optional maintenance request`
- `Reserve optional maintenance evidence`
- `Check installed candidate and recorded producer`
- `Validate committed wiki (native drift diagnostics are advisory)`
- `Derive advisory repository health policy from CI`
- `Upload optional maintenance evidence`
- `Report advisory change impact`
- `Save the exact prepared extractor-helper cache`
- `Upload fixed allowlisted wiki integrity evidence`

## Action references

- `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1`
- `actions/cache/restore@55cc8345863c7cc4c66a329aec7e433d2d1c52a9`
- `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
- `actions/cache/save@55cc8345863c7cc4c66a329aec7e433d2d1c52a9`

## Notes

This composite action prepares selected helpers and checks the committed wiki, with optional maintenance preflight and impact evidence. Native drift is advisory in this action. Step and input names describe its interface; generated summaries do not prove that the runner completed these operations.
