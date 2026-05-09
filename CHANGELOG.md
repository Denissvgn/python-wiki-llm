# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Codebase source-adapter support** — `extract` now emits stable
  `llm-wiki-extract/v1` JSON, `extract` and `context` support explicit
  `--output`, `--read-only`, and `--allow-external-src`, bootstrap supports
  `--format json` summaries and `--source-adapter`, and `llm_wiki_cli.api`
  exposes supported extraction/context calls for library consumers.

## [0.5.1] - 2026-05-09

### Changed
- Generated agent instructions and default sync prompts now require a semantic
  enrichment pass after deterministic `sync`, so new or generic wiki pages are
  not considered complete just because structural lint passes.

## [0.5.0] - 2026-05-09

### Added
- **Lint and sync performance runtime** — shared source snapshots, persistent built-in inventory caching, cache diagnostics, and opt-in `--jobs` parallel extraction for `lint`, `sync`, and `ci-check`.
- **Lint profiling** — `llm-wiki lint --profile` emits one JSON object with lint issues, diagnostics, phase timings, and optional cache stats.
- **Prepared extractor helpers** — new `llm-wiki prepare-extractors` command prepares TypeScript, Go, and Rust helpers ahead of time, with helper cache resolution through `--cache-dir`, `LLM_WIKI_CACHE_DIR`, or `.git/llm-wiki-extractors/`.
- **Go toolchain override** — `LLM_WIKI_GO` selects the Go executable used for helper preparation, with clearer diagnostics when Go is found but cannot run.
- **Lint speed analysis report** — added `LINT_SPEED_OPTIMIZATION_REPORT.md` documenting the optimization phases and follow-up performance work.

### Changed
- `sync` now uses the same deep-inventory cache and `--jobs` execution path as `lint`, while preserving normal manifest and page output behavior.
- `lint --profile` now remains valid JSON even when source extraction fails; extractor failures are returned as `extractor_failure` issues and still exit nonzero.
- `ci-check --report` now treats the report path as an explicit output destination, allowing absolute paths and relative paths outside the project root.
- Built-in TypeScript, Go, and Rust extraction no longer installs dependencies or compiles helpers during lint, CI, sync, bootstrap, migrate, or extract runs.
- Relationship generation uses an indexed import resolver and small sync diffs build relationships only for affected entities.
- Generated agent instructions now recommend `sync --jobs auto`, strict lint with jobs, helper preparation, broad-diff handling, and `LLM_WIKI_GO` when needed.

### Fixed
- `sync` repairs manifests with missing or malformed source hashes without modifying wiki pages.
- `sync` stops unusually broad source diffs before page writes unless `--force` is provided.
- `sync` avoids no-op rewrites for unchanged generated pages and summarizes unchanged files instead of printing one line per skipped source.
- Entity name collisions across modules and languages are handled consistently during incremental sync, including index and module links.
- Local metrics writes are best-effort and no longer fail validation commands when the metrics file cannot be written.
- Go helper preparation distinguishes "Go not found" from "Go found but failed to run", uses helper-cache-local `GOCACHE` when needed, and preserves user-provided Go cache settings across platforms.
- Windows CI compatibility improved for helper cache paths, executable casing, and environment variable casing.

## [0.3.41] - 2026-05-07

### Added
- **Obsidian Integration** — `llm-wiki obsidian export|check|install-plugin` mirrors the canonical wiki into an Obsidian vault with frontmatter, wikilinks, related links, sidecar human notes, and a desktop companion plugin
- **MCP Server** — optional `llm-wiki mcp` command exposes read-only wiki tools/resources over stdio or local Streamable HTTP, including wiki search, entity/module fetch, context payloads, lint checks, and status
- **Plugin & Skills Marketplace** — local-only `llm-wiki install` plus `llm-wiki plugins list|remove|validate`; manifest-gated plugins can add extractors, prompt templates, lint rules, and managed agent skill blocks
- **Team Features** — shared `.llm-wiki/team.json` policy, `llm-wiki team init|check|resolve-conflicts`, team prompt-template defaults, required plugin checks, team convention linting, and conservative generated-wiki conflict resolution
- **Wiki-as-Context Protocol v1** — `llm-wiki context --request FILE|-` accepts versioned JSON context requests and returns stable success/error envelopes for agents, IDEs, and CI tools
- **Agent Quality Layer** — strict wiki validation (`lint --strict`), `ci-check` reports, opt-in validation hooks, local metrics, smart prompt change-type guidance, and static `llm-wiki review`

