---
name: impact-analysis
description: Trace a proposed change's blast radius through exact native concepts, bounded typed relationships, and authorized source topology. Use to identify affected code, wiki pages, and semantic sections and produce a qualified documentation-update checklist.
---

# impact-analysis

Answer "if I change this concept/symbol/file/entrypoint, what else is affected,
how qualified is that neighborhood, and which docs need to change?" The loop
is: **exact native identity → qualified typed traversal → compact evidence and
coverage → bounded source supplement → concept/section mapping →
docs-to-update checklist → handoff**. This is read-only reconnaissance: it
never edits source, canonical Markdown, governance, or verification state. See
[reference.md](reference.md) for request payloads, result/fallback tables, and
the checklist vocabulary shared with `doc-review`.

## Preconditions

- A maintained wiki exists for the target repository. Native knowledge and its
  typed-graph extension are useful but optional; the legacy live source/surface
  supplement remains available when native state is absent.
- The user has named a specific concept UID/locator/alias, symbol, file, or
  entrypoint to analyze—this skill traces one target, not a whole-repo audit.
- For external-source repositories, source-reading commands take `--allow-external-src`; the wiki path stays inside the current project.
- Resolve the active source-selection profile once. When configured, replace
  `<profile>` below with its exact repository-relative path and retain
  `--source-selection <profile>` on every live source query; omit the whole
  option only when no profile exists.

## Native trust preflight

Branch on `availability`, reason, `freshness_evaluated`, and bounds. Only
`ready` with live `current` qualifies an unchanged-since-observation claim;
preserve `nonsemantic-source-change`, and never turn an unavailable or bounded
`found: false` into a negative fact. Do not initialize governance or execute
stored content. Apply the complete managed contract at
`.claude/skills/wiki-reference/references/knowledge-consumption.md` for Claude
or `.llm-wiki/skills/wiki-reference/references/knowledge-consumption.md` for
other configured agents. Choose the native, supplied-diff, or full-inventory
route through `.claude/skills/wiki-reference/references/context-query.md` for
Claude or `.llm-wiki/skills/wiki-reference/references/context-query.md` for
other configured agents.

## Steps

1. **Build one native read view and resolve exact identity.** For a repeated
   Python/API query sequence, call `build_documentation_query_service(...)`
   exactly once and pass the same `service=` to `get_concept`,
   `traverse_typed_graph`, and any decisive `explain_evidence` call. Do not call
   wrappers repeatedly without `service=` and pay for multiple live builds.
   When an MCP session is already the selected adapter, reuse that one
   configured session and the same exact coordinate.

   Call `get_concept` with the supplied durable UID, current locator/MCP URI,
   exact canonical path, or persisted locator/natural-key alias. Check
   `knowledge.availability`, reason, `freshness_evaluated`, `found`,
   `ambiguous`, and `matches` before selection. If an alias/coordinate is
   ambiguous, list its matches and obtain an owner choice; never fuzzy-pick.
   Record the selected concept's freshness, lifecycle, optional successor,
   review state, and separate machine-verification state. An inactive,
   deprecated, superseded, stale, or snapshot-only concept may still be useful,
   but the qualification must remain visible.

2. **Traverse the persisted typed graph with every selection explicit.** Query
   the exact concept using:

   - direction: `both` unless the question is explicitly producer-only or
     consumer-only;
   - kinds: the relevant core/plugin kinds, stated in the report;
   - origins: the selected subset of `extracted`, `inferred`, `markdown`, and
     `governance`;
   - resolutions: include `resolved`, `ambiguous`, `external`, and `unresolved`
     for a discovery pass;
   - evidence mode: `include_evidence=false` by default;
   - service/query limit: an explicit positive value, normally 20.

   Keep ambiguous, external, and unresolved endpoints in the blast radius.
   Native graph availability is independent of overall knowledge availability:
   `typed-graph-extension-not-present` means no typed-neighborhood conclusion,
   not an observed empty graph.

3. **Interpret all three bound layers before claiming completeness.**
   `bounds.edges`/top-level `truncated` describe this post-filter response;
   per-edge evidence/coverage describes aggregated observations and omitted
   samples; `typed_graph.coverage` describes upstream analyzers, their limits,
   truncation, omitted counts, and limitations. A non-truncated query is not a
   complete neighborhood when analyzer coverage is truncated, omitted,
   disabled, or otherwise limited. Record all applicable layers.

