import argparse
import os
import sys
from .commands import (
    bootstrap_cmd,
    bump_cmd,
    ci_check_cmd,
    context_cmd,
    extract_cmd,
    generate_prompt_cmd,
    hook_cmd,
    init_cmd,
    install_cmd,
    lint_cmd,
    mcp_cmd,
    metrics_cmd,
    migrate_cmd,
    obsidian_cmd,
    plugins_cmd,
    prepare_extractors_cmd,
    release_cmd,
    review_cmd,
    status_cmd,
    sync_cmd,
    team_cmd,
    trigger_cmd,
    uninstall_cmd,
    upgrade_cmd,
)
from .config import AGENT_CHOICES, DEFAULT_WIKI_DIR, PathValidationError
from .services.contracts import BOOTSTRAP_SKIP_DATA_FLOW_FLAG
from . import __version__


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _jobs_value(value: str) -> int:
    if value == "auto":
        return max(1, os.cpu_count() or 1)
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "must be a positive integer or 'auto'"
        ) from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


_COMMAND_MODULES = {
    "init": init_cmd,
    "extract": extract_cmd,
    "lint": lint_cmd,
    "prepare-extractors": prepare_extractors_cmd,
    "ci-check": ci_check_cmd,
    "install-hook": hook_cmd,
    "install": install_cmd,
    "plugins": plugins_cmd,
    "team": team_cmd,
    "trigger-agent": trigger_cmd,
    "bootstrap": bootstrap_cmd,
    "bump": bump_cmd,
    "generate-prompt": generate_prompt_cmd,
    "metrics": metrics_cmd,
    "review": review_cmd,
    "uninstall": uninstall_cmd,
    "status": status_cmd,
    "mcp": mcp_cmd,
    "obsidian": obsidian_cmd,
    "release": release_cmd,
    "upgrade": upgrade_cmd,
    "sync": sync_cmd,
    "migrate": migrate_cmd,
    "context": context_cmd,
}


def _build_parser():
    parser = argparse.ArgumentParser(description="LLM Wiki CLI")
    parser.add_argument(
        "--version", action="version", version=f"llm-wiki {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    _register_commands(subparsers)
    return parser


def _register_commands(subparsers):
    _add_init_command(subparsers)
    _add_extract_command(subparsers)
    _add_lint_command(subparsers)
    _add_prepare_extractors_command(subparsers)
    _add_ci_check_command(subparsers)
    _add_install_hook_command(subparsers)
    _add_install_command(subparsers)
    _add_plugins_command(subparsers)
    _add_team_command(subparsers)
    _add_trigger_agent_command(subparsers)
    _add_bootstrap_command(subparsers)
    _add_bump_command(subparsers)
    _add_generate_prompt_command(subparsers)
    _add_metrics_command(subparsers)
    _add_review_command(subparsers)
    _add_uninstall_command(subparsers)
    _add_status_command(subparsers)
    _add_mcp_command(subparsers)
    _add_obsidian_command(subparsers)
    _add_release_command(subparsers)
    _add_upgrade_command(subparsers)
    _add_sync_command(subparsers)
    _add_migrate_command(subparsers)
    _add_context_command(subparsers)


def _add_init_command(subparsers):
    init_parser = subparsers.add_parser(
        "init", help="Scaffold LLM Wiki structure and schema"
    )
    init_parser.add_argument(
        "--agent",
        choices=AGENT_CHOICES,
        default="generic",
        help="Target agent format for rules/constraints",
    )
    init_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to create (default: docs/llm_wiki)",
    )
    init_parser.add_argument(
        "--no-quality-hints",
        action="store_true",
        default=False,
        help="Omit agent quality guidelines from the constraint block",
    )


