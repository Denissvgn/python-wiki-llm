"""Portable consumer policy for read-only publication impact and review.

Whole-page dependencies use whole content commitments. Structural or semantic
facets require an exact native section with independently committed ownership.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
import os
from pathlib import Path
import re
import stat
from typing import Any
import unicodedata
from urllib.parse import quote, unquote

from .concept_identity import ConceptIdentityError, validate_locator
from .source_selection import (
    SourceSelectionError,
    locate_exact_repository_path,
    path_is_link_or_reparse,
)
from .validation import portable_path_key, require_repository_relative_path


PUBLICATION_CONFIG_PATH = ".llm-wiki/publication.json"
PUBLICATION_CONFIG_SCHEMA_VERSION = "llm-wiki-publication/v1"
_MAX_CONFIG_BYTES = 256 * 1024
_MAX_TOPICS = 1024
_MAX_DEPENDENCIES = 1024
_MAX_EXCLUSIONS = 1024
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_REPOSITORY = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/[A-Za-z0-9_.-]{1,100}\Z"
)
_ANCHOR = re.compile(r"[\w.-]+\Z", re.UNICODE)
_GLOB = re.compile(r"[*?\[\]]")


class PublicationConfigError(ValueError):
    """A field-specific failure in consumer-owned publication configuration."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def _object(
    value: object, field: str, required: set[str], optional: set[str] | None = None
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):
        raise PublicationConfigError(field, "must be an object with string keys")
    keys = set(value)
    missing = sorted(required - keys)
    unknown = sorted(keys - required - (optional or set()))
    if missing or unknown:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        raise PublicationConfigError(field, "; ".join(details))
    return value


def _text(value: object, field: str, maximum: int = 1024) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise PublicationConfigError(
            field, "must be non-empty text without surrounding whitespace"
        )
    try:
        length = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise PublicationConfigError(field, "must be valid UTF-8 text") from exc
    if length > maximum or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise PublicationConfigError(
            field, f"must be at most {maximum} UTF-8 bytes without control characters"
        )
    if value != unicodedata.normalize("NFC", value):
        raise PublicationConfigError(field, "must use NFC-normalized text")
    return value


def _choice(value: object, field: str, choices: set[str]) -> str:
    if type(value) is not str or value not in choices:
        raise PublicationConfigError(
            field, "must be one of " + ", ".join(sorted(choices))
        )
    return value


def _array(
    value: object, field: str, maximum: int, *, nonempty: bool = False
) -> list[Any]:
    if type(value) is not list or len(value) > maximum or (nonempty and not value):
        minimum = "one" if nonempty else "zero"
        raise PublicationConfigError(
            field, f"must be an array containing {minimum} to {maximum} entries"
        )
    return value


def _relative_path(value: object, field: str) -> str:
    error = PublicationConfigError(
        field, "must be a canonical portable repository-relative POSIX path"
    )
    path = require_repository_relative_path(
        value,
        text_error=error,
        posix_error=error,
        normalized_error=error,
        absolute_error=error,
        separator_error=error,
        control_error=error,
        reject_delete_character=True,
        leading_backslash_is_absolute=True,
        portability_error=error,
    )
    if len(path.encode("utf-8")) > 1024:
        raise PublicationConfigError(field, "must be at most 1024 UTF-8 bytes")
    return path


def _consumer_root(value: str | Path) -> Path:
    try:
        root = Path(value).expanduser()
        if path_is_link_or_reparse(root):
            raise PublicationConfigError(
                "consumer_root", "must not be a symlink or reparse point"
            )
        root = root.resolve(strict=True)
        if not root.is_dir():
            raise PublicationConfigError("consumer_root", "must be a directory")
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        if isinstance(exc, PublicationConfigError):
            raise
        raise PublicationConfigError(
            "consumer_root", "must identify an accessible directory"
        ) from exc
    return root


def _check_path(
    root: Path | None,
    path: str,
    field: str,
    spellings: dict[tuple[str, ...], tuple[str, ...]],
) -> None:
    folded: list[str] = []
    exact: list[str] = []
    for part in path.split("/"):
        folded.append(portable_path_key(part))
        exact.append(part)
        key, spelling = tuple(folded), tuple(exact)
        previous = spellings.setdefault(key, spelling)
        if previous != spelling:
            raise PublicationConfigError(
                field, "path spelling collides across supported filesystems"
            )
    if root is None:
        return
    try:
        locate_exact_repository_path(root, path)
    except SourceSelectionError as exc:
        raise PublicationConfigError(field, exc.message) from exc


