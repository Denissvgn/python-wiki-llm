# Manual Functionality Completeness Test Plan

Date: 2026-06-28

Product under test: `llm-wiki`

Purpose: provide a reusable manual test plan for evaluating whether `llm-wiki` can generate, validate, and export complete documentation for many project shapes, not just one happy-path repository.

## Use This Plan When

- validating a new language, framework, extractor, command option, or generated wiki surface;
- testing a real customer-style repository before declaring functionality complete;
- comparing generated documentation quality across project types;
- turning manual findings into backlog items with reproducible evidence.

The plan is intentionally manual and evidence-oriented. A run is complete only when the tester records commands, exits, artifact paths, counts, representative spot checks, failures, and follow-up backlog items.

## Project Coverage Matrix

Select at least one project from each applicable category. For release-quality functionality analysis, prefer real repositories over synthetic fixtures.

| Category | Include when | Required coverage |
|---|---|---|
| Python package or service | Python is a primary language | modules, classes, functions, imports, requirements/pyproject dependencies, tests excluded/included as intended |
| TypeScript or JavaScript app | frontend or Node code exists | TS/JS source discovery, React/TSX where present, route/user-flow detection, package dependencies |
| Go module | Go code exists | helper preparation, production files, optional `_test.go` inclusion, `go.mod` dependency resolution, stdlib collision checks |
| Rust crate | Rust code exists | helper preparation, Cargo project discovery, modules/functions/types, dependency extraction where supported |
| Haskell package or subsystem | `.hs` or `.lhs` files exist | explicit helper preparation, module declarations, imports, functions, declarations, declared-module dependency edges |
| Mixed-language monorepo | multiple languages or nested services | per-language inventory counts, nested manifest scoping, cross-service dependency and navigation behavior |
| Infrastructure-heavy project | Docker, Compose, workflows, deployment files exist | infrastructure pages, workflow pages, dependency/load-order pages, static-site export compatibility |
| Docs-only or sparse-code project | little or no supported source exists | graceful no-source behavior, unsupported-source diagnostics, no false success claims |
| External-source workflow | source root is outside runner cwd | `--allow-external-src` paths for read commands, write guards for wiki/report outputs |
| Plugin or unsupported-language project | language support is plugin-backed or advisory only | plugin discovery, unsupported-source diagnostics, no blocking issues unless strict policy requires it |

## Run Record Template

Create a per-project report before running commands. Use this skeleton:

```markdown
# <Project Name> Manual Functionality Completeness Run

Date:
Project:
Project commit:
llm-wiki commit:
Workspace:
Tester:

## Project Shape

- Languages:
- Frameworks/services:
- Package manifests:
- Infrastructure/workflow files:
- Source root strategy: local / external
- Helper languages required:

## Command Results

| Step | Command | Exit | Artifact | Result |
|---|---|---:|---|---|

## Inventory Counts

| Language | Files | Notes |
|---|---:|---|

## Generated Surface Counts

| Surface | Count | Notes |
|---|---:|---|

## Spot Checks

| Area | File/page checked | Expected | Result |
|---|---|---|---|

## Findings

| ID | Severity | Area | Evidence | Suggested backlog item |
|---|---|---|---|---|
```

## Environment Setup

Use the project virtual environment for every Python command:

```bash
.venv/bin/python --version
.venv/bin/python -m llm_wiki_cli.cli --help
```

Record external helper versions when used:

```bash
go version
rustc --version
ghc --numeric-version
node --version
npm --version
```

For mixed-language runs, record any helper binary overrides explicitly when
the default `PATH` lookup is not enough:

```bash
export LLM_WIKI_GO=<path-to-go>
export LLM_WIKI_GHC=<path-to-ghc>
```

Use fresh disposable workspaces for external-source dogfood. Keep helper cache
and inventory cache separate:

```bash
PROJECT=<path-to-llm-wiki-checkout>
RUNNER=<path-to-empty-runner-workspace>
mkdir -p "$RUNNER/logs" "$RUNNER/helper-cache" "$RUNNER/inventory-cache"
cd "$RUNNER"
```

Run this plan serially: never overlap `context`, full tests, coverage, builds,
browser suites, sync, lint, or CI. The `--jobs auto` commands in Sections 5 and
6 are explicit parallel-determinism tests and may run only in this disposable,
isolated terminal or on a capacity-reserved runner. In an interactive IDE,
replace them with `--jobs 1`. If ENOSPC, inotify, file-descriptor, severe
swapping, or editor-responsiveness failures occur, stop without retrying the
burst and mark remaining gates inconclusive until capacity is recovered.

## Core Command Path

Run the same command path for every project unless a category explicitly does not apply.

