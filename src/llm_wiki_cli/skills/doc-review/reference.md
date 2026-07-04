# doc-review reference

Supporting detail for [SKILL.md](SKILL.md).

## Input modes

- **Branch/diff workflow:** start from `git diff`, PR review comments, or patch review findings. Map each finding to changed source/wiki paths before editing.
- **Report-file workflow:** start from review JSON saved by `llm-wiki review` or another review pass. Preserve finding IDs, severity, path, line, and recommendation text.
- **Lint/sync workflow:** start from `llm-wiki lint --strict --profile` or `llm-wiki sync` output when the problem is stale or structurally invalid wiki content.

## Triage statuses

| Status | Meaning | Action |
|---|---|---|
| valid documentation defect | The finding is correct and the docs are wrong or incomplete. | Fix wiki/source docs and verify. |
| stale generated content | Generated wiki data is stale. | Run `llm-wiki sync`; do not hand-edit generated blocks. |
| source-code truth mismatch | Documentation and source disagree; source is authoritative. | Update docs, or escalate if source appears wrong. |
| duplicate finding | Another finding covers the same defect. | Link to the kept finding ID. |
| out-of-scope request | The finding asks for work outside the requested docs review. | Record and defer. |
| needs human confirmation | Product or policy intent is ambiguous. | Ask or record unresolved finding. |

## Safe edit rules

- Generated tables, diagrams, manifests, and "Do not edit by hand" blocks are protected.
- Semantic wiki sections, overview prose, `## Behavior`, and `## Notes` are editable when source evidence supports the change.
- A branch/diff workflow can include source documentation edits, but only when the reviewed truth surface is source docs rather than generated wiki output.
- Review JSON is evidence, not authority; verify against source before edits.

## Report format

```markdown
| Finding | Status | Evidence | Action | Verification |
|---|---|---|---|---|
| DOC-001 | valid documentation defect | `flows/api.md` behavior omitted new auth branch | Edited semantic prose | `llm-wiki ci-check ...` |
```

Always include an "Unresolved finding" section when anything remains open.
Mention duplicate finding IDs and false-positive rationale explicitly.
