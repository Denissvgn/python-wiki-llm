# wiki-semantic-enhance reference

Use this reference while executing the explicit `wiki-enrichment` packet. The
workspace wiki is canonical for the run; static-site output remains derived.

## Readiness ledger

Default path:
`.llm-wiki-docs/evidence/semantic-readiness.json`.

```json
{
  "schema_version": "llm-wiki-documentation-semantic-readiness/v1",
  "run_id": "docs-run-id",
  "stage_id": "wiki-enrichment",
  "packet_hash": "sha256:...",
  "baseline_strategy": "adopt_existing_wiki",
  "source_availability": "available",
  "source_freshness": "verified_current",
  "snapshot_hash": "sha256:...",
  "p0": {"total": 4, "completed": 2, "reused": 1, "deferred": 1},
  "p1_budget": {"declared": 10, "completed": 7, "reused": 3},
  "imported_pages": {
    "preserved": ["modules/api.md"],
    "reused": ["index.md"],
    "changed": [],
    "deferred": []
  },
  "unsupported_coverage": [],
  "generator_defects": [],
  "validation": {"lint": "pending", "ci_check": "pending"},
  "forbidden_writes": {"source": 0, "input_wiki": 0, "generated_blocks": 0},
  "ready_for_user_docs": false,
  "limitations": []
}
```

Use relative workspace paths and stable work ids. Counts must reconcile with
the item lists/result packet; never set readiness from counts alone.

## Work-item transitions

| Starting classification | Allowed terminal disposition | Evidence required |
|---|---|---|
| P0/P1 placeholder or weak prose | `completed` or `deferred` | Linked source/wiki evidence for completion; missing evidence and primary-doc exclusion for deferral |
| `candidate_reuse` | `reused`, `needs_grounding`, or `deferred` | Claim/evidence review; pre-existence is not proof |
| `needs_grounding` | `completed`, `reused`, or `deferred` | Source-backed evidence when source is available; otherwise retain the limitation |
| `needs_enhancement` | `completed` or `deferred` | Justified semantic edit and evidence link |
| `incompatible` | `deferred` | Compatibility reason and safe next action |
| Generator defect | `reported` | Generated block/path, deterministic symptom, and owning generator/check |

Keep completed and deferred history on resume. Never delete an item to make the
ledger totals pass.

## Ranking and editable surfaces

Read `wiki-bootstrap/reference.md` for the canonical P0 list, P1 centrality
source, and remainder fields. Consume the deterministic worklist order instead
of recomputing a second ranking.

| Surface | Agent may edit | Protected |
|---|---|---|
| `index.md` human introduction/custom trailing prose | Yes | Registry-owned surface tables/navigation |
| `guides/*.md` and other declared agent-owned narrative pages | Yes | Generated/exported mirrors |
| Entity/module `## Description` prose | Yes, when packet-owned and evidence-backed | Generated table rows/shape and ownership markers |
| Flow `## Behavior` | Yes | Call/data-flow diagrams and generated metadata |
| API/dependency/load-order `## Notes` | Yes | Generated inventories, graphs, diagnostics |
| `.llm-wiki-manifest.json`, `.llm-wiki-surface.json`, `.llm-wiki-knowledge.json`, generated front matter/Mermaid blocks | No | Entire artifact/block |

If ownership is ambiguous, do not edit. Report the path as a generator or
ownership defect and defer the work item.

The three native JSON artifacts are one controller-owned projection. After an
accepted semantic Markdown change, the supervisor refreshes that projection
from verified source evidence and re-anchors generated ownership. The worker
must not regenerate the artifacts or include their paths in
`changed_wiki_paths`. Strict lint/CI runs after that owning refresh, never
against the mixed pre-refresh Markdown snapshot. The refresh may expire a human
section review or stale a machine-verification receipt; retain and report the
existing reasons, and do not manufacture replacements.

## Imported enrichment decisions

- Preserve bytes at import. The semantic phase may change only the workspace
  copy after the packet authorizes the item.
- Prefer `reused` when prose is accurate, useful, and grounded. Style alone is
  not a reason to rewrite prior human/LLM work.
- List important claims and their evidence page/source. A source-backed run may
  resolve freshness; a wiki-only run cannot upgrade an imported claim to
  source-verified merely because multiple wiki pages repeat it.
- Record the before hash, after hash, item id, evidence, and rationale for every
  changed imported page. The immutable input-wiki hash must remain unchanged.
- Encode that audit trail in the optional result field below. Omit the field (or
  use an empty list) only when no imported semantic page changed. The
  supervisor rejects missing, extra, or hash-mismatched entries.

```json
{
  "imported_page_edits": [
    {
      "work_id": "stable-work-id",
      "canonical_path": "modules/api.md",
      "before_hash": "sha256:...",
      "after_hash": "sha256:...",
      "evidence": ["modules/api.md", "architecture.md"],
      "rationale": "Grounded the imported behavior claim against the recorded architecture evidence."
    }
  ]
}
```

For a run whose source baseline is not `verified_current`, primary guides must
not link to an imported semantic page as canonical evidence. Keep such material
deferred or link the guide to independently grounded, non-imported evidence.

## Exit gate

Set `ready_for_user_docs: true` only when all conditions hold:

- every P0 id is completed, reused, or explicitly deferred with primary-doc
  exclusion;
- completed plus reused P1 ids equal the declared budget (or every available P1
  item when fewer exist);
- every imported semantic page is preserved/reused/changed/deferred explicitly;
- unsupported coverage, unknowns, and generator defects remain visible;
- strict lint and `ci-check` pass;
- source, input-wiki, and generated-block write counts are zero;
- result paths and item counts reconcile with actual workspace diffs.

The supervisor, not the worker, confirms this gate. A worker may report
`complete`, but verification can keep the stage incomplete or blocked.

## Resume and failure matrix

| Condition | Response |
|---|---|
| Same source/snapshot and packet hashes | Resume open ids from the ledger; do not reprocess terminal items |
| Later verified source revision | Run the supervisor-authorized workspace sync, regenerate the worklist, and preserve prior ledger history |
| Wiki-only run | Resume from snapshot hash; preserve `unverified` limitation and source-dependent deferrals |
| Source/input/snapshot identity changed unexpectedly | Stop and request explicit refresh/re-import |
| Generated block changed | Stop; report the path and restore through deterministic regeneration outside this worker pass |
| Evidence insufficient | Defer with the missing evidence and bounded next context |
| Semantic budget exhausted | Return `partial`; preserve the remainder and exact next item |
| Helper/check unavailable | Record the requested check and limitation; do not claim the gate passed |
