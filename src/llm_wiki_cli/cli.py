import argparse
import os
import sys
from .commands import (
    bump_cmd,
    ci_check_cmd,
    docs_cmd,
    doctor_cmd,
    generate_prompt_cmd,
    hook_cmd,
    install_ci_cmd,
    init_cmd,
    install_cmd,
    knowledge_cmd,
    mcp_cmd,
    metrics_cmd,
    migrate_cmd,
    obsidian_cmd,
    plugins_cmd,
    prepare_extractors_cmd,
    release_cmd,
    review_cmd,
    site_cmd,
    skills_cmd,
    status_cmd,
    sync_cmd,
    team_cmd,
    trigger_cmd,
    uninstall_cmd,
    upgrade_cmd,
)
from .config import AGENT_CHOICES, DEFAULT_WIKI_DIR, PathValidationError
from .services import (
    bootstrap_runtime as bootstrap_cmd,
    context_service as context_cmd,
    extraction_service as extract_cmd,
    lint_service as lint_cmd,
)
from .services.contracts import BOOTSTRAP_SKIP_DATA_FLOW_FLAG
from .services.extraction_jobs import ExtractionJobsAction
from .services.resource_diagnostics import resource_failure_hint
from . import __version__


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must not be negative")
    return parsed


def _surface_values(value: str) -> tuple[str, ...]:
    values = tuple(part.strip().lower() for part in value.split(",") if part.strip())
    if not values:
        raise argparse.ArgumentTypeError("must name at least one surface")
    invalid = [
        surface for surface in values if surface not in sync_cmd.INITIALIZABLE_SURFACES
    ]
    if invalid:
        allowed = ", ".join(sync_cmd.INITIALIZABLE_SURFACES)
        raise argparse.ArgumentTypeError(
            f"unknown surface {invalid[0]!r}; choose from: {allowed}"
        )
    return values


def _add_helper_cache_argument(parser):
    parser.add_argument(
        "--helper-cache-dir",
        default=None,
        metavar="PATH",
        help=HELPER_CACHE_HELP,
    )


def _add_include_tests_argument(parser):
    parser.add_argument(
        "--include-tests",
        action="append",
        choices=INCLUDE_TEST_LANGUAGES,
        default=None,
        help=INCLUDE_TESTS_HELP,
    )


def _add_source_selection_argument(parser):
    parser.add_argument(
        "--source-selection",
        default=None,
        metavar="PATH",
        help=(
            "Repository-relative source-selection JSON override; otherwise "
            "discover .llm-wiki/source-selection.json under --src-dir"
        ),
    )


def _add_jobs_argument(parser):
    parser.set_defaults(requested_jobs=1)
    parser.add_argument(
        "--jobs",
        action=ExtractionJobsAction,
        default=1,
        metavar="JOBS",
        help=(
            "Parallel extractor jobs for built-ins and opted-in plugins: "
            "positive integer or 'auto' (default: 1)"
        ),
    )


_COMMAND_MODULES = {
    "init": init_cmd,
    "extract": extract_cmd,
    "lint": lint_cmd,
    "prepare-extractors": prepare_extractors_cmd,
    "ci-check": ci_check_cmd,
    "install-hook": hook_cmd,
    "install-ci": install_ci_cmd,
    "install": install_cmd,
    "knowledge": knowledge_cmd,
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
    "site": site_cmd,
    "skills": skills_cmd,
    "release": release_cmd,
    "upgrade": upgrade_cmd,
    "sync": sync_cmd,
    "migrate": migrate_cmd,
    "context": context_cmd,
    "docs": docs_cmd,
    "doctor": doctor_cmd,
}

HELPER_CACHE_HELP = (
    "Directory for prepared TypeScript/JavaScript/Go/Rust/Haskell extractor helpers"
)
INCLUDE_TEST_LANGUAGES = ("go",)
INCLUDE_TESTS_HELP = (
    "Include language-specific test files in extraction; may be repeated"
)


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
    _add_install_ci_command(subparsers)
    _add_install_command(subparsers)
    _add_knowledge_command(subparsers)
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
    _add_site_command(subparsers)
    _add_skills_command(subparsers)
    _add_release_command(subparsers)
    _add_upgrade_command(subparsers)
    _add_sync_command(subparsers)
    _add_migrate_command(subparsers)
    _add_context_command(subparsers)
    _add_docs_command(subparsers)
    _add_doctor_command(subparsers)


def _add_doctor_command(subparsers):
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Report current wiki knowledge health with CI-friendly exit codes",
    )
    doctor_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to inspect (default: docs/llm_wiki)",
    )
    doctor_parser.add_argument(
        "--src-dir",
        default=".",
        help="Source directory to compare with the wiki",
    )
    doctor_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )
    doctor_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    doctor_parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Classify indeterminate or nonsemantic source drift as unhealthy"
        ),
    )
    _add_helper_cache_argument(doctor_parser)
    _add_include_tests_argument(doctor_parser)
    _add_source_selection_argument(doctor_parser)
    _add_jobs_argument(doctor_parser)


