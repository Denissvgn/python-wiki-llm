"""Shared, side-effect-free validators for service-layer contracts.

The helpers in this module deliberately receive caller-owned exceptions.  That
keeps domain-specific exception types and established diagnostic text at the
service boundary while ensuring the underlying acceptance rules cannot drift.
"""

from __future__ import annotations

import math
import os
import posixpath
import re
import unicodedata
import uuid
from collections.abc import (
    Callable,
    Container,
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
)
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any, TypeVar


_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")
_WINDOWS_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")
_WINDOWS_RESERVED_NAMES = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{number}" for number in range(1, 10)}
    | {f"lpt{number}" for number in range(1, 10)}
    | {f"com{number}" for number in ("¹", "²", "³")}
    | {f"lpt{number}" for number in ("¹", "²", "³")}
)
_WINDOWS_FORBIDDEN_PATH_CHARS = frozenset('<>:"|?*')
_UNSAFE_PAGE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ZERO_UTC_OFFSET = timedelta(0)

_ErrorFactory = Callable[[tuple[str, ...]], Exception]
_EnumValue = TypeVar("_EnumValue")


class SharedValidationError(ValueError):
    """Raised when a caller uses a shared validator without a domain adapter."""


def format_field_differences(
    missing: Iterable[object], unknown: Iterable[object]
) -> str:
    """Render deterministic exact-field differences."""

    detail: list[str] = []
    missing_values = tuple(str(value) for value in missing)
    unknown_values = tuple(str(value) for value in unknown)
    if missing_values:
        detail.append("missing " + ", ".join(missing_values))
    if unknown_values:
        detail.append("unknown " + ", ".join(unknown_values))
    return "; ".join(detail)


def _default_path_error(value: object) -> SharedValidationError:
    return SharedValidationError(
        f"Path must be a non-empty portable relative path: {value!r}"
    )


def require_portable_path_component(
    component: str,
    *,
    context: str | None = None,
    defer_non_nfc_error: bool = False,
    reject_delete_character: bool = True,
    utf8_error: Exception | None = None,
    control_error: Exception | None = None,
    non_nfc_error: Exception | None = None,
    nonportable_error: Exception | None = None,
    reserved_error: Exception | None = None,
) -> str:
    """Return a portable path component or raise a caller-owned exception.

    ``defer_non_nfc_error`` exists only for compatibility preflights that must
    detect a collection-level collision before strict per-path validation.
    Callers using it must subsequently validate the returned path strictly.
    """

    rendered = component if context is None else context
    try:
        component.encode("utf-8")
    except UnicodeEncodeError:
        raise utf8_error or nonportable_error or SharedValidationError(
            f"Path is not valid UTF-8 text: {rendered!r}"
        ) from None
    if (
        not defer_non_nfc_error
        and component != unicodedata.normalize("NFC", component)
    ):
        raise non_nfc_error or SharedValidationError(
            f"Path is not NFC-normalized: {rendered!r}"
        )
    if any(
        ord(character) < 32
        or (reject_delete_character and ord(character) == 127)
        for character in component
    ):
        raise control_error or nonportable_error or SharedValidationError(
            f"Path is not portable across supported systems: {rendered!r}"
        )
    if component.endswith((" ", ".")) or any(
        character in _WINDOWS_FORBIDDEN_PATH_CHARS
        for character in component
    ):
        raise nonportable_error or SharedValidationError(
            f"Path is not portable across supported systems: {rendered!r}"
        )
    if component.split(".", 1)[0].casefold() in _WINDOWS_RESERVED_NAMES:
        raise reserved_error or SharedValidationError(
            f"Path uses a reserved Windows name: {rendered!r}"
        )
    return component


def is_portable_path_component(component: str) -> bool:
    """Return whether *component* is portable on every supported filesystem."""

    try:
        require_portable_path_component(component)
    except (SharedValidationError, TypeError):
        return False
    return True


