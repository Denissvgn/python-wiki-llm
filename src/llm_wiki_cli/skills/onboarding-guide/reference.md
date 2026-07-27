# onboarding-guide reference

Supporting detail for [SKILL.md](SKILL.md).

## The guides surface contract

`guides/` is a first-class canonical wiki surface with an `agent_owned` edit model:

| Property | Value |
|---|---|
| Path pattern | `guides/{page_id}.md` |
| Label | `Guides` |
| MCP kind | `guides` |
| Obsidian mirror directory | `Guides` |
| Bootstrap/init | creates `guides/` with `.gitkeep` |
| Sync behavior | counts and links existing guide pages in the index `## Guides` section; never creates guide pages, never rewrites guide bodies |

Consequences:

- Guide prose is durable: `sync`, `bootstrap --force`, and hook-driven runs will not touch it. There is no generated section to preserve and no `_Auto-generated from ..._` marker to replace.
- Discovery is automatic: lint validates guide pages and their links, MCP/API search and reads include them, and site/Obsidian exports mirror them. A guide page needs no registration step beyond existing at the path pattern.
- Because nothing regenerates guides, stale guide prose is a real risk. Add a line to the guide's frontmatter-free header noting the wiki state it was written against (for example the flow pages it links), so `doc-review` passes can judge staleness.

## Default personas

| Persona | Cares about | Tour skeleton |
|---|---|---|
| contributor | Where code lives, how to build/test, what to touch first | core modules → main flow → test/validation gate → first-task suggestion |
| operator | How it starts, what it touches at runtime, what breaks | entrypoints → load-order/startup caveats → infrastructure pages → failure modes |
| reviewer | What gates exist, where risk concentrates | validation flows → dependency/cycle notes → high fan-in entities → review checklist |
| product/user reader | What the product does and which user-facing workflows matter | overview guide → primary workflow pages → generated reference for details |

Use the product/user reader persona when the repository exposes user-facing workflows and the next step is `publish-docs --profile user`. Use `user-docs-author` instead of this focused persona-guide pass when the project needs a complete user-docs layer driven by deterministic site/check evidence. Rename or replace personas freely when the repository's audience differs — the budget and remainder rules stay the same.

## Guide page template

```markdown
# <Persona> onboarding

**Audience:** <who this is for>
**Prerequisites:** <tools, access, prior knowledge>
**Written against:** <wiki state, e.g. "flows as of 2026-07-04 sync">

## Mental model

<2-4 paragraphs: what the system is, the one framing that makes the structure make sense, where the seams are.>

## Guided tour

1. Start at [<flow page>](../flows/<page>.md) — <why first>.
2. Then [<module page>](../modules/<page>.md) — <what to notice>.
3. ...

## Your first task

<A bounded, real first contribution or operation, with links.>

## Going deeper

<Links to dependencies.md, load-order.md, architecture pages, other guides.>
```

Rules:

- Relative links only, so lint validates them against the live wiki.
- Ordered tours (reading order is the value the guide adds).
- 3–5 tour stops per persona; a guide that links everything guides nothing.
- No generated content, no volatile counts, no copied docstrings.

## Flow-ranking recipe

Rank candidate flows per persona with existing evidence:

```
persona_match * 100 + fan_in * 10 + boundary_count * 5 + behavior_prose_bonus * 20
```

- `persona_match`: entrypoint category fits the persona (operator ↔ `process`/service startup, contributor ↔ core `cli`/`api` development loop, reviewer ↔ validation and CI flows).
- `fan_in`: from `dependencies.metrics.most_depended_on` or `dependency_neighborhood`.
- `boundary_count`: boundary-effect rows on the flow page.
- `behavior_prose_bonus`: the flow's `## Behavior` section has real prose, not a placeholder.

The formula is a tie-breaking heuristic, not a contract — the point is to pick flows a newcomer meets early, preferring already-explained flows.

## Remainder format

When personas or topics exceed the run budget, append rows to the wiki's `bootstrap-remainder.md` (reusing the `WB-<YYYYMMDD>-<4-digit sequence>` ID convention) or record a `## Deferred guides` section in the run report:

```markdown
| ID | Persona | Intended flows | Reason deferred | Suggested context |
|---|---|---|---|---|
| WB-20260704-0101 | operator | startup, deploy | run budget (3 pages) | load-order.md + infrastructure/ |
```

## Failure modes

| Symptom | Cause | Response |
|---|---|---|
| Lint rejects guide links | Linked page name drifted or never existed | Link to live pages only; re-run sync first, then fix the link, never suppress. |
| Sync rewrites the guide's index links oddly | Custom index sections collide with the generated `## Guides` section | Keep custom index content in trailing custom sections; let sync own `## Guides`. |
| No flows exist to link | Wiki bootstrapped without deep extraction or flows are placeholders | Run `wiki-bootstrap`/`wiki-sync` first; a guide is narrative over structure, not a substitute for it. |
| Guides drift stale over months | Nothing regenerates guide prose | State the written-against baseline in each guide; let `doc-review` passes flag drift; refresh guides when their linked flows change behavior. |
| Huge repo, many personas | Budget exhausted | Ship the highest-value persona pages, record the rest in the remainder — an explicit deferral, not a failure. |

## Usage examples handoff

After guide prose exists and validates, use `usage-examples` to attach evidence-linked screenshots, recordings, or terminal captures under the wiki `assets/` surface. Do not mix capture policy into onboarding guide drafting.

## External documentation workspace

- Use the recorded intake audiences and jobs as the persona authority. Never re-ask intake on resume or replace `unspecified` intent with an inferred one.
- Enter only after semantic readiness passes. Reused imported guide prose may
  satisfy a persona surface when its important claims are grounded; otherwise
  preserve it as evidence and defer or revise only the workspace copy.
- For wiki-only runs, cite the snapshot's wiki evidence and retain the
  `unverified` freshness limitation. Do not claim source-backed prerequisites.
- Write guide/remainder paths only inside the workspace. Managed mode keeps its
  normal `docs(wiki):` commit contract; external mode returns a result packet
  and does not stage or commit source/input paths.
