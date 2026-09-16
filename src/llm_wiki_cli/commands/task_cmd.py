"""CLI for explicit task-context requests and canonical counted output."""

import json
import sys

from ..services.io import write_text_output, write_utf8_stdout
from ..services.request_json import load_request


def run(args):
    from .. import api
    from ..services.token_counting import LocalTokenizerCounter

    try:
        request = load_request(args.request)
        policy = api.WorkflowPolicy(read_scope="full-inventory" if args.allow_full_inventory else "selected")
        profile = api.load_workflow_profile(args.profile, policy=policy) if args.profile else None
        counter = LocalTokenizerCounter(args.tokenizer) if args.tokenizer else None
        result = api.build_task_context(request, src_dir=args.src_dir, wiki_dir=args.wiki_dir,
            profile=profile, policy=policy, counter=counter, allow_external_src=args.allow_external_src,
            source_selection=args.source_selection, helper_cache_dir=args.helper_cache_dir)
        if not result.ok:
            print(json.dumps(result.to_payload(), sort_keys=True), file=sys.stderr)
            raise SystemExit(3)
        if args.output:
            write_text_output(args.output, result.rendered)
        else:
            write_utf8_stdout(result.rendered)
    except (ValueError, api.LlmWikiApiError) as exc:
        invalid = isinstance(exc, (ValueError, api.InvalidRequestError))
        print(json.dumps({"ok": False, "error": {"code": getattr(exc, "code", None) or
            ("invalid-request" if invalid else "workspace-state-error"),
            "message": "Task context unavailable", "details": getattr(exc, "details", None) or {}}},
            sort_keys=True), file=sys.stderr)
        raise SystemExit(2 if invalid else 1) from exc
