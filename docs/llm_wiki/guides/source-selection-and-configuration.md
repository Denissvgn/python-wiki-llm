# Source Selection and Configuration

Source selection is the repository boundary shared by extraction, generation,
validation, context, review, and MCP reads. Define it once and pass the same
profile to every source-reading command.

## Default discovery

Without a profile, LLM Wiki walks the selected `--src-dir`, honors
`.gitignore`, omits dependency and build directories, and classifies supported
source, package, Docker, Compose, and targeted YAML files. Source paths in
generated output are POSIX paths relative to that root.

For a source tree outside the current workspace, opt in explicitly:

```bash
llm-wiki bootstrap \
  --src-dir /path/to/project \
  --wiki-dir docs/llm_wiki \
  --allow-external-src
```

The wiki target remains constrained to the current project. Do not use
`--allow-external-src` as a general path-policy bypass.

## Commit a narrow profile

Place the default profile at `.llm-wiki/source-selection.json` in the source
root:

```json
{
  "schema_version": "llm-wiki-source-selection/v1",
  "include": ["pyproject.toml", "src", "integrations/public"],
  "exclude": ["src/private"]
}
```

Entries are literal files or directory roots, not globs. They use canonical
repository-relative POSIX paths. Excludes must be strict descendants of an
included root and take precedence. Absolute paths, traversal, backslashes,
overlapping roots, case collisions, selected links, and an empty effective
selection are rejected.

Use a non-default profile explicitly:

```bash
llm-wiki sync \
  --src-dir . \
  --wiki-dir docs/llm_wiki \
  --source-selection config/public-sources.json
```

Carry that exact argument through `prepare-extractors`, `bootstrap`, `sync`,
`lint`, `ci-check`, `context`, `review`, `generate-prompt`, and `mcp`. A managed
wiki records the profile and its controlling inputs; readers ask for sync when
the live selection no longer matches the committed wiki.

## Extractor helpers and caches

Python, Docker, Compose, and targeted YAML analysis use built-in support.
TypeScript/JavaScript, Go, Rust, and Haskell require explicitly prepared helper
dependencies or binaries:

```bash
llm-wiki prepare-extractors --src-dir .
```

For `prepare-extractors`, `--cache-dir` selects the helper build root. Pass
that same root to consuming commands with `--helper-cache-dir`. Commands that
offer a separate persistent inventory cache, such as `sync` and `lint`, use
their own `--cache-dir` option for `llm-wiki-inventory-cache.json`.
Preparation is deliberate: normal extraction, sync, and validation do not
install toolchains or build helpers automatically.

## Selection changes

Treat a profile edit like a source-boundary change. Preview the result, verify
that retired pages are expected, and then apply it:

```bash
llm-wiki sync --dry-run --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki
```

See [source_selection](../modules/source_selection.md) for policy validation and
[source_snapshot](../modules/source_snapshot.md) for shared tree discovery.
