# Integrations

The repository ships two GitHub composite actions and an Obsidian plugin. They
share the CLI contracts but have different build and documentation boundaries.

## GitHub Actions

### Full integrity gate

`integrations/wiki-integrity/action.yml` runs the same read-only integrity gate
used for this repository. Install a dedicated workflow into an initialized
project with an immutable release commit:

```bash
llm-wiki install-ci --action-ref "$RELEASE_COMMIT_SHA"
```

Set `RELEASE_COMMIT_SHA` to the complete 40-character commit published for the
release; abbreviated SHAs, tags, and branches are rejected.

The installer writes only `.github/workflows/llm-wiki-integrity.yml`. It is an
exact no-op when the generated workflow is current and safely updates an older
unmodified workflow installed by the command. An unmanaged or locally modified
file is preserved unless `--force` is explicit. The command also supports a
write-free `--dry-run` preview. The generated workflow grants only
`contents: read`, checks out without persisted credentials, and invokes the
reusable action at the supplied full commit rather than a mutable branch or
tag. `llm-wiki uninstall` removes the workflow only while its managed content
remains unmodified; project-owned changes are preserved.
See the [install-ci flow](../flows/cli-install-ci.md) and
[ci_installer](../modules/ci_installer.md) for the command boundary and
ownership checks.

The action installs the CLI from its own immutable checkout and discovers
helper languages through default source-selection discovery, using
`.llm-wiki/source-selection.json` when present. It installs checksum-verified
toolchains in runner-temporary storage only when required and prepares detected
TypeScript/JavaScript, Go, Rust, and Haskell helpers; Python extraction is built
in. It then runs the strict integrity check with advisory native-drift
diagnostics, verifies a clean worktree, and uploads a fixed, allowlisted set of
reports even when validation fails. Project-local Python plugins are disabled,
so pull-request content is never imported or executed; projects that depend on
trusted extractor, generation, or lint plugins need a separately reviewed
trusted workflow. Installation does not bootstrap or synchronize the wiki,
install hooks, add secrets, push changes, or alter branch protection.

### Context-health gate

`integrations/github-action/action.yml` defines the context-health gate. It:

1. installs this repository's Python package;
2. runs `llm-wiki doctor` with the configured source root, wiki path, source
   selection, and strictness;
3. captures the documented doctor exit code and JSON report; and
4. invokes `render_summary.py` to validate the complete report, publish a job
   summary, expose the status output, and apply the selected `fail-on`
   threshold.

The selected source snapshot includes both action descriptors, but the current
infrastructure classifiers do not model GitHub composite-action descriptors.
The scan therefore records them as unsupported YAML and produces zero supported
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