def _add_init_command(subparsers):
    init_parser = subparsers.add_parser(
        "init", help="Scaffold LLM Wiki structure and schema"
    )
    init_parser.add_argument(
        "--agent",
        choices=AGENT_CHOICES,
        default=None,
        help="Target agent format (default: stored agent, or generic for a new project)",
    )
    init_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to create (default: docs/llm_wiki)",
    )
    init_parser.add_argument(
        "--no-quality-hints",
        action="store_true",
        default=None,
        help="Omit agent quality guidelines from the constraint block",
    )
    init_parser.add_argument(
        "--no-skills",
        action="store_true",
        default=None,
        help="Skip installing the wiki-reference skill into the agent's skills directory (.claude/skills for claude, .llm-wiki/skills otherwise)",
    )
    init_issue_reporting = init_parser.add_mutually_exclusive_group()
    init_issue_reporting.add_argument(
        "--issue-reporting",
        dest="issue_reporting",
        action="store_true",
        default=None,
        help="Include local agent instructions for llm-wiki tool issues; does not submit reports",
    )
    init_issue_reporting.add_argument(
        "--no-issue-reporting",
        dest="issue_reporting",
        action="store_false",
        help="Omit local agent instructions for reporting llm-wiki tool issues (default)",
    )
    _add_source_selection_argument(init_parser)


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
        "--openapi-file",
        default=None,
        metavar="PATH",
        help="Use a source-contained OpenAPI 3.0/3.1 JSON or YAML contract (requires --deep)",
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
    _add_include_tests_argument(extract_parser)
    _add_helper_cache_argument(extract_parser)
    _add_source_selection_argument(extract_parser)
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
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )
    lint_parser.add_argument(
        "--strict",
        action="store_true",
        help="Require core wiki structure and a fresh sync manifest",
    )
    lint_parser.add_argument(
        "--knowledge-drift-report",
        action="store_true",
        help=(
            "Run strict lint and include native freshness/drift findings as "
            "nonblocking diagnostics (default: disabled)"
        ),
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
        "--media-size-warn-bytes",
        type=_positive_int,
        default=None,
        metavar="BYTES",
        help="Warn when a referenced media asset exceeds this size in bytes",
    )
    _add_helper_cache_argument(lint_parser)
    _add_include_tests_argument(lint_parser)
    _add_source_selection_argument(lint_parser)
    _add_jobs_argument(lint_parser)


def _add_prepare_extractors_command(subparsers):
    prepare_parser = subparsers.add_parser(
        "prepare-extractors",
        help="Prepare TypeScript/JavaScript, Go, Rust, and Haskell extractor helpers",
    )
    prepare_parser.add_argument(
        "--src-dir", default=".", help="Source directory to inspect"
    )
    prepare_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
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
        choices=["typescript", "go", "rust", "haskell"],
        help="Helper language to prepare; may be repeated",
    )
    prepare_parser.add_argument(
        "--plan",
        action="store_true",
        help="Print the selected helper languages without preparing or writing them",
    )
    prepare_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Plan output format (default: text; requires --plan for JSON)",
    )
    _add_source_selection_argument(prepare_parser)


def _add_ci_check_command(subparsers):
    ci_parser = subparsers.add_parser(
        "ci-check", help="Run strict wiki validation and write a CI report"
    )
    ci_parser.add_argument("--src-dir", default=".", help="Source directory to scan")
    ci_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )
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
        "--knowledge-drift-report",
        action="store_true",
        help=(
            "Include native freshness/drift findings as nonblocking diagnostics "
            "(default: disabled)"
        ),
    )
    ci_parser.add_argument(
        "--no-plugins",
        action="store_true",
        help="Disable project-local extractor, generation, and lint plugins",
    )
    _add_helper_cache_argument(ci_parser)
    _add_include_tests_argument(ci_parser)
    _add_source_selection_argument(ci_parser)
    _add_jobs_argument(ci_parser)


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
    _add_source_selection_argument(hook_parser)


def _add_install_ci_command(subparsers):
    install_ci_parser = subparsers.add_parser(
        "install-ci",
        help="Install a portable LLM Wiki integrity workflow",
    )
    install_ci_parser.add_argument(
        "--action-ref",
        required=True,
        metavar="SHA",
        help="Immutable 40-hex commit for the reusable integrity action",
    )
    install_ci_parser.add_argument(
        "--src-dir",
        default=".",
        help="Project-relative source directory evaluated by the wiki (default: .)",
    )
    install_ci_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Managed wiki directory (default: docs/llm_wiki)",
    )
    install_ci_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview the workflow without writing it",
    )
    install_ci_parser.add_argument(
        "--force",
        action="store_true",
        help="Replace a workflow not recognized as unmodified llm-wiki output",
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


def _add_knowledge_wiki_argument(parser):
    parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory (default: docs/llm_wiki)",
    )


def _add_knowledge_dry_run(parser):
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview the complete change without writing files",
    )


