"""Explicit setup-time preparation for helpers selected by a source boundary."""

from __future__ import annotations

from pathlib import Path

from . import extractor_helpers as helpers
from .source_snapshot import build_source_snapshot


def selected_helper_languages(
    src_dir: str | Path,
    *,
    source_selection: str | Path | None = None,
) -> list[str]:
    snapshot = build_source_snapshot(src_dir, source_selection=source_selection)
    return [
        language
        for language in helpers.SUPPORTED_HELPERS
        if snapshot.files_by_language.get(language)
    ]


def ensure_source_helpers(
    src_dir: str | Path,
    *,
    cache_dir: str | None = None,
    source_selection: str | Path | None = None,
) -> list[helpers.HelperPrepareResult]:
    """Prepare missing/stale helpers, reusing valid artifacts without build tools.

    Call only from an explicitly authorized setup operation, never a read path.
    Selection is validated before invoking any toolchain or creating a cache.
    """
    languages = selected_helper_languages(src_dir, source_selection=source_selection)
    if not languages:
        return []
    cache_root = helpers.resolve_helper_cache_root(src_dir, cache_dir)
    if cache_root is None:
        raise ValueError(
            "helper cache directory unavailable. Use --helper-cache-dir PATH "
            "or run inside a git repository."
        )

    results = []
    for language in languages:
        artifact = (
            helpers.get_prepared_typescript_root(src_dir, cache_dir)
            if language == "typescript"
            else helpers.get_prepared_binary(language, src_dir, cache_dir)
        )
        if artifact is not None:
            results.append(
                helpers.HelperPrepareResult(
                    language,
                    "already_current",
                    "Helper already prepared",
                    str(artifact),
                )
            )
            continue
        try:
            result = helpers.prepare_helper(language, cache_root)
        except OSError as exc:
            result = helpers.HelperPrepareResult(language, "failed", str(exc))
        results.append(result)
    return results