def require_portable_relative_path(
    value: object,
    *,
    normalize_backslashes: bool = False,
    normalize_posix_spelling: bool = False,
    required_suffix: str | None = None,
    defer_non_nfc_error: bool = False,
    reject_delete_character: bool = True,
    text_error: Exception | None = None,
    relative_error: Exception | None = None,
    escape_error: Exception | None = None,
    traversal_error: Exception | None = None,
    separator_error: Exception | None = None,
    utf8_error: Exception | None = None,
    control_error: Exception | None = None,
    non_nfc_error: Exception | None = None,
    nonportable_error: Exception | None = None,
    reserved_error: Exception | None = None,
    collision_seen: MutableMapping[str, str] | None = None,
    collision_error: Callable[[str, str], Exception] | None = None,
) -> str:
    """Return a canonical portable relative path.

    The strict default accepts only canonical ``/`` separators.  A filesystem
    API that intentionally accepts native Windows spelling can opt into
    backslash normalization without weakening any other check.
    ``normalize_posix_spelling`` is an explicit compatibility mode for legacy
    observational inputs: it collapses redundant ``/`` and ``.`` spelling,
    but still rejects traversal and every cross-platform hazard.
    ``defer_non_nfc_error`` is reserved for a compatibility preflight whose
    result is subsequently passed through this helper again in strict mode.
    """

    if not isinstance(value, (str, os.PathLike)):
        raise text_error or _default_path_error(value) from None
    raw = os.fspath(value)
    if not isinstance(raw, str):
        raise text_error or _default_path_error(value)
    try:
        raw.encode("utf-8")
    except UnicodeEncodeError:
        raise utf8_error or nonportable_error or relative_error or (
            _default_path_error(raw)
        ) from None
    if "\\" in raw and not normalize_backslashes:
        raise separator_error or relative_error or _default_path_error(raw)
    normalized = raw.replace("\\", "/") if normalize_backslashes else raw
    path = PurePosixPath(normalized)
    if path.is_absolute() or _WINDOWS_ABSOLUTE_RE.match(raw):
        raise escape_error or relative_error or _default_path_error(raw)
    if ".." in path.parts:
        raise (
            traversal_error
            or escape_error
            or relative_error
            or _default_path_error(raw)
        )
    canonical = path.as_posix()
    if (
        not normalized
        or normalized in {".", ".."}
        or normalized != normalized.strip()
        or "." in path.parts
        or (not normalize_posix_spelling and canonical != normalized)
        or (
            required_suffix is not None
            and not canonical.casefold().endswith(required_suffix.casefold())
        )
    ):
        raise relative_error or _default_path_error(raw)
    for component in path.parts:
        require_portable_path_component(
            component,
            context=canonical,
            defer_non_nfc_error=defer_non_nfc_error,
            reject_delete_character=reject_delete_character,
            utf8_error=utf8_error,
            control_error=control_error,
            non_nfc_error=non_nfc_error,
            nonportable_error=nonportable_error,
            reserved_error=reserved_error,
        )
    if collision_seen is not None:
        key = portable_path_key(canonical)
        previous = collision_seen.setdefault(key, canonical)
        if previous != canonical:
            if collision_error is None:
                raise SharedValidationError(
                    f"Paths collide across supported filesystems: "
                    f"{previous!r} and {canonical!r}"
                )
            raise collision_error(previous, canonical)
    return canonical


def require_repository_relative_path(
    value: object,
    *,
    text_error: Exception,
    posix_error: Exception,
    normalized_error: Exception,
    absolute_error: Exception | None = None,
    separator_error: Exception | None = None,
    control_error: Exception | None = None,
    reject_delete_character: bool = False,
    control_after_normalization: bool = False,
    leading_backslash_is_absolute: bool = False,
    normalize_posix_spelling: bool = False,
    portability_error: Exception | None = None,
) -> str:
    """Return one strict repository-relative path with tiered diagnostics.

    The three required exceptions preserve the established distinction between
    missing/non-text input, non-POSIX spelling, and non-normalized paths.
    Cross-platform hazards that the legacy repository validators accepted are
    rejected as normalization failures unless the caller supplies a dedicated
    portability diagnostic.
    """

    if not isinstance(value, str) or not value:
        raise text_error
    if value != value.strip():
        raise posix_error
    has_control_character = any(
        ord(character) < 0x20
        or (reject_delete_character and ord(character) == 0x7F)
        for character in value
    )
    if has_control_character and not control_after_normalization:
        raise control_error or posix_error
    if (
        value.startswith("/")
        or (leading_backslash_is_absolute and value.startswith("\\"))
        or _WINDOWS_DRIVE_PREFIX_RE.match(value)
    ):
        raise absolute_error or posix_error
    if "\\" in value:
        raise separator_error or posix_error
    parts = value.split("/")
    if normalize_posix_spelling:
        if ".." in PurePosixPath(value).parts:
            raise normalized_error
    elif (
        any(part in {"", ".", ".."} for part in parts)
        or posixpath.normpath(value) != value
    ):
        raise normalized_error
    if has_control_character:
        raise control_error or posix_error
    strict_error = portability_error or normalized_error
    return require_portable_relative_path(
        value,
        normalize_posix_spelling=normalize_posix_spelling,
        text_error=text_error,
        relative_error=normalized_error,
        escape_error=absolute_error or posix_error,
        traversal_error=normalized_error,
        separator_error=separator_error or posix_error,
        utf8_error=strict_error,
        control_error=control_error or strict_error,
        non_nfc_error=strict_error,
        nonportable_error=strict_error,
        reserved_error=strict_error,
    )


