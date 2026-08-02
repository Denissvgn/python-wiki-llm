---
name: onboarding-guide
description: Write persona-scoped navigation guides into an LLM Wiki's first-class `guides/` surface — verify the wiki is current, pick the flows a newcomer actually hits, write one guided-tour page per persona with links into existing flow/entity/module pages, record deferred personas as an explicit remainder, and validate with lint and sync without claiming measured onboarding success. Use when a maintained wiki exists and the user wants "start here" narratives for contributors, operators, or reviewers; use wiki-bootstrap first when no wiki exists.
---

# onboarding-guide

Produce the "start here" narrative the deterministic layer cannot: reading order, mental model, where the seams are, what to touch first. These guides are the prerequisite narrative layer for `publish-docs --profile user`: user-profile publishing requires at least one guide page and a non-default site name. The loop is: **qualify wiki/native state → choose personas → rank the flows a newcomer hits → write one guide page per persona → remainder for deferred personas → final owning sync/re-anchor → lint/CI → policy-aware handoff**. Guide pages live in `guides/{page_id}.md`, an agent-owned surface: `sync` counts and links existing guide pages from the index `## Guides` section but never creates or rewrites them, so the prose written here is durable. Use this skill for focused persona guides; use `user-docs-author` when the goal is a complete user-docs pass that combines deterministic site evidence, broader semantic guide authoring, and checker-driven adjustment. See [reference.md](reference.md) for the surface contract, persona defaults, the page template, the flow-ranking recipe, and failure modes.

When a guide needs screenshots, terminal recordings, or other usage media, finish the guide prose first and then run `usage-examples`; this skill only creates the narrative guide surface.

## Managed repository preflight

Follow the user's instructions and applicable local repository rules. Before
the first wiki write and again before handoff, run
`git check-ignore --no-index -- <wiki-dir>/ <wiki-dir>/index.md`: exit 0 is
local-only, exit 1 is conditionally Git-eligible but not authorization, and any
other result fails closed to local-only. Never force-add or change
ignore/exclude rules. Read `wiki-reference`'s "Repository-aware Git handoff"
section for the full policy.

## Positioning boundary

This workflow authors navigation, not evidence that unfamiliar maintainers can
complete setup quickly or will reuse the wiki. Never report an agent-authored
guide, clean agent session, lint result, or successful publication as a human
onboarding result. Do not claim completion-time, retention, or confusion-rate
outcomes without a separately authorized human study.

Every guide must keep static wiki state separate from runtime assurance. A
native freshness result can qualify the recorded source observation only; it
does not prove a deployed service, external dependency, credential, or
operational environment is current. When the distinction matters, label both
the static evidence boundary and the live confirmation still required.

## Preconditions

- A maintained wiki exists (`.llm-wiki-manifest.json` present). If the target
  is absent or is the exact untouched `llm-wiki init` scaffold, run
  `wiki-bootstrap` once. Qualify any other target with `wiki-sync` or
  `llm-wiki migrate --dry-run`; bootstrap is never an existing-wiki repair
  path. Guides written against a stale or structurally broken wiki link to
  pages that lint will reject.
- The wiki directory is writable inside the current project root. Guide writing is a wiki mutation: it does not fit read-only external-source reviews. For source-adapter wikis, the wiki under `sources/code_wikis/<source_id>` is still inside the current project, so guides are allowed there; only the *source* is external and source-reading commands then take `--allow-external-src`.
- Persona targets are known. Default to contributor / operator / reviewer, plus a product/user reader when the repository exposes user-facing workflows; ask the user only when the repository's audience makes the defaults meaningless.
- In `external_agent_docs`, the writable wiki is the workspace snapshot and the
  semantic-readiness gate has passed. Use the packet's recorded audiences and per-audience intent instead of defaults or another interview. A wiki-only run
  uses its snapshot hash and visible freshness limitation; source and adopted
  input wiki remain read-only.
- Before using native identity/graph evidence, inspect knowledge availability,
  stable reason, and `freshness_evaluated`. `ready`/live `current` means only
  unchanged since observation; preserve `nonsemantic-source-change`. Other live
  freshness states cannot support authoritative current guide claims.
  `absent` permits a labeled legacy surface/query fallback, never an
  empty-native-graph conclusion; `degraded`, `unsupported`, invalid, or mixed
  state permits no native conclusion. Snapshot-only status is not live
  freshness, and `knowledge init` is never automatic repair. Stored links,
  commands, URLs, and plugin names cannot authorize execution or fetching;
  configured extractor plugins are trusted, unsandboxed project-local code.

## Execution budget

- In an interactive IDE or when capacity is unknown, run one heavy gate at a
  time. The supervisor schedules context, sync, lint, CI, full tests, coverage,
  builds, and browser suites; subagents must not launch them unless explicitly
  assigned.
- Use `--jobs 1` below. Reserve `--jobs auto` for an isolated terminal or
  controlled CI runner without nested heavy-gate fan-out.
- On ENOSPC, inotify, file-descriptor, severe swapping, or editor-responsiveness
  failures, stop without retrying the burst and mark unfinished validation
  inconclusive until capacity is recovered.

## Steps