### 1. Source Snapshot And Summary Extraction

Goal: prove the project shape is discovered correctly before generating docs.

```bash
"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli extract \
  --src-dir <source-root> \
  --allow-external-src \
  --read-only \
  --summary \
  --output logs/01_extract_summary.json
```

Record:

- total file count;
- per-language file counts;
- unsupported-source diagnostics;
- whether tests are excluded by default for languages with test opt-ins;
- whether source paths are stable, relative, and portable.

Failure signals:

- known source files are missing;
- generated paths are absolute when they should be project-relative;
- unsupported-source diagnostics hide a language that should be supported;
- helper-backed languages fail without a clear preparation message.

### 2. Helper Preparation

Goal: prove helper-backed extractors are explicit and reproducible.

```bash
"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli prepare-extractors \
  --src-dir <local-source-or-copy> \
  --cache-dir helper-cache \
  --language go \
  --language rust \
  --language haskell
```

Adjust `--language` to only the helpers required by the project. If the source root is external and `prepare-extractors` does not support external roots, use a trusted local copy or a small local helper-preparation fixture and record that choice.

Record:

- helper cache path;
- prepared helper languages;
- binary paths;
- expected failure output when a required helper is missing.

Failure signals:

- normal extraction silently builds helpers;
- helper lookup uses the inventory cache by mistake;
- helper failures lack clear user remediation text;
- helper paths assume Unix-only separators or binary names.

### 3. Deep Extraction

Goal: capture the complete inventory contract for supported project languages.

```bash
"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli extract \
  --src-dir <source-root> \
  --allow-external-src \
  --read-only \
  --deep \
  --helper-cache-dir helper-cache \
  --output logs/02_extract_deep.json
```

For each supported language, spot-check representative inventory entries:

- source file path;
- module/package name;
- functions or methods;
- classes, structs, interfaces, types, declarations, or equivalent entities;
- imports;
- source spans;
- language-specific additive fields;
- error fields and unsupported-source sections.

Failure signals:

- entity names collide without disambiguation;
- nested package roots lose declared module identity;
- imports are extracted but cannot later resolve to dependency edges;
- language-specific pages later show wording from another language.

### 4. Bootstrap Wiki Generation

Goal: prove a complete wiki can be generated from a real source tree.

```bash
"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli bootstrap \
  --src-dir <source-root> \
  --wiki-dir wiki-external \
  --source-adapter \
  --allow-external-src \
  --helper-cache-dir helper-cache \
  --format json
```

Record:

- source file count;
- entity count;
- module count;
- flow count;
- infrastructure count;
- architecture/dependency page count;
- manifest path;
- created/updated/skipped file counts.

Spot-check:

- `index.md` links all major surfaces;
- module pages exist for representative files in every language;
- entity pages use stable page names;
- source links and module links are relative;
- generated sections are labeled as generated;
- no page has a blank or broken diagram fence.

Failure signals:

- bootstrap can read an external source root but writes outside the runner;
- generated pages omit a supported language;
- relationship or declaration wording is language-inappropriate;
- duplicate page names overwrite each other.

### 5. Sync From Same Source

Goal: prove generated output is stable, cache behavior is correct, and the
isolated `auto` request reports its actual concurrency before work begins.

```bash
"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli sync \
  --src-dir <source-root> \
  --wiki-dir wiki-external \
  --allow-external-src \
  --helper-cache-dir helper-cache \
  --cache-dir inventory-cache \
  --cache-stats \
  --jobs auto
```

Record:

- whether sync reports "up to date";
- cache status, hits, misses, changed, stale, deleted;
- inventory cache path;
- helper cache path;
- the single stderr extractor-plan line, including requested, resolved,
  eligible, effective, parallel, sequential, and cache-elided values;
- generated file changes, if any.

Failure signals:

- sync rewrites unchanged generated files;
- `--cache-dir` breaks helper lookup;
- external source validation differs from bootstrap;
- the extractor plan is missing, duplicated, or appears after extraction work;
- parallel jobs change generated output.

### 6. Lint And CI Check

Goal: prove validation works against the same source/wiki pair, distinguishes
blocking issues from advisory diagnostics, and preserves parseable JSON while
exposing additive execution metadata.

The `auto` commands below are explicit parallel-determinism checks for this
isolated or capacity-reserved runner; use `--jobs 1` everywhere else.

```bash
"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli lint \
  --src-dir <source-root> \
  --wiki-dir wiki-external \
  --allow-external-src \
  --helper-cache-dir helper-cache \
  --cache-dir inventory-cache \
  --cache-stats \
  --jobs auto \
  --strict \
  --profile

"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli ci-check \
  --src-dir <source-root> \
  --wiki-dir wiki-external \
  --allow-external-src \
  --helper-cache-dir helper-cache \
  --jobs auto \
  --format json \
  --report logs/ci_report.json
```

