# github action: action.yml

**Path:** `integrations/wiki-impact/action.yml`
**Format:** `github_action`

Structural summary only; templates, expressions and referenced files are not evaluated. Read the source for complete configuration.

## Inputs

- `config`
- `baseline`
- `reviews`
- `target-dir`
- `working-directory`
- `fail-on`
- `evidence-id`

## Outputs

- `report-path`
- `summary-path`
- `provider-receipt`
- `complete`
- `review_required`
- `changed`
- `ready`

## Runtime

- `composite`

## Steps

- `Set up the provider Python`
- `Install and verify the action provider in an isolated environment`
- `Evaluate local publication impact`
- `Retain publication impact evidence`
- `Validate the impact report and enforce its policy`

## Action references

- `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1`
- `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`

## Notes

_Add reviewed operational context here; generated sections are replaced from source observations._