def _add_governance_actor_arguments(parser):
    parser.add_argument(
        "--actor-kind",
        choices=sorted(knowledge_cmd.ACTOR_KINDS),
        required=True,
        help="Explicit lifecycle-event actor kind",
    )
    parser.add_argument(
        "--actor-id",
        required=True,
        help="Explicit lifecycle-event actor identifier",
    )
    parser.add_argument(
        "--authored-at",
        required=True,
        metavar="RFC3339",
        help="Real authored event time with timezone",
    )


def _add_lifecycle_arguments(
    parser,
    *,
    reason: str,
    successor: bool = False,
):
    _add_knowledge_wiki_argument(parser)
    parser.add_argument("--uid", required=True, help="Stable concept UID")
    if successor:
        parser.add_argument(
            "--successor-uid",
            required=True,
            help="Different existing UID that supersedes this concept",
        )
    _add_governance_actor_arguments(parser)
    parser.add_argument(
        "--reason",
        default=reason,
        help="Lowercase machine reason recorded with the event",
    )
    _add_knowledge_dry_run(parser)


def _add_knowledge_command(subparsers):
    knowledge = subparsers.add_parser(
        "knowledge",
        help="Manage durable concept identity, lifecycle, review, and verification",
    )
    actions = knowledge.add_subparsers(dest="knowledge_action", required=True)

    initialize = actions.add_parser(
        "init",
        help="Initialize stable bundle identity and allocate concept UIDs",
    )
    _add_knowledge_wiki_argument(initialize)
    initialize.add_argument(
        "--bundle-id",
        default=None,
        help="Explicit stable bundle ID; generated securely when omitted",
    )
    _add_knowledge_dry_run(initialize)

    status = actions.add_parser(
        "status",
        help="Show validated governance, lifecycle, and review state",
    )
    _add_knowledge_wiki_argument(status)
    status.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    status.add_argument(
        "--event-limit",
        type=_positive_int,
        default=20,
        help="Maximum lifecycle and review events shown per concept",
    )

    move = actions.add_parser(
        "move",
        help="Explicitly carry one UID to a new current locator and natural key",
    )
    _add_knowledge_wiki_argument(move)
    move.add_argument("--uid", required=True, help="Stable concept UID")
    move.add_argument(
        "--locator",
        "--to-locator",
        dest="locator",
        required=True,
        help="New canonical concept locator",
    )
    move.add_argument(
        "--natural-key",
        "--to-natural-key",
        dest="natural_key",
        required=True,
        help="New stable-allocation natural key",
    )
    _add_knowledge_dry_run(move)

    alias = actions.add_parser(
        "alias",
        help="Add one explicit historical locator or natural-key alias",
    )
    _add_knowledge_wiki_argument(alias)
    alias.add_argument("--uid", required=True, help="Stable concept UID")
    alias.add_argument(
        "--type",
        dest="alias_type",
        choices=(
            knowledge_cmd.ALIAS_LOCATOR,
            knowledge_cmd.ALIAS_NATURAL_KEY,
        ),
        required=True,
        help="Alias coordinate type",
    )
    alias.add_argument("--value", required=True, help="Historical alias value")
    _add_knowledge_dry_run(alias)

    lifecycle = actions.add_parser(
        "lifecycle",
        help="Append an explicit lifecycle transition",
    )
    lifecycle_actions = lifecycle.add_subparsers(
        dest="lifecycle_action",
        required=True,
    )
    lifecycle_set = lifecycle_actions.add_parser(
        "set",
        help="Set an allowed lifecycle state",
    )
    _add_lifecycle_arguments(
        lifecycle_set,
        reason="explicit-lifecycle-change",
    )
    lifecycle_set.add_argument(
        "--state",
        choices=("draft", "active", "deprecated", "superseded"),
        required=True,
    )
    lifecycle_set.add_argument(
        "--successor-uid",
        default=None,
        help="Required only when --state superseded",
    )

    lifecycle_deprecate = lifecycle_actions.add_parser(
        "deprecate",
        help="Explicitly deprecate one concept",
    )
    _add_lifecycle_arguments(
        lifecycle_deprecate,
        reason="explicit-deprecation",
    )
    lifecycle_supersede = lifecycle_actions.add_parser(
        "supersede",
        help="Explicitly supersede one concept",
    )
    _add_lifecycle_arguments(
        lifecycle_supersede,
        reason="explicit-supersession",
        successor=True,
    )

    deprecate = actions.add_parser(
        "deprecate",
        help="Explicitly deprecate one concept",
    )
    _add_lifecycle_arguments(
        deprecate,
        reason="explicit-deprecation",
    )
    supersede = actions.add_parser(
        "supersede",
        help="Explicitly supersede one concept",
    )
    _add_lifecycle_arguments(
        supersede,
        reason="explicit-supersession",
        successor=True,
    )

    review = actions.add_parser(
        "review",
        help="Record a digest-bound human review of one semantic section",
    )
    _add_knowledge_wiki_argument(review)
    review.add_argument("--uid", required=True, help="Stable concept UID")
    review.add_argument(
        "--section",
        required=True,
        help="Exact semantic section locator",
    )
    review.add_argument(
        "--reviewer-kind",
        choices=("human",),
        required=True,
        help="Explicit reviewer actor kind",
    )
    review.add_argument(
        "--reviewer-id",
        required=True,
        help="Explicit reviewer identifier",
    )
    review.add_argument(
        "--method",
        required=True,
        help="Review method identifier",
    )
    review.add_argument(
        "--method-version",
        required=True,
        help="Review method version",
    )
    review.add_argument(
        "--authored-at",
        required=True,
        metavar="RFC3339",
        help="Real authored event time with timezone",
    )
    _add_knowledge_dry_run(review)

    verify = actions.add_parser(
        "verify",
        help="Explicitly run application-owned pure knowledge checkers",
    )
    _add_knowledge_wiki_argument(verify)
    verify.add_argument(
        "--checker",
        action="append",
        choices=("artifact-integrity", "internal-links"),
        default=None,
        help="Application-owned checker ID; may be repeated (default: all)",
    )
    verify.add_argument(
        "--uid",
        default=None,
        help="Limit checker scope to one current governed concept UID",
    )
    _add_knowledge_dry_run(verify)


