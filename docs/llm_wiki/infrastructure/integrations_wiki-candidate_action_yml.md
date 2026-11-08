# github action: action.yml

**Path:** `integrations/wiki-candidate/action.yml`
**Format:** `github_action`

Structural summary only; templates, expressions and referenced files are not evaluated. Read the source for complete configuration.

## Inputs

- `working-directory`
- `config`
- `src-dir`
- `source-revision`
- `target-dir`
- `target-revision`
- `accepted-state-revision`
- `baseline`
- `reviews`
- `previous-receipt`
- `candidate-review`
- `fail-on`
- `evidence-id`

## Outputs

- `candidate-dir`
- `receipt-path`
- `report-path`
- `diff-path`
- `provider-receipt`
- `changed`
- `ready`

## Runtime

- `composite`

## Steps

- `Set up provider Python`
- `Install and verify the pinned action provider`
- `Prepare the selected language toolchains`
- `Export and independently check the public candidate`
- `Retain the candidate and review evidence`

## Action references

- `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1`
- `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`

## Notes

_Add reviewed operational context here; generated sections are replaced from source observations._