Record:

- `ok` value;
- issue count;
- diagnostic count by category;
- strict-mode behavior;
- profile phase timings;
- a single pre-execution stderr plan line for each command;
- `execution.extractor_jobs` values in lint profile and CI JSON, including the
  raw `requested_jobs` value and resolved/effective concurrency;
- report path and size.

Failure signals:

- external `lint` or `ci-check` rejects a trusted source root with opt-in;
- `--allow-external-src` also relaxes wiki/report write boundaries;
- stdout contains progress text in addition to the single JSON object;
- profile or CI JSON omits execution metadata, while default/MCP report shapes
  gain it unexpectedly;
- unsupported-source diagnostics block healthy projects unexpectedly;
- diagnostics are too vague to turn into backlog work.

### 7. Dependency And Load-Order Pages

Goal: prove dependency analysis is useful and not materially noisy.

Inspect:

```bash
wiki-external/dependencies.md
wiki-external/load-order.md
```

Check:

- internal edges use real package/module identity, not only filepath stems;
- external imports are not converted into internal nodes;
- standard-library imports do not collide with local files;
- nested manifests only apply to their own package scope;
- declared-but-unused and imported-but-undeclared diagnostics are plausible;
- cycles are listed with enough context to investigate.

Language-specific checks:

- Python package directories resolve through `__init__.py` where applicable;
- Go imports use module path context from `go.mod`;
- Haskell imports resolve by declared module name;
- Rust crate/module edges match Cargo source layout where supported;
- TypeScript path aliases or framework conventions are either resolved or reported as clear limitations.

### 8. Flow And Data-Flow Pages

Goal: prove user-facing or process flows are discovered and rendered usefully.

Inspect representative pages under:

```bash
wiki-external/flows/
```

Check:

- HTTP, CLI, worker, process, or test flows are detected where expected;
- flow steps are ordered and tied to source locations;
- data-flow gaps are surfaced as diagnostics, not hidden;
- generated diagrams are non-empty or replaced by explicit no-data text;
- large flows are summarized without losing the most important steps.

Failure signals:

- top-level command modules are missed;
- framework handlers are ignored;
- diagrams are empty but still rendered as diagram fences;
- data-flow diagnostics do not identify a target flow.

### 9. Infrastructure And Workflow Pages

Goal: prove non-source project surfaces are represented.

Inspect:

```bash
wiki-external/infrastructure/
wiki-external/workflows/
```

Check:

- Dockerfiles and Compose files produce pages;
- CI workflow files produce pages when present;
- services, ports, build contexts, images, dependencies, and commands are summarized accurately;
- infra pages link back to related modules or docs where supported.

Failure signals:

- generated documentation ignores deployment-critical files;
- nested Compose or Docker paths collide;
- infrastructure pages are generated but unlinked.

### 10. Static Site Export

Goal: prove generated wiki content can be published without broken navigation.

```bash
"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli site export \
  --wiki-dir wiki-external \
  --out-dir site-mkdocs \
  --format mkdocs \
  --output-format json

"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-mkdocs \
  --output-format json

"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli site export \
  --wiki-dir wiki-external \
  --out-dir site-docusaurus \
  --format docusaurus \
  --output-format json

"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli site check \
  --wiki-dir wiki-external \
  --out-dir site-docusaurus \
  --output-format json
```

Record:

- export `ok`;
- check `ok`;
- page counts;
- issue counts;
- warning counts;
- duplicate MkDocs nav labels;
- duplicate Docusaurus titles/sidebar labels;
- broken link count.

Failure signals:

- two pages with the same H1 produce indistinguishable nav labels;
- Docusaurus front matter differs from sidebar labels;
- generated links pass in wiki but fail after export;
- static-site page counts differ unexpectedly from wiki page counts.

## Language And Project-Specific Manual Checks

### Python

- Verify modules from package directories, loose scripts, and nested packages.
- Check class and function pages for accurate source line links.
- Confirm imports from the same package do not become undeclared dependencies.
- Confirm dependencies from `requirements.txt`, `pyproject.toml`, or setup files are scoped to the correct project or nested package.
- If tests are present, record whether they are included by default.

### TypeScript And JavaScript

- Verify `.ts`, `.tsx`, `.js`, and `.jsx` handling where applicable.
- Spot-check React components, route handlers, services, and utilities.
- Check package dependency extraction from the nearest relevant manifest.
- Record path-alias limitations if imports do not resolve.
- Confirm generated pages do not collapse components with the same display name.

### Go

