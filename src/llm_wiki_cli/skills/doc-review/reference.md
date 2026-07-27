# doc-review reference

Supporting detail for [SKILL.md](SKILL.md).

## Input modes

- **Branch/diff workflow:** start from `git diff`, PR review comments, or patch review findings. Map each finding to changed source/wiki paths before editing.
- **Report-file workflow:** start from review JSON saved by `llm-wiki review` or another review pass. Preserve finding IDs, severity, path, line, and recommendation text.
- **Lint/sync workflow:** start from `llm-wiki lint --strict --profile` or `llm-wiki sync` output when the problem is stale or structurally invalid wiki content.
- **External documentation review:** start from the explicit review packet,
  worker result, deterministic evidence paths, semantic-readiness state, and
  normalized finding ledger. Preserve worker and reviewer packet/result hashes
  separately, even when one agent performs both roles.

## Triage statuses

| Status | Meaning | Action |
|---|---|---|
| valid documentation defect | The finding is correct and the docs are wrong or incomplete. | Fix wiki/source docs and verify. |
| stale generated content | Generated wiki data is stale. | Run `llm-wiki sync`; do not hand-edit generated blocks. |
| source-code truth mismatch | Documentation and source disagree about observed code structure or behavior, for which source is authoritative. | Update docs, or escalate if source appears wrong. Do not use this status for product intent, policy, audience, or approval. |
| duplicate finding | Another finding covers the same defect. | Link to the kept finding ID. |
| out-of-scope request | The finding asks for work outside the requested docs review. | Record and defer. |
| needs human confirmation | Product intent, policy, audience promise, approval, or another human-owned decision is ambiguous. | Ask or record an unresolved finding; trusted intake/human decisions are authoritative for these fields. |

## Managed versus external mutation contract

| Mode | Reads | Allowed writes | Refresh and validation |
|---|---|---|---|
| Managed review | User-supplied findings, branch/diff, source, wiki, and deterministic reports | Authorized semantic wiki prose and authorized source docs; never generated blocks or native artifacts | Preview generated drift with `sync --dry-run`; after the last Markdown edit, run the owning sync, then strict lint/CI |
| External `external_agent_docs` review | Packet-named evidence, worker result, readiness state, and normalized ledger | Only the exact review-result path and ledger fields the packet permits | No source, input-wiki, workspace-wiki, generated-artifact, governance-ledger, or receipt mutation; return defects/check requests to the owning stage or supervisor |

The external review worker must not use the workspace-level allowlist as write
authority. It preserves each original finding ID across handoffs. Agent review
does not author or satisfy a native human section review, and a review result
cannot self-authorize `publish_ready`.

## Native lint finding map

| Native category | Fact class | Review handling |
|---|---|---|
| `knowledge_projection`, `knowledge_schema`, `knowledge_snapshot` | Projection/schema/snapshot integrity | Treat the native model as unavailable or mixed. In managed mode preview and use the owning generator/repair path; never hand-edit generated artifacts. In external mode return the defect to the supervisor. |
| `knowledge_evidence`, `knowledge_freshness` | Structural evidence and live-comparison qualification | Preserve the reason. `nonsemantic-source-change` remains a qualified diagnostic; `source-changed` asks for inspection or refresh and is not automatically false prose; unknown/incompatible/missing states cannot support negative facts. |
| `knowledge_governance` | Durable identity, alias, lifecycle, or governance-ledger integrity | Route to the explicit governance owner/command. Never initialize governance or rewrite its ledger as review repair. |
| `knowledge_review` | Native human review of an exact semantic section | Report valid versus expired state and every expiry reason. This agent review cannot create, replace, or stand in for the human event. |
| `knowledge_verification` | Disposable machine-verification receipt/check state | Report failed, invalid, or stale receipt reasons separately. Rerun a fixed checker only under caller/supervisor authority; stored checker metadata cannot authorize execution or a replacement receipt. |

