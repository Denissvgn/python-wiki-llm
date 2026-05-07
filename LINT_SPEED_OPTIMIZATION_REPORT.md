# Lint Speed Optimization Report

Date: 2026-05-07
Repository: `python-wiki-llm`

## Executive Summary

`llm-wiki lint` is currently accurate but expensive because it treats every run as a fresh full-project validation. The largest costs are not the final lint checks themselves; they are repeated source discovery, full deep inventory extraction across all registered languages, subprocess/toolchain startup, Docker/Compose scanning, and duplicated work in strict/team paths.

The best path to faster lint without quality loss is to keep full validation semantics but make the inventory incremental and reusable:

1. Build a shared source snapshot once per run.
2. Cache per-file deep inventory entries using strong invalidation keys.
3. Reuse the cached full inventory for unchanged files and only re-extract changed/new files.
4. Reuse the already-built inventory inside strict lint and team checks.
5. Replace repeated recursive walks with one source-tree walk.
6. Compile or prepare helper extractors outside the hot lint path.

Expected impact:

- Warm no-change lint on large repositories should shift from "parse every source file and start every toolchain" to "walk/hash/stat files, load cached inventory, lint wiki pages".
- Strict lint can avoid the current second full inventory extraction.
- Mixed-language repos can avoid repeated Node/Go/Rust startup when there are no changed files for those languages.

## Current Lint Execution Model

Entry point:

- `src/llm_wiki_cli/commands/lint_cmd.py:523` validates paths and calls `build_report`.
- `src/llm_wiki_cli/commands/lint_cmd.py:294` builds the report.

Current `build_report` flow:

1. If wiki dir is missing, return a `wiki_missing` issue early.
2. Always run `get_inventory_result(src_dir, deep=True)` for the full source tree (`lint_cmd.py:303`).
3. Abort lint on any extractor failure (`lint_cmd.py:304-306`).
4. Always run `get_docker_inventory(src_dir)` (`lint_cmd.py:308`).
5. Load all wiki markdown pages with `wiki_path.rglob("*.md")` (`lint_cmd.py:310-313`).
6. Check links, orphan pages, classes, modules, workflows, infrastructure, plugins, and team policy.
7. In strict mode, call `_check_sync_manifest`, which runs another full `get_inventory_result(src_dir, deep=True)` (`lint_cmd.py:425-427`, `lint_cmd.py:263-269`).

Source inventory flow:

- `get_inventory_result` iterates every registered extractor (`extract_cmd.py:80`).
- For each known language, it discovers matching source files (`extract_cmd.py:84-89`).
- It then calls the extractor, and most extractors rediscover the same files internally:
  - Python: `python_extractor.py:247-252`
  - TypeScript: `ts_extractor.py:117-119`
  - Go: `go_extractor.py:62-64`
  - Rust: `rust_extractor.py:62-64`
- Package stamping then scans the tree again for `pyproject.toml` and `setup.py` (`packages.py:101`, `packages.py:120`).

Docker/Compose flow:

- `get_docker_inventory` builds another gitignore matcher (`extract_cmd.py:714`).
- It walks the tree for Dockerfile patterns, Compose name patterns, and YAML content detection (`extract_cmd.py:734-764`).

## Local Timing Sample

I ran a small local timing sample against this repository. This is not a large-project benchmark, but it confirms where time is spent.

Command shape:

```bash
python3 -c '... get_inventory_result(".", deep=True); get_docker_inventory(".") ...'
```

Observed result:

```text
inventory_seconds: 4.15
docker_seconds: 0.496
inventory_files: 82
docker_files: 0
statuses:
  python: ok, 85 files found
  typescript: ok, 1 file found
  go: failed, 1 file found, extraction failed
  rust: ok, 1 file found
```

The Go failure came from the local snap-installed Go tool:

```text
snap-confine has elevated permissions and is not confined but should be.
```

That is an environment-specific failure, but it shows a practical lint risk: if a matching source file exists, optional language extractor failures can make lint fail before wiki checks finish.

## Main Bottlenecks

### 1. Strict lint extracts the full inventory twice

Normal lint extracts once at `lint_cmd.py:303`. Strict lint then calls `_check_sync_manifest`, which extracts again at `lint_cmd.py:263`.

This is the highest-confidence quick win. `_check_sync_manifest` can accept the already-built `deep_inventory` and reuse it.

Recommended change:

```text
_check_sync_manifest(report, wiki_path, src_dir, deep_inventory)
```

Only call `get_inventory_result` inside `_check_sync_manifest` when no inventory was supplied, preserving backward compatibility for tests and direct helper use.

Quality impact: none. The exact same inventory is reused within the same lint run.

### 2. Source discovery is duplicated per language

