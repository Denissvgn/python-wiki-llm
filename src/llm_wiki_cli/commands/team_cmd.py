from __future__ import annotations

import json
import sys
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from ..services import team
from ..services.extraction_service import get_docker_inventory, get_inventory_result
from ..services.extraction_jobs import extraction_job_request_from_args
from ..services.infrastructure_inventory import get_yaml_infrastructure_inventory
from ..services.source_selection import (
    resolve_source_selection,
    validate_persisted_source_selection_identity,
)
from ..services.source_snapshot import (
    SourceSnapshot,
    build_source_snapshot,
    capture_source_selection_inputs,
)
from ..services.sync_manifest import SyncManifest, SyncManifestError


def _render_issues_text(title: str, issues: list[dict]) -> str:
    lines = [title]
    if not issues:
        lines.append("No team issues found.")
        return "\n".join(lines) + "\n"
    for issue in issues:
        path = f" ({issue['path']})" if issue.get("path") else ""
        lines.append(f"- {issue['category']}{path}: {issue['message']}")
    return "\n".join(lines) + "\n"


def _render_conflicts_text(result: dict) -> str:
    mode = "write" if result["write"] else "dry-run"
    lines = [f"Team conflict resolution ({mode})"]
    if result["conflict_count"] == 0:
        lines.append("No wiki conflict markers found.")
        return "\n".join(lines) + "\n"
    for item in result["resolved"]:
        verb = "RESOLVED" if result["write"] else "WOULD RESOLVE"
        lines.append(f"- {verb} {item['path']}: {item['action']}")
    for item in result["unresolved"]:
        lines.append(f"- UNRESOLVED {item['path']}: {item['reason']}")
    return "\n".join(lines) + "\n"


def _print_payload(
    payload: dict, output_format: str, *, conflict: bool = False
) -> None:
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif conflict:
        print(_render_conflicts_text(payload), end="")
    else:
        print(_render_issues_text("Team check", payload["issues"]), end="")


def _run_init(args) -> None:
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    validate_path(wiki_dir, "--wiki-dir")
    path = team.team_config_path()
    if path.exists():
        print(f"Team config already exists: {path}")
        return
    written = team.write_default_team_config(wiki_dir)
    print(f"Team config written to: {written}")


def _preflight_team_source_selection(
    src_dir: str,
    wiki_dir: str | Path,
    source_selection: str | Path | None,
    *,
    include_tests=None,
) -> tuple[SourceSnapshot, SyncManifest | None]:
    policy = resolve_source_selection(src_dir, source_selection)
    manifest = None
    try:
        manifest = SyncManifest.load(Path(wiki_dir))
    except FileNotFoundError:
        wiki_path = Path(wiki_dir)
        generation_inputs = (
            {}
            if wiki_path.is_dir() and next(wiki_path.iterdir(), None) is not None
            else None
        )
    else:
        generation_inputs = manifest.generation_inputs
    validate_persisted_source_selection_identity(
        generation_inputs,
        None if policy is None else policy.identity,
        operation="team check",
    )
    selection_inputs = capture_source_selection_inputs(
        src_dir,
        source_selection=source_selection,
        selection_policy=policy,
    )
    validate_persisted_source_selection_identity(
        generation_inputs,
        None if policy is None else policy.identity,
        operation="team check",
        live_selection_inputs=selection_inputs,
    )
    source_snapshot = build_source_snapshot(
        src_dir,
        include_tests=include_tests,
        source_selection=source_selection,
        selection_policy=policy,
        expected_selection_inputs=selection_inputs,
    )
    return source_snapshot, manifest