def _add_plugins_command(subparsers):
    plugins_parser = subparsers.add_parser(
        "plugins", help="Manage installed llm-wiki plugins"
    )
    plugins_sub = plugins_parser.add_subparsers(dest="plugins_action", required=True)
    plugins_sub.add_parser("list", help="List installed plugins")
    plugins_samples = plugins_sub.add_parser(
        "samples", help="List or export bundled sample plugins"
    )
    samples_sub = plugins_samples.add_subparsers(dest="samples_action", required=True)
    samples_sub.add_parser("list", help="List bundled sample plugins")
    samples_export = samples_sub.add_parser(
        "export", help="Export a bundled sample plugin to a local directory"
    )
    samples_export.add_argument("sample_id", help="Bundled sample plugin id")
    samples_export.add_argument(
        "--dest",
        required=True,
        metavar="PATH",
        help="Destination directory for the exported sample plugin",
    )
    samples_export.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing exported sample plugin directory",
    )
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
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )
    team_check.add_argument(
        "--wiki-dir", default=DEFAULT_WIKI_DIR, help="Wiki directory to validate"
    )
    team_check.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    _add_source_selection_argument(team_check)
    team_resolve = team_sub.add_parser(
        "resolve-conflicts", help="Safely resolve generated wiki conflicts"
    )
    team_resolve.add_argument("--src-dir", default=".", help="Source directory to scan")
    team_resolve.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )
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
    _add_source_selection_argument(team_resolve)


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
        "--src-dir",
        default=".",
        help="Source directory to scan (default: current directory)",
    )
    trigger_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
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
    _add_source_selection_argument(trigger_parser)


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
        help=argparse.SUPPRESS,
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
        "--api-contracts",
        action="store_true",
        help=(
            "Generate the optional api-contracts.md production HTTP inventory "
            "from static FastAPI analysis"
        ),
    )
    bootstrap_parser.add_argument(
        "--openapi-file",
        default=None,
        metavar="PATH",
        help=(
            "Use a source-root-relative OpenAPI JSON/YAML document as the "
            "authoritative HTTP contract; implies --api-contracts and full depth"
        ),
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
    _add_helper_cache_argument(bootstrap_parser)
    _add_include_tests_argument(bootstrap_parser)
    _add_source_selection_argument(bootstrap_parser)


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
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
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
    _add_source_selection_argument(gp_parser)


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
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )
    metrics_parser.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to scan for coverage",
    )
    _add_source_selection_argument(metrics_parser)


def _add_review_command(subparsers):
    review_parser = subparsers.add_parser(
        "review", help="Run a static wiki-aware review of proposed code changes"
    )
    review_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan"
    )
    review_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
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
    _add_source_selection_argument(review_parser)


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
    status_parser.add_argument(
        "--src-dir",
        default=".",
        help="Source directory used to evaluate source-selection identity",
    )
    status_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )
    _add_source_selection_argument(status_parser)


def _add_mcp_command(subparsers):
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Run a local MCP server exposing read-only LLM Wiki tools and resources",
    )
    mcp_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan (default: .)"
    )
    mcp_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
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
    _add_source_selection_argument(mcp_parser)


