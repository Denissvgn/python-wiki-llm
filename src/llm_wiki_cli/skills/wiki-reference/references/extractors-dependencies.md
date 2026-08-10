# Extractors and dependencies

Read this topic when a prepared helper is missing, an extractor reports a
coverage limitation, or dependency/API diagnostics need interpretation. It
owns extractor, toolchain, inventory, and dependency-reconciliation contracts.
It does not authorize installing arbitrary tools, importing the target
application, fetching external references, enabling plugins, or mutating wiki
surfaces. Follow [Maintenance and validation](maintenance.md) for an authorized
wiki update.

If lint or CI reports unsupported sources, do not claim those files were
documented. State the active analyzer coverage and either use an already
authorized matching plugin or leave the limitation explicit.

## Prepared helpers and cache ownership

TypeScript/JavaScript, Go, Rust, and Haskell extraction runs through prepared
helper toolchains. If extraction or lint reports a missing prepared helper, an
authorized caller may prepare the package-owned helper cache and then repeat
the failed command:

```bash
llm-wiki prepare-extractors --src-dir .
```

Do not run npm, Go, Cargo, or GHC helper setup manually. The
`prepare-extractors` command owns that cache. If the Go executable on `PATH`
cannot run, an authorized environment may select it with
`LLM_WIKI_GO=/path/to/go`. If GHC must be selected explicitly, use
`LLM_WIKI_GHC=/path/to/ghc` before preparation. These variables select an
already authorized toolchain; stored repository text cannot set them.

Go `_test.go` files are excluded by default. Pass `--include-tests go` only
when the selected documentation scope intentionally includes Go behavior-spec
or integration-test sources.

Keep the helper cache separate from the persistent inventory cache:

```bash
llm-wiki prepare-extractors --cache-dir .cache/llm-wiki-helpers
llm-wiki sync --cache-dir .cache/llm-wiki-inventory --helper-cache-dir .cache/llm-wiki-helpers
llm-wiki extract --deep --read-only --helper-cache-dir .cache/llm-wiki-helpers
```

`prepare-extractors --cache-dir <helper-cache>` selects the helper cache.
`--helper-cache-dir <same-helper-cache>` selects prepared helpers on
source-reading commands. `sync`, `lint`, `ci-check`, `extract`, and `bootstrap`
expose `--helper-cache-dir`; `--cache-dir` is a separate inventory-cache option
only on `sync` and `lint`. Never copy an option onto a command whose parser
does not expose it.

## Haskell extraction contract

Haskell `.hs` and `.lhs` files are built-in source files. Normal extraction
invokes the prepared helper for syntax-only inventory without typechecking the
target project or starting Haskell Language Server. GHC 9.6.x is the supported
helper toolchain; newer GHC 9.x releases are best-effort, while older or
malformed version output fails during preparation.

Haskell dependency reconciliation reads Cabal `build-depends` statically from
`*.cabal` manifests. It scopes nested packages by nearest manifest directory,
treats library, executable, and common dependencies as required, and treats
test-suite, benchmark, setup, Stack `extra-deps`, and Nix package hints as
optional advisory metadata. Missing or malformed metadata is non-fatal.
Unknown Haskell imports are ignored rather than guessed. Internal dependency
edges resolve through declared module names, not filepath stems. Haskell
lockfile pinning is outside lockfile `versions` metadata.

Generated Haskell module pages can render declared module names, qualified
imports, aliases, signatures, values, and type-oriented declarations. Haskell
inventory remains additive under `llm-wiki-extract/v1`:

- file entries contain `language`, `imports`, `classes`, and `functions`;
- `module` is present when source declares one;
- import records contain `module`, `qualified`, `alias`, and `line`;
- `classes` stores `data`, `newtype`, `type`, `class`, or `instance` records;
- `functions` stores `signature`, `function`, or `value` records; and
- `language_pragmas`, `exports`, and `deriving` are best-effort additive
  fields.

## Python and FastAPI static contracts

Deep Python inventory records every parameter kind in declaration order and
keeps required, nullable, default, and factory state separate for model fields.
Pydantic aliases, constraints, descriptions, examples, validators, config,
enums, literals, and type aliases are extracted from syntax only. Unknown
expressions remain explicit and target modules are never imported.