def _run_check(args) -> None:
    src_dir = getattr(args, "src_dir", ".")
    wiki_dir = getattr(args, "wiki_dir", None)
    output_format = getattr(args, "format", "text")
    allow_external_src = bool(getattr(args, "allow_external_src", False))
    src_root = validate_source_root(
        src_dir, "--src-dir", allow_external=allow_external_src
    )
    if allow_external_src:
        src_dir = str(src_root)
    if wiki_dir is not None:
        validate_path(wiki_dir, "--wiki-dir")
    try:
        policy = team.resolve_team_policy(wiki_dir, required=True)
    except team.TeamConfigError as exc:
        _finish_check(
            str(wiki_dir or DEFAULT_WIKI_DIR),
            src_dir,
            output_format,
            [team.team_config_issue(exc)],
        )
        return
    wiki_dir = policy.wiki_dir
    validate_path(wiki_dir, "--wiki-dir")

    source_selection = getattr(args, "source_selection", None)
    try:
        source_snapshot, manifest = _preflight_team_source_selection(
            src_dir,
            wiki_dir,
            source_selection,
            include_tests=getattr(args, "include_tests", None),
        )
    except (
        SyncManifestError,
        OSError,
        json.JSONDecodeError,
        UnicodeError,
        RuntimeError,
    ) as exc:
        _finish_check(
            wiki_dir,
            src_dir,
            output_format,
            [
                team.team_config_issue(
                    team.TeamConfigError(f"Invalid canonical page authority: {exc}")
                )
            ],
        )
        return
    wiki_path = Path(wiki_dir)
    pages = list(wiki_path.rglob("*.md")) if wiki_path.exists() else []
    inventory_result = get_inventory_result(
        src_dir,
        deep=True,
        source_selection=source_selection,
        source_snapshot=source_snapshot,
        include_tests=getattr(args, "include_tests", None),
        helper_cache_dir=getattr(args, "helper_cache_dir", None),
        include_plugins=not bool(getattr(args, "no_plugins", False)),
        parallel_jobs=getattr(args, "jobs", 1),
        job_request=extraction_job_request_from_args(args),
    )
    if getattr(inventory_result, "failed", ()):
        issues = [
            {
                "category": "extractor_failure",
                "severity": "error",
                "path": None,
                "target": status.language,
                "message": f"{status.language} extraction failed: {status.message}",
            }
            for status in inventory_result.failed
        ]
        _finish_check(wiki_dir, src_dir, output_format, issues)
        return
    docker_inventory = get_docker_inventory(
        src_dir,
        source_snapshot=inventory_result.source_snapshot,
    )
    yaml_inventory = get_yaml_infrastructure_inventory(
        src_dir, source_snapshot=inventory_result.source_snapshot
    )
    issues = team.build_team_issues(
        wiki_dir,
        src_dir,
        inventory_result.inventory,
        pages,
        require_config=True,
        docker_inventory=docker_inventory,
        policy=policy,
        manifest=manifest,
        yaml_infrastructure_inventory=yaml_inventory,
    )
    _finish_check(wiki_dir, src_dir, output_format, issues)


def _finish_check(
    wiki_dir: str, src_dir: str, output_format: str, issues: list
) -> None:
    payload = {
        "ok": not issues,
        "wiki_dir": wiki_dir,
        "src_dir": src_dir,
        "issues": issues,
        "issue_count": len(issues),
    }
    _print_payload(payload, output_format)
    if issues:
        sys.exit(1)


def _run_resolve_conflicts(args) -> None:
    src_dir = getattr(args, "src_dir", ".")
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    output_format = getattr(args, "format", "text")
    allow_external_src = bool(getattr(args, "allow_external_src", False))
    src_root = validate_source_root(
        src_dir,
        "--src-dir",
        allow_external=allow_external_src,
    )
    if allow_external_src:
        src_dir = str(src_root)
    validate_path(wiki_dir, "--wiki-dir")

    write = bool(getattr(args, "write", False))
    source_selection = getattr(args, "source_selection", None)
    result = (
        team.resolve_conflicts(wiki_dir, src_dir, write=write)
        if source_selection is None
        else team.resolve_conflicts(
            wiki_dir,
            src_dir,
            write=write,
            source_selection=source_selection,
        )
    )
    _print_payload(result, output_format, conflict=True)
    if result["unresolved"]:
        sys.exit(1)


def run(args) -> None:
    action = getattr(args, "team_action", None)
    if action == "init":
        _run_init(args)
    elif action == "check":
        _run_check(args)
    elif action == "resolve-conflicts":
        _run_resolve_conflicts(args)
    else:
        print("Error: missing team action.", file=sys.stderr)
        sys.exit(1)