def _add_obsidian_command(subparsers):
    obsidian_parser = subparsers.add_parser(
        "obsidian",
        help="Export and check an Obsidian-friendly mirror of the LLM Wiki",
    )
    obsidian_sub = obsidian_parser.add_subparsers(dest="obsidian_action", required=True)
    obs_export = obsidian_sub.add_parser(
        "export", help="Export an Obsidian mirror vault"
    )
    obs_export.add_argument(
        "--src-dir",
        default=".",
        help=(
            "Source directory for the legacy unenriched relationship scan; "
            "knowledge-enriched export does not scan it"
        ),
    )
    obs_export.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
    )
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
    _add_source_selection_argument(obs_export)
    _add_projection_metadata_arguments(
        obs_export,
        public_identity_dest="knowledge_public_repository_identity",
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
    _add_projection_metadata_arguments(
        obs_check,
        public_identity_dest="knowledge_public_repository_identity",
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


def _add_site_command(subparsers):
    site_parser = subparsers.add_parser(
        "site",
        help="Export and check a static-site-friendly mirror of the LLM Wiki",
    )
    site_sub = site_parser.add_subparsers(dest="site_action", required=True)
    site_export = site_sub.add_parser(
        "export", help="Export a static-site-friendly Markdown mirror"
    )
    site_export.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Canonical wiki directory (default: docs/llm_wiki)",
    )
    _add_site_hub_arguments(site_export)
    site_export.add_argument(
        "--out-dir",
        required=True,
        help="Output directory for the derived static-site mirror",
    )
    site_export.add_argument(
        "--format",
        choices=site_cmd.SITE_FORMAT_CHOICES,
        default="plain",
        help="Static-site output format (default: plain)",
    )
    site_export.add_argument(
        "--file-friendly",
        action="store_true",
        help=(
            "For MkDocs exports opened directly from disk, emit direct-file "
            "links with use_directory_urls: false"
        ),
    )
    site_export.add_argument(
        "--profile",
        choices=site_cmd.SITE_PROFILE_CHOICES,
        default="reference",
        help="Documentation profile to export (default: reference)",
    )
    site_export.add_argument(
        "--site-name",
        default=None,
        help="Human-facing site name required by --profile user",
    )
    site_export.add_argument(
        "--front-matter",
        action="store_true",
        help="Add safe llm_wiki front matter to exported pages",
    )
    site_export.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview mirror writes without changing files",
    )
    site_export.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Console output format (default: text)",
    )
    _add_projection_metadata_arguments(
        site_export,
        public_identity_dest="public_repository_identity",
    )
    site_check = site_sub.add_parser(
        "check", help="Check a static-site mirror for missing pages and links"
    )
    site_check.add_argument(
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Canonical wiki directory (default: docs/llm_wiki)",
    )
    _add_site_hub_arguments(site_check)
    site_check.add_argument(
        "--out-dir",
        required=True,
        help="Output directory for the derived static-site mirror",
    )
    site_check.add_argument(
        "--format",
        choices=site_cmd.SITE_FORMAT_CHOICES,
        default=None,
        help=(
            "Require the mirror receipt to use this static-site format "
            "(default: use the recorded format)"
        ),
    )
    site_check.add_argument(
        "--built-site-dir",
        default=None,
        help="Built static site directory to validate for internal HTML links",
    )
    site_check.add_argument(
        "--link-mode",
        choices=site_cmd.LINK_MODE_CHOICES,
        default="http",
        help=(
            "Required publication distribution and built-link contract: "
            "HTTP routing or direct file browsing (default: http)"
        ),
    )
    site_check.add_argument(
        "--profile",
        choices=site_cmd.SITE_PROFILE_CHOICES,
        default="reference",
        help="Documentation profile quality gates to apply (default: reference)",
    )
    site_check.add_argument(
        "--site-name",
        default=None,
        help="Human-facing site name required by --profile user",
    )
    site_check.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Console output format (default: text)",
    )
    _add_projection_metadata_arguments(
        site_check,
        public_identity_dest="public_repository_identity",
    )


def _add_projection_metadata_arguments(parser, *, public_identity_dest: str):
    parser.add_argument(
        "--knowledge-metadata",
        choices=site_cmd.KNOWLEDGE_METADATA_CHOICES,
        default=None,
        help=(
            "Opt in to validated native-knowledge front matter "
            "(currently: summary)"
        ),
    )
    parser.add_argument(
        "--knowledge-profile",
        choices=site_cmd.KNOWLEDGE_PROFILE_CHOICES,
        default="public-portable",
        help="Knowledge redaction profile (default: public-portable)",
    )
    parser.add_argument(
        "--knowledge-public-repository-identity",
        dest=public_identity_dest,
        default=None,
        metavar="IDENTITY",
        help=(
            "Disclose an exact configured-public repository identity in the "
            "public projection"
        ),
    )


def _add_site_hub_arguments(parser):
    parser.add_argument(
        "--wiki-root",
        default=None,
        help=(
            "Directory containing source wiki subdirectories for hub export/check "
            "(for example sources/code_wikis)"
        ),
    )
    parser.add_argument(
        "--wiki",
        action="append",
        default=None,
        help=("Explicit source wiki directory for hub export/check; may be repeated"),
    )


def _add_skills_command(subparsers):
    skills_parser = subparsers.add_parser(
        "skills",
        help="List, export, and install bundled agent skills (SKILL.md workflows)",
    )
    skills_sub = skills_parser.add_subparsers(dest="skills_action", required=True)
    skills_list = skills_sub.add_parser("list", help="List bundled agent skills")
    skills_list.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    skills_export = skills_sub.add_parser(
        "export", help="Export bundled agent skills to a directory"
    )
    skills_export.add_argument(
        "--dest",
        required=True,
        help="Destination skills directory (e.g. ~/.claude/skills)",
    )
    _add_skills_selection_arguments(skills_export)
    skills_install = skills_sub.add_parser(
        "install", help="Install bundled agent skills into this project"
    )
    skills_install.add_argument(
        "--dest",
        default=None,
        help=(
            "Project-relative skills directory (default: the configured "
            "agent's skills dir — .claude/skills for claude, "
            ".llm-wiki/skills otherwise)"
        ),
    )
    _add_skills_selection_arguments(skills_install)


