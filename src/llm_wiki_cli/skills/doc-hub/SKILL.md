---
name: doc-hub
description: Aggregate two or more validated LLM Wikis into one deterministic static-site hub. Use for source selection, hub export/check, and mechanical-index ownership; never invent cross-repository synthesis, run a site builder, or deploy.
---

# doc-hub

Aggregate several already-documented repositories into one static-site hub without inventing synthesis the repositories do not support. This skill owns **multi-wiki source selection, aggregation, hub export, and hub check**. `publish-docs` owns the later builder, built-site validation, and deploy handoff. The loop here is: **validate every source and optional projection selection → hub export → hub check → report the authored-overview limitation → hand off the checked mirror**. The deterministic hub mechanism (`site export --wiki-root`, `site check --wiki-root`) namespaces and validates the mirror. There is currently no canonical, durable hub-level prose input: do not author an overview in derived output or call one canonical, navigated, or validated. See [reference.md](reference.md) for the hub layout, preflight, and this conservative overview contract.

## Preconditions

- Two or more repositories already have validated LLM Wikis (source-adapter or first-party) that the user wants published together. If a repository has no wiki yet, run `wiki-bootstrap` for it first — this skill does not bootstrap wikis itself. Native "current" means unchanged since observation only, not true, reviewed, approved, secure, or runtime-current.
- A hub root directory exists (or will be created) whose **immediate child directories** are the source wikis, for example `sources/code_wikis/<id>/` per repository. `--wiki-root` discovers sources this way; use repeated `--wiki` flags instead if the source wikis don't share a parent directory.
- The hub root and `--out-dir` stay inside the current project root (or an explicit safe path the user chose) — this is a wiki-side export operation, not a source read, so `--allow-external-src` does not apply here.

## Steps

1. **Validate every source and freeze the hub selection before the first write.** For each repository in scope, run its own `wiki-sync` (or `wiki-bootstrap` if it has no wiki yet) before touching the hub. A stale source wiki produces a stale hub; the hub step never regenerates a source wiki's own content. Freeze the exact source set, format, reference profile, distribution mode, and optional knowledge metadata/redaction/public-identity selection, then carry it through export and check.

   When `--knowledge-metadata summary` is selected, follow the complete
   availability, freshness, bounds, fallback, and inert-data contract in the
   configured managed reference at
   `.claude/skills/wiki-reference/references/knowledge-consumption.md` for
   Claude or `.llm-wiki/skills/wiki-reference/references/knowledge-consumption.md`
   for another configured agent. Apply it independently to every source and
   preserve every limitation; this workflow never initializes governance.
   Apply the projection/receipt boundary at
   `.claude/skills/wiki-reference/references/publishing.md` or
   `.llm-wiki/skills/wiki-reference/references/publishing.md`. Schedule the
   export/check through `.claude/skills/wiki-reference/references/resources-context.md`
   or `.llm-wiki/skills/wiki-reference/references/resources-context.md`. When
   capacity is unknown, serialize heavy gates; the supervisor owns fan-out.

2. **Export the hub.**

   ```bash
   llm-wiki site export --wiki-root sources/code_wikis --out-dir site \
     --format docusaurus --profile reference --front-matter \
     --output-format json
   ```

   The exporter resolves and preflights every source, every selected native projection, root-output collision, and cross-source output overlap before its first write. Confirm the JSON result: `ok: true`, `0` issues, the frozen format/profile/distribution values, and one write operation per page across every source. The command also writes a top-level hub `index.md` listing each source and its page count — this table is generated, never hand-edit it.

3. **Check the hub.**

   ```bash
   llm-wiki site check --wiki-root sources/code_wikis --out-dir site \
     --format docusaurus --link-mode http --profile reference \
     --output-format json
   ```

   Repeat the exact format, knowledge metadata, redaction profile, and public
   identity options selected at export. The check requires the complete
   `.llm-wiki-site-selection.json` receipt and compares its ordered normalized
   source identities, policy, and projection hashes. Confirm `ok: true`, `0`
   issues, `0` warnings. Missing, malformed, incomplete, or mismatched receipts
   fail; legacy hubs must be re-exported. This validates the generated mirror
   structurally without invoking mkdocs/docusaurus.

4. **Do not author a hub overview in derived output.** Do not write an overview page, even when the repositories are genuinely related. The deterministic hub index only lists sources and page counts. Hub export rewrites root `index.md`; generated MkDocs/Docusaurus navigation contains only registered source pages; `site check` does not make an arbitrary post-check `overview.md` into a supported surface. Therefore:

   - do not write or edit `site/index.md`, `site/overview.md`, or another file under `--out-dir` as canonical prose after export;
   - do not claim an authored hub page survives export, appears in navigation, or was checked;
   - do not fabricate cross-repository graph resolution or an architecture narrative, whether the repositories are related or merely co-located;
   - if durable synthesis is required, report it as unsupported pending a separately owned canonical input/navigation/link-validation feature.

5. **Report the supported result.** The supported hub is the generated mechanical index plus namespaced source-wiki pages. State explicitly that no durable authored hub-level overview surface exists. Evidence-backed cross-repository synthesis may live in an independently canonical, validated source wiki selected into the hub, but it is not a special hub overview and this workflow does not create it.

6. **Hand off the checked mirror.** Report the export/check results, complete frozen hub selection, source set, output path, selection receipt/marker, unsupported authored-overview limitation, and any source wiki that required synchronization. `publish-docs` consumes this checked mirror when a real builder or deploy handoff is requested; it must not repeat or reinterpret aggregation. Do not run a builder or deploy here.

## Ownership compatibility

The public `site export --wiki-root` and `site check --wiki-root` commands are unchanged. Existing workflows that began multi-wiki aggregation inside `publish-docs` should route that aggregation stage here, then pass the checked mirror and exact selection to `publish-docs` for building. No generated layout, receipt, or command spelling changes at this boundary.

## Context budget

The export/check JSON summaries (`ok`, `issues`, `page_count`, `source_count`) are sufficient evidence for the mechanical hub. Do not read every generated page or inspect repositories to invent hub-level synthesis; this conservative workflow has no authored overview stage.