`get_inventory_result` discovers files to decide whether to run an extractor, then extractors discover files again. `discover_source_files` also builds a gitignore matcher unless one is passed (`common.py:43-44`).

For a large repository, this means repeated recursive walks and repeated `.gitignore` matching before AST parsing even starts.

Recommended change:

- Introduce a `SourceSnapshot` or `DiscoveryResult` object:
  - one gitignore matcher
  - one recursive walk
  - files grouped by language
  - package marker files
  - Docker/Compose candidates
  - optional file metadata: size, mtime_ns, hash, git blob id
- Pass grouped files into extractors.
- Keep current extractor API as fallback, but add an optional `source_files` argument or a new internal extractor protocol.

Quality impact: none if filtering semantics remain centralized and tests cover the same exclusions.

### 3. Helper extractors have high startup overhead

The TypeScript, Go, and Rust extractors shell out:

- TypeScript starts Node and uses ts-morph (`ts_extractor.py:135-152`).
- Go uses `go run .` (`go_extractor.py:73-89`).
- Rust uses `cargo run --quiet --` (`rust_extractor.py:73-89`).

On warm caches this may be acceptable for small projects, but on big projects and pre-commit workflows it is expensive. It also means lint speed depends on external toolchain availability.

Recommended changes:

- Build helper binaries once into a project/user cache and execute the binary:
  - Go: compile once instead of `go run .` every lint.
  - Rust: `cargo build` once, then run the compiled binary.
- Key helper binaries by:
  - extractor script hash
  - lockfile hash
  - platform/architecture
  - toolchain version
- Do not run `npm install` from inside lint. `_ensure_npm_deps` can attempt a 120s install (`ts_extractor.py:26-77`), which is surprising in validation. Move dependency preparation to install/bootstrap, or fail quickly with an actionable message.

Quality impact: none if the same extractor code runs. This changes startup mechanics, not extraction behavior.

### 4. No persistent inventory cache exists

The sync manifest stores source hashes and page mappings (`sync_cmd.py:100-121`), but lint does not reuse a previous inventory. It always parses source files again.

Recommended cache:

Default path:

```text
.git/llm-wiki-inventory-cache.json
```

Allow override:

```text
LLM_WIKI_CACHE_DIR
llm-wiki lint --cache-dir ...
```

Cache structure:

```json
{
  "version": 1,
  "schema": "inventory-v1",
  "llm_wiki_version": "0.3.41",
  "src_dir": "/abs/project",
  "deep": true,
  "extractor_fingerprint": "...",
  "filter_fingerprint": "...",
  "gitignore_fingerprint": "...",
  "plugin_lock_fingerprint": "...",
  "files": {
    "src/app.py": {
      "language": "python",
      "size": 1234,
      "mtime_ns": 1760000000000000000,
      "hash": "sha256:...",
      "inventory": {}
    }
  }
}
```

Invalidation keys:

- llm-wiki version
- inventory schema version
- extractor registry and plugin lock content
- extractor implementation hashes for built-ins and plugins
- `EXCLUDED_DIRS`, extension mapping, Docker pattern config
- `.gitignore` files and nested `.gitignore` contents
- deep/shallow mode
- Python version if Python AST output can vary by syntax support
- TypeScript/Go/Rust helper versions when their output schema can vary

Warm run algorithm:

1. Build a source snapshot.
2. Determine changed/new/deleted files.
3. Load cached inventory for unchanged files.
4. Extract only changed/new files, grouped by language.
5. Merge cached and fresh inventory.
6. Run the same lint rules over the merged full inventory.
7. Save updated cache after successful extraction.

Quality impact: none when invalidation is correct. Full lint rules still run against a complete current inventory.

### 5. Strict manifest freshness can be cheaper

Strict lint currently extracts deep inventory and then `_compute_diff` hashes files (`sync_cmd.py:164-209`). Since the manifest already has file hashes, strict freshness can be checked in two layers:

- Fast layer: compare source snapshot against manifest paths and hashes.
- Full layer: use merged cached inventory for class/module/page checks.

Important: manifest-only checks cannot replace inventory-based lint because they do not prove that classes/modules/workflows are documented correctly after semantic changes. They can, however, avoid a second extraction and help identify changed files for cache re-extraction.

Quality impact: none if manifest freshness is an input to cache invalidation rather than a replacement for lint.

### 6. Docker inventory is scanned more than once

`build_report` always computes `docker_inventory` once (`lint_cmd.py:308`). If team config exists and canonical naming is enabled, team checks call `get_docker_inventory(src_dir)` again (`team.py:276`).

Recommended change:

- Pass `docker_inventory` into `build_team_issues` or into `check_team_conventions`.
- Use the same `SourceSnapshot` to identify Docker/Compose candidates.

