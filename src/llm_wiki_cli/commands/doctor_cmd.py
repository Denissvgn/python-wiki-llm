"""CLI adapter for the read-only knowledge health report."""

from __future__ import annotations

import json

from ..config import DEFAULT_WIKI_DIR
from ..services.doctor_service import build_doctor_report, render_doctor_text
from ..services.extraction_jobs import extraction_job_request_from_args


def run(args) -> None:
    report = build_doctor_report(
        getattr(args, "wiki_dir", DEFAULT_WIKI_DIR),
        getattr(args, "src_dir", "."),
        strict=bool(getattr(args, "strict", False)),
        allow_external_src=bool(getattr(args, "allow_external_src", False)),
        helper_cache_dir=getattr(args, "helper_cache_dir", None),
        include_tests=getattr(args, "include_tests", None),
        parallel_jobs=getattr(args, "jobs", 1),
        job_request=extraction_job_request_from_args(args),
        source_selection=getattr(args, "source_selection", None),
    )
    if getattr(args, "format", "text") == "json":
        print(json.dumps(report.to_payload(), indent=2, sort_keys=True))
    else:
        print(render_doctor_text(report), end="")
    if report.exit_code:
        raise SystemExit(report.exit_code)