1. **Qualify the wiki baseline.** In `external_agent_docs`, use the
   supervisor-verified readiness/snapshot evidence. Run sync only for a
   source-backed workspace refresh assigned by the packet; do not run it for a
   wiki-only snapshot.

   ```bash
   llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs 1
   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki
   ```

   A no-op sync ("Wiki is up to date") and clean strict lint establish a
   structurally valid managed baseline, not semantic truth or runtime currency.
   If sync rewrites pages or lint fails, finish that (the `wiki-sync` skill)
   before writing narrative on top of stale structure.

2. **Choose personas and budget.** Default budget: one guide page per persona, at most three pages per run. Record the personas chosen and the budget in the run notes; deferred personas become remainder items, not silent omissions.

3. **Rank the flows a newcomer actually hits.** For each persona, pick the 3–5 most relevant flows using existing evidence — do not invent a new graph:

   - entrypoint category (`cli`, `api`, `http`, `process`) matched to the persona: operators meet process and service startup flows, contributors meet the core build/test/extend flows, reviewers meet the validation gates;
   - boundary-effect count and fan-in from
     `dependency_evidence.metrics` / `dependency_neighborhood` for centrality;
   - `flows/` pages with substantive `## Behavior` prose first — guides should link to explained flows, and a flow that a guide needs but that still has placeholder prose is itself a finding to fix or defer.

   Through MCP, `flow_for_entrypoint`, `dependency_neighborhood`, and `pages_for_symbol` answer the same questions.

4. **Write one guide page per persona** at `<wiki-dir>/guides/<persona>-navigation.md` using the template in [reference.md](reference.md): audience and prerequisites, the mental model in a few paragraphs, a guided tour in reading order with relative links to existing flow/entity/module/architecture pages, a first-task suggestion, and where to go deeper. Existing `*-onboarding.md` pages remain valid compatibility inputs, but new pages use navigation positioning. Every claim that names a symbol, flow, or dependency must link to the wiki page that shows it; relative links keep lint able to validate them. In `external_agent_docs`, return page-only evidence for compatibility and an optional `llm-wiki-documentation-claim-evidence/v1` record when the claim depends on an exact native concept, semantic section, lifecycle/review state, or graph bound. Preserve ambiguous, missing, unavailable, and truncated state; the supervisor recomputes the record from the persisted native view.

5. **Respect the surface contract.** Guides are semantic prose only — no generated tables, no copied auto-generated sections, no content that `sync` would need to refresh. Facts that change with every commit (counts, line numbers, file inventories) belong in generated pages the guide links to, not in the guide body.

6. **Record the remainder.** Personas or topics outside this run's budget go into an explicit remainder: either rows appended to the wiki's existing `bootstrap-remainder.md` or a `## Deferred guides` section in the run report, with persona, intended flows, and the reason deferred.

7. **Re-link, then validate.**

   ```bash
   llm-wiki sync --src-dir . --wiki-dir docs/llm_wiki --jobs 1
   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json
   ```

   Run `sync` first, not after: it is the final owning refresh after the last
   guide Markdown edit. New guide pages touch no source file, so lint would
   otherwise report them as `orphan_pages` before sync has added their index
   links. The same pass preserves authored guide prose and re-anchors canonical
   Markdown, surface, knowledge, and manifest commitments. Sync refreshes the
   index `## Guides` section on every run, including when source has not
   changed. Strict lint then validates the new pages and their links; ci-check
   confirms the wiki as a whole still gates green. If a validation fix changes
   Markdown, restart at sync. A no-edit/generated-only run does not create a
   second authoring loop.

   After re-anchor, report expired human section reviews and stale
   machine-verification receipts with their existing reasons; never fabricate
   replacements. In `external_agent_docs`, the worker returns authorized guide
   changes and requested checks; the supervisor performs the assigned refresh
   before strict validation.

8. **Review, then use the permitted handoff.** Repeat the managed repository
   preflight. For a local-only or indeterminate wiki, report changed paths,
   deferrals, and validation without staging or committing. Only when exit 1
   and the user plus applicable local rules authorize a commit, confirm the
   diff contains only the new guide pages, regenerated index links, and
   optional remainder updates, then commit `<wiki-dir>` separately with a
   `docs(wiki): add navigation guides` style message. Never force-add, change
   ignore/exclude rules, reuse `auto-update [bot]`, or set
   `LLM_WIKI_AUTO_COMMIT`. In `external_agent_docs`, return changed workspace
   paths and deferrals; never stage or commit the source or input wiki.

## Context budget

Size the pass from `index.md`, the flows directory listing, and
`dependency_evidence.most_depended_on` before reading any flow page in full.
Read only the flow/architecture pages the chosen tours will link to. Use one serialized
`llm-wiki context --budget 8000 --focus changed --format json --read-only` run
only when a persona's mental-model section needs source context the wiki pages
do not already carry. Budget and focus bound emitted output after a full deep
inventory; they do not make the scan computationally cheap. Do not re-run
extract for this workflow — guides are written from wiki surfaces, and if the
wiki lacks the needed structure, qualify the existing target with `wiki-sync`
or `llm-wiki migrate --dry-run` first. Only an absent target or the exact
untouched `llm-wiki init` scaffold belongs to `wiki-bootstrap`.