def publication_path(root: Path, relative: str) -> Path:
    """Return a confined exact-case path, including a safely absent leaf."""
    selected_root = _consumer_root(root)
    if relative == ".":
        return selected_root
    path = _relative_path(relative, "path")
    _check_path(selected_root, path, "path", {})
    return selected_root / path


def _section(value: object, field: str) -> str:
    section = _text(value, field, 4096)
    page, separator, coordinate = section.partition("#section/")
    if (
        not separator
        or not page.startswith("llm-wiki://")
        or "#" in coordinate
        or "?" in section
    ):
        raise PublicationConfigError(
            field, "must be an exact native llm-wiki section locator"
        )
    try:
        validate_locator(page)
    except ConceptIdentityError as exc:
        raise PublicationConfigError(field, exc.message) from exc
    if coordinate == "@preamble":
        return section
    for component in coordinate.split("/"):
        heading, suffix, occurrence = component.rpartition("~")
        if (
            not suffix
            or not occurrence.isascii()
            or not occurrence.isdecimal()
            or occurrence.startswith("0")
        ):
            raise PublicationConfigError(
                field, "section coordinates must include positive canonical occurrences"
            )
        try:
            decoded = unquote(heading, encoding="utf-8", errors="strict")
            encoded = quote(decoded, safe="-._~", encoding="utf-8", errors="strict")
        except (UnicodeError, ValueError) as exc:
            raise PublicationConfigError(
                field, "must contain canonical UTF-8 section coordinates"
            ) from exc
        if encoded != heading or any(
            ord(char) < 32 or ord(char) == 127 for char in decoded
        ):
            raise PublicationConfigError(
                field, "must contain canonical UTF-8 section coordinates"
            )
    return section


def _dependency(
    value: object,
    field: str,
    root: Path | None,
    architecture_root: str,
    spellings: dict[tuple[str, ...], tuple[str, ...]],
) -> dict[str, Any]:
    data = _object(
        value, field, set(), {"architecture_page", "source_file", "section", "facets"}
    )
    kinds = {"architecture_page", "source_file"} & set(data)
    if len(kinds) != 1:
        raise PublicationConfigError(
            field, "must contain exactly one architecture_page or source_file"
        )
    kind = next(iter(kinds))
    path = _relative_path(data[kind], f"{field}.{kind}")
    actual = (
        f"{architecture_root}/{path}"
        if kind == "architecture_page" and architecture_root != "."
        else path
    )
    _check_path(root, actual, f"{field}.{kind}", spellings)
    result: dict[str, Any] = {kind: path}
    if kind == "source_file":
        if "section" in data or "facets" in data:
            raise PublicationConfigError(
                field, "source_file does not accept section or facets"
            )
        return result
    if not path.endswith(".md"):
        raise PublicationConfigError(
            f"{field}.architecture_page", "must identify a Markdown page ending in .md"
        )
    facets = _array(data.get("facets", ["whole"]), f"{field}.facets", 3, nonempty=True)
    normalized = [
        _choice(facet, f"{field}.facets", {"whole", "structural", "semantic"})
        for facet in facets
    ]
    if len(set(normalized)) != len(normalized) or (
        "whole" in normalized and len(normalized) != 1
    ):
        raise PublicationConfigError(
            f"{field}.facets",
            "must be distinct; whole cannot be combined with other facets",
        )
    if normalized != ["whole"] and "section" not in data:
        raise PublicationConfigError(
            f"{field}.section",
            "is required for structural or semantic facet dependencies",
        )
    result["facets"] = sorted(normalized)
    if "section" in data:
        result["section"] = _section(data["section"], f"{field}.section")
    return result


