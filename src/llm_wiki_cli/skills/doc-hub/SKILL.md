---
name: doc-hub
description: Aggregate multiple source-adapter LLM Wikis into one static-site hub — keep each source wiki current, export/check the multi-wiki hub with `llm-wiki site export --wiki-root`/`site check`, and write one LLM-owned hub overview page only when the source repositories are genuinely related. Use when a user wants to publish two or more documented repositories (a multi-service platform, a monorepo split into source-adapter wikis) as one browsable site; never fabricate a relationship between unrelated repositories.
---

# doc-hub

Aggregate several already-documented repositories into one static-site hub without inventing a synthesis the repositories don't actually have. The loop is: **keep each source wiki current → hub export → hub check → write one overview page only if the sources are genuinely related → hand off**. The deterministic hub mechanism (`site export --wiki-root`, `site check --wiki-root`) namespaces and validates the mirror; the only LLM-owned artifact is a single optional hub overview page. See [reference.md](reference.md) for the hub layout, the namespacing/index contract, and the overview guardrail.

## Preconditions

- Two or more repositories already have LLM Wikis (source-adapter or first-party) that the user wants published together. If a repository has no wiki yet, run `wiki-bootstrap` for it first — this skill does not bootstrap wikis itself.
- A hub root directory exists (or will be created) whose **immediate child directories** are the source wikis, for example `sources/code_wikis/<id>/` per repository. `--wiki-root` discovers sources this way; use repeated `--wiki` flags instead if the source wikis don't share a parent directory.
- The hub root and `--out-dir` stay inside the current project root (or an explicit safe path the user chose) — this is a wiki-side export operation, not a source read, so `--allow-external-src` does not apply here.

## Steps

1. **Keep every source wiki current first.** For each repository in scope, run its own `wiki-sync` (or `wiki-bootstrap` if it has no wiki yet) before touching the hub. A stale source wiki produces a stale hub; the hub step never regenerates a source wiki's own content.

2. **Export the hub.**

   ```bash
   llm-wiki site export --wiki-root sources/code_wikis --out-dir site \
     --format docusaurus --front-matter --output-format json
   ```

   Confirm the JSON result: `ok: true`, `0` issues, and one write operation per page across every source. The command also writes a top-level hub `index.md` listing each source and its page count — this table is generated, never hand-edit it.

3. **Check the hub.**

   ```bash
   llm-wiki site check --wiki-root sources/code_wikis --out-dir site \
     --output-format json
   ```

   Confirm `ok: true`, `0` issues, `0` warnings. This validates the generated mirror structurally without invoking mkdocs/docusaurus.

4. **Decide whether a hub overview page is honest to write.** The deterministic hub index only lists sources and page counts — it cannot describe how the documented systems relate, because nothing in a single-repo extraction can see across repositories. Before writing one:

   - Confirm the source repositories are **actually related** — a real multi-service platform, a monorepo intentionally split into source-adapter wikis, or systems with a real deployment/data dependency on each other.
   - If they are not related (independent projects merely published to the same hub for convenience), **do not write an overview page** — say so explicitly in the handoff instead of fabricating an architecture narrative. Not every hub has genuine cross-repo content to write.

5. **Write the overview page, if step 4 confirmed a real relationship.**
   Place it outside the generated per-source directories (for example `site/overview.md`, or the current project's own `guides/` surface if this hub is for the current project) and link it from the hub index's custom sections rather than editing the generated table. Cover: what each source system does, how they actually connect (shared data, network calls, shared deployment), and where to start reading in each source wiki. Cite the specific pages that show the relationship (a flow page with an external call to another service, a shared infrastructure file) rather than asserting it abstractly.

6. **Hand off.** Report the export/check results, the hub path, whether an overview page was written and why (or explicitly why not), and any source wikis that were stale and had to be synced first. Do not run an external site builder or deploy anything — that belongs to the `publish-docs` skill.

## Context budget

The export/check JSON summaries (`ok`, `issues`, `page_count`, `source_count`) are sufficient evidence for steps 2-3; do not read every generated page. For step 4-5, read only the specific pages that would show a real cross-repo relationship (entrypoint flows with external calls, shared infrastructure/dependency pages) rather than the whole hub.
