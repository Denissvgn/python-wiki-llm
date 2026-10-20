"""CLI adapter for the read-only knowledge health report."""

from __future__ import annotations

import json

from ..config import DEFAULT_WIKI_DIR
from ..services.doctor_service import build_doctor_report, render_doctor_text
from ..services.extraction_jobs import extraction_job_request_from_args


def _render_analysis_input_text(report) -> str:
    """Readable classification diagnostics with unchanged scope and work bounds."""
    bounds = report["bounds"]
    lines = [
        f"Analysis inputs: {report['status']}",
        f"Scope: {report['scope']}",
        f"Registry: {report['registry']}",
        f"Paths: {bounds['returned']} of {bounds['total']}; omitted: {bounds['omitted']}",
    ]
    if report["reason"]:
        lines.append(f"Reason: {report['reason']}")
    lines.extend(
        f"- {row['kind']}: {json.dumps(row['path'], ensure_ascii=True)}"
        for row in report["paths"]
    )
    if report["next_action"]:
        lines.append(f"Next action: {report['next_action']}")
    lines.append(f"Qualification: {report['qualification']}")
    return "\n".join(lines)


def run(args) -> None:
    report_schema = getattr(args, "report_schema", "auto")
    if getattr(args, "target_runtime", None):
        if (
            getattr(args, "strict", False)
            or getattr(args, "comparison_policy", "auto") != "auto"
        ):
            raise ValueError(
                "--target-runtime checks declared prerequisites only; run strict health and comparison-policy checks separately"
            )
        from ..config import validate_path
        from ..services.analysis_targets import inspect_targets, load_targets

        validate_path(args.wiki_dir, "--wiki-dir")
        validate_path(args.target_runtime, "--target-runtime")
        report = inspect_targets(args.wiki_dir, load_targets(args.target_runtime))
        if args.format == "json":
            print(json.dumps(report, sort_keys=True, ensure_ascii=True))
        else:
            print("Target runtime prerequisites: " + report["status"])
            for row in report["rows"]:
                print(
                    json.dumps(
                        {k: row[k] for k in ("owner", "component", "state", "reasons")},
                        ensure_ascii=True,
                    )
                )
            print(report["next_action"])
            print(report["qualification"])
        if report["status"] != "requirements-match":
            raise SystemExit(2)
        return
    if getattr(args, "analysis_inputs", False):
        if report_schema != "auto":
            raise ValueError(
                "--analysis-inputs and --report-schema are mutually exclusive"
            )
        from ..api import get_analysis_input_status

        report = get_analysis_input_status()
        print(
            json.dumps(report, sort_keys=True, ensure_ascii=True)
            if getattr(args, "format", "text") == "json"
            else _render_analysis_input_text(report)
        )
        if report["status"] != "ready":
            raise SystemExit(2)
        return
    if report_schema not in {"auto", "v1", "v3", "v4"}:
        raise ValueError("--report-schema must be v1 or v3")
    if getattr(args, "capabilities", False):
        if report_schema not in {"auto", "v1"}:
            raise ValueError(
                "--capabilities and --report-schema are mutually exclusive"
            )
        from ..services.capability_diagnostics import (
            build_capability_doctor,
            render_capability_doctor,
        )

        report = build_capability_doctor(
            args.wiki_dir,
            args.src_dir,
            strict=args.strict,
            allow_external_src=args.allow_external_src,
            helper_cache_dir=args.helper_cache_dir,
            source_selection=args.source_selection,
            include_tests=args.include_tests,
            parallel_jobs=args.jobs,
            job_request=extraction_job_request_from_args(args),
        )
        print(
            json.dumps(report, indent=2, sort_keys=True)
            if args.format == "json"
            else render_capability_doctor(report),
            end="\n" if args.format == "json" else "",
        )
        if report["exit_code"]:
            raise SystemExit(report["exit_code"])
        return
    report = build_doctor_report(
        getattr(args, "wiki_dir", DEFAULT_WIKI_DIR),
        getattr(args, "src_dir", "."),
        comparison_policy=getattr(args, "comparison_policy", "auto"),
        strict=bool(getattr(args, "strict", False)),
        allow_external_src=bool(getattr(args, "allow_external_src", False)),
        helper_cache_dir=getattr(args, "helper_cache_dir", None),
        include_tests=getattr(args, "include_tests", None),
        parallel_jobs=getattr(args, "jobs", 1),
        job_request=extraction_job_request_from_args(args),
        source_selection=getattr(args, "source_selection", None),
        report_schema=report_schema,
    )
    if getattr(args, "format", "text") == "json":
        print(
            json.dumps(
                report.to_payload(report_schema=report_schema), indent=2, sort_keys=True
            )
        )
    else:
        print(render_doctor_text(report, report_schema=report_schema), end="")
    if report.exit_code:
        raise SystemExit(report.exit_code)