### Changed
- PyPI distribution renamed to `agent-wiki-cli`; the installed `llm-wiki` command and `llm_wiki_cli` import package remain unchanged.
- Generic agent instructions now use `AGENTS.md` for new installs and upgrades; legacy `.agents.md` files are still supported for cleanup but are not automatically migrated.

### Fixed
- Bootstrap workflow pages now link to collision-aware module pages when multiple modules share a stem, such as `models_task.md` and `schemas_task.md`.
- Migrate now repairs legacy workflow links like `../modules/task.md` per workflow using path-aware call graph metadata.
- Lint no longer double-counts broken workflow links already reported by the general markdown link pass.
- Restore CI compatibility for Python 3.9 and Windows, including MCP optional-dependency messaging and Windows path normalization in MCP results.
- Context protocol and MCP callers now receive structured extractor failure errors instead of terminating the process.

## [0.3.28] - 2026-05-02

### Added
- **`llm-wiki upgrade` command** — refreshes all framework-managed artifacts (schema constraint blocks, git hooks, wiki dirs, `.gitignore`) in a single idempotent command; supports agent switching via `--agent`
- **Context-optimized extract** — `--changed` flag restricts extraction to files modified in the last commit; `--summary` produces compact class/function-name-only output; `--paths FILE...` extracts specific files for drill-down
- **Chunked `llm-wiki migrate`** — `--chunk-size`, `--chunk`, and `--plan-chunks` split large legacy migrations into bounded page-operation batches
- **GitHub community health files** — code of conduct, security policy, and issue templates tailored to the CLI's local-agent workflow

### Changed
- Shared schema utilities extracted to `services/schema.py` — constraint block markers, `build_schema_content()`, `strip_wiki_block()`, `replace_schema_block()` now centralised; eliminates duplication across `init_cmd`, `uninstall_cmd`, `bootstrap_cmd`
- Source extraction skips more generated dependency/environment directories, including arbitrary virtualenv `site-packages` layouts, PEP 582 `__pypackages__`, `.nox`, `.direnv`, JS package-manager caches, and Go/Rust `--only-files` paths inside excluded trees

### Fixed
- Prevent wiki auto-sync bot commits from recursively triggering the post-commit hook.
- Preserve Python relative import levels in deep extraction and resolve relative import relationships correctly.
- Avoid wiki page collisions for same-directory multi-language files that share a stem.
- Apply `.gitignore` filtering consistently before TypeScript, Go, and Rust extractor subprocesses run.
- Deprecate qualified entity pages correctly during incremental sync after source deletion.
- Handle local markdown anchors and `mailto:` links correctly during wiki linting.

## [0.1.5] - 2026-04-11

### Added
- **Docker/Compose wiki support** — `bootstrap` now discovers Dockerfiles and docker-compose/compose YAML files, parses them, and generates structured `infrastructure/` wiki pages with build stages, ports, env vars, volumes, services, and cross-references to Python modules for COPY targets
- **Dockerfile parser** — line-based parser extracts FROM (multi-stage), EXPOSE, ENV, VOLUME, COPY/ADD, WORKDIR, ARG, LABEL, ENTRYPOINT, CMD, HEALTHCHECK; handles continuation lines
- **docker-compose parser** — lightweight line-based YAML parser (zero dependencies) extracting services, ports, volumes, environment, depends_on, command, networks, named volumes
- **`infrastructure/` wiki section** — new directory alongside entities, modules, workflows; scaffolded by `init`, populated by `bootstrap`, indexed in `index.md`
- **Infrastructure lint checks** — `lint` now detects undocumented Docker files and stale infrastructure pages
- **Compose parser rewrite** — arbitrary-depth nesting for deploy/healthcheck/depends_on/build, inline YAML list parsing (`["CMD", ...]` and `[infra]`), lazy list-to-dict promotion fixing environment/build/depends_on returning empty lists
- **Recursive Docker file discovery** — `get_docker_inventory()` now searches subdirectories and detects non-standard compose filenames (e.g., `core.yml`, `infra.yml`) via content-based heuristic

