"""CLI access to the same read-only search service used by MCP."""

import json

from ..config import validate_path, validate_source_root


def run(args):
    from ..api import search_wiki
    validate_source_root(
        args.src_dir, "--src-dir", allow_external=args.allow_external_src
    )
    validate_path(args.wiki_dir, "--wiki-dir")
    result = search_wiki(
        args.query, kinds=args.kind, limit=args.limit, mode=args.mode,
        src_dir=args.src_dir,
        wiki_dir=args.wiki_dir,
        source_selection=args.source_selection,
        allow_external_src=args.allow_external_src,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        for match in result["results"]:
            print(f"{match['path']}: {match['title']}")
            print("  " + match["snippet"])
        print(f"{result['returned']} of {result['total']} matches")
