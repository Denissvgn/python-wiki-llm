from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from ..services.change_selection import changes_from_args
from ..services.review_service import (
    ReviewFinding,
    _preflight_review_source_selection,
    build_findings as build_findings,
)


def _read_patch(args, *, src_dir: str | None = None) -> str:
    patch = getattr(args, "patch", None)
    selection = changes_from_args(args)
    if patch and selection is not None:
        raise ValueError("--patch cannot be combined with other change inputs")
    if patch:
        if patch == "-":
            return sys.stdin.read()
        validate_path(patch, "--patch")
        return Path(patch).read_text(encoding="utf-8")

    if selection is not None and selection["mode"] == "paths":
        return ""
    base = getattr(args, "base", None)
    head = getattr(args, "head", None)
    if base or head:
        if not base or not head:
            print(
                "Error: --base and --head must be provided together.", file=sys.stderr
            )
            sys.exit(1)
        cmd = ["git", "diff", "--no-ext-diff", "--no-textconv", base, head, "--"]
    elif getattr(args, "staged", False):
        cmd = ["git", "diff", "--no-ext-diff", "--no-textconv", "--cached", "--"]
    else:
        cmd = ["git", "diff", "--no-ext-diff", "--no-textconv"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
            cwd=src_dir or getattr(args, "src_dir", "."),
        )
        return result.stdout
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as exc:
        print(f"Error: failed to read git diff: {exc}", file=sys.stderr)
        sys.exit(1)


def render_markdown(findings: list[ReviewFinding]) -> str:
    lines = ["# LLM Wiki Review", ""]
    if not findings:
        lines.append("No wiki-aware review findings.")
        return "\n".join(lines) + "\n"
    for finding in findings:
        pages = ", ".join(f"`{page}`" for page in finding.wiki_pages) or "none"
        lines.extend(
            [
                f"## {finding.severity.upper()}: {finding.source_path}",
                "",
                f"- Related wiki pages: {pages}",
                f"- Reason: {finding.reason}",
                f"- Suggested follow-up: {finding.suggested_follow_up}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_json(findings: list[ReviewFinding]) -> str:
    return (
        json.dumps(
            {"ok": True, "findings": [asdict(finding) for finding in findings]},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def run(args) -> None:
    src_dir: str = getattr(args, "src_dir", ".")
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    output_format: str = getattr(args, "format", "markdown")
    allow_external = bool(getattr(args, "allow_external_src", False))
    source_root = validate_source_root(
        src_dir,
        "--src-dir",
        allow_external=allow_external,
    )
    if allow_external:
        src_dir = str(source_root)
    validate_path(wiki_dir, "--wiki-dir")

    _preflight_review_source_selection(
        src_dir,
        Path(wiki_dir),
        getattr(args, "source_selection", None),
    )

    diff_text = _read_patch(args, src_dir=src_dir)
    if output_format in {"impact-json", "impact-markdown", "github"}:
        from ..services.impact import build_impact, render_github, render_summary
        from ..services.io import write_text_output

        impact = build_impact(
            diff_text,
            src_dir=src_dir,
            wiki_dir=wiki_dir,
            changes=changes_from_args(args),
            helper_cache_dir=getattr(args, "helper_cache_dir", None),
            source_selection=getattr(args, "source_selection", None),
        )
        if getattr(args, "summary_output", None):
            write_text_output(args.summary_output, render_summary(impact))
        if getattr(args, "impact_output", None):
            write_text_output(
                args.impact_output, json.dumps(impact, indent=2, sort_keys=True) + "\n"
            )
        if output_format == "impact-json":
            print(json.dumps(impact, indent=2, sort_keys=True))
        elif output_format == "github":
            print(render_github(impact), end="")
        else:
            print(render_summary(impact), end="")
        return
    if getattr(args, "summary_output", None) or getattr(args, "impact_output", None):
        raise ValueError("Impact artifacts require an impact or github format")
    findings = build_findings(
        diff_text,
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        source_selection=getattr(args, "source_selection", None),
        changes=changes_from_args(args),
    )
    if output_format == "json":
        print(render_json(findings), end="")
    else:
        print(render_markdown(findings), end="")