def is_portable_relative_path(
    value: object,
    *,
    normalize_backslashes: bool = False,
) -> bool:
    """Return whether *value* is a canonical portable relative path."""

    try:
        require_portable_relative_path(
            value,
            normalize_backslashes=normalize_backslashes,
        )
    except (SharedValidationError, TypeError, ValueError):
        return False
    return True


def normalize_legacy_portable_relative_path(
    value: object,
    *,
    text_error: Exception | None = None,
    absolute_error: Exception | None = None,
    traversal_error: Exception | None = None,
    empty_error: Exception | None = None,
    invalid_error: Exception | None = None,
    reject_dot_prefixed_absolute: bool = False,
) -> str | None:
    """Normalize a legacy observational path, returning ``None`` if unsafe.

    This deliberately loose compatibility boundary trims surrounding
    whitespace, converts backslashes, and collapses redundant POSIX separators
    and ``.`` segments.  Its output still passes the strict portable-path
    contract.  It must not be used for mutation or authority-bearing paths.
    """

    if not isinstance(value, str) or not value.strip():
        if text_error is not None:
            raise text_error
        return None
    normalized_input = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized_input)
    if (
        (
            reject_dot_prefixed_absolute
            and normalized_input.startswith(".//")
        )
        or path.is_absolute()
        or _WINDOWS_ABSOLUTE_RE.match(normalized_input)
        or _WINDOWS_DRIVE_PREFIX_RE.match(normalized_input)
    ):
        if absolute_error is not None:
            raise absolute_error
        return None
    if ".." in path.parts:
        if traversal_error is not None:
            raise traversal_error
        return None
    normalized = path.as_posix()
    if normalized in {"", "."}:
        if empty_error is not None:
            raise empty_error
        return None
    try:
        return require_portable_relative_path(normalized)
    except SharedValidationError:
        if invalid_error is not None:
            raise invalid_error from None
        return None


def normalize_optional_portable_relative_path(value: object) -> str | None:
    """Normalize legacy observational spelling and return ``None`` if unsafe.

    This compatibility boundary accepts surrounding whitespace, native
    backslashes, and leading ``./`` segments before applying the strict
    cross-platform path contract. It is intentionally unsuitable for mutation
    or authority-bearing paths.
    """

    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    try:
        return require_portable_relative_path(normalized)
    except SharedValidationError:
        return None


def normalize_observational_posix_path(value: object) -> str | None:
    """Normalize display-only path metadata without asserting path safety.

    This deliberately preserves legacy review-report behavior: arbitrary
    scalar values are stringified, surrounding whitespace and native
    separators are normalized, and absolute or traversing spellings remain
    visible to reviewers.  The result must never authorize filesystem access;
    authority-bearing callers must use ``require_portable_relative_path``.
    """

    raw = str(value).strip().replace("\\", "/")
    while raw.startswith("./"):
        raw = raw[2:]
    return PurePosixPath(raw).as_posix() if raw else None


def portable_path_key(value: str) -> str:
    """Return the collision key used by normalizing/case-insensitive filesystems."""

    return unicodedata.normalize("NFC", value).casefold()


def path_is_under(path: str, prefix: str) -> bool:
    """Return whether a slash-delimited path is inside a non-empty prefix."""

    return bool(prefix) and (path == prefix or path.startswith(prefix + "/"))


