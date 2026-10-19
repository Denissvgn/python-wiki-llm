"""CLI adapter for explicit ordinary maintenance review operations."""

from __future__ import annotations

import json

from ..services.request_json import load_request


def _capture_options(args):
    return {
        "source_selection": args.source_selection,
        "helper_cache_dir": args.helper_cache_dir,
        "allow_external_src": args.allow_external_src,
    }


def _render_status(result):
    lines = [f"Maintenance: {result['availability']} ({result['analysis_scope']})"]
    if result.get("requires_sync"):
        lines.append("Current prose requires sync before acknowledgment.")
    for record in result.get("records", []):
        target = record["target"]
        effective = record.get("effective_status")
        status = (
            effective
            if effective is not None
            else f"recorded {record['recorded_status']}"
        )
        lines.append(f"{record['record_id']} [{status}] {target['canonical_path']}")
        lines.append("  section: " + target["section_locator"])
        reasons = record.get("reasons", [])
        if reasons:
            lines.append("  reasons: " + ", ".join(reasons))
        if record["mapping"]["state"] != "resolved":
            lines.append("  mapping: " + record["mapping"]["state"])
            for candidate in record["mapping"].get("candidates", []):
                candidate_target = candidate["target"]
                lines.append(
                    "  candidate: "
                    + candidate_target["canonical_path"]
                    + " :: "
                    + candidate_target["section_locator"]
                )
    bounds = result.get("bounds", {})
    if bounds.get("truncated"):
        lines.append(
            f"{bounds.get('omitted', 0)} record(s) omitted; select an exact record for its basis."
        )
    return "\n".join(lines)


def run(args) -> None:
    from .. import api

    try:
        if args.maintenance_action == "adopt":
            result = api.adopt_maintenance(
                args.src_dir,
                args.wiki_dir,
                recovery_dir=args.recovery_dir,
                manifest_format=args.manifest_format,
                **_capture_options(args),
            )
        elif args.maintenance_action == "status":
            result = api.get_maintenance_status(
                args.src_dir,
                args.wiki_dir,
                live=not args.snapshot,
                record_id=args.record_id,
                limit=args.limit,
                **_capture_options(args),
            )
        elif args.maintenance_action == "acknowledge":
            result = api.acknowledge_maintenance(
                args.src_dir,
                args.wiki_dir,
                record_id=args.record_id,
                expected_state_hash=args.expected_state_hash,
                expected_basis=load_request(args.basis_file),
                actor_kind=args.actor_kind,
                actor_id=args.actor_id,
                recovery_dir=args.recovery_dir,
                **_capture_options(args),
            )
        elif args.maintenance_action == "recover-new-pages":
            from ..config import validate_path
            from ..services.sync_recovery import recover_new_sync_pages

            result = recover_new_sync_pages(
                validate_path(args.wiki_dir, "--wiki-dir"),
                recovery_dir=args.recovery_dir,
                expected_journal_hash=args.expected_journal_hash,
                dry_run=args.dry_run,
            )
        else:
            result = api.recover_maintenance(
                args.wiki_dir,
                recovery_dir=args.recovery_dir,
                expected_adoption_id=args.expected_adoption_id,
                src_dir=args.src_dir,
                allow_prepared_adoption=args.allow_prepared_adoption,
                allow_captured_preimage=args.allow_captured_preimage,
            )
    except api.LlmWikiApiError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": exc.code,
                        "message": str(exc),
                        "details": exc.details,
                    },
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        raise SystemExit(1) from exc
    except (ValueError, OSError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {"code": "invalid-request", "message": str(exc)},
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        raise SystemExit(1) from exc
    if args.format == "text" and args.maintenance_action == "status":
        print(_render_status(result))
    else:
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
        )