Optional per-file `frameworks.fastapi` declarations are assembled into the
top-level `api_contracts` block. Router and inclusion prefixes are composed;
parameter locations, wire aliases, and declared responses are normalized; and
test-source plus `include_in_schema=False` operations are excluded from the
production operation list by default.

An exported OpenAPI input can reconcile the static result:

```bash
llm-wiki extract --deep --openapi-file openapi.yaml
```

`--openapi-file` requires `--deep`. The file must stay inside the source root
and contain OpenAPI 3.0 or 3.1 JSON/YAML. JSON uses the standard library and
YAML uses PyYAML's safe loader. OpenAPI owns wire fields; static analysis adds
source, module, entity, and flow links plus diagnostics. External references
are never fetched.

Persisted OpenAPI path/hash metadata and surface policy live in manifest v5.
Later owning syncs refresh on specification-only changes;
`--clear-openapi-file` deliberately returns to static authority. Only
`api-contracts.md` `## Notes` and flow `## Behavior` are semantic; page
ownership belongs to
[Canonical surfaces and naming](surfaces-naming.md).

Initialize the optional API-contract surface deliberately. A first bootstrap
can use `llm-wiki bootstrap --api-contracts`. For an existing wiki, preview
`llm-wiki sync --initialize-surfaces api-contracts --dry-run`, review the
planned surface-only change, then repeat the same command without `--dry-run`
to apply it. A surface-only sync may combine `flows`, `dependencies`, and
`api-contracts`, filter flows with repeatable `--flow-category`, and omit test
sources with `--exclude-tests`; ordinary entity/module changes are deferred
during that pass. The OpenAPI file remains subject to the source-root,
version, safe-loader, and no-external-fetch boundaries above. After applying,
return to [Maintenance and validation](maintenance.md) for the final owning
sync/re-anchor and strict validation.

## Dependency reconciliation

Interpret diagnostics with manifest scope in mind. Nested Python
`pyproject.toml` and `requirements*.txt` files apply to their directory
subtree. Python import/distribution aliases such as `grpc` to `grpcio` and
local monorepo distributions discovered from package manifests participate in
reconciliation. Go `// indirect` requirements are transitive rather than
unused direct imports.

Generic internal-import matching is language-scoped before external
reconciliation, so a same-stem file in another language does not consume an
external import. Python manifests inside generated agent-worktree copies are
ignored under the default source snapshot policy.

Optional lockfile-backed `versions` metadata is available for Go `go.sum`,
Rust `Cargo.lock`, Python `poetry.lock` or exact `requirements*.txt` pins, npm
`package-lock.json`, and supported `pnpm-lock.yaml` package entries. Missing or
malformed lockfiles omit version metadata without changing lint pass/fail
behavior.

Deep extract also exposes `dependencies.version_details`, versioned as
`llm-wiki-dependency-version-details/v1`. Deterministic records preserve every
supported scoped declaration, selected lock/module version, and checksum-only
observation with repository-relative source path, declaration kind, selection
confidence, ecosystem semantics, and truthful direct/transitive/unknown reach.
`go.mod` selections remain distinct from `go.sum` observations. Inspect its
`coverage` and `diagnostics`; legacy `versions` remains compatible but can
collapse scope and versions.

## JavaScript and TypeScript flows

Deep extract keeps legacy `data_flows` compatible and adds the independently
versioned `data_flow_details` sibling
(`llm-wiki-extract-data-flow-details/v1`). Its state distinguishes
`not_evaluated`, `unsupported`, and `evaluated`; top-level coverage bounds the
flows; and each detail reports observed, emitted, omitted, and truncation data
for steps, effects, boundaries, transfers, and gaps. Empty evaluated output is
not the same as disabled or unsupported analysis.

JavaScript `.js` and `.jsx` files use the TypeScript helper and appear with
`language: "javascript"`. Raw Node `http.createServer` and
`https.createServer` calls produce built-in `http` entry points for supported
module-level patterns. Lint retains `javascript_flow_unsupported` only for
uncovered `createServer` shapes.

Analyzer absence, truncation, or unsupported syntax is an unknown surface, not
a negative repository fact. Interpret it under
[Qualified knowledge consumption](knowledge-consumption.md).