### Fixed
- Compose parser flush-list bug — nested key:value blocks (environment, build, depends_on, healthcheck, deploy) were overwritten with `[]` on the next sibling key
- Dockerfile discovery no longer matches `.md` documentation files as Dockerfiles
- **Docker inventory in prompts** — `generate-prompt` and `extract` now include Docker/Compose file inventory for agent context
- **44 new tests** — `test_docker_extract.py` (24), `test_docker_bootstrap.py` (11), `test_docker_lint.py` (9)
- **`status` command** — displays wiki directory, configured agent, installed hooks, circuit breaker state, and page counts
- **`config.py` module** — centralized `DEFAULT_WIKI_DIR`, `AGENT_CHOICES`, `CLI_AGENTS`, `IDE_AGENTS` constants and `validate_path()` utility
- **Path validation** — `--wiki-dir` and `--src-dir` arguments are validated to prevent path traversal; rejects paths outside the project root
- **`.gitignore` auto-entries** — `init` appends llm-wiki temp file patterns (`.git/llm-wiki-*.txt`, `.lock`, `.json`, `.log`) to `.gitignore`
- **Global error handler** — `cli.py` catches unhandled exceptions and prints a friendly message instead of a raw traceback
- **22 new tests** — `test_config.py` (7), `test_status.py` (10), `test_trigger.py` (5) covering path validation, status output, and trigger edge cases (mock-based)
- **`generate-prompt` command** — builds a diff + AST sync prompt and writes it to `.git/llm-wiki-prompt.txt` for pasting into IDE agent chats; supports `--print`, `--no-diff`, `--output`, `--wiki-dir`, `--src-dir`
- **IDE agent hook** — `install-hook` now installs a prompt-generation post-commit hook for `copilot`, `cursor`, and `generic` agents (instead of skipping); prints a reminder box after every commit
- **Agent config persistence** — `init` writes `{wiki_dir}/.llm-wiki-agent` so `install-hook` and `generate-prompt` automatically pick up the chosen agent without requiring `--agent` every time
- **`install-hook --agent` and `--wiki-dir` flags** — explicit override of the persisted agent config and wiki directory path
- **Agent install check** — `init` warns (without blocking) when a CLI agent (`claude`, `aider`, `opencode`) binary is not found on PATH
- **IDE-aware instructions** — `copilot`, `cursor`, and `generic` schema files now include an explicit "How to sync the wiki" section describing the `generate-prompt` workflow
- **`--wiki-dir` flag for `init`** — scaffold the wiki at a custom directory path instead of the default `docs/llm_wiki`

### Changed
- `install-hook` for CLI agents (`claude`, `aider`, `opencode`) now bakes the agent name directly into the post-commit script (`--agent <name>`) rather than relying on the default
- `install-hook` for IDE agents no longer skips installation — it installs the prompt-generation hook instead
- Standardized exit codes: `init`, `hook`, and `trigger-agent` now use `sys.exit(1)` on error paths (matching `lint`)
- `trigger-agent` prompt template now respects `--wiki-dir` instead of hardcoding `docs/llm_wiki`
- Expanded directory exclusions in `extract` — skips `env`, `.tox`, `node_modules`, `__pycache__`, `.eggs`, `build`, `dist`, `.git` in addition to `venv`/`.venv`
- Shell hook scripts now quote `"$CLI"` and shell variables for paths containing spaces