def path_is_under_scope(path: str, scope_root: str) -> bool:
    """Return whether a native-spelled path is inside an optional scope root."""

    normalized = path.replace("\\", "/").strip("/")
    return not scope_root or path_is_under(normalized, scope_root)


def path_is_within(path: Path, root: Path) -> bool:
    """Return whether *path* is equal to or lexically below *root*."""

    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def paths_overlap(left: Path, right: Path) -> bool:
    """Return whether either lexical path is equal to or below the other."""

    return path_is_within(left, right) or path_is_within(right, left)


def resolved_paths_equal(
    left: str | Path,
    right: str | Path,
) -> bool:
    """Return whether two path spellings resolve to the same location."""

    return Path(left).resolve() == Path(right).resolve()


def path_is_in_top_level_directory(
    path: Path,
    root: Path,
    directory: str,
) -> bool:
    """Return whether a path is inside one named top-level root directory."""

    try:
        relative = path.relative_to(root)
    except ValueError:
        try:
            relative = path.resolve().relative_to(root.resolve())
        except ValueError:
            return False
    return relative.parts[:1] == (directory,)


def posix_path_text(value: object) -> str:
    """Render path-like display text with portable separators."""

    return str(value).replace("\\", "/")


def resolve_workspace_path(
    workspace_root: Path,
    relative: str,
    *,
    escape_error: Exception,
) -> Path:
    """Resolve *relative* below *workspace_root* and reject symlink escapes."""

    resolved_root = workspace_root.resolve()
    target = (resolved_root / relative).resolve()
    try:
        target.relative_to(resolved_root)
    except ValueError as exc:
        raise escape_error from exc
    return target


def resolve_portable_workspace_path(
    workspace_root: Path,
    relative: str | Path,
    *,
    path_error: Exception,
    escape_error: Exception,
    traversal_error: Exception | None = None,
) -> Path:
    """Resolve one strict portable relative path below *workspace_root*."""

    canonical = require_portable_relative_path(
        relative,
        text_error=path_error,
        relative_error=path_error,
        escape_error=escape_error,
        traversal_error=traversal_error or escape_error,
        separator_error=path_error,
        utf8_error=path_error,
        control_error=path_error,
        non_nfc_error=path_error,
        nonportable_error=path_error,
        reserved_error=path_error,
    )
    return resolve_workspace_path(
        workspace_root,
        canonical,
        escape_error=escape_error,
    )


def require_safe_base_path(path: Path, *, error: Exception) -> None:
    """Reject ambiguous filesystem base paths."""

    if path.name in {"", ".", ".."}:
        raise error


def require_existing_directory(path: Path, *, error: Exception) -> None:
    """Require an existing directory while preserving caller diagnostics."""

    if not path.exists() or not path.is_dir():
        raise error


def require_existing_file(path: Path, *, error: Exception) -> Path:
    """Require an existing regular file while preserving caller diagnostics."""

    if not path.is_file():
        raise error
    return path


def portable_page_component(value: object, *, fallback: str = "page") -> str:
    """Return a generated wiki page component portable on supported filesystems."""

    def sanitize(candidate: object) -> str:
        raw = str(candidate).strip() if candidate not in (None, "") else ""
        normalized = unicodedata.normalize("NFC", raw)
        safe = _UNSAFE_PAGE_COMPONENT_RE.sub("_", normalized).strip("_")
        safe = re.sub(r"_+", "_", safe).lstrip(".").rstrip(". ")
        while ".." in safe:
            safe = safe.replace("..", "._")
        if safe and not is_portable_path_component(safe):
            safe = f"_{safe}"
        return safe

    return sanitize(value) or sanitize(fallback) or "page"


def require_nonempty_text(
    value: object,
    *,
    error: Exception,
    trim_error: Exception | None = None,
    normalize: bool = False,
    require_trimmed: bool = False,
    reject_control_characters: bool = True,
    reject_delete_character: bool = False,
) -> str:
    """Return non-empty text under an explicit normalization policy."""

    if not isinstance(value, str):
        raise error
    trimmed = value.strip()
    parsed = trimmed if normalize else value
    if not parsed:
        raise error
    if require_trimmed and trimmed != value:
        raise trim_error or error
    if reject_control_characters and any(
        ord(character) < 0x20
        or (reject_delete_character and ord(character) == 0x7F)
        for character in parsed
    ):
        raise error
    return parsed


