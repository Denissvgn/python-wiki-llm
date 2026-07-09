# wiki-reference reference

Supporting detail for [SKILL.md](SKILL.md). Each section stands alone; read
the one that matches the command or diagnostic in front of you. Commands
assume the project root; substitute the project's configured `--wiki-dir`
(default `docs/llm_wiki`) where a command takes one.

## Extractor helpers and toolchains

- TypeScript/JavaScript, Go, Rust, and Haskell extraction runs through
  prepared helper toolchains. If extraction or lint reports a missing prepared
  helper, run `llm-wiki prepare-extractors --src-dir .` once and repeat the
  failed command.
- Do not run npm/go/cargo/ghc helper setup manually; `prepare-extractors`
  owns that cache.
- If the Go executable on `PATH` cannot run, set `LLM_WIKI_GO=/path/to/go`
  and retry. If GHC needs to be selected explicitly, set
  `LLM_WIKI_GHC=/path/to/ghc` before preparing extractors.
- Go `_test.go` files are excluded by default; pass `--include-tests go` to
  document Go behavior-spec or integration-test files intentionally.
- To keep prepared helpers separate from the inventory cache, use separate
  paths:

  ```
  llm-wiki prepare-extractors --cache-dir .cache/llm-wiki-helpers
  llm-wiki sync --cache-dir .cache/llm-wiki-inventory --helper-cache-dir .cache/llm-wiki-helpers
  ```

  On `sync`, `lint`, `ci-check`, and `extract`, `--helper-cache-dir` selects
  prepared TypeScript/JavaScript/Go/Rust/Haskell helpers; `--cache-dir` controls only
  `llm-wiki-inventory-cache.json`.

## Haskell extraction contract

Haskell `.hs` and `.lhs` files are registered as built-in source files, and
normal CLI extraction invokes the prepared Haskell helper for syntax-only
inventory. The helper emits syntax-only Haskell inventory without
typechecking the target project and does not start Haskell Language Server.
GHC 9.6.x is the supported Haskell helper toolchain for this release; newer
GHC 9.x releases are best-effort, and older or malformed GHC version output
fails during helper preparation.

Haskell dependency reconciliation reads Cabal `build-depends` statically from
`*.cabal` manifests, scopes nested Cabal packages by nearest manifest
directory, treats library/executable/common dependencies as required, treats
test-suite, benchmark, setup, Stack `extra-deps` and Nix package hints as
optional advisory metadata, and keeps missing or malformed metadata
non-fatal. Unknown Haskell imports are ignored rather than guessed. Haskell
internal dependency edges resolve through declared module names from
inventory entries rather than filepath stems. Haskell lockfile pinning is
intentionally out of scope for lockfile `versions` metadata.

Generated Haskell module pages render declared module names, qualified
imports, aliases, signatures, values, and type-oriented declarations when
present. Haskell inventory stays additive under `llm-wiki-extract/v1`:
Haskell file entries include `language`, `imports`, `classes`, and
`functions`; `module` is present when the source declares one. Haskell import
records include `module`, `qualified`, `alias`, and `line`. `classes` stores
type-oriented declarations with `kind` set to
`data`, `newtype`, `type`, `class`, or `instance`; `functions` stores
top-level signatures, functions, and values with `kind` set to
`signature`, `function`, or `value`. Optional Haskell-specific fields such
as `language_pragmas`, `exports`, and `deriving` are best-effort additive
metadata.

## Dependency reconciliation

- Interpret monorepo dependency diagnostics with manifest scope in mind:
  nested Python `pyproject.toml` and `requirements*.txt` files apply to their
  directory subtree. Python import/distribution aliases such as `grpc` ->
  `grpcio` and local monorepo distributions discovered from package manifests
  participate in reconciliation, while Go `// indirect` requirements are
  transitive rather than unused direct imports.
- Generic internal import matching is language-scoped before external
  dependency reconciliation, so same-stem files in other languages do not
  consume external imports. Python manifests inside generated agent worktree
  copies are ignored during reconciliation, matching the default source
  snapshot policy.
- Dependency reconciliation may expose optional lockfile-backed `versions`
  metadata for Go `go.sum`, Rust `Cargo.lock`, Python `poetry.lock` or exact
  `requirements*.txt` pins, npm `package-lock.json`, and supported
  `pnpm-lock.yaml` package entries. Missing or malformed lockfiles omit
  version metadata without changing lint pass/fail behavior.

## JavaScript and TypeScript flows

- JavaScript `.js` and `.jsx` files use the TypeScript extractor helper and
  appear in inventory with `language: "javascript"` when extracted.
- Raw Node `http.createServer` and `https.createServer` calls create built-in
  `http` entry points for supported module-level server patterns. Lint keeps
  `javascript_flow_unsupported` only for uncovered `createServer` patterns
  outside that raw Node shape.

## Static-site export

Use `llm-wiki site export|check` or the site export service to build and
validate plain, MkDocs-compatible, or Docusaurus-compatible Markdown as
generated distribution output. The default `--profile reference` mirror
preserves the agent/reference wiki shape. `--profile user --site-name ...` is
an opt-in human-docs profile that writes a concise landing page, expects
authored guide pages, and moves the exhaustive generated inventory to
`generated-reference.md`. MkDocs exports include generated `llm_wiki` front
matter and `mkdocs.yml` navigation; `--file-friendly` is MkDocs-only and
writes direct-file-safe configuration plus a theme override for local disk
handoffs. Docusaurus exports include generated front matter and sidebars.json.

Generated static-site labels may include page-id context when duplicate
Markdown headings would otherwise make navigation ambiguous. Mermaid fences
are preserved for the site's configured Markdown/Mermaid renderer. The
static-site checker validates missing pages, local Markdown links, generated
front matter metadata, duplicate Docusaurus ids, and output path containment
without invoking external builders. When `--built-site-dir` is supplied it
also parses built HTML links; `--link-mode http` accepts hosted MkDocs
directory URLs, while `--link-mode file` requires direct `.html` targets.
User-profile checks add quality gates for default site names, missing guides,
oversized landing pages, and placeholder text in primary human docs.
Warning-only findings do not fail the check.

## `llm-wiki context` for large codebases

`context` produces a token-budgeted, priority-ranked snapshot of the codebase
— ideal for feeding into an LLM prompt when the full extract output is too
large:

```
llm-wiki context --budget <TOKENS> --src-dir . --format markdown --focus changed
```

- **`--budget`** (required): maximum token count for the output.
- **`--focus changed`** (default): prioritises files from the last git commit.
  Changed files get full detail, their 1-hop import neighbours get slim
  detail, everything else gets names only. Use `--focus all` to treat every
  file equally.
- **`--format`**: `json` (default, structured) or `markdown` (human-readable
  with tier-labelled sections).
- **When to use:** before starting a complex task on a large project, pass the
  context output to the agent so it has an accurate, right-sized view of the
  codebase without exceeding the context window.
