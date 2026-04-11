# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/Denissvgn/python-wiki-llm/releases/tag/v0.1.0
