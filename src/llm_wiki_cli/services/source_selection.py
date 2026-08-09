"""Canonical repository source-selection policy and provenance helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import EXCLUDED_DIRS, is_agent_worktree_path
from .validation import portable_path_key, require_repository_relative_path

SOURCE_SELECTION_PATH = ".llm-wiki/source-selection.json"
SOURCE_SELECTION_SCHEMA_VERSION = "llm-wiki-source-selection/v1"
SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION = (
    "llm-wiki-source-selection-identity/v1"
)
SOURCE_SELECTION_GENERATION_INPUT_KEY = "source_selection"
SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY = "source_selection_inputs"
SOURCE_SELECTION_INPUTS_SCHEMA_VERSION = "llm-wiki-source-selection-inputs/v1"

_UNSET_SELECTION_INPUTS = object()

_SOURCE_SELECTION_ORIGINS = frozenset({"default", "explicit"})
_MAX_CONFIG_BYTES = 64 * 1024
_MAX_PATH_BYTES = 1024
_MAX_PATH_COUNT = 512
_MAX_SELECTION_SCAN_ENTRIES = 100_000
_GLOB_CHARACTERS = frozenset("*?[]")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class SourceSelectionError(ValueError):
    """Field-specific failure loading or validating source selection."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def _require_selection_path(value: object, field: str) -> str:
    """Delegate repository-path validation to the shared strict validator."""

    return require_repository_relative_path(
        value,
        text_error=SourceSelectionError(
            field, "must be a non-empty repository-relative path"
        ),
        posix_error=SourceSelectionError(
            field, "must be a repository-relative POSIX path"
        ),
        normalized_error=SourceSelectionError(
            field, "must be a normalized repository-relative path"
        ),
        absolute_error=SourceSelectionError(
            field, "must not be absolute or use a drive/device prefix"
        ),
        separator_error=SourceSelectionError(
            field, "must use POSIX '/' separators"
        ),
        control_error=SourceSelectionError(
            field, "must not contain control characters"
        ),
        reject_delete_character=True,
        leading_backslash_is_absolute=True,
        portability_error=SourceSelectionError(
            field, "must be portable across supported filesystems"
        ),
    )


def _selection_path(value: object, field: str, *, reject_glob: bool) -> str:
    try:
        path = _require_selection_path(value, field)
    except SourceSelectionError:
        raise
    except (TypeError, ValueError) as exc:
        raise SourceSelectionError(
            field, "must be a normalized portable repository-relative path"
        ) from exc
    if len(path.encode("utf-8")) > _MAX_PATH_BYTES:
        raise SourceSelectionError(
            field, f"must be at most {_MAX_PATH_BYTES} UTF-8 bytes"
        )
    if reject_glob and any(character in path for character in _GLOB_CHARACTERS):
        raise SourceSelectionError(field, "must be a literal path without glob syntax")
    return path