### Fixed
- **Python 3.9 crash** — added `from __future__ import annotations` to `init_cmd.py` and `hook_cmd.py` (used PEP 585/604 syntax without import)
- **Windows lock size** — `msvcrt.locking()` now locks 4096 bytes instead of 1 byte in `lockfile.py`
- **Windows unlock** — prints warning to stderr instead of silently swallowing `OSError` on unlock
- **Circuit breaker** — `trigger-agent` now records failure when `git diff` raises `CalledProcessError` (was silently returning)
- **Version write validation** — `write_version()` raises `ValueError` if the regex doesn't match (was silently writing unchanged content)
- Removed debug comment (`# Debug sync`) from `cli.py`

### Removed
- **`storage.py`** — removed unused `WikiStorage` class and `pydantic` runtime dependency (zero dependencies now)

## [0.1.1] - 2026-04-11

### Added
- New agent targets: `aider` (`.aider.conf.yml`) and `opencode` (`.opencode/instructions.md`)
- Improved agent constraint templates with structured sections and agent-specific preambles
- Full test suite — 89 unit, integration, and E2E tests (pytest + pytest-cov)
- GitHub Actions CI matrix: Python 3.9 / 3.12 / 3.13 on Ubuntu, macOS, Windows
- PyPI publish workflow via OIDC trusted publisher on `v*` tags

### Fixed
- Python 3.9 compatibility: added `from __future__ import annotations` to source files using PEP 604/585 type hint syntax
- Windows: `os.rename()` → `os.replace()` in circuit breaker for atomic state writes on NTFS
- Windows: lock file opened in `w+` mode so PID can be read back through the lock's own file descriptor
- GitHub Actions: bumped `actions/checkout` to v6 and `actions/setup-python` to v6 (Node.js 24)

## [0.1.0] - 2026-04-11

### Added
- **Core CLI** with 8 subcommands: `init`, `extract`, `lint`, `install-hook`, `trigger-agent`, `bootstrap`, `bump`, `uninstall`
- **AST extraction** via Python `ast` module — deep mode extracts docstrings, attributes with types/defaults, method signatures, decorators, imports
- **Wiki bootstrap** — generates entity, module, and workflow pages from existing codebases with cross-reference relationship graphs
- **Wiki linting** — validates broken links, orphan pages, entity/module/workflow consistency against live AST (CI-compatible exit codes)
- **Post-commit automation** — detached background hook spawns LLM subagent with diff + AST context to autonomously update wiki
- **Agent support** — Claude Code, Aider, OpenCode (headless CLI); Cursor, Copilot, Generic (schema-only)
- **Semantic version bumping** — auto-detects pyproject.toml, setup.cfg, package.json, VERSION; patch on commit, minor on push (opt-in hooks)
- **Safety fuses:**
  - File-based exclusive lock (fcntl/msvcrt) prevents concurrent wiki syncs
  - Circuit breaker auto-disables after 3 consecutive subagent failures
  - Configurable timeout for subagent processes (default 5 min)
  - Diff size guard skips sync on oversized commits (default 1000 lines)
- **Workflow detection** — call-graph analysis identifies cross-module functions touching 3+ internal modules as workflow candidates
- **Clean uninstall** — safely removes hooks, strips constraint blocks from agent schema files, preserves user content
- **Cross-platform locking** — fcntl on POSIX, msvcrt on Windows
- **Test suite** — 89 unit + integration tests with pytest
- **CI** — GitHub Actions matrix (Python 3.9–3.13, Linux/macOS/Windows) + PyPI publish on tag

[Unreleased]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.5.1...HEAD
[0.5.1]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.3.41...v0.5.0
[0.3.41]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.3.28...v0.3.41
[0.3.28]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.1.5...v0.3.28
[0.1.5]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.1.1...v0.1.5
[0.1.1]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Denissvgn/python-wiki-llm/releases/tag/v0.1.0