def require_bounded_text(
    value: object,
    *,
    maximum: int,
    error: Exception,
    minimum: int = 1,
    control_error: Exception | None = None,
    require_trimmed: bool = False,
    reject_control_characters: bool = True,
    reject_delete_character: bool = True,
) -> str:
    """Return text within inclusive bounds under an explicit scalar policy."""

    if (
        not isinstance(value, str)
        or len(value) < minimum
        or len(value) > maximum
        or (require_trimmed and value != value.strip())
    ):
        raise error
    if reject_control_characters and any(
        ord(character) < 0x20
        or (reject_delete_character and ord(character) == 0x7F)
        for character in value
    ):
        raise control_error or error
    return value


def require_no_control_characters(
    value: object,
    *,
    error: Exception,
    reject_delete_character: bool = False,
) -> str:
    """Return text without ASCII controls, optionally including DEL."""

    if not isinstance(value, str) or contains_control_character(
        value,
        reject_delete_character=reject_delete_character,
    ):
        raise error
    return value


def contains_control_character(
    value: str,
    *,
    reject_delete_character: bool = False,
) -> bool:
    """Return whether text contains an ASCII control selected by policy."""

    return any(
        ord(character) < 0x20
        or (reject_delete_character and ord(character) == 0x7F)
        for character in value
    )


def require_trimmed_text(
    value: object,
    *,
    error: Exception,
    reject_control_characters: bool = True,
) -> str:
    """Return non-empty text with canonical surrounding whitespace."""

    return require_nonempty_text(
        value,
        error=error,
        require_trimmed=True,
        reject_control_characters=reject_control_characters,
    )


def require_trimmed_text_list(
    value: object,
    *,
    error: Exception,
    item_error: Exception | None = None,
    duplicate_error: Exception | None = None,
    sort: bool = False,
    require_trimmed_items: bool = True,
    reject_control_characters: bool = True,
    reject_duplicates: bool = False,
    container_type: type[object] | tuple[type[object], ...] = list,
) -> list[str]:
    """Return text items from a caller-selected sequence container."""

    if not isinstance(value, container_type) or not isinstance(value, Iterable):
        raise error
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise item_error or error
        if require_trimmed_items and item != item.strip():
            raise item_error or error
        if reject_control_characters and any(
            ord(character) < 0x20 for character in item
        ):
            raise item_error or error
        items.append(item)
    if reject_duplicates and len(set(items)) != len(items):
        raise duplicate_error or error
    return sorted(items) if sort else items


def require_string(
    value: object,
    *,
    error: Exception,
    utf8_error: Exception | None = None,
) -> str:
    """Return a string, optionally requiring UTF-8-encodable scalar text."""

    if not isinstance(value, str):
        raise error
    if utf8_error is not None:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise utf8_error from exc
    return value


def require_mapping(
    value: object,
    *,
    error: Exception,
    require_string_keys: bool = False,
    key_error: Exception | None = None,
    require_utf8_keys: bool = False,
    utf8_key_error: Exception | None = None,
) -> Mapping[str, Any]:
    """Return a mapping with optional JSON string/scalar key requirements."""

    if not isinstance(value, Mapping):
        raise error
    if require_string_keys or require_utf8_keys:
        for key in value:
            if not isinstance(key, str):
                raise key_error or error
            if not require_utf8_keys:
                continue
            try:
                key.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise utf8_key_error or key_error or error from exc
    return value


def require_sequence(
    value: object,
    *,
    error: Exception,
    container_type: type[object] | tuple[type[object], ...] = Sequence,
    reject_mapping: bool = False,
) -> Sequence[Any]:
    """Return a non-text sequence from caller-selected container types."""

    if (
        isinstance(value, (str, bytes))
        or (reject_mapping and isinstance(value, Mapping))
        or not isinstance(value, container_type)
    ):
        raise error
    assert isinstance(value, Sequence)
    return value


def require_list(value: object, *, error: Exception) -> list[Any]:
    """Return a concrete list without accepting other sequence types."""

    if not isinstance(value, list):
        raise error
    return value