- Prepare the Go helper explicitly.
- Confirm default extraction excludes `_test.go` files.
- Run an opt-in extraction with `--include-tests go` and record delta counts.
- Spot-check imports that share names with local files, especially standard library names such as `context`.
- Confirm internal edges use `go.mod` module path context.

### Rust

- Prepare the Rust helper explicitly.
- Spot-check `lib.rs`, `main.rs`, module files, structs, enums, traits, and impl blocks where supported.
- Check Cargo manifest discovery and nested crate behavior.
- Record unsupported or partial surfaces as diagnostics, not silent omissions.

### Haskell

- Prepare the Haskell helper explicitly.
- Confirm missing-helper extraction fails with a clear `prepare-extractors --language haskell` message.
- Spot-check declared module names, imports, functions, data declarations, type aliases, type classes, and instances.
- Confirm internal dependency edges resolve by declared module name.
- Confirm entity relationship summaries use Haskell wording such as `Declaration kind`, not Python-specific columns.
- Confirm external imports such as package modules do not become internal wiki nodes.

### Unsupported Or Plugin Languages

- Confirm unsupported source files are visible in diagnostics.
- Confirm plugin-supported languages do not also appear as unsupported.
- Record whether the project still has enough generated documentation to be useful.
- Do not mark a language complete from absence of errors alone.

## External Source And Path Policy Checks

Run at least one local-source and one external-source workflow when validating command behavior.

Expected behavior:

- source-read commands accept external roots only with `--allow-external-src`;
- wiki output directories remain constrained to the runner project root;
- report paths remain explicit caller-selected outputs;
- source paths in generated files are stable and relative where appropriate;
- commands fail closed before doing expensive work when external-source opt-in is missing.

Negative checks:

```bash
"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli lint \
  --src-dir <external-source-root> \
  --wiki-dir wiki-external \
  --strict

"$PROJECT/.venv/bin/python" -m llm_wiki_cli.cli sync \
  --src-dir <external-source-root> \
  --wiki-dir <path-outside-runner>/outside-wiki \
  --allow-external-src
```

Expected result:

- first command fails closed for external source without opt-in;
- second command fails closed for wiki output outside the project root.

## Completeness Scoring

Score each area as `Pass`, `Partial`, `Fail`, or `Not applicable`.

| Area | Pass criteria |
|---|---|
| Source discovery | Expected source files appear with correct language and path normalization |
| Helper lifecycle | Helpers are explicit, cached separately, and fail clearly when missing |
| Inventory richness | Representative files expose modules, entities, imports, spans, and language-specific metadata |
| Wiki generation | Modules/entities/flows/infra/architecture pages are generated and linked |
| Incremental sync | Repeated sync is stable and cache behavior is explainable |
| Lint/CI | Strict validation passes or reports actionable issues/diagnostics |
| Dependencies | Internal/external edges are accurate enough to guide users |
| Flow/data-flow | Important user/process flows appear with useful diagrams or explicit limitations |
| Static export | MkDocs and Docusaurus exports/checks pass with clear navigation labels |
| External paths | Source-read opt-ins and write guards behave consistently |
| Cross-platform readiness | Commands and generated paths avoid Unix-only assumptions where possible |
| Documentation usefulness | A new contributor can navigate generated output to understand the project |

Overall classification:

- `Complete`: every applicable area is `Pass`, and diagnostics are expected or already triaged.
- `Functionally complete with known limitations`: no blocking issues, but one or more `Partial` areas need documented follow-up.
- `Not complete`: any `Fail` area blocks trustworthy documentation generation for this project type.

## Finding Template

Use this shape for each weakness:

```markdown
### FINDING-<N>: <short title>

Severity: P0 / P1 / P2 / P3
Area:
Project:
Command:
Artifact:

Expected:
Actual:
Evidence:
Root cause hypothesis:
Suggested backlog item:
Acceptance:
```

Severity guidance:

- `P0`: command cannot complete a core workflow for the project type.
- `P1`: generated output is materially misleading or misses a major supported language/surface.
- `P2`: generated output is useful but noisy, incomplete, or confusing.
- `P3`: polish, wording, or documentation improvement.

## Closure Requirements

Do not close a manual functionality completeness run until all of the following are true:

- command table records every command, exit code, and artifact path;
- source and generated surface counts are recorded;
- at least one representative page per language/surface was spot-checked;
- lint and CI diagnostics are classified as expected, backlog-worthy, or environment-only;
- static-site export/check results are recorded when generated wiki content is intended for publication;
- all findings are converted into backlog items or explicitly marked out of scope;
- the final report distinguishes real project confirmation from unit-test coverage;
- any committed report/backlog changes are scoped and leave unrelated dirty worktree edits unstaged.
