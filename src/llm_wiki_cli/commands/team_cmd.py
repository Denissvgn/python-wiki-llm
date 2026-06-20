from __future__ import annotations

import json
import sys
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path
from ..services import team
from .extract_cmd import get_inventory


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


def _run_check(args) -> None:
    src_dir = getattr(args, "src_dir", ".")
    wiki_dir = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    output_format = getattr(args, "format", "text")
    validate_path(src_dir, "--src-dir")
    validate_path(wiki_dir, "--wiki-dir")

    wiki_path = Path(wiki_dir)
    pages = list(wiki_path.rglob("*.md")) if wiki_path.exists() else []
    inventory = get_inventory(src_dir)
    issues = team.build_team_issues(
        wiki_dir, src_dir, inventory, pages, require_config=True
    )
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
    validate_path(src_dir, "--src-dir")
    validate_path(wiki_dir, "--wiki-dir")

    result = team.resolve_conflicts(
        wiki_dir,
        src_dir,
        write=bool(getattr(args, "write", False)),
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