def require_bool(value: object, *, error: Exception) -> bool:
    """Return a strict boolean value."""

    if not isinstance(value, bool):
        raise error
    return value


def require_int(value: object, *, error: Exception) -> int:
    """Return a strict integer (booleans are not integers here)."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise error
    return value


def require_nonnegative_int(value: object, *, error: Exception) -> int:
    """Return a strict non-negative integer (booleans are not integers here)."""

    parsed = require_int(value, error=error)
    if parsed < 0:
        raise error
    return parsed


def nonnegative_int_or_none(value: object) -> int | None:
    """Return a strict non-negative integer, or ``None`` for other values."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def require_positive_int(
    value: object,
    *,
    invalid_error: Exception,
    zero_error: Exception | None = None,
) -> int:
    """Return a strict positive integer."""

    parsed = require_nonnegative_int(value, error=invalid_error)
    if parsed == 0:
        raise zero_error or invalid_error
    return parsed


def require_int_at_least(
    value: object,
    *,
    minimum: int,
    error: Exception,
) -> int:
    """Return a strict integer at or above a caller-selected lower bound."""

    parsed = require_int(value, error=error)
    if parsed < minimum:
        raise error
    return parsed


def require_bounded_int(
    value: object,
    *,
    minimum: int,
    maximum: int,
    invalid_error: Exception,
    bounds_error: Exception | None = None,
) -> int:
    """Return a strict integer within inclusive caller-selected bounds."""

    parsed = require_int(value, error=invalid_error)
    if parsed < minimum or parsed > maximum:
        raise bounds_error or invalid_error
    return parsed


def require_bounded_integral_number(
    value: object,
    *,
    invalid_error: Exception,
    minimum: int | None = None,
    maximum: int | None = None,
    bounds_error: Exception | None = None,
    zero_error: Exception | None = None,
) -> int:
    """Return an int or finite integral float within optional inclusive bounds."""

    if isinstance(value, bool):
        raise invalid_error
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, float) and math.isfinite(value) and value.is_integer():
        parsed = int(value)
    else:
        raise invalid_error
    if (
        (minimum is not None and parsed < minimum)
        or (maximum is not None and parsed > maximum)
    ):
        raise bounds_error or invalid_error
    if parsed == 0 and zero_error is not None:
        raise zero_error
    return parsed


def positive_int_or_none(value: object) -> int | None:
    """Return a strict positive integer, or ``None`` for any other value."""

    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def coerce_nonnegative_int(value: object, *, error: Exception) -> int:
    """Coerce an integer-like value and require a non-negative result."""

    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise error from exc
    if isinstance(value, bool) or parsed < 0:
        raise error
    return parsed


def coerce_positive_int(value: object, *, error: Exception) -> int:
    """Coerce an integer-like value and require a positive result."""

    parsed = coerce_nonnegative_int(value, error=error)
    if parsed == 0:
        raise error
    return parsed


def coerce_trimmed_text(value: object) -> str:
    """Return legacy display text: ``None`` becomes empty, all else is stripped."""

    return "" if value is None else str(value).strip()


def trimmed_text_or_none(
    value: object,
    *,
    error: Exception | None = None,
) -> str | None:
    """Return stripped optional text under an explicit invalid-value policy."""

    if not isinstance(value, str):
        if value is not None and error is not None:
            raise error
        return None
    trimmed = value.strip()
    return trimmed or None


def filtered_trimmed_text_list(
    value: object,
    *,
    limit: int | None = None,
) -> list[str]:
    """Normalize a loose observational sequence of text.

    Invalid containers and items are deliberately ignored; this helper is for
    bounded diagnostic evidence, never authority-bearing protocol input.
    """

    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    items = sorted(
        {item.strip() for item in value if isinstance(item, str) and item.strip()}
    )
    return items if limit is None else items[:limit]


def bool_or_none(value: object) -> bool | None:
    """Return a strict boolean, or ``None`` for any other value."""

    return value if isinstance(value, bool) else None


def require_string_list(value: object, *, error: Exception) -> list[str]:
    """Return the caller's concrete list after strict string-item validation."""

    items = require_list(value, error=error)
    for item in items:
        require_string(item, error=error)
    return items  # type: ignore[return-value]