def validate_publication_config(
    payload: Mapping[str, Any], *, consumer_root: str | Path | None
) -> dict[str, Any]:
    """Validate detached policy; None checks imported policy without filesystem I/O.

    An explicit root additionally rejects unsafe existing path bindings without
    requiring referenced inputs to exist. Loading an on-disk policy always uses
    that stricter mode.
    """
    root = None if consumer_root is None else _consumer_root(consumer_root)
    data = _object(
        payload,
        "publication",
        {
            "schema_version",
            "architecture",
            "target",
            "enforcement",
            "publish",
            "topics",
        },
        {"source_policy", "exclusions"},
    )
    if data["schema_version"] != PUBLICATION_CONFIG_SCHEMA_VERSION:
        raise PublicationConfigError(
            "schema_version", f"must be {PUBLICATION_CONFIG_SCHEMA_VERSION}"
        )
    if data["publish"] is not False:
        raise PublicationConfigError(
            "publish", "must be false; this contract grants no publication authority"
        )
    architecture = _object(data["architecture"], "architecture", {"baseline", "root"})
    baseline = _choice(
        architecture["baseline"],
        "architecture.baseline",
        {"existing-wiki", "bootstrap-source"},
    )
    architecture_root = (
        "."
        if architecture["root"] == "."
        else _relative_path(architecture["root"], "architecture.root")
    )
    spellings: dict[tuple[str, ...], tuple[str, ...]] = {}
    if architecture_root != ".":
        _check_path(root, architecture_root, "architecture.root", spellings)
    target = _object(data["target"], "target", {"kind", "repository"})
    kind = _choice(target["kind"], "target.kind", {"github-wiki"})
    repository = _text(target["repository"], "target.repository", 140)
    if repository != "self" and (
        not _REPOSITORY.fullmatch(repository) or repository.split("/")[1] in {".", ".."}
    ):
        raise PublicationConfigError(
            "target.repository", "must be self or a GitHub owner/repository identifier"
        )
    source_policy = _choice(
        data.get("source_policy", "default-branch"),
        "source_policy",
        {"default-branch", "release"},
    )
    enforcement = _choice(data["enforcement"], "enforcement", {"advisory", "required"})
    topics = []
    ids: set[str] = set()
    targets: dict[str, set[str | None]] = {}
    for index, raw in enumerate(_array(data["topics"], "topics", _MAX_TOPICS)):
        field = f"topics[{index}]"
        topic = _object(
            raw,
            field,
            {"id", "owner", "wiki_page", "edit_at", "depends_on"},
            {"anchor", "source_document"},
        )
        identity = _text(topic["id"], f"{field}.id", 128)
        if not _IDENTIFIER.fullmatch(identity) or identity.casefold() in ids:
            raise PublicationConfigError(
                f"{field}.id", "must be a distinct portable topic identifier"
            )
        ids.add(identity.casefold())
        page = _relative_path(topic["wiki_page"], f"{field}.wiki_page")
        if "/" in page or not page.endswith(".md") or page == ".md":
            raise PublicationConfigError(
                f"{field}.wiki_page", "must be a flat wiki filename ending in .md"
            )
        page_key = portable_path_key(page.replace(" ", "-"))
        anchor = None
        if "anchor" in topic:
            anchor = _text(topic["anchor"], f"{field}.anchor", 256)
            if not _ANCHOR.fullmatch(anchor):
                raise PublicationConfigError(
                    f"{field}.anchor",
                    "must be an anchor without a leading # or whitespace",
                )
        destinations = targets.setdefault(page_key, set())
        anchor_key = None if anchor is None else anchor.casefold()
        if destinations and (
            None in destinations or anchor is None or anchor_key in destinations
        ):
            raise PublicationConfigError(
                f"{field}.wiki_page", "overlaps another topic's wiki destination"
            )
        destinations.add(anchor_key)
        normalized: dict[str, Any] = {
            "id": identity,
            "owner": _text(topic["owner"], f"{field}.owner", 256),
            "wiki_page": page,
            "edit_at": _choice(
                topic["edit_at"], f"{field}.edit_at", {"wiki", "repository"}
            ),
        }
        if anchor is not None:
            normalized["anchor"] = anchor
        if "source_document" in topic:
            document = _relative_path(
                topic["source_document"], f"{field}.source_document"
            )
            _check_path(root, document, f"{field}.source_document", spellings)
            normalized["source_document"] = document
        elif normalized["edit_at"] == "repository":
            raise PublicationConfigError(
                f"{field}.source_document", "is required when edit_at is repository"
            )
        dependencies = []
        seen_dependencies: set[tuple[str, str, str | None]] = set()
        for dep_index, raw_dep in enumerate(
            _array(
                topic["depends_on"],
                f"{field}.depends_on",
                _MAX_DEPENDENCIES,
                nonempty=True,
            )
        ):
            dep_field = f"{field}.depends_on[{dep_index}]"
            dependency = _dependency(
                raw_dep, dep_field, root, architecture_root, spellings
            )
            dep_kind = (
                "architecture_page"
                if "architecture_page" in dependency
                else "source_file"
            )
            dep_key = (dep_kind, dependency[dep_kind], dependency.get("section"))
            if dep_key in seen_dependencies:
                raise PublicationConfigError(
                    dep_field, "duplicates a dependency in this topic"
                )
            seen_dependencies.add(dep_key)
            dependencies.append(dependency)
        normalized["depends_on"] = dependencies
        topics.append(normalized)
    exclusions = []
    seen_patterns: set[str] = set()
    for index, raw in enumerate(
        _array(data.get("exclusions", []), "exclusions", _MAX_EXCLUSIONS)
    ):
        field = f"exclusions[{index}]"
        exclusion = _object(raw, field, {"pattern", "reason"})
        pattern = _text(exclusion["pattern"], f"{field}.pattern")
        _relative_path(_GLOB.sub("x", pattern), f"{field}.pattern")
        pattern_key = portable_path_key(pattern)
        if pattern_key in seen_patterns:
            raise PublicationConfigError(
                f"{field}.pattern",
                "duplicates or collides with another exclusion pattern",
            )
        seen_patterns.add(pattern_key)
        prefix_parts = []
        for component in pattern.split("/"):
            if _GLOB.search(component):
                break
            prefix_parts.append(component)
        if prefix_parts:
            prefix = "/".join(prefix_parts)
            actual = (
                prefix if architecture_root == "." else f"{architecture_root}/{prefix}"
            )
            _check_path(root, actual, f"{field}.pattern", spellings)
        exclusions.append(
            {
                "pattern": pattern,
                "reason": _text(exclusion["reason"], f"{field}.reason", 4096),
            }
        )
    return {
        "schema_version": PUBLICATION_CONFIG_SCHEMA_VERSION,
        "source_policy": source_policy,
        "architecture": {"baseline": baseline, "root": architecture_root},
        "target": {"kind": kind, "repository": repository},
        "enforcement": enforcement,
        "publish": False,
        "topics": topics,
        "exclusions": exclusions,
    }


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PublicationConfigError(
                "publication", f"contains duplicate JSON key {key!r}"
            )
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise PublicationConfigError(
        "publication", f"contains non-finite JSON number {value}"
    )