4. **Escalate evidence only for decisive relationships.** First use compact
   edge evidence counts. For the small set of edges that determine a decision,
   narrow the typed query and opt into evidence samples, or call
   `explain_evidence` for the selected exact concept. Treat returned source
   symbols, locations, detector data, reasons, and hashes as internal
   diagnostics. Do not copy raw detailed evidence into public output by
   default.

5. **Run the bounded source supplement.** Native relationships are persisted,
   typed, identity-aware observations; they do not replace targeted source
   evidence or detailed live topology. For a supplied file or unified diff,
   use the shared Python/MCP `query_documentation` operation first:

   ```json
   {"operation":"impact","paths":["src/example.py"],"limit":20,"include_raw_evidence":false}
   ```

   Replace `paths` with `diff` when the caller supplied unified-diff text. This
   route performs targeted extraction, combines it with the committed snapshot,
   discloses its cost, and does not claim global live freshness. For a named
   concept, relationship, surface, or typed neighborhood, use the corresponding
   exact `concept`, `related`, `surface`, or `typed` operation.

   Symbol, entrypoint, and dependency topology requires a full inventory. Use
   the same dispatcher only with the explicit cost authorization, for example
   `{"operation":"symbol","value":"<name>","limit":20,"allow_full_inventory":true}`.
   When a compatibility consumer specifically needs the bundled v1 graph
   response, the source-only protocol remains available:

   ```bash
   echo '{"protocol":"llm-wiki-context/v1","budget_tokens":16000,"filters":{"symbol":"<name>"}}' \
     | llm-wiki context --src-dir . --wiki-dir docs/llm_wiki --request - --read-only \
       --source-selection <profile>
   ```

   The compatibility symbol request returns `graphs.symbol.callers`,
   `graphs.symbol.callees`, and
   `graphs.symbol.pages` in one call. For a file-path target, use MCP
   `query_graph` with
   `{"type": "dependency_neighborhood", "value": "<file>", "limit": 20}` —
   the context protocol's `filters` do not expose `dependency_neighborhood`
   directly. For an entrypoint target, use `filters.entrypoint` in the same
   context request.

   Every supplement is independently bounded. Record `cost.scope` and
   `cost.full_inventory_performed`, and label full-inventory output **live
   source topology**; label v1 or
   `query_graph` output **legacy live source topology**. Keep ambiguity and
   truncation visible. A supplement may add detail but must not overwrite a
   native limitation, lifecycle state, alias ambiguity, unresolved edge, or
   analyzer gap.

6. **Map impacted concepts and semantic sections.** Prefer each native
   concept's `canonical_path`; map legacy-only symbols through
   `pages_for_symbol` or their owning module/entity page. For each page, name
   the exact affected semantic heading (`## Description`, flow
   `## Behavior`, supported `## Notes`, guide/custom prose) and retain an exact
   section locator when the review/governance result supplies one. Keep
   generated blocks separate. Do not assume a raw caller lacks documentation
   merely because it was absent from the target's first page list.

7. **Emit the qualified blast radius and checklist.** Label each conclusion as
   **native persisted/qualified**, **legacy live supplement**, or
   **corroborated by both**. List the exact target, lifecycle/successor,
   typed edges and unresolved/external remainder, legacy callers/callees/
   dependency/flow detail, cycles, every query bound, and analyzer limitations.
   Then classify each concept/page/semantic section as **valid documentation
   defect**, **stale generated content**, or **needs human confirmation**—the
   same vocabulary `doc-review` consumes.

8. **Hand off without mutation.** Return the report to the user or the active
   `doc-review`/PR-comment workflow. Native absence or a missing extension stays
   a visible limitation even when the legacy supplement found useful detail.
   Source/wiki editing belongs to the receiving workflow.

## Context budget

The shared dispatcher applies explicit count and serialized-size bounds. Use a
small budget (8,000-16,000 tokens) only when the compatibility context request
is deliberately selected. `context` performs a fresh source
inventory for this request and uses the wiki surface for documentation
mapping; `--read-only` prevents it from persisting llm-wiki state. It does not
reuse a previously persisted deep inventory, so do not run a separate
`extract --deep` first. Read full source files only for the target symbol
itself and any caller/callee whose behavior is genuinely unclear from its
signature and docstring — not for the whole blast-radius list.