def require_string_tuple(
    value: object,
    *,
    error: Exception,
    item_error: Exception | None = None,
    minimum: int = 0,
    maximum: int | None = None,
    container_type: type[object] | tuple[type[object], ...] = Sequence,
    item_parser: Callable[[object], str] | None = None,
) -> tuple[str, ...]:
    """Return parsed strings from a bounded, caller-selected sequence."""

    items = require_sequence(
        value,
        error=error,
        container_type=container_type,
    )
    if len(items) < minimum or (
        maximum is not None and len(items) > maximum
    ):
        raise error
    if item_parser is None:
        return tuple(
            require_string(item, error=item_error or error) for item in items
        )
    return tuple(item_parser(item) for item in items)


def require_mapping_tuple(
    value: object,
    *,
    error: Exception,
    item_error: Exception | None = None,
    container_type: type[object] | tuple[type[object], ...] = Sequence,
) -> tuple[Mapping[str, Any], ...]:
    """Return mapping items from a caller-selected non-text sequence."""

    items = require_sequence(
        value,
        error=error,
        container_type=container_type,
    )
    return tuple(
        require_mapping(item, error=item_error or error) for item in items
    )


def require_mapping_list(
    value: object,
    *,
    error: Exception,
    item_error: Exception | None = None,
    require_string_keys: bool = False,
) -> list[Mapping[str, Any]]:
    """Return the caller's list after strict mapping-item validation."""

    items = require_list(value, error=error)
    for item in items:
        require_mapping(
            item,
            error=item_error or error,
            require_string_keys=require_string_keys,
        )
    return items  # type: ignore[return-value]


def require_choice(
    value: object,
    choices: Iterable[str],
    *,
    text_error: Exception,
    choice_error: Callable[[frozenset[str]], Exception],
    reject_control_characters: bool = True,
) -> str:
    """Return trimmed text from one closed set."""

    parsed = require_trimmed_text(
        value,
        error=text_error,
        reject_control_characters=reject_control_characters,
    )
    allowed = frozenset(choices)
    if parsed not in allowed:
        raise choice_error(allowed)
    return parsed


def require_exact_choice(
    value: object,
    choices: Iterable[str],
    *,
    error: Exception,
) -> str:
    """Return an exact string member without trimming or normalization."""

    parsed = require_string(value, error=error)
    if parsed not in frozenset(choices):
        raise error
    return parsed


def require_enum_value(
    value: object,
    enum_type: Callable[[str], _EnumValue],
    *,
    text_error: Exception,
    choice_error: Callable[[], Exception],
) -> _EnumValue:
    """Return one exact string-backed enum member with caller diagnostics."""

    parsed = require_string(value, error=text_error)
    try:
        return enum_type(parsed)
    except ValueError as exc:
        raise choice_error() from exc


def require_member(
    value: object,
    choices: Container[object],
    *,
    error: Exception,
) -> object:
    """Return an exact collection member using the collection's own semantics."""

    if value not in choices:
        raise error
    return value


def require_sha256(
    value: object,
    *,
    digest_error: Exception,
    text_error: Exception | None = None,
    reject_control_characters: bool = True,
    allow_empty: bool = False,
) -> str:
    """Return a canonical ``sha256:<lowercase hex>`` digest."""

    if text_error is None:
        if not isinstance(value, str):
            raise digest_error
        parsed = value
    else:
        parsed = require_trimmed_text(
            value,
            error=text_error,
            reject_control_characters=reject_control_characters,
        )
    if allow_empty and parsed == "":
        return parsed
    if _SHA256_RE.fullmatch(parsed) is None:
        raise digest_error
    return parsed


def require_uuid(
    value: object,
    *,
    text_error: Exception,
    uuid_error: Exception,
    canonical_error: Exception,
    reject_control_characters: bool = True,
) -> str:
    """Return a canonical lowercase, hyphenated UUID."""

    parsed = require_trimmed_text(
        value,
        error=text_error,
        reject_control_characters=reject_control_characters,
    )
    try:
        normalized = str(uuid.UUID(parsed))
    except ValueError as exc:
        raise uuid_error from exc
    if parsed != normalized:
        raise canonical_error
    return parsed


