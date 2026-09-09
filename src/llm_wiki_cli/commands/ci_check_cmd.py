from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from ..services.ci_report import build_ci_check_payload
from ..services.extraction_jobs import (
    extraction_job_request_from_args,
    print_extraction_job_plan,
)
from ..services.inventory_cache import (
    InventoryCacheStats,
    cache_options_from_args,
    format_cache_stats,
    prepare_cache_options,
)
from ..services.io import write_bytes_atomic
from ..services.progress import observed_phase
from ..services.runtime_output import (
    RuntimeDestination,
    RuntimeOutputError,
    prepare_destination,
    stderr_warning,
)
from ..services.metrics import record_validation_event
from ..services.lint_service import (
    build_report,
    render_markdown,
    render_text,
)

DEFAULT_REPORT = ".git/llm-wiki-ci-report.md"


def _render_console(report, output_format: str, **payload_options) -> str:
    if output_format == "json":
        return (
            json.dumps(
                build_ci_check_payload(report, **payload_options),
                # ``ci-check`` owns a separately versioned public envelope.
                # Generic lint/MCP serializers intentionally remain unchanged.
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    if output_format == "markdown":
        return render_markdown(report)
    return render_text(report)


def _report_destination(args) -> RuntimeDestination:
    selected = getattr(args, "report", None)
    if bool(getattr(args, "no_report", False)):
        if selected is not None:
            raise RuntimeOutputError("--report and --no-report are mutually exclusive")
        return RuntimeDestination(None)
    try:
        path = (
            Path(selected if selected is not None else DEFAULT_REPORT)
            .expanduser()
            .absolute()
        )
    except (ValueError, TypeError, OSError) as exc:
        raise RuntimeOutputError(f"Invalid report destination: {exc}") from exc
    return prepare_destination(
        path, kind="report", explicit=selected is not None, warning=stderr_warning
    )


@observed_phase("report_persistence")
def _persist_report(destination: RuntimeDestination, report) -> int:
    command_exit = 0 if report.passed else 1
    if destination.status == "pending":
        assert destination.path is not None
        try:
            write_bytes_atomic(
                destination.path, render_markdown(report).encode("utf-8")
            )
        except OSError as exc:
            destination.status = "failed"
            destination.error = str(exc)
            stderr_warning(f"CI report was not saved at {destination.path}: {exc}")
            if destination.explicit:
                command_exit = 2
        else:
            destination.status = "written"

    return command_exit


def run(args) -> None:
    src_dir: str = getattr(args, "src_dir", ".")
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    output_format: str = getattr(args, "format", "text")
    report_schema = getattr(args, "report_schema", "v1")
    if report_schema not in {"v1", "v2"}:
        raise RuntimeOutputError("--report-schema must be v1 or v2")
    helper_cache_dir: str | None = getattr(args, "helper_cache_dir", None)
    include_tests = getattr(args, "include_tests", None)
    allow_external_src = bool(getattr(args, "allow_external_src", False))
    source_selection = getattr(args, "source_selection", None)

    src_root = validate_source_root(
        src_dir, "--src-dir", allow_external=allow_external_src
    )
    if allow_external_src:
        src_dir = str(src_root)
    validate_path(wiki_dir, "--wiki-dir")

    cache_options = cache_options_from_args(args)
    destination = _report_destination(args)
    cache_options = prepare_cache_options(src_dir, cache_options)
    assert cache_options is not None
    if report_schema == "v2":
        cache_options = replace(cache_options, stats_enabled=True)

    started = time.monotonic()
    job_request = extraction_job_request_from_args(args)
    report = build_report(
        wiki_dir,
        src_dir,
        strict=True,
        knowledge_drift_report=bool(getattr(args, "knowledge_drift_report", False)),
        cache_options=cache_options,
        parallel_jobs=getattr(args, "jobs", 1),
        helper_cache_dir=helper_cache_dir,
        include_tests=include_tests,
        job_request=job_request,
        plan_reporter=print_extraction_job_plan,
        include_plugins=not bool(getattr(args, "no_plugins", False)),
        source_selection=source_selection,
    )
    duration_ms = int((time.monotonic() - started) * 1000)

    command_exit = _persist_report(destination, report)

    cache_stats = report.cache_stats
    if cache_stats is None:
        prepared_cache = cache_options.destination
        cache_failed = prepared_cache is not None and prepared_cache.status == "failed"
        cache_enabled = bool(
            cache_options.enabled
            and prepared_cache is not None
            and prepared_cache.path is not None
            and not cache_failed
        )
        cache_stats = InventoryCacheStats(
            enabled=cache_enabled,
            path=str(prepared_cache.path)
            if prepared_cache is not None and prepared_cache.path is not None
            else None,
            status="not_evaluated" if cache_enabled else "disabled",
            load_error=prepared_cache.error or "" if prepared_cache is not None else "",
            failure_stage="preflight" if cache_failed else None,
        )
    print(
        _render_console(
            report,
            output_format,
            report_schema=report_schema,
            runtime={
                "cache": cache_stats.to_dict(),
                "report": destination.to_payload(),
            },
            command_exit_code=command_exit,
        ),
        end="",
    )
    if destination.status == "written":
        print(f"CI report written to: {destination.path}", file=sys.stderr)
    if (
        getattr(args, "cache_stats", False)
        and output_format == "json"
        and report_schema == "v1"
    ):
        for line in format_cache_stats(cache_stats):
            print(line, file=sys.stderr)

    try:
        record_validation_event(
            command="ci-check",
            passed=report.passed,
            issue_count=report.issue_count,
            strict=True,
            duration_ms=duration_ms,
            wiki_dir=wiki_dir,
            src_dir=src_dir,
            knowledge_summary=(
                None
                if report.knowledge_summary is None
                else report.knowledge_summary.aggregate_payload()
            ),
        )
    except Exception:  # noqa: BLE001,S110 - metrics are best-effort observability
        pass

    if command_exit:
        sys.exit(command_exit)
