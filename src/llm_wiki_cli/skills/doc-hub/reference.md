# doc-hub reference

Supporting detail for [SKILL.md](SKILL.md).

## Overview guardrail

Hub export/check proves the static-site mechanics: source wiki discovery, namespace layout, generated index links, and mirror validation. It does not prove that the source repositories have an architectural relationship, and it does not create cross-repository evidence by itself.

The generated hub index is deliberately mechanical: it lists source IDs, page counts, and links to each source wiki. Treat any LLM-authored overview as optional and evidence-backed. Write it only when the sources are genuinely related, such as a real multi-service platform, a monorepo split into source-adapter wikis, or systems with direct deployment, data, or API dependencies. When sources are only co-located for convenience, do not write an overview page and do not invent a relationship.

The skill should cite generated pages that demonstrate the relationship before writing synthesis prose. Suitable evidence includes flow pages with external calls, shared infrastructure pages, dependency pages, or source-owned docs that name the cross-system contract.

## CLI contract

| Flag | Meaning |
|---|---|
| `--wiki-root DIR` | Directory whose immediate child directories are source wikis; auto-discovers sources. |
| `--wiki DIR` | Explicit source wiki directory; may be repeated instead of/alongside `--wiki-root` when sources don't share a parent directory. |
| `--out-dir DIR` | Output directory for the hub mirror. |
| `--format {docusaurus,mkdocs,plain}` | Static-site output format; same choices as single-wiki export. |
| `--front-matter` | Add safe llm_wiki front matter to exported pages. |
| `--output-format {text,json}` | Console output format; use `json` so the skill can parse results directly. |

## Hub output layout

```
<out-dir>/
  index.md                  # generated: source table, page counts, links
  sidebars.json             # generated (docusaurus format)
  <source_id_1>/...         # namespaced mirror of source wiki 1
  <source_id_2>/...         # namespaced mirror of source wiki 2
```

- `<source_id>` is the child directory name under `--wiki-root` (or the basename of each `--wiki` path) — pick meaningful directory names before running export, since they become the hub's public namespace.
- The generated `index.md` table (`| Source | Pages | Index |`) is regenerated on every export; never hand-edit it. Put the hub overview narrative in a separate file and link it from there, or from a custom section the export step doesn't own.
- Both single-wiki (`--wiki-dir`) and hub (`--wiki-root`/`--wiki`) modes   remain valid; passing neither hub flag falls back to single-wiki behavior unchanged.

## Failure modes

| Symptom | Cause | Response |
|---|---|---|
| `site check` reports issues after export | A source wiki changed after export ran (stale mirror) | Re-run export for the affected source, or all sources, then re-check. |
| A source's page count looks wrong in the hub index | That source wiki itself is stale (not synced before hub export) | Run that repository's `wiki-sync` first — this skill never regenerates a source wiki's own content. |
| No real content for the overview page | Sources aren't actually related (see the pilot finding) | Skip the overview page and say so explicitly in the handoff; do not invent a relationship. |
| Hub root has non-wiki subdirectories | `--wiki-root` treats every immediate child as a source wiki | Use repeated `--wiki` flags instead, naming only the real source wikis. |