def _is_under(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def _is_strictly_under(path: str, root: str) -> bool:
    return path.startswith(root + "/")


def _validate_case_spelling(paths: tuple[str, ...]) -> None:
    spellings: dict[tuple[str, ...], tuple[str, ...]] = {}
    for path in paths:
        parts = tuple(path.split("/"))
        folded: list[str] = []
        exact: list[str] = []
        for component in parts:
            folded.append(portable_path_key(component))
            exact.append(component)
            key = tuple(folded)
            spelling = tuple(exact)
            previous = spellings.setdefault(key, spelling)
            if previous != spelling:
                raise SourceSelectionError(
                    "source_selection",
                    "paths collide or use inconsistent case across supported "
                    f"filesystems: {'/'.join(previous)!r} and "
                    f"{'/'.join(spelling)!r}",
                )


def _validate_no_overlaps(paths: tuple[str, ...], field: str) -> None:
    for index, path in enumerate(paths):
        for other in paths[index + 1 :]:
            if _is_strictly_under(other, path) or _is_strictly_under(path, other):
                raise SourceSelectionError(
                    field,
                    f"paths must not overlap: {path!r} and {other!r}",
                )


def _normalized_policy_paths(
    include: object,
    exclude: object,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    normalized: list[tuple[str, ...]] = []
    for field, value, require_nonempty in (
        ("include", include, True),
        ("exclude", exclude, False),
    ):
        if not isinstance(value, (list, tuple)):
            raise SourceSelectionError(field, "must be an array of literal paths")
        if require_nonempty and not value:
            raise SourceSelectionError(field, "must contain at least one path")
        if len(value) > _MAX_PATH_COUNT:
            raise SourceSelectionError(
                field, f"must contain at most {_MAX_PATH_COUNT} paths"
            )
        entries: list[str] = []
        seen: set[str] = set()
        for index, raw_path in enumerate(value):
            path = _selection_path(raw_path, f"{field}[{index}]", reject_glob=True)
            if path in seen:
                raise SourceSelectionError(
                    f"{field}[{index}]", f"duplicates literal path {path!r}"
                )
            seen.add(path)
            entries.append(path)
        normalized.append(tuple(sorted(entries)))

    include_paths, exclude_paths = normalized
    _validate_case_spelling(include_paths + exclude_paths)
    _validate_no_overlaps(include_paths, "include")
    _validate_no_overlaps(exclude_paths, "exclude")
    for index, excluded in enumerate(exclude_paths):
        if not any(
            _is_strictly_under(excluded, included) for included in include_paths
        ):
            raise SourceSelectionError(
                f"exclude[{index}]",
                "must be strictly below one configured include path",
            )
    return include_paths, exclude_paths


@dataclass(frozen=True)
class SourceSelectionPolicy:
    """Validated, immutable source-selection policy bound to one repository."""

    schema_version: str
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    source_root: Path
    path: str
    origin: str
    raw_content_hash: str

    def __post_init__(self) -> None:
        if self.schema_version != SOURCE_SELECTION_SCHEMA_VERSION:
            raise SourceSelectionError(
                "schema_version",
                f"must be {SOURCE_SELECTION_SCHEMA_VERSION!r}",
            )
        include, exclude = _normalized_policy_paths(self.include, self.exclude)
        object.__setattr__(self, "include", include)
        object.__setattr__(self, "exclude", exclude)
        try:
            root = Path(self.source_root).resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            raise SourceSelectionError(
                "source_root", "must resolve to a repository directory"
            ) from exc
        object.__setattr__(self, "source_root", root)
        object.__setattr__(
            self,
            "path",
            _selection_path(self.path, "path", reject_glob=True),
        )
        _validate_case_spelling(self.include + self.exclude + (self.path,))
        if self.origin not in _SOURCE_SELECTION_ORIGINS:
            raise SourceSelectionError(
                "origin", "must be either 'default' or 'explicit'"
            )
        if not isinstance(self.raw_content_hash, str) or _SHA256_RE.fullmatch(
            self.raw_content_hash
        ) is None:
            raise SourceSelectionError(
                "raw_content_hash", "must use canonical sha256:<hex> form"
            )

    @property
    def fingerprint(self) -> str:
        """Return the canonical semantic policy fingerprint."""
        return selection_fingerprint(self)

    @property
    def identity(self) -> dict[str, str]:
        """Return the canonical persisted selection identity."""
        return {
            "schema_version": SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION,
            "path": self.path,
            "fingerprint": self.fingerprint,
        }


def canonical_selection_payload(policy: SourceSelectionPolicy) -> bytes:
    """Serialize semantic policy fields independent of formatting/list order."""
    if not isinstance(policy, SourceSelectionPolicy):
        raise SourceSelectionError("source_selection", "must be a selection policy")
    payload = {
        "schema_version": policy.schema_version,
        "include": sorted(policy.include),
        "exclude": sorted(policy.exclude),
    }
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def selection_fingerprint(policy: SourceSelectionPolicy) -> str:
    """Return a domain-stable SHA-256 over canonical semantic policy bytes."""
    return "sha256:" + hashlib.sha256(canonical_selection_payload(policy)).hexdigest()


def path_is_selected(
    policy: SourceSelectionPolicy | None,
    rel_path: str,
) -> bool:
    """Return whether a strict repository-relative path is inside *policy*."""
    path = _selection_path(rel_path, "source_path", reject_glob=False)
    if policy is None:
        return True
    if not isinstance(policy, SourceSelectionPolicy):
        raise SourceSelectionError("source_selection", "must be a selection policy")
    return any(_is_under(path, root) for root in policy.include) and not any(
        _is_under(path, root) for root in policy.exclude
    )


def selection_may_contain_path(
    policy: SourceSelectionPolicy | None,
    rel_path: str,
) -> bool:
    """Return whether a directory is selected or is an ancestor of selection."""
    if policy is None:
        return True
    if rel_path in {"", "."}:
        return True
    path = _selection_path(rel_path, "source_directory", reject_glob=False)
    if any(_is_under(path, excluded) for excluded in policy.exclude):
        return False
    return any(
        _is_under(path, included) or _is_under(included, path)
        for included in policy.include
    )


def _is_link_or_reparse_stat(metadata: os.stat_result) -> bool:
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def path_is_link_or_reparse(path: Path) -> bool:
    """Return whether *path* is a symlink or Windows reparse point."""
    try:
        return _is_link_or_reparse_stat(path.lstat())
    except OSError:
        return False


def _locate_exact_path(
    root: Path,
    rel_path: str,
    *,
    allow_leaf_link: bool = False,
) -> Path | None:
    current = root
    parts = rel_path.split("/")
    for index, component in enumerate(parts):
        try:
            with os.scandir(current) as entries:
                materialized = list(entries)
        except FileNotFoundError:
            return None
        except (NotADirectoryError, OSError) as exc:
            raise SourceSelectionError(
                "source_selection",
                f"cannot inspect repository path {rel_path!r}: {exc}",
            ) from exc
        exact = next((entry for entry in materialized if entry.name == component), None)
        if exact is None:
            folded = portable_path_key(component)
            collision = next(
                (
                    entry.name
                    for entry in materialized
                    if portable_path_key(entry.name) == folded
                ),
                None,
            )
            if collision is not None:
                raise SourceSelectionError(
                    "source_selection",
                    f"path {rel_path!r} does not match filesystem case "
                    f"at component {collision!r}",
                )
            return None
        try:
            metadata = exact.stat(follow_symlinks=False)
        except OSError as exc:
            raise SourceSelectionError(
                "source_selection", f"cannot inspect repository path {rel_path!r}"
            ) from exc
        is_leaf = index == len(parts) - 1
        if _is_link_or_reparse_stat(metadata) and not (allow_leaf_link and is_leaf):
            raise SourceSelectionError(
                "source_selection",
                f"selected path {rel_path!r} traverses a symlink or reparse point",
            )
        current = Path(exact.path)
    return current


def locate_exact_repository_path(
    root: Path,
    rel_path: str,
    *,
    allow_leaf_link: bool = False,
) -> Path | None:
    """Locate an exact-case path without traversing links or reparse points."""
    return _locate_exact_path(
        root,
        rel_path,
        allow_leaf_link=allow_leaf_link,
    )


def _read_config(path: Path) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise SourceSelectionError(
            "source_selection", f"cannot inspect selection file {path}"
        ) from exc
    if _is_link_or_reparse_stat(metadata) or not stat.S_ISREG(metadata.st_mode):
        raise SourceSelectionError(
            "source_selection",
            "selection file must be a regular file without symlink/reparse components",
        )
    try:
        with path.open("rb") as handle:
            content = handle.read(_MAX_CONFIG_BYTES + 1)
    except OSError as exc:
        raise SourceSelectionError(
            "source_selection", f"cannot read selection file {path}"
        ) from exc
    if len(content) > _MAX_CONFIG_BYTES:
        raise SourceSelectionError(
            "source_selection",
            f"selection file must be at most {_MAX_CONFIG_BYTES} bytes",
        )
    return content


def _duplicate_checked_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SourceSelectionError(
                "source_selection", f"contains duplicate JSON key {key!r}"
            )
        result[key] = value
    return result


def _decode_config(content: bytes) -> Mapping[str, object]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceSelectionError(
            "source_selection", "must contain strict UTF-8 JSON"
        ) from exc
    if text.startswith("\ufeff"):
        raise SourceSelectionError(
            "source_selection", "must not contain a UTF-8 byte-order mark"
        )
    try:
        value = json.loads(text, object_pairs_hook=_duplicate_checked_object)
    except SourceSelectionError:
        raise
    except (json.JSONDecodeError, RecursionError) as exc:
        raise SourceSelectionError(
            "source_selection", "must contain valid bounded JSON"
        ) from exc
    if not isinstance(value, Mapping):
        raise SourceSelectionError("source_selection", "must contain a JSON object")
    return value


def _policy_from_content(
    *,
    root: Path,
    rel_path: str,
    origin: str,
    content: bytes,
) -> SourceSelectionPolicy:
    data = _decode_config(content)
    required = {"schema_version", "include", "exclude"}
    keys = set(data)
    missing = sorted(required - keys)
    unknown = sorted(keys - required)
    if missing:
        raise SourceSelectionError(
            f"source_selection.{missing[0]}", "is required"
        )
    if unknown:
        raise SourceSelectionError(
            f"source_selection.{unknown[0]}", "is not supported"
        )
    schema_version = data["schema_version"]
    if schema_version != SOURCE_SELECTION_SCHEMA_VERSION:
        raise SourceSelectionError(
            "schema_version", f"must be {SOURCE_SELECTION_SCHEMA_VERSION!r}"
        )
    return SourceSelectionPolicy(
        schema_version=SOURCE_SELECTION_SCHEMA_VERSION,
        include=data["include"],  # type: ignore[arg-type]
        exclude=data["exclude"],  # type: ignore[arg-type]
        source_root=root,
        path=rel_path,
        origin=origin,
        raw_content_hash="sha256:" + hashlib.sha256(content).hexdigest(),
    )


def _register_portable_filesystem_path(
    spellings: dict[str, str],
    rel_path: str,
) -> None:
    key = portable_path_key(rel_path)
    previous = spellings.setdefault(key, rel_path)
    if previous != rel_path:
        raise SourceSelectionError(
            "source_selection",
            "selected filesystem paths collide across supported filesystems: "
            f"{previous!r} and {rel_path!r}",
        )


def _bounded_directory_entries(
    directory: Path,
    *,
    selected_root: str,
    remaining: int,
) -> list[os.DirEntry[str]]:
    entries: list[os.DirEntry[str]] = []
    try:
        with os.scandir(directory) as iterator:
            for entry in iterator:
                entries.append(entry)
                if len(entries) > remaining:
                    raise SourceSelectionError(
                        "include",
                        "selected tree exceeds the bounded validation limit of "
                        f"{_MAX_SELECTION_SCAN_ENTRIES} entries",
                    )
    except SourceSelectionError:
        raise
    except OSError as exc:
        raise SourceSelectionError(
            "include", f"selected root {selected_root!r} is not readable"
        ) from exc
    return sorted(entries, key=lambda entry: entry.name)


def _validate_policy_filesystem(policy: SourceSelectionPolicy) -> None:
    readable_file_found = False
    inspected_entries = 0
    spellings: dict[str, str] = {}
    for path in policy.include:
        candidate = _locate_exact_path(policy.source_root, path)
        if candidate is None:
            continue
        stack = [(candidate, path)]
        while stack:
            current, rel_path = stack.pop()
            if not path_is_selected(policy, rel_path):
                continue
            rel_parts = tuple(rel_path.split("/"))
            if not EXCLUDED_DIRS.isdisjoint(rel_parts) or is_agent_worktree_path(
                rel_path
            ):
                continue
            _register_portable_filesystem_path(spellings, rel_path)
            try:
                metadata = current.lstat()
            except OSError as exc:
                raise SourceSelectionError(
                    "include", f"selected path {rel_path!r} is not readable"
                ) from exc
            if _is_link_or_reparse_stat(metadata):
                # Do not follow links during the bounded proof.  The snapshot
                # walk remains the authoritative fail-closed reporter for a
                # nested selected link.
                continue
            if stat.S_ISREG(metadata.st_mode):
                try:
                    with current.open("rb"):
                        pass
                except OSError as exc:
                    raise SourceSelectionError(
                        "include", f"selected file {rel_path!r} is not readable"
                    ) from exc
                readable_file_found = True
                continue
            if not stat.S_ISDIR(metadata.st_mode):
                continue
            entries = _bounded_directory_entries(
                current,
                selected_root=path,
                remaining=_MAX_SELECTION_SCAN_ENTRIES - inspected_entries,
            )
            inspected_entries += len(entries)
            for entry in reversed(entries):
                child_rel = f"{rel_path}/{entry.name}"
                if path_is_selected(policy, child_rel):
                    stack.append((Path(entry.path), child_rel))
    for path in policy.exclude:
        _locate_exact_path(policy.source_root, path, allow_leaf_link=True)
    if not readable_file_found:
        raise SourceSelectionError(
            "include",
            "must select at least one readable regular file after excludes; "
            "individual missing roots are allowed",
        )


def _override_text(override: str | Path) -> str:
    try:
        value = os.fspath(override)
    except TypeError as exc:
        raise SourceSelectionError(
            "source_selection", "override must be a repository-relative path"
        ) from exc
    if not isinstance(value, str):
        raise SourceSelectionError(
            "source_selection", "override must be a repository-relative text path"
        )
    return _selection_path(value, "source_selection", reject_glob=True)


def resolve_source_selection(
    root: str | Path,
    override: str | Path | None = None,
) -> SourceSelectionPolicy | None:
    """Load an explicit or repository-default selection policy.

    The explicit path is always interpreted relative to *root*. If no explicit
    path is supplied and the default file is absent, legacy broad discovery is
    preserved by returning ``None``.
    """
    try:
        source_root = Path(root).resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise SourceSelectionError(
            "source_root", "must resolve to a repository path"
        ) from exc
    if override is None:
        rel_path = SOURCE_SELECTION_PATH
        origin = "default"
    else:
        rel_path = _override_text(override)
        origin = "explicit"

    if not source_root.is_dir():
        if override is None:
            return None
        raise SourceSelectionError("source_root", "must be an existing directory")
    config_path = _locate_exact_path(source_root, rel_path)
    if config_path is None:
        if override is None:
            return None
        raise SourceSelectionError(
            "source_selection", f"selection file does not exist: {rel_path!r}"
        )
    content = _read_config(config_path)
    policy = _policy_from_content(
        root=source_root,
        rel_path=rel_path,
        origin=origin,
        content=content,
    )
    _validate_policy_filesystem(policy)
    return policy


def _validated_identity(value: object, field: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        raise SourceSelectionError(field, "must be an object with string keys")
    required = {"schema_version", "path", "fingerprint"}
    keys = set(value)
    missing = sorted(required - keys)
    unknown = sorted(keys - required)
    if missing:
        raise SourceSelectionError(f"{field}.{missing[0]}", "is required")
    if unknown:
        raise SourceSelectionError(f"{field}.{unknown[0]}", "is not supported")
    schema_version = value["schema_version"]
    if schema_version != SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION:
        raise SourceSelectionError(
            f"{field}.schema_version",
            f"must be {SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION!r}",
        )
    path = _selection_path(value["path"], f"{field}.path", reject_glob=True)
    fingerprint = value["fingerprint"]
    if not isinstance(fingerprint, str) or _SHA256_RE.fullmatch(fingerprint) is None:
        raise SourceSelectionError(
            f"{field}.fingerprint", "must use canonical sha256:<hex> form"
        )
    return {
        "schema_version": SOURCE_SELECTION_IDENTITY_SCHEMA_VERSION,
        "path": path,
        "fingerprint": fingerprint,
    }


def source_selection_identity_from_generation_inputs(
    generation_inputs: Mapping[str, object] | None,
) -> dict[str, str] | None:
    """Strictly decode the optional persisted source-selection identity."""
    if generation_inputs is None:
        return None
    if not isinstance(generation_inputs, Mapping) or any(
        not isinstance(key, str) for key in generation_inputs
    ):
        raise SourceSelectionError("generation_inputs", "must be an object")
    if SOURCE_SELECTION_GENERATION_INPUT_KEY not in generation_inputs:
        return None
    return _validated_identity(
        generation_inputs[SOURCE_SELECTION_GENERATION_INPUT_KEY],
        f"generation_inputs.{SOURCE_SELECTION_GENERATION_INPUT_KEY}",
    )


def _validated_selection_inputs(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) for key in value
    ):
        raise SourceSelectionError(field, "must be an object with string keys")
    if set(value) != {"schema_version", "inputs"}:
        raise SourceSelectionError(
            field,
            "must contain exactly schema_version and inputs",
        )
    if value["schema_version"] != SOURCE_SELECTION_INPUTS_SCHEMA_VERSION:
        raise SourceSelectionError(
            f"{field}.schema_version",
            f"must be {SOURCE_SELECTION_INPUTS_SCHEMA_VERSION!r}",
        )
    raw_inputs = value["inputs"]
    if not isinstance(raw_inputs, list):
        raise SourceSelectionError(f"{field}.inputs", "must be an array")
    if not raw_inputs or len(raw_inputs) > _MAX_PATH_COUNT:
        raise SourceSelectionError(
            f"{field}.inputs",
            f"must contain between 1 and {_MAX_PATH_COUNT} records",
        )
    inputs: list[dict[str, str]] = []
    portable_paths: dict[str, str] = {}
    for index, raw_input in enumerate(raw_inputs):
        item_field = f"{field}.inputs[{index}]"
        if not isinstance(raw_input, Mapping) or set(raw_input) != {
            "path",
            "content_hash",
        }:
            raise SourceSelectionError(
                item_field,
                "must contain exactly path and content_hash",
            )
        path = _selection_path(
            raw_input["path"],
            f"{item_field}.path",
            reject_glob=True,
        )
        portable_key = portable_path_key(path)
        previous = portable_paths.setdefault(portable_key, path)
        if previous != path:
            raise SourceSelectionError(
                f"{item_field}.path",
                f"collides across supported filesystems with {previous!r}",
            )
        content_hash = raw_input["content_hash"]
        if (
            not isinstance(content_hash, str)
            or _SHA256_RE.fullmatch(content_hash) is None
        ):
            raise SourceSelectionError(
                f"{item_field}.content_hash",
                "must use canonical sha256:<hex> form",
            )
        inputs.append({"path": path, "content_hash": content_hash})
    canonical = sorted(inputs, key=lambda item: item["path"])
    if inputs != canonical or len({item["path"] for item in inputs}) != len(inputs):
        raise SourceSelectionError(
            f"{field}.inputs",
            "must be unique and sorted by repository-relative path",
        )
    return {
        "schema_version": SOURCE_SELECTION_INPUTS_SCHEMA_VERSION,
        "inputs": canonical,
    }


def source_selection_inputs_from_generation_inputs(
    generation_inputs: Mapping[str, object] | None,
) -> dict[str, object] | None:
    """Strictly decode configured selection-control content commitments."""

    if generation_inputs is None:
        return None
    if not isinstance(generation_inputs, Mapping) or any(
        not isinstance(key, str) for key in generation_inputs
    ):
        raise SourceSelectionError("generation_inputs", "must be an object")
    if SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY not in generation_inputs:
        return None
    return _validated_selection_inputs(
        generation_inputs[SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY],
        f"generation_inputs.{SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY}",
    )


def validate_persisted_source_selection_identity(
    persisted_generation_inputs: Mapping[str, object] | None,
    live_identity: Mapping[str, object] | None,
    *,
    operation: str,
    explicit_path_authorized: bool = False,
    allow_same_path_update: bool = False,
    live_selection_inputs: Mapping[str, object] | None | object = (
        _UNSET_SELECTION_INPUTS
    ),
) -> None:
    """Fail closed when a live selection would cross a persisted boundary.

    ``persisted_generation_inputs=None`` means there is no usable persisted
    manifest and therefore no boundary to enforce.  Read-only consumers use
    the exact default comparison.  Mutating convergence operations may allow a
    fingerprint update at the same path; only an explicit profile argument may
    authorize a different path.  A legacy-to-configured transition is a
    narrowing and is also valid for mutating convergence.
    """

    if persisted_generation_inputs is None:
        return
    persisted = source_selection_identity_from_generation_inputs(
        persisted_generation_inputs
    )
    live = (
        None
        if live_identity is None
        else _validated_identity(live_identity, "live_source_selection")
    )
    identities_match = persisted == live
    selection_inputs_match = True
    if live_selection_inputs is not _UNSET_SELECTION_INPUTS:
        persisted_inputs = source_selection_inputs_from_generation_inputs(
            persisted_generation_inputs
        )
        live_inputs = (
            None
            if live_selection_inputs is None
            else _validated_selection_inputs(
                live_selection_inputs,
                "live_source_selection_inputs",
            )
        )
        selection_inputs_match = persisted_inputs == live_inputs
    if identities_match and selection_inputs_match:
        return
    if explicit_path_authorized:
        return
    if allow_same_path_update:
        if persisted is None and live is not None:
            return
        if (
            persisted is not None
            and live is not None
            and persisted["path"] == live["path"]
        ):
            return

    if identities_match and not selection_inputs_match:
        raise SourceSelectionError(
            "source_selection_inputs",
            f"{operation} cannot use the managed wiki because applicable "
            "source-selection inputs changed; run llm-wiki sync with the "
            "active source-selection profile",
        )

    if persisted is not None and live is None:
        persisted_path = persisted["path"]
        if persisted_path == SOURCE_SELECTION_PATH:
            action = f"restore {persisted_path!r} before continuing"
        else:
            action = (
                "repeat the operation with "
                f"--source-selection {persisted_path}"
            )
    elif allow_same_path_update and persisted is not None and live is not None:
        action = (
            "pass --source-selection "
            f"{live['path']} to intentionally change the recorded profile path"
        )
    else:
        action = "run llm-wiki sync with the active source-selection profile"
    raise SourceSelectionError(
        "source_selection",
        f"{operation} cannot cross the managed wiki's persisted "
        f"source-selection boundary; {action}",
    )


def with_source_selection_generation_input(
    generation_inputs: Mapping[str, object] | None,
    identity: Mapping[str, object] | None,
    selection_inputs: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return generation inputs with canonical selection identity merged."""
    if generation_inputs is None:
        result: dict[str, object] = {}
    elif not isinstance(generation_inputs, Mapping) or any(
        not isinstance(key, str) for key in generation_inputs
    ):
        raise SourceSelectionError("generation_inputs", "must be an object")
    else:
        result = deepcopy(dict(generation_inputs))
    if identity is None:
        result.pop(SOURCE_SELECTION_GENERATION_INPUT_KEY, None)
        result.pop(SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY, None)
    else:
        result[SOURCE_SELECTION_GENERATION_INPUT_KEY] = _validated_identity(
            identity,
            SOURCE_SELECTION_GENERATION_INPUT_KEY,
        )
        if selection_inputs is None:
            raise SourceSelectionError(
                SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY,
                "is required when source_selection is present",
            )
        else:
            result[SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY] = (
                _validated_selection_inputs(
                    selection_inputs,
                    SOURCE_SELECTION_INPUTS_GENERATION_INPUT_KEY,
                )
            )
    return result
