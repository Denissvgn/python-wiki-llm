"""Exact documentation queries from bounded, explicit JSON input."""

from __future__ import annotations

import json
import sys

from ..services.io import write_text_output, write_utf8_stdout
from ..services.request_json import load_request


def run(args):
    from .. import api

    try:
        request = load_request(args.request)
        result = api.query_documentation(request, src_dir=args.src_dir,
                    wiki_dir=args.wiki_dir, source_selection=args.source_selection,
                    allow_external_src=args.allow_external_src)
        rendered = json.dumps(result, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":"), allow_nan=False) + "\n"
        if args.output:
            write_text_output(args.output, rendered)
        else:
            write_utf8_stdout(rendered)
    except (ValueError, api.LlmWikiApiError) as exc:
        invalid = isinstance(exc, (ValueError, api.InvalidRequestError))
        print(json.dumps({"ok": False, "error": {
            "code": getattr(exc, "code", None) or ("invalid-request" if invalid else "workspace-state-error"),
            "message": "Invalid query request" if invalid else "Query workspace unavailable",
            "details": getattr(exc, "details", None) or {},
        }}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2 if invalid else 1) from exc