def _add_extract_command(subparsers):
    extract_parser = subparsers.add_parser(
        "extract", help="Extract project AST and structure into wiki"
    )
    extract_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan"
    )
    extract_parser.add_argument(
        "--changed",
        action="store_true",
        help="Only extract files changed in the last git commit",
    )
    extract_parser.add_argument(
        "--summary",
        action="store_true",
        help="Compact output: file paths with class/function names only",
    )
    extract_parser.add_argument(
        "--paths",
        nargs="+",
        metavar="FILE",
        help="Only extract specific file paths (relative to --src-dir)",
    )
    extract_parser.add_argument(
        "--deep",
        action="store_true",
        help="Include docstrings, params, attributes, and imports",
    )
    extract_parser.add_argument(
        "--package",
        default=None,
        metavar="NAME",
        help="Only include files belonging to the named package",
    )
    extract_parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Include all .py files even if they have no extractable components",
    )
    extract_parser.add_argument(
        "--output", metavar="PATH", help="Write JSON output to a file instead of stdout"
    )
    extract_parser.add_argument(
        "--read-only",
        action="store_true",
        help="Guarantee source-adapter mode writes no llm-wiki files except explicit --output",
    )
    extract_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )


def _add_lint_command(subparsers):
    lint_parser = subparsers.add_parser(
        "lint", help="Lint LLM Wiki for broken links, orphans, and AST drift"
    )
    lint_parser.add_argument(
        "--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory to lint"
    )
    lint_parser.add_argument(
        "--src-dir", default=".", help="Source directory to cross-reference against"
    )
    lint_parser.add_argument(
        "--strict",
        action="store_true",
        help="Require core wiki structure and a fresh sync manifest",
    )
    lint_parser.add_argument(
        "--profile",
        action="store_true",
        help="Print combined lint report and phase timings as JSON",
    )
    lint_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable persistent inventory cache for this run",
    )
    lint_parser.add_argument(
        "--rebuild-cache",
        action="store_true",
        help="Ignore existing inventory cache and rewrite it after extraction",
    )
    lint_parser.add_argument(
        "--cache-stats",
        action="store_true",
        help="Include inventory cache diagnostics in lint output",
    )
    lint_parser.add_argument(
        "--cache-dir",
        default=None,
        metavar="PATH",
        help="Directory for llm-wiki-inventory-cache.json",
    )
    lint_parser.add_argument(
        "--jobs",
        type=_jobs_value,
        default=1,
        metavar="JOBS",
        help="Parallel extractor jobs for built-ins and opted-in plugins: positive integer or 'auto' (default: 1)",
    )


def _add_prepare_extractors_command(subparsers):
    prepare_parser = subparsers.add_parser(
        "prepare-extractors",
        help="Prepare TypeScript, Go, and Rust extractor helpers",
    )
    prepare_parser.add_argument(
        "--src-dir", default=".", help="Source directory to inspect"
    )
    prepare_parser.add_argument(
        "--cache-dir",
        default=None,
        metavar="PATH",
        help="Directory for extractor helper cache",
    )
    prepare_parser.add_argument(
        "--language",
        action="append",
        choices=["typescript", "go", "rust"],
        help="Helper language to prepare; may be repeated",
    )


def _add_ci_check_command(subparsers):
    ci_parser = subparsers.add_parser(
        "ci-check", help="Run strict wiki validation and write a CI report"
    )
    ci_parser.add_argument("--src-dir", default=".", help="Source directory to scan")
    ci_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to validate (default: docs/llm_wiki)",
    )
    ci_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Console output format (default: text)",
    )
    ci_parser.add_argument(
        "--report",
        default=".git/llm-wiki-ci-report.md",
        help="Markdown report path (default: .git/llm-wiki-ci-report.md)",
    )
    ci_parser.add_argument(
        "--jobs",
        type=_jobs_value,
        default=1,
        metavar="JOBS",
        help="Parallel extractor jobs for built-ins and opted-in plugins: positive integer or 'auto' (default: 1)",
    )


