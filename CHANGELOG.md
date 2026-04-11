# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Denissvgn/python-wiki-llm/releases/tag/v0.1.0


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

[0.1.1]: https://github.com/Denissvgn/python-wiki-llm/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Denissvgn/python-wiki-llm/releases/tag/v0.1.0
