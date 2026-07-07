---
name: impact-analysis
description: Trace the blast radius of a proposed change to a symbol, file, or entrypoint using LLM Wiki's read-only graph queries — callers, callees, dependency neighborhood, and entrypoint flows — then map affected code to the wiki pages that describe it and emit a docs-to-update checklist in the doc-review classification vocabulary. Use before or during a code change to answer "what breaks if I change X" and "which docs need updating alongside it."
---

# impact-analysis

Answer "if I change this symbol/file/entrypoint, what else is affected, and which docs need to change alongside it?" using only existing wiki graph queries — no new analysis engine. The loop is: **identify the target → bounded graph query (callers/callees/dependency neighborhood/entrypoint flow) → map hits to wiki pages → blast-radius summary → docs-to-update checklist → hand off**. This is read-only reconnaissance: it never edits source or wiki pages itself. See [reference.md](reference.md) for the exact query payloads, the CLI protocol request format, and the checklist vocabulary shared with `doc-review`.

## Preconditions

- A maintained wiki exists for the target repository (graph queries read from the deep inventory and the wiki surface index together).
- The user has named a specific symbol, file, or entrypoint to analyze — this skill traces one target's blast radius, not a whole-repo audit.
- For external-source repositories, source-reading commands take `--allow-external-src`; the wiki path stays inside the current project.

## Steps

1. **Identify the target's query shape.** A callable symbol name → `callers` / `callees` query. A source file path → `dependency_neighborhood` query.
   An entry point id or symbol → `flow_for_entrypoint` / `data_flow_for_entrypoint` query. If the target is ambiguous (matches multiple symbols/files), read the query result's `matches`/`ambiguous` field and ask the user to disambiguate rather than guessing.

2. **Run the bounded graph query** via `llm-wiki context --request` (CLI, no MCP server required) or the MCP `query_graph` tool when already connected:

   ```bash
   echo '{"protocol":"llm-wiki-context/v1","budget_tokens":16000,"filters":{"symbol":"<name>"}}' \
     | llm-wiki context --src-dir . --wiki-dir docs/llm_wiki --request -
   ```

   This returns `graphs.symbol.callers`, `graphs.symbol.callees`, and `graphs.symbol.pages` in one call. For a file-path target, use MCP `query_graph` with `{"query_type": "dependency_neighborhood", "path": "<file>"}` — the context protocol's `filters` do not expose `dependency_neighborhood` directly. For an entrypoint target, use `filters.entrypoint` in the same context request.

   Every result is bounded and reports `truncated: true` when a full answer would exceed the limit — treat a truncated result as a partial blast radius, not a complete one, and say so.

3. **Map hits to wiki pages.** `graphs.symbol.pages` (from `pages_for_symbol`) already lists the wiki pages covering the target's source file.
   For callers/callees returned as raw symbols, resolve each to its owning file, then either re-query `pages_for_symbol` for that file or check the wiki's module/entity page for it directly — do not assume a caller has no documentation just because it wasn't in the first query's page list.

4. **Build the blast-radius summary.** List: the target; direct callers and callees (or dependency neighbors); any entrypoints whose flow reaches the target (cross-reference against flow pages); any import cycles the target participates in (`dependency_neighborhood.cycle_groups`); and the `truncated`/`ambiguous` flags from every query used, stated plainly as known gaps rather than omitted.

5. **Emit the docs-to-update checklist** using the same finding vocabulary `doc-review` uses, so its output can be picked up mechanically: for each affected wiki page, classify as **valid documentation defect** (the page describes behavior the change will alter and needs a real prose edit), **stale generated content** (a generated section like a call diagram will refresh via `sync`, no manual edit needed), or **needs human confirmation** (unclear whether the page needs a change). Do not invent a fourth category — reuse `doc-review`'s so downstream automation doesn't need a second vocabulary.

6. **Hand off.** Report the blast-radius summary and the checklist to the user (or to a `doc-review`/PR-comment workflow if one is running this skill as a feeder). This skill does not edit source or wiki pages; that is `doc-review`'s or the user's next step.

## Context budget

Use a small budget (8,000-16,000 tokens) for the context request — graph query results are already bounded server-side. Do not re-run `extract --deep` for this workflow; the wiki's existing surface index and deep inventory are the data source. Read full source files only for the target symbol itself and any caller/callee whose behavior is genuinely unclear from its signature and docstring — not for the whole blast-radius list.