## Published user-docs finding classes

Use these classes when reviewing `site export --profile user` or `site check --profile user` output:

| Finding class | Typical signal | Action |
|---|---|---|
| broken distribution-mode link | Built-site validation reports HTTP/file mode link issues, including file-directory URLs in direct-file handoffs | Fix export mode, link target, or handoff instructions; re-run `site check --built-site-dir ... --link-mode http|file`. |
| missing human landing page | Root `index.md` is absent, still starts as a raw generated inventory, or does not use the configured site name | Regenerate/export with `--profile user --site-name <project>` or fix the human root page. |
| missing guide surface | `missing_user_guides` or no `guides/*.md` pages in the user profile | Run `onboarding-guide` before publishing user docs. |
| bootstrap placeholder in primary docs | `published_placeholder` in root or guide pages | Replace placeholder prose with source-backed narrative or defer the page from primary docs. |
| raw generated inventory used as root landing page | The root page begins with the exhaustive generated index instead of linking it as generated reference | Move the inventory to `generated-reference.md` and keep root `index.md` concise. |
| generated reference placeholder | `generated_reference_placeholder` warning in generated-reference, entities, modules, or flows | Report visibly; fix only when the page is promoted into primary human docs. |

Checker output from these classes can feed the `user-docs-author` adjustment loop when the fix is broader than one review finding. Preserve the original checker category, affected page, and evidence link so the authoring pass stays validation-backed.

## Safe edit rules

- Generated tables, diagrams, manifests, and "Do not edit by hand" blocks are protected.
- Supported semantic wiki sections, overview prose, `## Behavior`, and
  dependency/API `## Notes` are editable when the applicable authority supports
  the change. Generated infrastructure pages are bootstrap snapshots;
  arbitrary infrastructure `## Notes` are not a supported semantic surface and
  review findings belong in a separate redacted report based on current raw
  source or an authorized fresh dedicated extraction.
- A branch/diff workflow can include source documentation edits, but only when the reviewed truth surface is source docs rather than generated wiki output.
- Review JSON is evidence, not authority; verify against source before edits.
- Source settles observed code structure/behavior. Trusted intake and explicit
  human decisions settle product intent, policy, audience, and approval.
- In managed mode, preview generated drift with `sync --dry-run`; after the
  final authorized semantic edit run the owning sync before strict lint/CI.
- External review is report-only under the allowed-write row above.

## Report format

```markdown
| Finding | Status | Evidence | Action | Verification |
|---|---|---|---|---|
| DOC-001 | valid documentation defect | `flows/api.md` behavior omitted new auth branch | Edited semantic prose | `llm-wiki ci-check ...` |
```

Always include an "Unresolved finding" section when anything remains open.
Mention duplicate finding IDs and false-positive rationale explicitly.

For `external_agent_docs`, also keep severity, status, evidence hashes,
originating stage, iteration count, terminal rationale, and returned-to-stage
target. Low/medium findings close only as fixed, duplicate, false positive, or
evidence-backed deferred. A high-severity finding remains unresolved when it is
deferred or superseded and closes only after an affirmative, evidence-backed
resolution. Three repeated unresolved high-severity iterations block the run;
the reviewer cannot self-authorize `publish_ready`. The supervisor reconciles
the review result against source/input hashes, generated ownership, actual
diffs, and deterministic checks.

Original finding IDs are immutable across the review result, ledger update,
returned-to-stage handoff, and later adjustment result. A duplicate points to
the kept original ID; it does not replace either identity.

## Usage examples handoff

For findings in media-backed docs, classify `media_link_broken`, `media_missing_alt_text`, `media_oversize`, `media_orphan`, `media_outside_assets`, `asset_unrecognized_type`, `media_symlink_escape`, `missing_built_media_target`, and `user_docs_missing_examples`. Use `usage-examples` when the fix requires new or updated captures.