def _add_skills_selection_arguments(parser):
    parser.add_argument(
        "--skill",
        action="append",
        default=None,
        metavar="NAME",
        help="Skill to include; may be repeated (default: all bundled skills)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing skill files that differ from the bundled version",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
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
    upgrade_skills = upgrade_parser.add_mutually_exclusive_group()
    upgrade_skills.add_argument(
        "--skills",
        dest="skills",
        action="store_true",
        default=None,
        help="Refresh the wiki-reference skill in the configured agent's skills directory (.claude/skills for claude, .llm-wiki/skills otherwise)",
    )
    upgrade_skills.add_argument(
        "--no-skills",
        dest="skills",
        action="store_false",
        help="Skip refreshing the wiki-reference skill in the configured agent's skills directory (.claude/skills for claude, .llm-wiki/skills otherwise)",
    )
    upgrade_issue_reporting = upgrade_parser.add_mutually_exclusive_group()
    upgrade_issue_reporting.add_argument(
        "--issue-reporting",
        dest="issue_reporting",
        action="store_true",
        default=None,
        help="Include local agent instructions for llm-wiki tool issues; does not submit reports",
    )
    upgrade_issue_reporting.add_argument(
        "--no-issue-reporting",
        dest="issue_reporting",
        action="store_false",
        help="Omit local agent instructions for reporting llm-wiki tool issues",
    )
    _add_source_selection_argument(upgrade_parser)


def _add_sync_command(subparsers):
    sync_parser = subparsers.add_parser(
        "sync",
        help="Incrementally update wiki pages for files that changed since last bootstrap/sync",
    )
    sync_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan (default: .)"
    )
    sync_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
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
    _add_helper_cache_argument(sync_parser)
    _add_include_tests_argument(sync_parser)
    _add_jobs_argument(sync_parser)
    sync_parser.add_argument(
        "--force",
        action="store_true",
        help="Allow sync to apply unusually broad source or surface diffs",
    )
    openapi_group = sync_parser.add_mutually_exclusive_group()
    openapi_group.add_argument(
        "--openapi-file",
        default=None,
        metavar="PATH",
        help=(
            "Use a source-root-contained OpenAPI 3.0/3.1 JSON or YAML file as "
            "the authoritative API contract"
        ),
    )
    openapi_group.add_argument(
        "--clear-openapi-file",
        action="store_true",
        help="Clear persisted OpenAPI authority and return to static contracts",
    )
    sync_parser.add_argument(
        "--initialize-surfaces",
        action="append",
        type=_surface_values,
        default=None,
        metavar="SURFACE[,SURFACE...]",
        help=(
            "Initialize optional wiki surfaces; accepted values are flows, "
            "dependencies, and api-contracts; may be repeated"
        ),
    )
    sync_parser.add_argument(
        "--flow-category",
        action="append",
        default=None,
        metavar="CATEGORY",
        help="Only initialize flow entry points in this category; may be repeated",
    )
    sync_parser.add_argument(
        "--exclude-tests",
        action="store_true",
        help="Exclude test sources from explicitly initialized surfaces",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Preview source, optional-surface, and knowledge artifact actions "
            "without modifying files"
        ),
    )
    sync_parser.add_argument(
        "--no-plugins",
        action="store_true",
        help="Disable all project-local plugins during sync",
    )
    sync_parser.add_argument(
        "--no-preserve-semantic",
        action="store_true",
        help="Disable preservation of existing semantic wiki descriptions",
    )
    _add_source_selection_argument(sync_parser)


