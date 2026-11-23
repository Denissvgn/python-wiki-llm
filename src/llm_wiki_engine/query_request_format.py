"""Request checks shared by documentation query services.

These checks bound and normalize what a caller asks a documentation query
for (limits, exact coordinates and supplied source paths) before any source
or wiki is read, and require a live query's source selection to match the
boundary the wiki was generated with. Answering the query is the
application's work.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from itertools import islice
import os
from pathlib import Path

from .concept_identity import ConceptIdentityError, validate_concept_uid, validate_natural_key
from . import wiki_surface
from .source_selection import SourceSelectionError, validate_persisted_source_selection_identity
from .sync_manifest import SyncManifest, SyncManifestError
from .validation import require_portable_relative_path

QUERY_IDENTITY_BYTE_LIMIT = 4 * 1024
DEFAULT_DOCUMENTATION_QUERY_LIMIT = 20
MAX_DOCUMENTATION_QUERY_LIMIT = 100
MAX_SUPPLIED_PATHS = 100
_UNSET_LIVE_SELECTION_INPUTS = object()


class DocumentationQueryError(ValueError):
    """Raised when a documentation graph query request is invalid."""

    def __init__(self, message: str = "", *, field: str | None = None):
        super().__init__(message)
        self.field = field


def normalize_documentation_query_limit(value: object) -> int:
    """Return the shared bounded query limit before any source work starts."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DocumentationQueryError("limit must be a positive integer.")
    return min(value, MAX_DOCUMENTATION_QUERY_LIMIT)


def normalize_documentation_query_text(value: object, *, field: str) -> str:
    """Return one non-empty exact query coordinate."""

    if not isinstance(value, str) or not value.strip():
        raise DocumentationQueryError(f"{field} must be a non-empty string.")
    selected = value.strip()
    if len(selected.encode("utf-8")) > QUERY_IDENTITY_BYTE_LIMIT:
        raise DocumentationQueryError(
            f"{field} must not exceed {QUERY_IDENTITY_BYTE_LIMIT} UTF-8 bytes."
        )
    return selected


def normalize_concept_coordinate(value: object) -> str:
    """Validate a concept coordinate without attempting fuzzy resolution."""

    selected = normalize_documentation_query_text(
        value,
        field="locator_or_exact_route",
    )
    try:
        return wiki_surface.validate_exact_page_coordinate(selected)
    except wiki_surface.WikiSurfaceError:
        pass
    for validator in (validate_concept_uid, validate_natural_key):
        try:
            return validator(selected)
        except ConceptIdentityError:
            continue
    raise DocumentationQueryError(
        "locator_or_exact_route must be an exact canonical wiki path or "
        "llm-wiki URI, durable concept UID, or natural-key alias."
    )


def _supplied_path_values(values: object) -> list[object]:
    """Consume no more than the declared supplied-path request bound."""

    if isinstance(values, (str, bytes, Mapping)) or not isinstance(values, Iterable):
        raise DocumentationQueryError("paths must be an array of source paths.")
    try:
        requested = list(islice(iter(values), MAX_SUPPLIED_PATHS + 1))
    except Exception as exc:
        raise DocumentationQueryError(
            "paths must be an array of source paths."
        ) from exc
    if len(requested) > MAX_SUPPLIED_PATHS:
        raise DocumentationQueryError(
            f"paths must contain at most {MAX_SUPPLIED_PATHS} entries."
        )
    return requested


def _portable_supplied_path(value: object) -> str:
    """Adapt shared portable-path validation to the query error contract."""

    error = DocumentationQueryError(
        "paths must contain normalized portable relative source paths."
    )
    return require_portable_relative_path(
        value,
        text_error=error,
        relative_error=error,
        escape_error=error,
        traversal_error=error,
        separator_error=error,
        utf8_error=error,
        control_error=error,
        non_nfc_error=error,
        nonportable_error=error,
        reserved_error=error,
    )


def normalize_supplied_paths(values: object) -> tuple[str, ...]:
    """Validate, deduplicate, and deterministically order supplied source paths."""

    normalized = {
        _portable_supplied_path(value) for value in _supplied_path_values(values)
    }
    return tuple(
        sorted(
            normalized,
            key=lambda item: (item.casefold(), item),
        )
    )



def _wiki_has_persisted_read_state(wiki_root: Path) -> bool:
    """Return whether a wiki contains anything beyond empty scaffolding."""

    try:
        if not wiki_root.is_dir():
            return False
        for root, directories, files in os.walk(wiki_root, followlinks=False):
            directories[:] = [
                name for name in directories if not (Path(root) / name).is_symlink()
            ]
            if any(name not in {".gitkeep", ".llm-wiki-agent"} for name in files):
                return True
    except OSError:
        return True
    return False


def validate_live_query_source_selection(
    *,
    source_root: Path,
    wiki_root: Path,
    live_identity: Mapping[str, object] | None,
    live_selection_inputs: Mapping[str, object] | None | object = (
        _UNSET_LIVE_SELECTION_INPUTS
    ),
    operation: str,
    allow_empty_wiki: bool = False,
) -> None:
    """Require a live query profile to match the persisted wiki boundary."""

    try:
        manifest = SyncManifest.load(wiki_root)
    except FileNotFoundError as exc:
        if live_identity is None or (
            allow_empty_wiki and not _wiki_has_persisted_read_state(wiki_root)
        ):
            return
        raise DocumentationQueryError(
            f"{operation} cannot validate the active source-selection profile "
            "because the wiki has no usable sync manifest; run `llm-wiki sync` "
            "with the same --src-dir, --wiki-dir, and --source-selection first", field="source_selection"
        ) from exc
    except SyncManifestError as exc:
        raise DocumentationQueryError(
            f"{operation} cannot validate the active source-selection profile "
            "because the wiki sync manifest is invalid; restore it or run "
            "`llm-wiki sync` with the same active profile before querying", field="source_selection"
        ) from exc
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        raise DocumentationQueryError(
            f"{operation} cannot validate the active source-selection profile "
            "because the wiki sync manifest is invalid; restore it or run "
            "`llm-wiki sync` with the same active profile before querying", field="source_selection"
        ) from exc

    try:
        if live_selection_inputs is _UNSET_LIVE_SELECTION_INPUTS:
            validate_persisted_source_selection_identity(
                manifest.generation_inputs,
                live_identity,
                operation=operation,
            )
        else:
            validate_persisted_source_selection_identity(
                manifest.generation_inputs,
                live_identity,
                operation=operation,
                live_selection_inputs=live_selection_inputs,
            )
    except SourceSelectionError as exc:
        raise DocumentationQueryError(str(exc), field="source_selection") from exc


__all__ = [
    "DEFAULT_DOCUMENTATION_QUERY_LIMIT",
    "DocumentationQueryError",
    "MAX_DOCUMENTATION_QUERY_LIMIT",
    "MAX_SUPPLIED_PATHS",
    "QUERY_IDENTITY_BYTE_LIMIT",
    "normalize_concept_coordinate",
    "normalize_documentation_query_limit",
    "normalize_documentation_query_text",
    "normalize_supplied_paths",
    "validate_live_query_source_selection",
]
