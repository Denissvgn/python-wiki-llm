"""Compare supplied local OpenAPI exports without invoking target code."""

import json

from ..config import validate_source_root
from ..services.api_diff import compare_openapi, render_markdown


def run(args):
    validate_source_root(
        args.src_dir, "--src-dir", allow_external=args.allow_external_src
    )
    report = compare_openapi(args.baseline, args.candidate, source_root=args.src_dir)
    print(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
        if args.format == "json"
        else render_markdown(report),
        end="\n" if args.format == "json" else "",
    )
    if report["breaking_count"]:
        raise SystemExit(1)