def _add_migrate_command(subparsers):
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Reconcile legacy wiki pages with current canonical naming",
    )
    migrate_parser.add_argument(
        "--src-dir", default=".", help="Source directory to scan (default: .)"
    )
    migrate_parser.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow --src-dir to point outside the current working directory",
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
    _add_source_selection_argument(migrate_parser)


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
        "--wiki-dir",
        default=DEFAULT_WIKI_DIR,
        help="Wiki directory to read graph surface metadata from (default: docs/llm_wiki)",
    )
    context_parser.add_argument(
        "--format",
        choices=["json", "markdown", "packet"],
        default="json",
        help="Output format; packet emits canonical Qualified Context Packet JSON (default: json)",
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
    context_parser.add_argument(
        "--prefer-fresh",
        action="store_true",
        help="Under budget pressure, prefer CURRENT context within an existing relevance tier",
    )
    _add_source_selection_argument(context_parser)


def _add_docs_command(subparsers):
    docs_parser = subparsers.add_parser(
        "docs",
        help="Prepare and supervise a standalone documentation workspace",
    )
    docs_sub = docs_parser.add_subparsers(dest="docs_action", required=True)

    prepare = docs_sub.add_parser(
        "prepare",
        help="Create or idempotently resume a deterministic documentation run",
    )
    prepare.add_argument(
        "--workspace",
        required=True,
        help="Explicit external documentation workspace",
    )
    prepare.add_argument(
        "--baseline",
        choices=["bootstrap-source", "existing-wiki"],
        required=True,
        help="Build a wiki from source or adopt an existing llm-wiki snapshot",
    )
    prepare.add_argument(
        "--src-dir",
        default=None,
        help="Read-only source directory; required by bootstrap-source",
    )
    prepare.add_argument(
        "--input-wiki-dir",
        default=None,
        help="Read-only llm-wiki directory; required by existing-wiki",
    )
    prepare.add_argument(
        "--wiki-freshness",
        choices=["require-current", "refresh-snapshot", "allow-unverified"],
        default="require-current",
        help="Freshness policy for an adopted wiki (default: require-current)",
    )
    prepare.add_argument(
        "--site-name",
        required=True,
        help="Human-facing documentation site name",
    )
    intake_source = prepare.add_mutually_exclusive_group()
    intake_source.add_argument(
        "--project-brief",
        metavar="FILE",
        help="UTF-8 project-purpose brief supplied by the supervisor",
    )
    intake_source.add_argument(
        "--intake-file",
        metavar="FILE|-",
        help="Structured JSON intake object supplied by the supervisor",
    )
    prepare.add_argument(
        "--audience",
        action="append",
        help="Audience name or comma-separated audience names; may be repeated",
    )
    prepare.add_argument(
        "--audience-intent",
        action="append",
        metavar="AUDIENCE=INTENT",
        help="Trusted audience job/intent; may be repeated",
    )
    prepare.add_argument(
        "--live-service-url",
        default=None,
        help="Caller-owned HTTP(S) staging/demo endpoint to record",
    )
    prepare.add_argument(
        "--live-service-access-mode",
        choices=["unspecified", "anonymous", "non-secret"],
        default="unspecified",
        help="Non-secret access mode for the declared service",
    )
    prepare.add_argument(
        "--observe-live-service",
        action="store_true",
        help="Authorize read-only observation; requires --capture-dir",
    )
    prepare.add_argument(
        "--helper-cache-dir",
        default=None,
        metavar="PATH",
        help="Explicit cache containing already-prepared extractor helpers",
    )
    prepare.add_argument(
        "--capture-dir",
        default=None,
        metavar="PATH",
        help="Explicit disposable root for authorized live-service captures",
    )
    prepare.add_argument(
        "--trust-source-plugins",
        action="store_true",
        help="Explicitly opt in to executing source-repository extractor plugins",
    )
    prepare.add_argument(
        "--allow-external-src",
        action="store_true",
        help="Allow source/input-wiki evidence roots outside the current directory",
    )
    prepare.add_argument(
        "--semantic-budget",
        type=_nonnegative_int,
        default=30,
        metavar="COUNT",
        help="Maximum P1 semantic work items (default: 30)",
    )
    prepare.add_argument(
        "--adjustment-loop-limit",
        type=_positive_int,
        default=3,
        metavar="COUNT",
        help="Maximum review adjustment loops (default: 3)",
    )
    prepare.add_argument(
        "--site-format",
        choices=["mkdocs", "plain", "docusaurus"],
        default="mkdocs",
        help="Persisted distribution format (default: mkdocs)",
    )
    prepare_link_mode = prepare.add_mutually_exclusive_group()
    prepare_link_mode.add_argument(
        "--link-mode",
        choices=["http", "file"],
        default="http",
        help="Persisted built-link contract (default: http)",
    )
    prepare_link_mode.add_argument(
        "--file-friendly",
        action="store_true",
        help="Persist direct-file link mode for local browsing",
    )
    prepare.add_argument(
        "--knowledge-mode",
        choices=docs_cmd.KNOWLEDGE_MODE_CHOICES,
        default="off",
        help=(
            "Persist native metadata policy: off, public-portable, or explicitly "
            "authorized internal (default: off)"
        ),
    )
    prepare.add_argument(
        "--knowledge-public-repository-identity",
        default=None,
        metavar="IDENTITY",
        help=(
            "Corroborated configured-public identity for public-portable metadata"
        ),
    )
    prepare.add_argument(
        "--refresh",
        action="store_true",
        help="Archive owned run artifacts and explicitly rebuild the workspace baseline",
    )
    _add_source_selection_argument(prepare)
    prepare.add_argument(
        "--output-format",
        "--format",
        dest="output_format",
        choices=["text", "json"],
        default="text",
        help="Console output format (default: text)",
    )

    status = docs_sub.add_parser("status", help="Show run state and next actions")
    status.add_argument("--workspace", required=True)
    status.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    packet = docs_sub.add_parser(
        "packet",
        help="Build a provider-neutral agent packet for one bounded stage",
    )
    packet.add_argument("--workspace", required=True)
    packet.add_argument(
        "--stage",
        choices=["wiki-enrichment", "user-docs", "review"],
        required=True,
    )
    packet.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    record_result = docs_sub.add_parser(
        "record-result",
        help="Reconcile a versioned agent-result JSON object with workspace changes",
    )
    record_result.add_argument("--workspace", required=True)
    record_result.add_argument(
        "--result",
        required=True,
        metavar="FILE|-",
        help="Agent-result JSON file, or - for stdin",
    )
    record_result.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    verify = docs_sub.add_parser(
        "verify",
        help="Run deterministic integrity and readiness checks",
    )
    verify.add_argument("--workspace", required=True)
    verify.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    verify.add_argument(
        "--no-advance",
        action="store_true",
        help="Report verification without advancing an eligible review run",
    )

    export = docs_sub.add_parser(
        "export",
        help="Export/check local user documentation and write a deployment handoff",
    )
    export.add_argument("--workspace", required=True)
    export.add_argument(
        "--format",
        choices=["mkdocs", "plain", "docusaurus"],
        default=None,
        help="Assert the distribution format selected during prepare",
    )
    export.add_argument(
        "--file-friendly",
        action="store_true",
        help="Assert direct-file link mode was selected during prepare",
    )
    export.add_argument(
        "--build",
        action="store_true",
        help="Authorize an installed site builder to run locally",
    )
    export.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Console output format (default: text)",
    )
    export.add_argument(
        "--knowledge-mode",
        choices=docs_cmd.KNOWLEDGE_MODE_CHOICES,
        default=None,
        help="Assert the native metadata policy selected during prepare",
    )
    export.add_argument(
        "--knowledge-public-repository-identity",
        default=None,
        metavar="IDENTITY",
        help="Assert the public repository identity selected during prepare",
    )
    export.add_argument(
        "--builder-command",
        nargs=argparse.REMAINDER,
        default=None,
        metavar="ARG",
        help=(
            "Explicit builder argv passed directly without a shell; requires --build "
            "and must be the final CLI option"
        ),
    )

    calibration = docs_sub.add_parser(
        "calibration",
        help="Supervise an evidence-backed documentation calibration cohort",
    )
    calibration_sub = calibration.add_subparsers(
        dest="calibration_action",
        required=True,
    )

    calibration_prepare = calibration_sub.add_parser(
        "prepare",
        help="Freeze two independently prepared documentation controls",
    )
    calibration_prepare.add_argument("--root", required=True)
    calibration_prepare.add_argument(
        "--control-workspace",
        action="append",
        required=True,
        metavar="PATH",
        help="Prepared documentation control workspace; specify exactly twice",
    )
    calibration_prepare.add_argument(
        "--execution-manifest",
        required=True,
        metavar="FILE|-",
        help="Versioned execution-manifest JSON file, or - for stdin",
    )

    calibration_admit = calibration_sub.add_parser(
        "admit",
        help="Authorize the frozen cohort after isolation evidence is verified",
    )
    calibration_admit.add_argument("--root", required=True)
    calibration_admit.add_argument(
        "--authority-grant",
        required=True,
        metavar="FILE|-",
        help="Versioned authority-grant JSON file, or - for stdin",
    )
    calibration_admit.add_argument(
        "--broker-attestation",
        default=None,
        metavar="FILE|-",
        help=(
            "External-broker attestation JSON; qualification also requires a "
            "separately established embedding-host authenticator"
        ),
    )

    calibration_status = calibration_sub.add_parser(
        "status",
        help="Show the current cohort state as JSON",
    )
    calibration_status.add_argument("--root", required=True)

    calibration_packet = calibration_sub.add_parser(
        "packet",
        help="Write one bounded provider-neutral role packet as JSON",
    )
    calibration_packet.add_argument("--root", required=True)
    calibration_packet.add_argument(
        "--role",
        choices=["intake-a", "intake-b", "intake-c", "verifier"],
        required=True,
    )
    calibration_packet.add_argument(
        "--output",
        required=True,
        metavar="FILE",
        help="Explicit packet JSON output path; packet content is never printed",
    )

    calibration_dispatch = calibration_sub.add_parser(
        "dispatch",
        help="Dispatch one role through the frozen broker",
    )
    calibration_dispatch.add_argument("--root", required=True)
    calibration_dispatch.add_argument(
        "--role",
        choices=["intake-a", "intake-b", "intake-c", "verifier"],
        required=True,
    )

    calibration_result = calibration_sub.add_parser(
        "record-result",
        help="Import a separately executed broker receipt and agent result",
    )
    calibration_result.add_argument("--root", required=True)
    calibration_result.add_argument(
        "--dispatch-receipt",
        required=True,
        metavar="FILE|-",
        help="Versioned dispatch-receipt JSON file, or - for stdin",
    )
    calibration_result.add_argument(
        "--result",
        required=True,
        metavar="FILE|-",
        help="Versioned calibration agent-result JSON file, or - for stdin",
    )

    calibration_verify = calibration_sub.add_parser(
        "verify",
        help="Recompute cohort evidence and advance only when eligible",
    )
    calibration_verify.add_argument("--root", required=True)
    calibration_verify.add_argument(
        "--no-advance",
        action="store_true",
        help="Report verification without advancing an eligible cohort",
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
        hint = resource_failure_hint(exc)
        if hint is not None:
            print(f"Resource guidance: {hint}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
