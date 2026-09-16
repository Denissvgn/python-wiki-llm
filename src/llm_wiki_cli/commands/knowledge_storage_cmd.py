"""CLI adapter for explicit native storage operations."""

from __future__ import annotations

import json

from ..services.knowledge_storage_diagnostics import storage_report, review_storage
from ..services.knowledge_storage_lifecycle import (
    migrate_knowledge_storage, recover_knowledge_storage,
    export_knowledge_v1, prune_knowledge_storage,
)


def run(args) -> None:
    from .knowledge_cmd import _wiki_root
    root = _wiki_root(args.wiki_dir)
    try:
        if args.knowledge_action == "migrate":
            result = migrate_knowledge_storage(root, dry_run=args.dry_run, recovery_dir=args.recovery_dir, to=args.to)
        elif args.knowledge_action == "recover-storage":
            result = recover_knowledge_storage(root, args.recovery_dir, dry_run=args.dry_run)
        elif args.knowledge_action == "export-storage":
            result = export_knowledge_v1(root, args.output)
        elif args.knowledge_action == "prune-storage":
            result = prune_knowledge_storage(root, dry_run=not args.apply)
        elif args.knowledge_action in {"inspect-storage", "diff-storage"}:
            result = review_storage(root, against=getattr(args, "against_wiki", None),
                                    limit=args.limit, max_bytes=args.max_bytes)
        else:
            result = storage_report(root, full=args.full, git_base=args.git_base, git_head=args.git_head)
    except (ValueError, OSError) as exc:
        result = {"ok": False, "error": {"code": getattr(exc, "code", "storage-invalid"), "message": str(exc)}}
    # Structured output keeps unusual paths and control characters escaped.
    if args.knowledge_action in {"inspect-storage", "diff-storage"}:
        print(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(result, sort_keys=True, ensure_ascii=True, indent=2))
    if not result.get("ok", True):
        raise SystemExit(1)