def _add_install_hook_command(subparsers):
    hook_parser = subparsers.add_parser(
        "install-hook", help="Install prompt-generation git hooks for wiki sync"
    )
    hook_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to read agent config from (default: docs/llm_wiki)",
    )
    hook_parser.add_argument(
        "--agent",
        choices=AGENT_CHOICES,
        default=None,
        help="Agent preference to display after installing the prompt hook",
    )
    hook_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing unrelated post-commit hook",
    )
    hook_parser.add_argument(
        "--enable-validation",
        action="store_true",
        help="Also install a pre-commit hook that runs `llm-wiki lint --strict`",
    )


def _add_install_command(subparsers):
    install_parser = subparsers.add_parser(
        "install", help="Install a local llm-wiki plugin"
    )
    install_parser.add_argument("ref", help="Local plugin path or local catalog name")
    install_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory used to refresh active agent skills",
    )
    install_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview the plugin without installing it",
    )
    install_parser.add_argument(
        "--yes", action="store_true", help="Install without prompting for confirmation"
    )


def _add_plugins_command(subparsers):
    plugins_parser = subparsers.add_parser(
        "plugins", help="Manage installed llm-wiki plugins"
    )
    plugins_sub = plugins_parser.add_subparsers(dest="plugins_action", required=True)
    plugins_sub.add_parser("list", help="List installed plugins")
    plugins_remove = plugins_sub.add_parser("remove", help="Remove an installed plugin")
    plugins_remove.add_argument("plugin_id", help="Plugin id to remove")
    plugins_remove.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory for path validation",
    )
    plugins_validate = plugins_sub.add_parser(
        "validate", help="Validate a local plugin manifest"
    )
    plugins_validate.add_argument(
        "path", help="Plugin directory or llm-wiki-plugin.json path"
    )


def _add_team_command(subparsers):
    team_parser = subparsers.add_parser(
        "team", help="Manage shared llm-wiki team policy"
    )
    team_sub = team_parser.add_subparsers(dest="team_action", required=True)
    team_init = team_sub.add_parser("init", help="Create .llm-wiki/team.json")
    team_init.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to record in team config",
    )
    team_check = team_sub.add_parser(
        "check", help="Validate team config and conventions"
    )
    team_check.add_argument("--src-dir", default=".", help="Source directory to scan")
    team_check.add_argument(
        "--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory to validate"
    )
    team_check.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    team_resolve = team_sub.add_parser(
        "resolve-conflicts", help="Safely resolve generated wiki conflicts"
    )
    team_resolve.add_argument("--src-dir", default=".", help="Source directory to scan")
    team_resolve.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to scan for conflict markers",
    )
    team_resolve.add_argument(
        "--write",
        action="store_true",
        help="Apply safe resolutions instead of dry-running",
    )
    team_resolve.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def _add_trigger_agent_command(subparsers):
    trigger_parser = subparsers.add_parser(
        "trigger-agent", help="Manually trigger a CLI agent to update wiki using diff"
    )
    trigger_parser.add_argument(
        "--agent",
        choices=AGENT_CHOICES,
        default="claude",
        help="Agent executable to invoke for manual trigger-agent sync",
    )
    trigger_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to update (default: docs/llm_wiki)",
    )
    trigger_parser.add_argument(
        "--reset-breaker",
        action="store_true",
        help="Reset the circuit breaker after consecutive failures and exit",
    )
    trigger_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for the subagent process (default: 300)",
    )
    trigger_parser.add_argument(
        "--max-diff-lines",
        type=int,
        default=1000,
        help="Skip sync if diff exceeds this many lines (default: 1000)",
    )
    trigger_parser.add_argument(
        "--max-prompt-bytes",
        type=_positive_int,
        default=None,
        help=f"Skip sync if generated prompt exceeds this many bytes (default: {trigger_cmd.DEFAULT_MAX_PROMPT_BYTES})",
    )
    trigger_parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass diff and prompt size guards (does not bypass lock or circuit breaker)",
    )


