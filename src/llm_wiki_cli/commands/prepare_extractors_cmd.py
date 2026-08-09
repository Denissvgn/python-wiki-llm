from __future__ import annotations

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


def _format_result(result: HelperPrepareResult) -> str:
    detail = f" ({result.path})" if result.path else ""
    return f"{result.language}: {result.status} - {result.message}{detail}"


def run(args) -> None:
    src_dir: str = getattr(args, "src_dir", ".")
    cache_dir: str | None = getattr(args, "cache_dir", None)
    selected_languages = _dedupe_languages(getattr(args, "language", None))
    source_selection = getattr(args, "source_selection", None)
    allow_external_src = bool(getattr(args, "allow_external_src", False))

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
