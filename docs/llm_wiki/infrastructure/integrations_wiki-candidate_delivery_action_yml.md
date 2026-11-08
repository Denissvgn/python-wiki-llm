# github action: action.yml

**Path:** `integrations/wiki-candidate/delivery/action.yml`
**Format:** `github_action`

Structural summary only; templates, expressions and referenced files are not evaluated. Read the source for complete configuration.

## Inputs

- `operation`
- `wiki-token`
- `source-token`
- `target-repository`
- `working-directory`
- `config`
- `approval-branch`
- `artifact-id`
- `receipt-id`
- `candidate-review`
- `reviews`
- `baseline`
- `previous-receipt`
- `target-revision`
- `restore-revision`
- `rollback-review`

## Outputs

- `result-path`
- `readback-verified`

## Runtime

- `composite`

## Steps

- `Check publisher inputs`
- `Set up the publisher Python`
- `Install and verify the pinned publisher`
- `Download the successful preparation artifact from this run`
- `Check policy, Git revisions and remote result`
- `Retain delivery evidence`

## Action references

- `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1`
- `actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c`
- `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`

## Notes

_Add reviewed operational context here; generated sections are replaced from source observations._
