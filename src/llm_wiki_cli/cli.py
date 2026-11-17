from contextlib import contextmanager
import os
import sys


from .commands import (
    api_diff_cmd,
    bump_cmd,
    ci_check_cmd,
    docs_cmd,
    doctor_cmd,
    generate_prompt_cmd,
    install_ci_cmd,
    init_cmd,
    install_cmd,
    knowledge_cmd,
    maintenance_cmd,
    mcp_cmd,
    metrics_cmd,
    migrate_cmd,
    obsidian_cmd,
    plugins_cmd,
    prepare_extractors_cmd,
    queue_cmd,
    query_cmd,
    reference_cmd,
    release_cmd,
    review_cmd,
    search_cmd,
    site_cmd,
    skills_cmd,
    status_cmd,
    sync_cmd,
    team_cmd,
    task_cmd,
    trigger_cmd,
    uninstall_cmd,
    upgrade_cmd,
)
from .config import PathValidationError
from llm_wiki_engine.runtime_output import RuntimeOutputError
from llm_wiki_engine.progress import Progress
from .services import (
    bootstrap_runtime as bootstrap_cmd,
    context_service as context_cmd,
    extraction_service as extract_cmd,
    lint_service as lint_cmd,
)
from .services.resource_diagnostics import resource_failure_hint
from .cli_declarations import _build_parser, build_cli_parser  # noqa: F401  (public re-export)


_COMMAND_MODULES = {
    "api-diff": api_diff_cmd,
    "init": init_cmd,
    "extract": extract_cmd,
    "lint": lint_cmd,
    "prepare-extractors": prepare_extractors_cmd,
    "ci-check": ci_check_cmd,
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
    "search": search_cmd,
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
    "reference": reference_cmd,
    "doctor": doctor_cmd,
    "queue": queue_cmd,
    "maintenance": maintenance_cmd,
    "query": query_cmd,
    "task-context": task_cmd,
}


def _helper_preparation_policy(args):
    from .services.helper_runtime import current_helper_configuration

    requested = getattr(args, "helper_preparation", None)
    configuration = current_helper_configuration()
    strict = any(bool(getattr(args, name, False)) for name in (
        "read_only", "dry_run", "preview", "plan_chunks", "capabilities",
    )) or (args.command == "prepare-extractors" and bool(getattr(args, "plan", False)))
    if args.command == "team" and args.team_action == "resolve-conflicts" and not args.write:
        strict = True
    if strict and requested == "auto":
        raise ValueError("Automatic helper preparation conflicts with this read-only or preview operation")
    selected = "never" if strict else requested or (
        configuration.policy if configuration is not None else "auto"
    )
    if selected == "never" and (
        args.command == "prepare-extractors" and not bool(getattr(args, "plan", False))
        or args.command == "init" and bool(getattr(args, "prepare_extractors", False))
    ):
        raise ValueError("Explicit helper preparation conflicts with --helper-preparation never")
    return selected


def _dispatch_command(args):
    if args.command in {"sync", "lint", "ci-check"}:
        with Progress(
            args.command,
            mode=args.progress,
            output_format=args.progress_format,
        ).run():
            _COMMAND_MODULES[args.command].run(args)
    else:
        _COMMAND_MODULES[args.command].run(args)


def _print_exception_notes(exc: BaseException) -> None:
    for note in getattr(exc, "__notes__", ()):
        print(note, file=sys.stderr)


@contextmanager
def _report_cli_errors():
    try:
        yield
    except KeyboardInterrupt as exc:
        print("\nAborted.")
        _print_exception_notes(exc)
        sys.exit(130)
    except SystemExit as exc:
        _print_exception_notes(exc)
        raise
    except PathValidationError as exc:
        print(str(exc), file=sys.stderr)
        _print_exception_notes(exc)
        sys.exit(1)
    except RuntimeOutputError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        _print_exception_notes(exc)
        sys.exit(2)
    except Exception as exc:
        if os.environ.get("LLM_WIKI_DEBUG"):
            raise
        print(f"Error: {exc}", file=sys.stderr)
        _print_exception_notes(exc)
        hint = resource_failure_hint(exc)
        if hint is not None:
            print(f"Resource guidance: {hint}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = _build_parser()
    args = parser.parse_args()

    with _report_cli_errors():
        from .services.analysis_compatibility import comparison_scope
        from .services.helper_runtime import helper_operation
        helper_policy = _helper_preparation_policy(args)
        with comparison_scope(getattr(args, "comparison_policy", "auto")):
            if args.command == "mcp":
                # The server owns fresh request scopes, never one operation
                # retained for the entire server lifetime.
                args.helper_preparation = helper_policy
                _dispatch_command(args)
            else:
                with helper_operation(helper_policy):
                    _dispatch_command(args)


if __name__ == "__main__":
    main()