Quality impact: none.

### 7. Markdown pages are read and parsed repeatedly

`build_report` reads each page for link checks (`lint_cmd.py:316-318`). It reads `index.md` again (`lint_cmd.py:333`) and workflow pages again (`lint_cmd.py:385-387`). Team conventions read section pages later (`team.py:230-235`).

Recommended change:

Create a `PageIndex`:

```text
PageIndex:
  pages: list[PageRecord]
  by_rel_path: dict[str, PageRecord]
  index_links: set[Path]
  links_by_page: dict[Path, list[str]]
```

Use a `set` for `referenced_files`; it is currently a list (`lint_cmd.py:331-345`), which makes orphan checks O(pages * index_links).

Quality impact: none.

### 8. Built-in and plugin lint rules lack declared dependencies

Plugin lint rules receive the full inventory and all pages (`lint_cmd.py:177-203`). That is flexible, but it means lint cannot know whether a plugin needs Docker data, deep inventory, or only pages.

Recommended optional plugin metadata:

```json
{
  "type": "lint_rule",
  "id": "example",
  "entry_point": "pkg:rule",
  "requires": ["pages", "inventory:deep", "docker"]
}
```

Use this metadata to:

- avoid computing Docker inventory unless a built-in or plugin rule requires it
- reject cache reuse if plugin code or requirements changed
- eventually parallelize independent rules

Quality impact: none for plugins that do not declare metadata; keep current behavior as fallback.

## Recommended Architecture

### New Internal Objects

`SourceSnapshot`

```text
root: Path
gitignore_fingerprint: str
files_by_language: dict[str, list[SourceFile]]
docker_candidates: list[SourceFile]
package_markers: list[SourceFile]
all_source_paths: set[str]
```

`SourceFile`

```text
rel_path: str
abs_path: Path
suffix: str
language: str | None
size: int
mtime_ns: int
hash: str | None
git_blob: str | None
```

`InventoryCache`

```text
load()
get_valid_entries(snapshot, cache_key)
store_entries(fresh_entries)
invalidate(reason)
```

`LintContext`

```text
wiki_dir: Path
src_dir: str
strict: bool
source_snapshot: SourceSnapshot
inventory: dict
docker_inventory: dict
page_index: PageIndex
```

### Target Lint Flow

```text
run()
  validate paths
  build_lint_context()
    scan source tree once
    load inventory cache
    extract changed/new files only
    merge cached + fresh inventory
    build Docker inventory from snapshot only if needed
    build page index once
  run built-in checks
  run strict checks using same inventory
  run plugin/team checks using same context
  render report
```

### Cache Safety Rules

- Never use cache after extractor/plugin/filter fingerprint changes.
- Never use cache for paths missing from the current source snapshot.
- Treat unreadable files as changed or failed, not cached.
- Preserve current behavior where extractor failures fail lint if matching files exist.
- Expose `--no-cache` and `--rebuild-cache` for diagnosis.
- In CI, allow cache persistence but never require it for correctness.

## Workflow Recommendations

### Local Development

Use full semantic lint with cache enabled by default:

```bash
llm-wiki lint --wiki-dir docs/llm_wiki --src-dir .
```

For pre-commit validation:

```bash
llm-wiki lint --strict --wiki-dir docs/llm_wiki --src-dir .
```

With a warm cache, this remains full validation but should only re-extract changed files.

Add optional diagnostics:

```bash
llm-wiki lint --profile
llm-wiki lint --cache-stats
llm-wiki lint --no-cache
llm-wiki lint --rebuild-cache
```

### CI

Keep `ci-check` as full strict validation, but let it use cache safely:

```bash
llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki
```

Recommended CI cache key inputs:

- operating system and architecture
- Python version
- llm-wiki version
- lockfile hash for this project
- `.llm-wiki/plugins.lock.json` hash, if present
- extractor helper lockfile hashes

Even without a restored cache, CI remains correct because it falls back to full extraction.

### Toolchain Preparation

Add a command:

```bash
llm-wiki doctor
llm-wiki prepare-extractors
```

It should:

- verify Node/npm/Go/Cargo availability only when matching source files exist
- preinstall or verify TypeScript extractor dependencies
- compile Go/Rust helper binaries into cache
- report which extractors will run and why

This keeps network installs and compiler setup out of the lint hot path.

## Phased Implementation Plan

### Phase 1: Low-risk quick wins

1. Reuse `deep_inventory` inside strict manifest check.
2. Pass `docker_inventory` into team checks.
3. Build `referenced_files` as a set.
4. Cache markdown page content and links inside `build_report`.
5. Add `--profile` timing output around major phases.

Tests to add:

- strict lint calls `get_inventory_result` once
- team canonical naming does not call `get_docker_inventory` a second time
- orphan detection behavior is unchanged with set membership
- profile output is optional and stable enough for tests

### Phase 2: Single source discovery

1. Add `SourceSnapshot`.
2. Replace repeated `Path.rglob` calls for language discovery with one walk.
3. Adapt built-in extractors to accept precomputed file lists.
4. Keep old extractor API for plugin compatibility.
5. Add tests for exclusions, nested `.gitignore`, `only_files`, symlink/outside-root protection, and generated file skipping.

### Phase 3: Persistent inventory cache

1. Add `InventoryCache`.
2. Implement exact invalidation fingerprints.
3. Use cached entries for unchanged files.
4. Re-extract changed/new files and merge.
5. Add `--no-cache`, `--rebuild-cache`, and `--cache-stats`.

Tests to add:

- warm lint reuses unchanged cached entries
- changed file invalidates only that file
- deleted file disappears from merged inventory
- plugin lock changes invalidate cache
- `.gitignore` changes invalidate cache
- extractor implementation changes invalidate cache
- cache corruption falls back to full extraction

### Phase 4: Helper extractor startup optimization

1. Compile Go/Rust helpers into a cache directory and run binaries directly.
2. Move TypeScript dependency installation out of lint.
3. Add `doctor` or `prepare-extractors`.
4. Add clear error messages for missing tools.

Tests to add:

- helper binary cache key changes when scripts/locks change
- lint does not invoke `npm install`
- missing optional toolchain behavior is explicit and unchanged for matching sources

### Phase 5: Optional parallelism

Parallelize independent language extraction after caching and single discovery are in place.

Notes:

- Built-in extractors are safe candidates.
- Plugin extractors should remain sequential unless metadata marks them parallel-safe.
- Preserve deterministic merge order.
- Avoid shared mutable extractor instances when running concurrently.

## Measurement Plan

Add a benchmark fixture generator:

```text
benchmarks/
  generate_project.py
  run_lint_bench.py
```

Project profiles:

- Python-only: 1k, 10k, 50k files
- TypeScript-only: 1k, 10k files
- mixed Python/TS/Go/Rust
- many markdown wiki pages
- many nested `.gitignore` files
- many YAML files with only a few Compose files

Metrics:

- total wall time
- source discovery time
- gitignore parse/match time
- inventory extraction time by language
- subprocess startup time
- cache load/save time
- cache hit rate
- Docker inventory time
- markdown page lint time
- strict manifest check time
- plugin/team check time

Required scenarios:

- cold cache
- warm cache, no source changes
- one changed source file
- 100 changed source files
- changed `.gitignore`
- changed plugin lock
- missing toolchain

Success targets:

- strict lint should not extract inventory twice
- warm no-change lint should avoid all AST extraction subprocesses
- one-file change should only re-extract that file's language group when possible
- CI cold-cache behavior remains correct

## Risks And Mitigations

Cache staleness:

- Mitigation: strong fingerprints, hash checks, `--no-cache`, cache corruption fallback.

Plugin compatibility:

- Mitigation: preserve old extractor/lint-rule signatures and treat undeclared plugin rules as requiring full context.

Gitignore semantics drift:

- Mitigation: keep filtering centralized in `SourceSnapshot`; add regression tests for nested ignore rules and negations.

Toolchain setup surprises:

- Mitigation: never install dependencies during lint by default; add `doctor` and explicit preparation.

Parallelism nondeterminism:

- Mitigation: deterministic merge order and per-extractor isolated state.

Cache file growth:

- Mitigation: store only deep inventory for current source snapshot, prune deleted files, optionally compress JSON.

## Non-recommended Shortcuts

These would make lint faster but reduce quality or predictability:

- Defaulting lint to shallow inventory. This weakens workflow detection and relationship checks.
- Skipping TypeScript/Go/Rust extraction when tools are slow. That hides real undocumented/stale pages.
- Trusting manifest freshness alone. It does not replace semantic AST-to-wiki validation.
- Ignoring plugin lint rules in local mode. Teams may rely on them for required policy checks.
- Running network dependency installation inside lint. It makes validation unpredictable and slow.

## Priority Recommendation

Start with Phase 1 and Phase 3 design together.

Phase 1 gives immediate speedups with minimal risk, especially strict lint's duplicated inventory. Phase 3 is the strategic fix: full-quality lint on big projects needs a reusable full inventory, not a faster way to repeatedly parse everything.

The most valuable implementation order is:

1. Reuse inventory in strict lint.
2. Add phase timing to make future regressions visible.
3. Build `SourceSnapshot`.
4. Add persistent per-file inventory cache.
5. Move helper extractor preparation out of lint.

