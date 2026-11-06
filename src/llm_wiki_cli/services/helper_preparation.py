"""Preparation of bundled helpers within a validated source boundary."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING
import sys

from . import extractor_helpers as helpers
from .source_snapshot import SourceSnapshot, build_source_snapshot

if TYPE_CHECKING:
    from .helper_runtime import PreparedHelperHandle


def _helper_progress(message: str) -> None:
    from .progress import current_progress

    # The command's phase sink owns its mode and output format. Preparation is
    # already represented by the helper_preparation phase below; emitting a
    # second free-form line would bypass --progress never and corrupt JSON
    # progress streams. Calls without that sink retain their bounded notice.
    if current_progress() is not None:
        return
    try:
        print("llm-wiki: " + message, file=sys.stderr, flush=True)
    except (OSError, ValueError):
        pass


def prepare_operation_helpers(
    snapshot: SourceSnapshot,
    registry: Mapping[str, str],
    *,
    only_files: Iterable[str] | None = None,
    cache_dir: str | None = None,
) -> tuple[PreparedHelperHandle, ...]:
    """Resolve helpers before capture, without changing an inspection's policy.

    Operation scopes belong to the CLI/API/service entry point. An unscoped
    low-level lookup keeps its historical existing-only behavior. The snapshot
    and registry must already have passed their caller's request validation.
    """
    from .helper_runtime import (
        bind_helper, current_helper_operation, pinned_helper,
        required_helper_languages,
    )
    from .helper_cache import (
        HelperPreparationError, cache_roots, ensure_helper, lookup_helper, validate_handle,
    )
    from .progress import phase

    operation = current_helper_operation()
    if operation is None:
        return ()
    selected = required_helper_languages(snapshot, registry, only_files=only_files)
    effective_cache = cache_dir if cache_dir is not None else operation.cache_dir
    handles = []
    for language in selected:
        pinned = pinned_helper(language, source_root=snapshot.root)
        if pinned is not None:
            if pinned.cache_root not in cache_roots(snapshot.root, effective_cache):
                raise HelperPreparationError(language, "helper cache scope changed during analysis")
            if not validate_handle(pinned):
                raise HelperPreparationError(language, "prepared helper changed during analysis")
            handle = pinned
        elif operation.policy == "never":
            handle = lookup_helper(language, snapshot.root, effective_cache)
            if handle is None:
                continue
        else:
            with phase("helper_preparation"):
                handle = ensure_helper(
                    language, snapshot.root, effective_cache,
                    progress=operation.progress or _helper_progress,
                )
        bind_helper(handle, source_root=snapshot.root)
        handles.append(handle)
    return tuple(handles)


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
