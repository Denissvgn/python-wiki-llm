# Maintenance and validation

## Contents

- [Establish the starting state](#establish-the-starting-state)
- [Optional ordinary review tracking](#optional-ordinary-review-tracking)
- [Complete owning loop](#complete-owning-loop)
- [Mutation and identity boundaries](#mutation-and-identity-boundaries)
- [Failure and recovery](#failure-and-recovery)

Read this topic after a relevant code change, source revision update, rebase,
or suspected wiki drift. It owns the minimum complete maintenance loop and its
failure ordering. It does not authorize source edits, governance, Git actions,
checker execution, plugins, network access, or a broader source selection than
the repository already configured.

Keep source targets read-only unless the user explicitly asks for source edits.
Follow the user's request and applicable repository instructions before any
wiki mutation. Use the configured wiki directory in place of
`docs/llm_wiki`, and carry one source root and source-selection profile through
the whole run.

## Establish the starting state

Before the first write, confirm the configured wiki path, source root, source
selection, and repository policy. Follow
[Repository handoff](repository-handoff.md) for the fail-closed Git check; it
classifies delivery but never grants write or commit authority.

Classify the wiki rather than guessing a repair:

| Starting state | Maintenance route |
| --- | --- |
| Managed wiki with a valid manifest | Continue with the owning sync below. |
| Ordinary-maintenance adoption marker present, but its owner/state/projections are missing or corrupt | Stop before sync, bootstrap or seeding. Restore a complete matching authority snapshot through `llm-wiki maintenance recover --wiki-dir docs/llm_wiki --recovery-dir <complete-snapshot> --expected-adoption-id <actual-id>`. Preserve the immutable marker and history; never reconstruct them from current pages. |
| Established canonical wiki with `index.md` but no manifest and no maintenance-adoption marker | Let sync **seed a baseline manifest** from the current source state without modifying pages. Inspect that result, then continue with an ordinary owning sync when source changes must be applied. |
| Manifest present but stored source hashes are invalid | Allow sync's bounded repair. If sync repairs only the manifest (its stored hashes were invalid, and no pages were modified), run the same sync command again before linting. |
| Absent, empty, or exact untouched initialization scaffold | Use the installed bootstrap route; incremental maintenance cannot invent its initial semantic baseline. |
| Other partial manifestless layout | Preview the supported migration route and resolve its diagnostics before sync. Do not overwrite it as though it were an empty wiki. |
| Governed snapshot with a missing ledger | Stop before mutation and restore the exact ledger from version control or its authorized backup. Never run `knowledge init` as recovery. |

If generated instructions name `--source-selection <profile>`, append that
exact argument to every source-reading command: sync, extract, lint, ci-check,
team check, context, migration, and automatic source-based helper preparation.
Explicit language-specific preparation uses `--language` and must omit
`--source-selection`; that combination is rejected. Preserve the original source
root and helper cache, then retry the original read with its original selection
and other options. Omit selection on source-reading commands only when the
project has no configured profile. Never replace it with discovery or a
broader scan during the same maintenance run.

For a trusted source root outside the working directory, pass the same external
`--src-dir` with `--allow-external-src` to `sync`, `lint`, and `ci-check`.
Apply the same pair to `team check` when that policy is configured. The wiki
directory remains inside the current project write boundary.

## Optional ordinary review tracking

Ordinary durable review is explicit adoption, independent of storage migration
and human governance. Start with a coherent generated wiki and retain an empty
recovery directory outside source/wiki:

```bash
llm-wiki maintenance adopt --src-dir src --wiki-dir wiki --recovery-dir maintenance-recovery
llm-wiki maintenance status --src-dir src --wiki-dir wiki
llm-wiki queue --src-dir src --wiki-dir wiki
```

Use the actual configured roots and source selection. Adoption starts tracked
prose as unreviewed. Sync preserves pending records across refresh and restart;
read-only status, context and queues do not acknowledge them. The queue remains
advisory. Read its JSON `qualification.ordinary_review_custody` availability,
`durable_owner_available` and `live_evaluation_performed` fields. Partial,
unadopted or unavailable custody remains a gap; even a ready status or an empty
queue establishes neither source/prose correctness nor ordinary-review completion.
Inspect exact source and semantic prose before using the status/acknowledgment
route below. Python executable syntax changes are scoped observations, separate
from source-byte and structural freshness; unchanged syntax proves neither
unchanged dependencies nor runtime behavior. Unsupported evidence stays
unavailable. Unadopted wikis retain their existing format and review limits.

Review an exact record's source and semantic section, then run the final owning
sync after any prose edit. Capture its current basis before acknowledgment:

```bash
llm-wiki maintenance status --src-dir src --wiki-dir wiki --record-id RECORD_UUID --format json
```

Save the returned JSON to `review.json` outside source/wiki. Substitute the
actual record ID. If `expected_basis` is null or status requires sync, resolve
the reported gap and recapture; do not acknowledge. Save that exact record's
`expected_basis` object as `basis.json`, also outside source/wiki, then use the
returned `state_hash`:

```bash
llm-wiki maintenance acknowledge --src-dir src --wiki-dir wiki --record-id RECORD_UUID --expected-state-hash STATE_HASH --basis-file basis.json --actor-kind agent --actor-id documentation-agent
```

Changed source, prose or state rejects a stale basis. Later relevant edits
reopen review, and an acknowledgment of one section does not cover its siblings.
Deleted or ambiguously moved targets retain pending identity rather than guessing
a new owner. Snapshot status reports historical review without live currentness.

An explicit `agent` identity records operational review of that exact basis. It
does not create human approval, satisfy governance policy or reactivate an
expired human review. Keep stricter existing review requirements separate.
Maintain the immutable adoption marker, owner, projections and recovery bundle
together; the recovery route below preserves history instead of reinitializing
it from current prose.

## Complete owning loop

**Never skip the update** — a stale wiki defeats the purpose of the system.
**After every code change in this session** that adds, removes, or modifies a
class, function, module, or cross-module flow, run the full sync-then-lint
workflow. Use the same loop for a relevant contract, dependency, entry-point,
infrastructure-observation, or source-revision change.

Complete this loop after a coherent edit batch, before relying on its changed
knowledge and before delivery; it is not a request to synchronize after each
keystroke. Source-only evidence does not exempt an existing affected wiki. If no
wiki is within the task's scope, preserve the reason and maintenance status in
the permitted handoff; creating a wiki is a separate explicit choice.

1. Run the deterministic owning pass, serialized for interactive or unknown
   capacity:

   ```bash
   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
   ```

   The pass owns generated pages, tables, diagrams, links, identifiers,
   manifests, the surface index, and the knowledge projection. Do not replace
   it with hand edits. If a prepared extractor is missing, follow
   [Extractors and dependencies](extractors-dependencies.md), then repeat the
   failed command.

   A successful unchanged sync may reuse its validated generation inputs and
   report unchanged artifact actions. The owning command still performs its
   validation. Use `--rebuild-knowledge` when an explicit full-builder comparison
   is needed; `--no-cache` only disables source caching. Keep the same prior
   wiki history when comparing retained pages with the full builder.

   Use `--progress always --progress-format json` for machine-readable progress
   events on stderr. Result JSON stays on stdout. For console-only CI, use
   `ci-check --no-report --format json --report-schema v2`; v2 separates check
   outcomes from required report-write failures. Select an explicit writable
   `--cache-dir` when repository metadata is read-only.

2. Inspect the sync plan and every affected canonical page. Treat its reported
   `CREATE`, `UPDATE`, `METADATA`, `SKIP`, `DEPRECATE`, `RENAME`, `MOVE`, and
   `REMOVE` rows as the change inventory. A source-removal or deprecation row is
   a generated surface observation, not an authored lifecycle decision.

3. Classify each affected page as generated-only or semantically affected.
   Leave generated structures to the CLI. Make surgical changes only in the
   semantic sections listed by
   [Canonical surfaces and naming](surfaces-naming.md). Update descriptions,
   responsibilities, collaborators, important behavior, usage constraints, and
   one concise append-only log summary when the current source supports them.
   Do not improve unrelated pages.

4. Inspect affected `dependencies.md` and `load-order.md` pages when present,
   including intentional cycles, dynamic imports, side effects, and dependency
   rationale. Inspect `api-contracts.md` operations, reconciliation
   diagnostics, and static-analysis unknowns; never treat an unknown contract
   field as a confirmed value. Inspect flow boundary effects and analysis gaps
   before aligning `## Behavior`. Analyzer output is bounded evidence, not
   runtime proof.

5. After the last canonical Markdown edit, run `llm-wiki sync --jobs 1
   --src-dir . --wiki-dir docs/llm_wiki` again. This final owning sync preserves
   supported semantic prose and re-anchors the Markdown, surface, knowledge,
   and manifest snapshot before validation. Skip the second sync only when no
   canonical Markdown changed. If a validation fix later edits Markdown,
   restart at this step.

6. Strict validation follows the final owning sync after any semantic Markdown
   edit. Run one heavy gate at a time and keep the same source root, external
   source permission, helper/test options, and source-selection profile on
   every source-reading gate:

   ```bash
   llm-wiki lint --strict --profile --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki ci-check --format json --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki team check --src-dir . --wiki-dir docs/llm_wiki
   ```

   Run `team check` only when team policy is configured. `--profile` exposes
   machine-readable lint `issues[]`, diagnostics, and timings; `ci-check`
   independently verifies the current source/wiki/artifact commitments. Fix
   supported errors without weakening a gate, and repeat the final owning sync
   first whenever a fix changes canonical Markdown. Review warning diagnostics
   even when lint exits zero. Normal lint runs the structural content checks;
   `--strict` additionally requires `index.md`, `log.md`, `entities/`,
   `modules/`, `workflows/`, `infrastructure/`, and a present, valid, fresh
   sync manifest. Dependency cycle, undeclared-dependency, and unused-dependency
   warnings remain diagnostics for the dependency-audit workflow; do not
   silence them or confuse them with strict structural failures. `team
   resolve-conflicts` only auto-resolves generated-page conflicts;
   workflow-page or other semantic conflicts remain a manual, evidence-backed
   decision. Never leave the wiki in a state where lint reports errors.

7. Inspect ordinary pending review separately when adopted. A semantic review
   may acknowledge an exact current basis with an explicit agent identity using
   the route above; sync alone never acknowledges prose. Report expired
   human-section reviews and stale machine-verification
   receipts with their existing reasons. Do not fabricate replacement human
   reviews or receipts. Then repeat the repository-policy check and follow
   [Repository handoff](repository-handoff.md).

For a trusted external source root, the configured team gate uses the same
explicit boundary:

```bash
llm-wiki team check --src-dir <repo> --allow-external-src --wiki-dir docs/llm_wiki --source-selection <profile>
```

`--wiki-dir` always remains inside the current project root. In an
`external_agent_docs` workspace, a semantic worker returns only the
packet-authorized changed paths and does not run an unassigned refresh. The
supervisor performs the owning sync/re-anchor and assigned validation against
the recorded source revision. A wiki-only snapshot cannot establish live
source freshness.

## Mutation and identity boundaries

Generated blocks and machine artifacts are application-owned. The semantic
sections and naming rules are owned by
[Canonical surfaces and naming](surfaces-naming.md); use that catalog rather
than inferring editability from prose-like formatting. Never hand-edit
`.llm-wiki-manifest.json`, `.llm-wiki-surface.json`,
`.llm-wiki-knowledge.json`, governance state, verification receipts, or a
derived site/vault to make a gate pass.

When governance exists, inspect rename identity before the first mutating
sync. An unambiguous supported one-to-one rename may carry the existing UID and
old aliases through sync or migration. An ambiguous fan-out, merge, target
collision, or manual move belongs to
[Durable knowledge governance](governance.md) and requires the governance
owner's explicit decision. Source disappearance never authors lifecycle. A
missing ledger is restored, not regenerated or reinitialized.

## Failure and recovery

Ordinary maintenance adoption stores a complete `committed` recovery snapshot
after successful publication. Use the actual retained complete directory and
adoption identity, not an invented path or latest projection. Recovery does not
approve prose or establish runtime currentness. Interrupted prepared adoption
and captured dirty-prose recovery require their explicit recovery options;
captured-preimage recovery requires owning sync before current review. Reads
and ordinary sync never implicitly adopt, downgrade or remove the marker.

- Stop on any sync, write, strict-lint, CI, or configured team-policy failure.
  Preserve the prior canonical state and report an unfinished gate as
  inconclusive; do not claim maintenance completed.
- Ordinary sync's broad-diff guard stops a plan affecting more than 50 files or
  more than 30 percent of tracked sources once the manifest contains at least
  10 sources. Inspect the reported paths and cause. Rerun with `--force` only
  when that exact broad change is intentional. Do not use force to conceal a
  stale or corrupt manifest, a governed identity conflict, or an unexpectedly
  broad source selection.
- Page writes and generated commitments are owned as one workflow. When an
  interrupted write leaves the old manifest authoritative, repeat the same
  owning command after capacity is safe rather than patching machine files.
- On disk-space, watcher, file-descriptor, swapping, or editor-responsiveness
  pressure, stop launching heavy work. Follow
  [Resource-aware execution](resources-context.md); a later single retry uses
  `--jobs 1`.
- Unsupported or unavailable analyzer coverage stays explicit. Do not claim
  affected files, relationships, contracts, or behavior were documented when
  the configured extractor could not observe them.
- Plain `sync` has no lock. An authorized unattended application uses
  `llm-wiki trigger-agent` with its timeout, diff/prompt bounds, lock, and
  circuit breaker instead of recreating that control loop. `--force` does not
  bypass the lock or breaker. Repository delivery policy still applies.
  LLM Wiki does not install Git hooks; repository updates remain explicit.
- `wiki-sync` may provide a richer changed-page worklist, optional-surface
  initialization, and automation diagnostics when it is separately installed.
  The complete correctness-critical loop is the procedure above and does not
  depend on that optional workflow.