def _add_bootstrap_command(subparsers):
    bootstrap_parser = subparsers.add_parser(
        "bootstrap", help="Generate initial wiki for an existing codebase"
    )
    bootstrap_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan"
    )
    bootstrap_parser.add_argument(
        "--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki output directory"
    )
    bootstrap_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing entity/module pages",
    )
    bootstrap_parser.add_argument(
        "--depth",
        choices=["shallow", "full"],
        default="full",
        help="shallow=names only, full=docstrings/attrs/methods/imports/relationships (default: full)",
    )
    bootstrap_parser.add_argument(
        "--skip-workflows",
        action="store_true",
        help="Skip automatic workflow page generation from call graph",
    )
    bootstrap_parser.add_argument(
        "--skip-flows",
        action="store_true",
        help="Skip automatic user-flow page generation from entry points",
    )
    bootstrap_parser.add_argument(
        BOOTSTRAP_SKIP_DATA_FLOW_FLAG,
        action="store_true",
        help="Generate user-flow pages without the generated data-flow section",
    )
    bootstrap_parser.add_argument(
        "--skip-dependencies",
        action="store_true",
        help="Skip dependency / load-order architecture page generation",
    )
    bootstrap_parser.add_argument(
        "--dependency-graph-detail",
        choices=["module", "package", "auto"],
        default="auto",
        help=(
            "Dependency graph granularity: full module graph, top-level "
            "packages, or auto-collapse large graphs (default: auto)"
        ),
    )
    bootstrap_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Console output format (default: text)",
    )
    bootstrap_parser.add_argument(
        "--source-adapter",
        action="store_true",
        help="Write only under --wiki-dir and skip agent constraint updates",
    )
    bootstrap_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )


def _add_bump_command(subparsers):
    bump_parser = subparsers.add_parser(
        "bump", help="Bump project version (patch or minor)"
    )
    bump_group = bump_parser.add_mutually_exclusive_group(required=True)
    bump_group.add_argument(
        "--patch",
        dest="bump_type",
        action="store_const",
        const="patch",
        help="Bump patch version (0.1.5 -> 0.1.6)",
    )
    bump_group.add_argument(
        "--minor",
        dest="bump_type",
        action="store_const",
        const="minor",
        help="Bump minor version (0.1.6 -> 0.2.0)",
    )
    bump_parser.add_argument(
        "--stage",
        action="store_true",
        help="Git-add the version file after bumping (for use in hooks)",
    )


def _add_generate_prompt_command(subparsers):
    gp_parser = subparsers.add_parser(
        "generate-prompt",
        help="Build a wiki sync prompt for IDE agents (Copilot, Cursor, etc.)",
    )
    gp_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory (default: docs/llm_wiki)",
    )
    gp_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan (default: .)"
    )
    gp_parser.add_argument(
        "--output",
        default=".git/llm-wiki-prompt.txt",
        help="Output file path (default: .git/llm-wiki-prompt.txt)",
    )
    gp_parser.add_argument(
        "--print",
        dest="print_prompt",
        action="store_true",
        help="Print the prompt to stdout instead of writing to a file",
    )
    gp_parser.add_argument(
        "--change-type",
        choices=generate_prompt_cmd.CHANGE_TYPES,
        default="auto",
        help="Prompt guidance profile (default: auto)",
    )
    gp_parser.add_argument(
        "--template", help="Installed prompt template id (or plugin_id/template_id)"
    )


def _add_metrics_command(subparsers):
    metrics_parser = subparsers.add_parser(
        "metrics", help="Show local llm-wiki quality metrics"
    )
    metrics_parser.add_argument(
        "--last",
        default="30d",
        help="Time window such as 30d, 12h, or 60m (default: 30d)",
    )
    metrics_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    metrics_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan for coverage"
    )
    metrics_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to scan for coverage",
    )


def _add_review_command(subparsers):
    review_parser = subparsers.add_parser(
        "review", help="Run a static wiki-aware review of proposed code changes"
    )
    review_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan"
    )
    review_parser.add_argument(
        "--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory to compare against"
    )
    review_parser.add_argument("--base", help="Base ref for git diff comparison")
    review_parser.add_argument("--head", help="Head ref for git diff comparison")
    review_parser.add_argument(
        "--patch", metavar="FILE|-", help="Read an explicit patch from a file or stdin"
    )
    review_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )


def _add_uninstall_command(subparsers):
    uninstall_parser = subparsers.add_parser(
        "uninstall", help="Remove all LLM Wiki artifacts from the project"
    )
    uninstall_parser.add_argument(
        "--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory path"
    )
    uninstall_parser.add_argument(
        "--remove-wiki",
        action="store_true",
        help="Also remove the wiki documentation directory",
    )
    uninstall_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be removed without deleting anything",
    )


def _add_status_command(subparsers):
    status_parser = subparsers.add_parser(
        "status", help="Show LLM Wiki status (agent, hooks, breaker, pages)"
    )
    status_parser.add_argument(
        "--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory path"
    )


def _add_mcp_command(subparsers):
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Run a local MCP server exposing read-only LLM Wiki tools and resources",
    )
    mcp_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan (default: .)"
    )
    mcp_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to expose (default: docs/llm_wiki)",
    )
    mcp_parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="MCP transport to serve (default: stdio)",
    )
    mcp_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP host for --transport http (default: 127.0.0.1)",
    )
    mcp_parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="HTTP port for --transport http (default: 8765)",
    )
    mcp_parser.add_argument(
        "--path",
        default="/mcp",
        help="HTTP MCP endpoint path for --transport http (default: /mcp)",
    )
    mcp_parser.add_argument(
        "--allowed-origin",
        action="append",
        help="Additional HTTP Origin allowed to call the local MCP endpoint",
    )


def _add_obsidian_command(subparsers):
    obsidian_parser = subparsers.add_parser(
        "obsidian",
        help="Export and check an Obsidian-friendly mirror of the LLM Wiki",
    )
    obsidian_sub = obsidian_parser.add_subparsers(dest="obsidian_action", required=True)
    obs_export = obsidian_sub.add_parser(
        "export", help="Export an Obsidian mirror vault"
    )
    obs_export.add_argument("--src-dir", default=".", help="Source directory to scan")
    obs_export.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Canonical wiki directory (default: docs/llm_wiki)",
    )
    obs_export.add_argument(
        "--vault-dir",
        required=True,
        help="Obsidian vault directory where the mirror is written",
    )
    obs_export.add_argument(
        "--notes-dir",
        default=".llm-wiki/obsidian-notes",
        help="Sidecar notes directory, relative to --vault-dir unless absolute",
    )
    obs_export.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mirror writes without changing files",
    )
    obs_export.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    obs_check = obsidian_sub.add_parser(
        "check", help="Check an Obsidian mirror for missing pages and broken wikilinks"
    )
    obs_check.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Canonical wiki directory (default: docs/llm_wiki)",
    )
    obs_check.add_argument(
        "--vault-dir", required=True, help="Obsidian vault directory to check"
    )
    obs_check.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    obs_install = obsidian_sub.add_parser(
        "install-plugin", help="Install the companion Obsidian plugin into a vault"
    )
    obs_install.add_argument(
        "--vault-dir", required=True, help="Obsidian vault directory"
    )
    obs_install.add_argument(
        "--plugin-dir",
        default="integrations/obsidian/llm-wiki",
        help="Source plugin directory (default: integrations/obsidian/llm-wiki)",
    )


def _add_release_command(subparsers):
    release_parser = subparsers.add_parser(
        "release",
        help="Stamp the [Unreleased] CHANGELOG section with the current version",
    )
    release_parser.add_argument(
        "--changelog",
        default="CHANGELOG.md",
        help="Path to the changelog file (default: CHANGELOG.md)",
    )
    release_parser.add_argument(
        "--stage",
        action="store_true",
        help="Git-add CHANGELOG.md after stamping (for use in hooks)",
    )


