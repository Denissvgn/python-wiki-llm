# wiki-bootstrap reference

Supporting detail for [SKILL.md](SKILL.md).

## Centrality-ranked semantic pass

The semantic pass is intentionally budgeted. Default budget: complete all P0 items plus the top 30 P1 module/entity pages. Raise or lower that number only when the user gives a time/token budget or the bootstrap is small enough to finish safely.

### P0: mandatory pages

Edited before any rank calculation because they define the reader's first experience:

1. `index.md`: replace generic introduction text and add a short custom section linking to the remainder backlog when one exists.
2. `flows/*`: fill each `## Behavior` section, ordered by entry-point category, boundary-effect count, then page path. For very large repos, finish at least the top 10 flows and backlog the rest.
3. `api-contracts.md`: review production-operation filtering, declared wire fields, unknowns, and static/OpenAPI diagnostics; add `## Notes` only for source-backed contract caveats.
4. `dependencies.md`: fill `## Notes` with intentional cycles, dynamic imports, package-boundary caveats, and dependency-graph interpretation.
5. `load-order.md`: fill `## Notes` with startup-order caveats and cycle rationale when generated.
6. Infrastructure/runtime pages begin as bootstrap observations and ordinary
   sync regenerates them incrementally. Their `## Notes` section is the sole
   agent-owned semantic surface; generated inventories and prose remain
   protected. For assurance conclusions, require matching live freshness,
   inspect current raw source, or run a fresh dedicated extraction.

### P1: module and entity pages

Rank pages with deterministic graph data:

1. Start from `dependency_evidence.most_depended_on` in the bootstrap JSON
   summary when available — it is already sorted by descending fan-in with a
   stable path tie-break.
2. Working through MCP/API instead of the raw bootstrap summary, call `dependency_neighborhood(<source path>)` and use the returned `metrics`.
3. Score modules as `fan_in * 100 + cycle_bonus * 25 + fan_out * 5 + entrypoint_bonus * 20`, where `cycle_bonus` is 1 when the module participates in a cycle and `entrypoint_bonus` is 1 when a flow page or entry point maps to that module.
4. Rank entity pages by their containing module score first; break ties by concrete relationship evidence (callers/callees, references, bases/subclasses), then canonical path.
5. Prefer central pages with placeholders over already-useful docstring-derived pages. A high-rank page that already has accurate semantic prose can be marked complete without rewriting it.

### P2: long-tail pages

Leaf modules, tiny value objects, generated adapters, and pages with no safe semantic context go to the remainder backlog. Do not fabricate importance for low-rank pages just to remove placeholders — it is acceptable for long-tail pages to keep `_Auto-generated from ..._` text when the backlog makes the deferral explicit.

## Remainder-backlog artifact format

Default path: `<wiki-dir>/bootstrap-remainder.md`, linked from a custom trailing `## Bootstrap Remainder` section in `index.md`. Fallback path: `reports/llm_wiki_bootstrap_remainder_<YYYY-MM-DD>.md` when the target project does not allow custom wiki pages — record that fallback in `log.md`. The artifact is agent-owned Markdown; keep it stable and easy to update by hand, with no custom parser required for routine use.

```markdown
# Bootstrap Remainder Backlog

Generated: 2026-07-04
Source directory: .
Wiki directory: docs/llm_wiki
Bootstrap command: `llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki --depth full --format json`
Bootstrap summary: `logs/bootstrap.json`
Semantic budget: P0 complete plus top 30 P1 module/entity pages
Ranking policy: fan_in * 100 + cycle_bonus * 25 + fan_out * 5 + entrypoint_bonus * 20
Last validation: `llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki` exited 0

## Completed In This Pass

| Page | Surface | Rank | Why completed |
|---|---|---:|---|
| `index.md` | overview | P0 | First-reader context. |
| `flows/api-run.md` | behavior | P0 | Main HTTP entry point. |
| `modules/api.md` | description | 245 | Highest fan-in service boundary. |

## Open Remainder

| ID | Status | Priority | Page | Source | Rank | Reason deferred | Acceptance |
|---|---|---|---|---|---:|---|---|
| WB-20260704-0001 | open | P1 | `modules/repo.md` | `src/repo.py` | 180 | Description is placeholder; needs repository role summary. | Replace `## Description`, preserve generated dependency map, run the owning sync, then rerun lint. |
| WB-20260704-0002 | open | P2 | `entities/UserDTO.md` | `src/models.py` | 25 | Leaf DTO; safe to defer. | Add one-sentence responsibility if source context is clear. |

## Item Details

### WB-20260704-0001

- Page: `modules/repo.md`
- Source: `src/repo.py`
- Surface: `## Description`
- Centrality: fan_in=1, fan_out=16, cycle=false, entrypoint_related=true
- Placeholder evidence: ``_Auto-generated from `src/repo.py`._``
- Why deferred: semantic budget exhausted before repository-adapter pages.
- Suggested context: `dependency_neighborhood("src/repo.py")`, `pages_for_symbol("Repository")`, and the source file.
- Completion check: preserve generated blocks, run the owning sync/re-anchor,
  then run `lint --strict` and change status to `done` with the date.
