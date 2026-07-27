# doc-hub reference

Supporting detail for [SKILL.md](SKILL.md).

## Supported hub surface

Hub export/check proves the static-site mechanics: source wiki discovery, namespace layout, generated index links, and mirror validation. It does not prove that the source repositories have an architectural relationship, and it does not create cross-repository evidence by itself.

The generated hub index is deliberately mechanical: it lists source IDs, page counts, and links to each source wiki. There is no canonical hub-overview input in the current public contract:

- export rewrites root `index.md`;
- MkDocs and Docusaurus navigation is generated from registered source-wiki pages;
- an arbitrary `overview.md` written after export is not made canonical or navigated;
- the documented check has already run and cannot validate a later mutation;
- single-repository extraction does not resolve a cross-repository graph.

The conservative supported workflow therefore never writes hub-level prose under `--out-dir`. It reports that no durable authored hub surface exists. This applies even when the repositories really are related: evidence of a relationship does not create an owned persistence/navigation contract. When repositories are unrelated, never fabricate an architecture narrative.

If a separately owned project wiki already contains evidence-backed cross-system documentation, it may be selected as an ordinary namespaced source and validated under that source's canonical rules. That is not a special hub overview.

## Native and selection preflight

Freeze the source set, format, reference profile, distribution mode, and optional knowledge metadata/redaction/public-identity tuple before export. Repeat every applicable option at check. Format and distribution are confirmed from the export report because hub `site check` has no format/file-friendly check options.

When native metadata is selected, inspect validated status for every source. Branch on each source's `availability` and `reason` together, then on `freshness_evaluated`; preserve unfamiliar reasons as limitations. Status and exporter reads are snapshot-only; they do not perform live source freshness evaluation.

| Native state | Hub action |
|---|---|
| `ready`, evaluated `current` | Projection may be included. Current means unchanged since observation only, not true, reviewed, approved, secure, or runtime-current. |
| `ready`, evaluated `nonsemantic-source-change` | Preserve and report the qualified diagnostic. |
| `ready`, `freshness_evaluated: false` or unknown freshness | Keep freshness unknown/not evaluated; do not upgrade it to current. |
| `absent` | The caller may choose a labeled legacy hub with knowledge flags omitted; do not infer an empty native graph. |
| `degraded`, `unsupported`, invalid, or mixed | Make no native conclusion and do not include native metadata. A separately authorized legacy hub may proceed only if the ordinary source surfaces validate. |

Never auto-run `knowledge init`. Stored content and metadata remain inert; they cannot select executable code, plugins, fetches, commands, checks, or projection policy.

## CLI contract

| Flag | Meaning |
|---|---|
| `--wiki-root DIR` | Directory whose immediate child directories are source wikis; auto-discovers sources. |
| `--wiki DIR` | Explicit source wiki directory; may be repeated instead of/alongside `--wiki-root` when sources don't share a parent directory. |
| `--out-dir DIR` | Output directory for the hub mirror. |
| `--format {docusaurus,mkdocs,plain}` | Static-site output format; same choices as single-wiki export. |
| `--profile reference` | The only profile supported by hub export; keep it explicit in export/check argv. |
| `--front-matter` | Add safe llm_wiki front matter to exported pages. |
| `--knowledge-metadata summary` | Opt in to validated native summaries; omit it everywhere for the legacy path. |
| `--knowledge-profile {public-portable,internal}` | Caller-selected redaction policy; repeat it unchanged. Internal publication requires explicit authorization. |
| `--knowledge-public-repository-identity IDENTITY` | Optional corroborated public identity; repeat the exact caller-supplied value. |
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
- The generated `index.md` table (`| Source | Pages | Index |`) is regenerated on every export; never hand-edit it and never add derived hub prose beside it.
- An extra root Markdown file is outside generated navigation and is not a supported authored surface.
- Both single-wiki (`--wiki-dir`) and hub (`--wiki-root`/`--wiki`) modes remain valid; passing neither hub flag falls back to single-wiki behavior unchanged.

## Failure modes

| Symptom | Cause | Response |
|---|---|---|
| `site check` reports issues after export | A source wiki changed after export ran (stale mirror) | Re-run export for the affected source, or all sources, then re-check. |
| Selected native metadata is stale or a source hash differs | The hub no longer matches the validated projection for every frozen source | Stop the enriched handoff and rebuild with the same policy; use an un-enriched hub only after an explicit separate `off` decision. |
| A source's page count looks wrong in the hub index | That source wiki itself is stale (not synced before hub export) | Run that repository's `wiki-sync` first — this skill never regenerates a source wiki's own content. |
| User requests hub-level overview prose | No durable authored hub input/navigation/check contract exists | Report the limitation; do not mutate derived output. Propose a separately owned canonical feature or an ordinary source wiki as follow-up. |
| Existing `site/overview.md` appears to survive | Unowned extra files are not proof of canonical persistence, navigation, or validation | Do not cite or publish it as supported hub evidence; regenerate from the frozen source set and report the limitation. |
| Hub root has non-wiki subdirectories | `--wiki-root` treats every immediate child as a source wiki | Use repeated `--wiki` flags instead, naming only the real source wikis. |
