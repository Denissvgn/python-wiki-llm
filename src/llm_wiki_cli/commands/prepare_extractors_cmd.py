from __future__ import annotations

import json
import sys
from pathlib import Path

from ..config import validate_source_root
from ..services.extractor_helpers import (
    SUPPORTED_HELPERS,
    HelperPrepareResult,
    prepare_helper,
    resolve_helper_cache_root,
)
from ..services.source_snapshot import build_source_snapshot
from ..services.source_selection import resolve_source_selection


PREPARE_EXTRACTORS_PLAN_SCHEMA = "llm-wiki-prepare-extractors-plan/v1"


def _dedupe_languages(values: list[str] | None) -> list[str]:
    if not values:
        return []
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _canonical_plan_languages(values: list[str]) -> list[str]:
    selected = set(values)
    return [language for language in SUPPORTED_HELPERS if language in selected]


def _languages_from_snapshot(
    src_dir: str,
    *,
    source_selection: str | Path | None = None,
) -> list[str]:
    snapshot = build_source_snapshot(
        src_dir,
        source_selection=source_selection,
    )
    return [
        language
        for language in SUPPORTED_HELPERS
        if snapshot.files_by_language.get(language)
    ]


def _print_plan(languages: list[str], output_format: str) -> None:
    canonical_languages = _canonical_plan_languages(languages)
    if output_format == "json":
        payload = {
            "schema": PREPARE_EXTRACTORS_PLAN_SCHEMA,
            "languages": canonical_languages,
        }
        print(json.dumps(payload, separators=(",", ":")))
        return

    selected = ", ".join(canonical_languages) if canonical_languages else "none"
    print(f"Extractor helper plan ({PREPARE_EXTRACTORS_PLAN_SCHEMA})")
    print(f"languages: {selected}")


def _format_result(result: HelperPrepareResult) -> str:
    detail = f" ({result.path})" if result.path else ""
    return f"{result.language}: {result.status} - {result.message}{detail}"


def run(args) -> None:
    src_dir: str = getattr(args, "src_dir", ".")
    cache_dir: str | None = getattr(args, "cache_dir", None)
    selected_languages = _dedupe_languages(getattr(args, "language", None))
    source_selection = getattr(args, "source_selection", None)
    allow_external_src = bool(getattr(args, "allow_external_src", False))
    plan = bool(getattr(args, "plan", False))
    output_format = getattr(args, "format", "text")

    src_root = validate_source_root(
        src_dir, "--src-dir", allow_external=allow_external_src
    )
    if allow_external_src:
        src_dir = str(src_root)
    if selected_languages and source_selection is not None:
        print(
            "Error: --source-selection cannot be combined with --language; "
            "explicit helper languages already override automatic source planning.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if selected_languages:
        default_policy = resolve_source_selection(src_dir)
        if default_policy is not None:
            # Explicit helper languages remain authoritative, but the discovered
            # project boundary is still a fail-closed contract input.
            build_source_snapshot(src_dir, selection_policy=default_policy)
    if not plan and output_format != "text":
        print(
            "Error: --format is only available with --plan.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if plan:
        languages = selected_languages or _languages_from_snapshot(
            src_dir,
            source_selection=source_selection,
        )
        _print_plan(languages, output_format)
        return

    cache_root = resolve_helper_cache_root(src_dir, cache_dir)
    if cache_root is None:
        print(
            "Error: helper cache directory unavailable. Use --cache-dir PATH or run inside a git repository.",
            file=sys.stderr,
        )
        sys.exit(1)

    languages = selected_languages or _languages_from_snapshot(
        src_dir,
        source_selection=source_selection,
    )
    if not languages:
        print(
            "No TypeScript/JavaScript, Go, Rust, or Haskell source files found. "
            "Nothing to prepare."
        )
        return

    print(f"Preparing extractor helpers in: {Path(cache_root)}")
    results = [prepare_helper(language, cache_root) for language in languages]
    for result in results:
        print(_format_result(result))

    if any(result.status == "failed" for result in results):
        sys.exit(1)
