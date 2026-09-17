"""CLI adapter for explicit native storage operations."""

from __future__ import annotations

import json
from pathlib import Path

from ..services.knowledge_storage_diagnostics import storage_report, review_storage
from ..services.knowledge_storage_lifecycle import (
    migrate_knowledge_storage, recover_knowledge_storage,
    export_knowledge_v1, prune_knowledge_storage, restore_pruned_storage,
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
            from ..services.knowledge_storage import decode_bytes, canonical_bytes, MAX_OBJECT_BYTES
            from ..services.knowledge_storage_io import read_guarded
            from ..services.filesystem_guard import atomic_write_guarded_bytes, ensure_guarded_directory
            plan = None if getattr(args, "plan", None) is None else decode_bytes(read_guarded(Path(args.plan), MAX_OBJECT_BYTES).content,
                                                               limit=MAX_OBJECT_BYTES, field="prune plan")
            result = prune_knowledge_storage(root, dry_run=not args.apply, plan=plan,
                                             recovery_dir=getattr(args, "recovery_dir", None), max_bytes=getattr(args, "max_bytes", 1_073_741_824))
            if getattr(args, "save_plan", None) is not None:
                from ..services.knowledge_storage_lifecycle import _outside_tree
                target = _outside_tree(Path(args.save_plan), root)
                ensure_guarded_directory(target.parent, mode=0o700)
                atomic_write_guarded_bytes(target, canonical_bytes(result["plan"]), mode=0o600, expected_existing=None)
        elif args.knowledge_action == "restore-pruned":
            result = restore_pruned_storage(root, args.recovery_manifest, dry_run=not args.apply)
        elif args.knowledge_action in {"inspect-storage", "diff-storage"}:
            result = review_storage(root, against=getattr(args, "against_wiki", None),
                                    limit=args.limit, max_bytes=args.max_bytes,
                                    selectors=getattr(args, "selector", None))
        else:
            if args.stream:
                if args.full or args.git_base is not None or args.git_head is not None:
                    raise ValueError("--stream is a separate audit scope; omit --full and Git range options")
                from ..services.knowledge_stream_audit import audit_knowledge_stream
                result = audit_knowledge_stream(root)
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
