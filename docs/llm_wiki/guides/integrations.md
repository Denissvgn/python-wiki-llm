# Integrations

The repository ships a GitHub composite action and an Obsidian plugin. They
share the CLI contracts but have different build and documentation boundaries.

## GitHub Action

`integrations/github-action/action.yml` defines the context-health gate. It:

1. installs this repository's Python package;
2. runs `llm-wiki doctor` with the configured source root, wiki path, source
   selection, and strictness;
3. captures the documented doctor exit code and JSON report; and
4. invokes `render_summary.py` to validate the complete report, publish a job
   summary, expose the status output, and apply the selected `fail-on`
   threshold.

The selected source snapshot includes `action.yml`, but the current
infrastructure classifiers do not model GitHub composite-action descriptors.
The scan therefore records it as unsupported YAML and produces zero supported
infrastructure pages for this repository. The Python summary renderer is
analyzed normally; see [render_summary](../modules/render_summary.md) and its
[process flow](../flows/process-render_summary.md).

The action pins `actions/setup-python` by commit and accepts only `unhealthy`
or `degraded` as failure thresholds. Its renderer rejects unreadable JSON,
missing required fields, unsupported states, inconsistent status and exit-code
values, and malformed nested health sections before writing the summary.

## Obsidian plugin

`integrations/obsidian/llm-wiki/src/main.ts` is the authoring source. It adds
commands for export, sync, lint, status, bounded context copy, and source
navigation, and launches the CLI with argument arrays through `execFile`.
Settings cover the command path, project and wiki roots, vault and sidecar-note
locations, context budget, and source-URI template.

`integrations/obsidian/llm-wiki/main.js` is the compiled CommonJS plugin loaded
by Obsidian. Treat it as a distribution artifact: change the TypeScript source
and rebuild the bundle rather than maintaining separate behavior in the
generated JavaScript.

Use these pages to follow each layer:

- [src_main](../modules/src_main.md) — TypeScript plugin source.
- [llm-wiki_main](../modules/llm-wiki_main.md) — compiled plugin bundle.
- [obsidian_cmd](../modules/obsidian_cmd.md) — CLI action dispatch.
- [obsidian](../modules/obsidian.md) — mirror generation, validation, link
  conversion, sidecar notes, and plugin installation.
- [cli-obsidian](../flows/cli-obsidian.md) — generated command flow.

The canonical wiki remains the source of truth. Obsidian output is a derived
mirror with frontmatter, wikilinks, related links, and optional portable
knowledge metadata; author changes belong in `docs/llm_wiki`, not the mirror.