def is_canonical_uuid(value: object) -> bool:
    """Return whether *value* is a canonical lowercase, hyphenated UUID."""

    error = SharedValidationError("value must be a canonical UUID")
    try:
        require_uuid(
            value,
            text_error=error,
            uuid_error=error,
            canonical_error=error,
        )
    except ValueError:
        return False
    return True


def parse_utc_timestamp(
    value: object,
    *,
    string_error: Exception,
    timestamp_error: Exception,
    require_z: bool = False,
    reject_control_characters: bool = True,
    control_error: Exception | None = None,
    z_error: Exception | None = None,
    utc_error: Exception | None = None,
) -> tuple[str, datetime]:
    """Return the original timestamp and its timezone-aware UTC value."""

    parsed = require_trimmed_text(
        value,
        error=string_error,
        reject_control_characters=False,
    )
    if reject_control_characters and any(
        ord(character) < 0x20 for character in parsed
    ):
        raise control_error or string_error
    if require_z and not parsed.endswith("Z"):
        raise z_error or timestamp_error
    normalized = parsed[:-1] + "+00:00" if parsed.endswith("Z") else parsed
    try:
        timestamp = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise timestamp_error from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() != _ZERO_UTC_OFFSET:
        raise utc_error or timestamp_error
    return parsed, timestamp


def require_exact_fields(
    value: object,
    *,
    allowed: Iterable[str],
    required: Iterable[str],
    mapping_error: Exception,
    missing_error: _ErrorFactory,
    unknown_error: _ErrorFactory,
    invalid_error: Callable[[tuple[str, ...], tuple[str, ...]], Exception]
    | None = None,
    stringify_keys: bool = False,
    unknown_first: bool = False,
) -> None:
    """Require an exact/allowed mapping shape with caller-owned diagnostics."""

    if not isinstance(value, Mapping):
        raise mapping_error
    keys = {str(key) for key in value} if stringify_keys else set(value)
    allowed_keys = set(allowed)
    required_keys = set(required)
    missing = tuple(sorted(required_keys - keys, key=str))
    unknown = tuple(sorted(keys - allowed_keys, key=str))
    if invalid_error is not None and (missing or unknown):
        raise invalid_error(missing, unknown)
    checks = (
        ((unknown, unknown_error), (missing, missing_error))
        if unknown_first
        else ((missing, missing_error), (unknown, unknown_error))
    )
    for fields, error_factory in checks:
        if fields:
            raise error_factory(fields)


__all__ = [
    "bool_or_none",
    "coerce_nonnegative_int",
    "coerce_positive_int",
    "coerce_trimmed_text",
    "contains_control_character",
    "filtered_trimmed_text_list",
    "format_field_differences",
    "SharedValidationError",
    "is_canonical_uuid",
    "is_portable_path_component",
    "is_portable_relative_path",
    "normalize_legacy_portable_relative_path",
    "normalize_observational_posix_path",
    "normalize_optional_portable_relative_path",
    "nonnegative_int_or_none",
    "parse_utc_timestamp",
    "path_is_in_top_level_directory",
    "path_is_under",
    "path_is_under_scope",
    "path_is_within",
    "paths_overlap",
    "portable_page_component",
    "portable_path_key",
    "posix_path_text",
    "positive_int_or_none",
    "require_bool",
    "require_bounded_int",
    "require_bounded_integral_number",
    "require_bounded_text",
    "require_choice",
    "require_exact_choice",
    "require_enum_value",
    "require_exact_fields",
    "require_int",
    "require_int_at_least",
    "require_list",
    "require_mapping",
    "require_mapping_list",
    "require_mapping_tuple",
    "require_member",
    "require_nonempty_text",
    "require_no_control_characters",
    "require_nonnegative_int",
    "require_existing_directory",
    "require_existing_file",
    "require_portable_path_component",
    "require_portable_relative_path",
    "require_repository_relative_path",
    "require_safe_base_path",
    "require_positive_int",
    "require_sequence",
    "require_sha256",
    "require_string",
    "require_string_list",
    "require_string_tuple",
    "require_trimmed_text",
    "require_trimmed_text_list",
    "require_uuid",
    "resolved_paths_equal",
    "resolve_portable_workspace_path",
    "resolve_workspace_path",
    "trimmed_text_or_none",
]
