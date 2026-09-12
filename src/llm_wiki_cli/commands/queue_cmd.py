"""Read-only managed-wiki maintenance triage."""

import json

from ..services.maintenance_queue import build_maintenance_queue, render_queue


def run(args):
    queue = build_maintenance_queue(
        args.src_dir,
        args.wiki_dir,
        limit=args.limit,
        allow_external_src=args.allow_external_src,
        source_selection=args.source_selection,
        helper_cache_dir=args.helper_cache_dir,
    )
    print(
        json.dumps(queue, ensure_ascii=False, sort_keys=True, indent=2)
        if args.format == "json"
        else render_queue(queue),
        end="\n" if args.format == "json" else "",
    )
