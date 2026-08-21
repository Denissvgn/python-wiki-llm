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
in. An exact helper-cache key binds the runner platform, locked toolchains,
selected helper sources and locks, helper-cache contract, CLI version, and
immutable action ref. Preparation always revalidates restored state; pull
requests restore but never save cache entries. The action then runs the strict
integrity check with advisory native-drift diagnostics, verifies a clean
worktree, and uploads a fixed, allowlisted set of reports and cache measurements
even when validation fails. Project-local Python plugins are disabled, so
pull-request content is never imported or executed; projects that depend on
trusted extractor, generation, or lint plugins need a separately reviewed
trusted workflow. Installation does not bootstrap or synchronize the wiki,
install hooks, add secrets, push changes, or alter branch protection.

The JSON evidence uses the `llm-wiki-ci-check/v1` envelope. Its nested
`llm-wiki-doctor/v1` projection is composed from the same lint evaluation, so
the summary can present knowledge health without a duplicate source scan. The
top-level `ok` value, blocking issue count, and original `ci-check` exit remain
authoritative.

### Manual convergence observation

`.github/workflows/llm-wiki-convergence.yml` runs one real, plugin-disabled
sync from an exact credential-free checkout of this repository's default
branch. It requires clean pre-sync state and treats any post-sync wiki change
or unrelated worktree change as a failure. The fixed artifact records complete
pre/post wiki status, full post-sync status, the tracked wiki diff, the sync
log, and a versioned hash receipt; only a bounded preview reaches the job
summary. This manually dispatched observation never uses `--dry-run` or
`--force` and never replaces the separate blocking integrity gate.

### Strict doctor dashboard

`integrations/github-action/action.yml` defines a separately named diagnostic
knowledge-health dashboard. It does not run or replace the blocking
`llm-wiki ci-check` gate, general wiki integrity, trusted plugin validation, or
team-owned review policy. The action:

1. installs this repository's Python package from the same immutable action
   checkout;
2. uses default source-selection discovery to plan and prepare detected
   TypeScript/JavaScript, Go, Rust, or Haskell extractor helpers with the
   release's checksum-verified toolchains;
3. runs `llm-wiki doctor` with the configured source root, wiki path, source
   selection, and strictness;
4. captures the documented doctor exit code and JSON report; and
5. invokes `render_summary.py` to validate the complete report, publish a
   bounded job summary, expose the status output, apply the selected `fail-on`
   threshold, and write a hash-bound dashboard receipt.

The action reserves isolated runner-temporary cache, toolchain, and evidence
directories.
Its artifact contains only the doctor JSON, dashboard receipt, extractor plan,
and helper-preparation log. A validated `evidence-id` keeps repeated action
invocations in one job separate; unsafe identifiers or occupied paths fail
before artifact upload. The repository's manually dispatched dashboard
workflow is read-only and has no scheduled, pull-request, or push trigger.
Protected branches should require the exact `LLM Wiki integrity` context from
the full gate, never this diagnostic workflow.

The selected source snapshot includes both action descriptors, but the current
infrastructure classifiers do not model GitHub composite-action descriptors.
The scan therefore records them as unsupported YAML and produces zero supported
infrastructure pages for this repository. The Python summary renderer is
analyzed normally; see [render_summary](../modules/render_summary.md) and its
[process flow](../flows/process-render_summary.md).

The action pins its GitHub dependencies by commit and accepts only `unhealthy`
or `degraded` as failure thresholds. Its renderer rejects unreadable JSON,
missing required fields, unsupported states, inconsistent strictness, status,
or exit-code values, and malformed nested health sections before writing the
summary. Human disclosure cells are escaped and clipped before rendering.

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
