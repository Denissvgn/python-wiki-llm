# dep-audit reference

Supporting detail for [SKILL.md](SKILL.md).

## Input contracts

Use current command outputs only:

- `llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki`
- `llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json`
- saved review JSON when a review workflow raised the dependency concern
- generated wiki pages such as `dependencies.md` and `load-order.md`

The skill consumes existing diagnostics. It does not require an unimplemented dependency-audit command.

## Triage statuses

| Status | Meaning | Typical action |
|---|---|---|
| valid dependency issue | Source and metadata disagree in a way that affects runtime or packaging. | Fix source or manifest, then verify. |
| documentation-only mismatch | Code is correct but wiki prose or notes are stale. | Update semantic wiki notes, run the owning sync/re-anchor, then rerun lint. |
| expected/generated dependency | Dynamic, generated, optional, or plugin-provided dependency is intentional. | Document intent or add a deferral note. |
| third-party/vendor noise | Diagnostic points at vendored, dependency, cache, or build output. | Exclude from action unless the user explicitly owns it. |
| needs human confirmation | Evidence is insufficient or policy-sensitive. | Record the exact question and stop before edits. |

Report-only audit output outside the wiki does not require a wiki refresh. When
the selected action changes canonical dependency/load-order Markdown, the
managed command order is final semantic edit, owning `llm-wiki sync --jobs 1
...`, strict lint, then CI. That refresh may expose expired human review or a
stale machine-verification receipt; preserve its reason and do not manufacture
a replacement.

## Source verification checklist

- Confirm the import/use site and the dependency declaration that should own it.
- Check whether the dependency is runtime, test-only, optional, generated, or plugin-provided.
- Read nearby package docs before changing manifests.
- No manifest edits without source evidence.
- Do not remove an unused-looking dependency that is loaded dynamically unless the dynamic load path is understood.

## Report format

Use stable rows so the audit can be resumed:

```markdown
| ID | Diagnostic | Status | Evidence | Action | Verification |
|---|---|---|---|---|---|
| DEP-001 | undeclared-dependency `requests` in `src/api.py` | valid dependency issue | imported in runtime path; absent from manifest | add declaration | `llm-wiki ci-check ...` |
```

Record dependency-cycle, undeclared-dependency, and unused-dependency items separately. If a warning is intentional, the action can be a wiki note rather than code.
