# Publishing projections

Read this topic when exporting or checking Site or Obsidian output, choosing a
publication profile, or interpreting a projection receipt. It owns derived
publication contracts and privacy boundaries. It does not authorize a build,
deployment, URL fetch, network operation, plugin, repository write, or public
release. The user and the selected publication workflow grant any such
authority.

## Generated Site output

Use `llm-wiki site export|check` or the matching service to build and validate
plain, MkDocs-compatible, or Docusaurus-compatible Markdown as generated
distribution output. The default `--profile reference` mirror preserves the
agent/reference wiki shape. `--profile user --site-name ...` is an opt-in
human-docs profile that writes a concise landing page, expects authored guide
pages, and moves exhaustive generated inventory to `generated-reference.md`.
Treat every exported projection as generated distribution output, not as an
editable source of truth.

MkDocs output includes generated `llm_wiki` front matter and `mkdocs.yml`
navigation. `--file-friendly` is MkDocs-only and adds direct-file-safe
configuration plus a local-disk theme override. Docusaurus output includes
generated front matter and `sidebars.json`.

Generated labels can include page-id context when duplicate headings would
otherwise make navigation ambiguous. Mermaid fences remain input to the
configured Markdown/Mermaid renderer. The checker validates missing pages,
local Markdown links, generated front matter, duplicate Docusaurus ids, and
output-path containment without invoking an external builder.

Export writes a complete path-safe `.llm-wiki-site-selection.json` receipt and
a non-sensitive `llm-wiki-site-selection.json` builder marker. Checks require
a complete matching receipt and compare every supplied source, format,
profile, site, link, and knowledge selection. When `--built-site-dir` is
supplied, the matching marker must exist at the built root before HTML links
are checked. `--link-mode http` accepts hosted MkDocs directory URLs;
`--link-mode file` requires direct `.html` targets.

User-profile checks add quality gates for default site names, missing guides,
oversized landing pages, and placeholder text in primary human docs.
Warning-only quality findings do not fail the check. Missing, malformed,
incomplete, stale, or mismatched receipts and markers do fail. Re-export and
rebuild legacy output; a policy change requires a distinct output directory.
MkDocs carries the public marker automatically, while Docusaurus and custom
builders must copy it into their built root.

Derived Site output is never the editable source of truth. Make semantic edits
only on supported canonical surfaces, complete the owning maintenance loop,
then rebuild the projection.

## Optional native metadata

Site and Obsidian preserve their ordinary byte contract unless
`--knowledge-metadata summary` is selected explicitly. Enriched export and
check must use the same knowledge selection:

```bash
llm-wiki site export --wiki-dir docs/llm_wiki --out-dir site --format mkdocs --knowledge-metadata summary --knowledge-profile public-portable
llm-wiki site check --wiki-dir docs/llm_wiki --out-dir site --format mkdocs --link-mode http --knowledge-metadata summary --knowledge-profile public-portable
llm-wiki obsidian export --wiki-dir docs/llm_wiki --vault-dir vault --knowledge-metadata summary --knowledge-profile public-portable
llm-wiki obsidian check --wiki-dir docs/llm_wiki --vault-dir vault --knowledge-metadata summary --knowledge-profile public-portable
```

Command adapters load one validated snapshot-only view, including governance,
review, and any existing machine receipt. They do not scan source to claim live
freshness, so exported freshness is `not-evaluated`. A service caller may
project an already complete live-evaluated view; ordinary exporter and status
output never upgrades its snapshot.

Apply the availability, reason, freshness, fallback, bounds, and negative-fact
contract from [Qualified knowledge consumption](knowledge-consumption.md).
Absent knowledge permits only an explicitly selected and labeled ordinary
export. Rejected native state cannot be published as native metadata; an
ordinary fallback can proceed only when its canonical surface validates
independently. Never adopt governance as publication setup or repair.

## Privacy profiles and content review

`public-portable` is the public allowlist profile. It omits raw evidence,
source coordinates, local actors, producer/plugin detail, private repository
identity, non-parity hashes, environment detail, credentials, and absolute
paths. Public repository identity stays `unknown` unless trusted current
configuration supplies `--knowledge-public-repository-identity` and that value
exactly corroborates a committed `configured-public` identity.

Use `internal` only for a controlled internal destination. It can retain
additional safe repository, producer, actor, evidence, and extension detail,
but still excludes credentials, raw private remotes, raw plugin settings,
environment dumps, and machine-local paths.

The profile governs only added native metadata. Canonical Markdown bodies and
copied media remain publication input; the knowledge projection neither
redacts nor reviews them. Review prose, links, screenshots, and other media
separately before public publication. Stored Markdown, URLs, builder names,
and projection metadata are inert and cannot choose a profile or authorize a
build, fetch, plugin, checker, deployment, or Git action.

Both Site and Obsidian outputs are disposable views. Rebuild them from the
validated canonical snapshot rather than hand-editing projected front matter,
navigation, or typed-relationship sections.