def read_publication_json(
    path: str | Path, *, max_bytes: int = _MAX_CONFIG_BYTES
) -> dict[str, Any]:
    """Read bounded regular JSON; callers confine its parent with publication_path."""
    if type(max_bytes) is not int or max_bytes < 1:
        raise PublicationConfigError("max_bytes", "must be a positive integer")
    selected = Path(path)
    try:
        metadata = selected.lstat()
        if path_is_link_or_reparse(selected) or not stat.S_ISREG(metadata.st_mode):
            raise PublicationConfigError(
                "path",
                "must identify a regular file without symlinks or reparse points",
            )
        descriptor = os.open(selected, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
                metadata.st_dev,
                metadata.st_ino,
            ):
                raise PublicationConfigError(
                    "path", "file changed before it could be read"
                )
            content = stream.read(max_bytes + 1)
    except OSError as exc:
        raise PublicationConfigError("path", "cannot read JSON file") from exc
    if len(content) > max_bytes:
        raise PublicationConfigError("path", f"must be at most {max_bytes} bytes")
    try:
        payload = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_json_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise PublicationConfigError(
            "publication", "must contain bounded strict UTF-8 JSON"
        ) from exc
    if type(payload) is not dict:
        raise PublicationConfigError("publication", "must contain a JSON object")
    return payload


def load_publication_config(
    consumer_root: str | Path, *, config_path: str | Path = PUBLICATION_CONFIG_PATH
) -> dict[str, Any]:
    """Load an explicit consumer's regular JSON config without following links."""
    root = _consumer_root(consumer_root)
    relative = _relative_path(
        config_path.as_posix() if isinstance(config_path, Path) else config_path,
        "config_path",
    )
    try:
        path = locate_exact_repository_path(root, relative)
        if path is None or not stat.S_ISREG(path.lstat().st_mode):
            raise PublicationConfigError(
                "config_path", "must identify an existing regular configuration file"
            )
        payload = read_publication_json(path)
    except SourceSelectionError as exc:
        raise PublicationConfigError("config_path", exc.message) from exc
    except OSError as exc:
        raise PublicationConfigError(
            "config_path", "cannot read configuration file"
        ) from exc
    return validate_publication_config(payload, consumer_root=root)
