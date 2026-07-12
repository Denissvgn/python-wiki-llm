from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from ..services.inventory_cache import InventoryCacheOptions
from ..services.extraction_jobs import (
    extraction_job_request_from_args,
    print_extraction_job_plan,
)
from ..services.metrics import record_validation_event
from .lint_cmd import build_report, render_markdown, render_text, report_to_dict

DEFAULT_REPORT = ".git/llm-wiki-ci-report.md"


def _render_console(report, output_format: str) -> str:
    if output_format == "json":
        return (
            json.dumps(
                report_to_dict(report, include_execution=True),
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    if output_format == "markdown":
        return render_markdown(report)
    return render_text(report)


def run(args) -> None:
    src_dir: str = getattr(args, "src_dir", ".")
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    output_format: str = getattr(args, "format", "text")
    report_path = Path(getattr(args, "report", DEFAULT_REPORT))
    helper_cache_dir: str | None = getattr(args, "helper_cache_dir", None)
    include_tests = getattr(args, "include_tests", None)
    allow_external_src = bool(getattr(args, "allow_external_src", False))

    src_root = validate_source_root(
        src_dir, "--src-dir", allow_external=allow_external_src
    )
    if allow_external_src:
        src_dir = str(src_root)
    validate_path(wiki_dir, "--wiki-dir")

    started = time.monotonic()
    job_request = extraction_job_request_from_args(args)
    report = build_report(
        wiki_dir,
        src_dir,
        strict=True,
        cache_options=InventoryCacheOptions(enabled=True),
        parallel_jobs=getattr(args, "jobs", 1),
        helper_cache_dir=helper_cache_dir,
        include_tests=include_tests,
        job_request=job_request,
        plan_reporter=print_extraction_job_plan,
    )
    duration_ms = int((time.monotonic() - started) * 1000)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(report), encoding="utf-8")

    print(_render_console(report, output_format), end="")
    print(f"CI report written to: {report_path}", file=sys.stderr)

    try:
        record_validation_event(
            command="ci-check",
            passed=report.passed,
            issue_count=report.issue_count,
            strict=True,
            duration_ms=duration_ms,
            wiki_dir=wiki_dir,
            src_dir=src_dir,
        )
    except OSError:
        pass

    if not report.passed:
        sys.exit(1)