def _add_upgrade_command(subparsers):
    upgrade_parser = subparsers.add_parser(
        "upgrade",
        help="Refresh all framework-managed artifacts (schema, hooks, dirs) in place",
    )
    upgrade_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory path (default: docs/llm_wiki)",
    )
    upgrade_parser.add_argument(
        "--agent",
        choices=AGENT_CHOICES,
        default=None,
        help="Switch to a different agent (default: keep current)",
    )
    upgrade_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing unrelated post-commit hook",
    )
    upgrade_hints = upgrade_parser.add_mutually_exclusive_group()
    upgrade_hints.add_argument(
        "--quality-hints",
        dest="quality_hints",
        action="store_true",
        default=None,
        help="Include agent quality guidelines in the constraint block",
    )
    upgrade_hints.add_argument(
        "--no-quality-hints",
        dest="quality_hints",
        action="store_false",
        help="Omit agent quality guidelines from the constraint block",
    )


def _add_sync_command(subparsers):
    sync_parser = subparsers.add_parser(
        "sync",
        help="Incrementally update wiki pages for files that changed since last bootstrap/sync",
    )
    sync_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan (default: .)"
    )
    sync_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory (default: docs/llm_wiki)",
    )
    sync_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable persistent inventory cache for this run",
    )
    sync_parser.add_argument(
        "--rebuild-cache",
        action="store_true",
        help="Ignore existing inventory cache and rewrite it after extraction",
    )
    sync_parser.add_argument(
        "--cache-stats",
        action="store_true",
        help="Include inventory cache diagnostics in sync output",
    )
    sync_parser.add_argument(
        "--cache-dir",
        default=None,
        metavar="PATH",
        help="Directory for llm-wiki-inventory-cache.json",
    )
    sync_parser.add_argument(
        "--jobs",
        type=_jobs_value,
        default=1,
        metavar="JOBS",
        help="Parallel extractor jobs for built-ins and opted-in plugins: positive integer or 'auto' (default: 1)",
    )
    sync_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow sync to apply unusually broad source diffs",
    )
    sync_parser.add_argument(
        "--no-preserve-semantic",
        action="store_true",
        help="Disable preservation of existing semantic wiki descriptions",
    )


def _add_migrate_command(subparsers):
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Reconcile legacy wiki pages with current canonical naming",
    )
    migrate_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan (default: .)"
    )
    migrate_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory (default: docs/llm_wiki)",
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration actions without modifying files",
    )
    migrate_parser.add_argument(
        "--chunk-size",
        type=_positive_int,
        metavar="PAGES",
        help="Apply at most this many pending page operations in one migration chunk",
    )
    migrate_parser.add_argument(
        "--chunk",
        type=_positive_int,
        metavar="N",
        help="Apply chunk N from the current --chunk-size plan (default: 1)",
    )
    migrate_parser.add_argument(
        "--plan-chunks",
        action="store_true",
        help="Print the current chunk plan and exit without modifying files",
    )


def _add_context_command(subparsers):
    context_parser = subparsers.add_parser(
        "context",
        help="Return priority-ranked, token-budgeted codebase context for LLM agents",
    )
    context_parser.add_argument(
        "--budget",
        type=int,
        help="Token budget for the context payload (required unless --request is used)",
    )
    context_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan (default: .)"
    )
    context_parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    context_parser.add_argument(
        "--focus",
        choices=["changed", "all"],
        default="changed",
        help="changed=prioritise git diff files, all=treat every file as high priority (default: changed)",
    )
    context_parser.add_argument(
        "--request",
        metavar="FILE|-",
        help="Read a Wiki-as-Context protocol JSON request from a file or stdin",
    )
    context_parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write generated context to a file instead of stdout",
    )
    context_parser.add_argument(
        "--read-only",
        action="store_true",
        help="Guarantee source-adapter mode writes no llm-wiki files except explicit --output",
    )
    context_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )


def _dispatch_command(args):
    _COMMAND_MODULES[args.command].run(args)


def main():
    parser = _build_parser()
    args = parser.parse_args()

    try:
        _dispatch_command(args)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except PathValidationError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        if os.environ.get("LLM_WIKI_DEBUG"):
            raise
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