```

Required fields for every open item:

- Stable ID: `WB-<YYYYMMDD>-<4-digit sequence>`.
- Status: `open`, `in_progress`, `done`, `skipped_no_safe_context`, or `superseded`.
- Priority: `P1` for central pages deferred after the budget, `P2` for long tail, `P3` for cosmetic improvements.
- Page and source path using the canonical wiki/index path, not guessed slugs.
- Rank or `P0`, plus the centrality evidence that produced it.
- Reason deferred and concrete acceptance criteria.
- The minimum context needed to resume without rereading the entire wiki.

When closing an item, keep the row and change `Status` to `done`; do not delete history. Add a short note in the item detail with the completion date and the validation command.

## Native artifact ownership and recovery

Keep authority explicit throughout bootstrap:

Bootstrap is not a recovery or regeneration command. It accepts only a new,
empty, or untouched initialized scaffold. Existing canonical Markdown and native
artifacts stay byte-for-byte outside its authority; use sync for a maintained
layout or migration's dry-run/archive workflow for an older or partial layout.

| Artifact/surface | Authority and owner | Permitted bootstrap handling |
|---|---|---|
| Canonical Markdown semantic sections | Human/agent-authored under the supported section policy | Edit only the semantic surfaces listed by this skill, then run the owning sync/re-anchor. |
| Generated Markdown blocks/tables plus `.llm-wiki-manifest.json`, `.llm-wiki-surface.json`, and `.llm-wiki-knowledge.json` | CLI-owned disposable projection | Never hand-edit or reconstruct one member independently. Bootstrap/sync commits the generated set together. |
| `.llm-wiki-governance.json` | Version-controlled, non-rebuildable governance authority for bundle identity, UIDs, aliases, lifecycle, and human review | Absent by default. Create only through separately confirmed `knowledge init`; mutate only through explicit governance commands; restore a missing committed ledger from version control/backup. |
| Governance data joined into `.llm-wiki-knowledge.json` | Disposable projection of the ledger | Regenerate from the intact ledger through the owning writer; it cannot replace or recover the ledger. |
| `.llm-wiki-verification.json` | Disposable receipt from explicit application-owned `knowledge verify` checkers | Never fabricate, edit, or treat as review. Report stale/failed state; an authorized caller may rerun the fixed checker. |

The current writer emits manifest v5 with the manifest, surface, and knowledge
files as one CLI-owned generated projection. Never add those paths to the
semantic edit budget or repair one by hand. In managed mode, use the owning
deterministic sync workflow to refresh the projection after semantic Markdown
changes and before final strict validation. In an `external_agent_docs` run,
return only the authorized Markdown changes; the supervisor refreshes the
generated set and re-anchors ownership. Neither the worker nor supervisor may
invent a missing governance ledger or replacement review/verification event.

The final managed refresh is conditional on an actual canonical Markdown
change; generated-only bootstrap output does not need a second no-op authoring
cycle. The refresh preserves supported semantic sections while committing the
new Markdown tree. Its validation result may expose expired human section
reviews or stale machine-verification receipts. Preserve and report their
existing reasons; never create replacement review events or receipts as part
of bootstrap.

Locator-only output remains the default when no ledger exists. Governance
adoption is optional overhead justified by a named durable-identity or
section-review consumer, not a bootstrap completeness requirement.

## Validation expectations

A successful run has:

- `bootstrap --format json` completed and the summary reviewed.
- No unexplained `skipped_files` in the summary — remaining skips are backlogged as structural defects, not hidden inside the semantic remainder.
- P0 semantic pages completed or explicitly recorded in the remainder backlog.
- Top central module/entity pages completed up to the run's stated budget.
- `bootstrap-remainder.md` exists when placeholders remain, and `index.md` links it when the default wiki artifact path is used.
- `lint --strict` exits 0.
- `ci-check` exits 0, or any non-zero result is explained as an existing warning-only dependency/coverage condition with a follow-up backlog item.
- The final diff contains generated wiki pages, semantic edits, the remainder backlog, and optional report/log artifacts only.

## Failure modes and edge cases

- **Any existing wiki content.** Stop before extraction or writes. A manifest,
  legacy page, partial generated page, custom prose, governance ledger, or
  verification receipt routes to wiki-sync or
  `llm-wiki migrate --dry-run`; explicit “re-bootstrap” wording does not change
  that rule.
- **Large monorepo.** Do not attempt full semantic coverage. Complete P0, then top central pages, then backlog the rest.
- **Unsupported sources.** Treat unsupported-language summaries as coverage notices. Include them in the validation notes and backlog if the user expects those languages to be first-class.
- **Skipped generated pages.** Page skips can hide missing documentation due to collisions or unsafe output paths. Triage before semantic polishing.
- **Source-adapter wikis.** Keep `--allow-external-src` consistent across `prepare-extractors`, `bootstrap`, `lint`, `sync`, `ci-check`, and `team check` after the initial run. Examples: `llm-wiki prepare-extractors --src-dir <repo> --allow-external-src` and `llm-wiki team check --src-dir <repo> --allow-external-src --wiki-dir docs/llm_wiki`. The `--wiki-dir` remains project-root guarded.
- **Placeholder pressure.** Removing every placeholder is not the goal. The goal is to make central pages meaningful and make deferred work explicit.
- **Custom backlog page lint.** If `bootstrap-remainder.md` is reported as an orphan, link it from `index.md`. If the target project forbids custom wiki pages, move it to `reports/` and record that fallback in `log.md`.

## Related workflows

- Every refresh after first bootstrap belongs to wiki-sync. Older or partial
  layouts first use migration preview and its archive-preserving workflow.
- An external documentation workspace uses this workflow only to materialize
  the deterministic `bootstrap-source` baseline. Its separate, resumable
  semantic phase belongs to `wiki-semantic-enhance`, which consumes the same P0
  definitions and P1 ranking source from this reference and writes readiness
  evidence inside the workspace. It never commits the source repository.
- Dependency-warning remediation belongs to the dep-audit workflow; this skill may document obvious intentional cycles in `## Notes` but should not chase every warning.
- Security attack-path reasoning belongs to the attack-surface workflow; static-site export/publishing belongs to the publish-docs workflow.
