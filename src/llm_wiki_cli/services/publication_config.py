"""Portable consumer policy for read-only publication impact and review.

Whole-page dependencies use whole content commitments. Structural or semantic
facets require an exact native section with independently committed ownership.
Reference dependencies require an explicitly declared, non-executable provider.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
import ipaddress
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any
import unicodedata
from urllib.parse import quote, unquote, urlsplit

from .concept_identity import ConceptIdentityError, validate_locator
from .source_selection import (
    SOURCE_SELECTION_PATH,
    SourceSelectionError,
    locate_exact_repository_path,
    path_is_link_or_reparse,
)
from .validation import portable_path_key, require_repository_relative_path
from .wiki_media import MEDIA_EXTENSIONS


PUBLICATION_CONFIG_PATH = ".llm-wiki/publication.json"
PUBLICATION_CONFIG_SCHEMA_VERSION = "llm-wiki-publication/v1"
_MAX_CONFIG_BYTES = 256 * 1024
_MAX_TOPICS = 1024
_MAX_DEPENDENCIES = 1024
_MAX_EXCLUSIONS = 1024
_MAX_REFERENCE_PROVIDERS = 64
_MAX_COMMAND_TOKENS = 32
_MAX_CONTENT_ITEMS = 1024
_PUBLIC_ASSET_EXTENSIONS = MEDIA_EXTENSIONS | {".pdf", ".txt"}
_METADATA_DIRECTORIES = frozenset({".git", ".hg", ".svn", ".llm-wiki"})
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
    return _text(
        require_repository_relative_path(
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
        ),
        field,
    )


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


def publication_input_controls(root: Path, config, config_path) -> set[Path]:
    """Reserve implicit discovery inputs, including safely absent coordinates."""
    root = Path(root)
    roots = {root, root / config["architecture"]["root"]}
    return {root / config_path} | {
        directory / relative
        for directory in roots
        for relative in (".gitignore", SOURCE_SELECTION_PATH)
    }


def publication_control_overlap(left: Path, right: Path) -> bool:
    """Compare protected input namespaces across portable filesystem names."""
    first = tuple(
        portable_path_key(part) for part in Path(left).resolve(strict=False).parts
    )
    second = tuple(
        portable_path_key(part) for part in Path(right).resolve(strict=False).parts
    )
    length = min(len(first), len(second))
    return first[:length] == second[:length]


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
    reference_providers: Mapping[str, Any],
) -> dict[str, Any]:
    data = _object(
        value,
        field,
        set(),
        {
            "architecture_page",
            "source_file",
            "reference",
            "command",
            "section",
            "facets",
        },
    )
    kinds = {"architecture_page", "source_file", "reference"} & set(data)
    if len(kinds) != 1:
        raise PublicationConfigError(
            field,
            "must contain exactly one architecture_page, source_file or reference",
        )
    kind = next(iter(kinds))
    if kind == "reference":
        _object(data, field, {"reference"}, {"command"})
        provider = _text(data["reference"], f"{field}.reference", 128)
        if not _IDENTIFIER.fullmatch(provider) or provider not in reference_providers:
            raise PublicationConfigError(
                f"{field}.reference", "must name a declared reference provider"
            )
        command = []
        for index, raw_token in enumerate(
            _array(data.get("command", []), f"{field}.command", _MAX_COMMAND_TOKENS)
        ):
            token_field = f"{field}.command[{index}]"
            token = _text(raw_token, token_field, 128)
            if not _IDENTIFIER.fullmatch(token):
                raise PublicationConfigError(
                    token_field, "must be a literal portable command token"
                )
            command.append(token)
        return {"reference": provider, "command": command}
    if "command" in data:
        raise PublicationConfigError(
            f"{field}.command", "is only accepted for reference dependencies"
        )
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


def _reference_providers(
    value: object,
    root: Path | None,
    spellings: dict[tuple[str, ...], tuple[str, ...]],
) -> dict[str, dict[str, Any]]:
    providers = _object(
        value,
        "reference_providers",
        set(),
        set(value) if isinstance(value, Mapping) else set(),
    )
    if len(providers) > _MAX_REFERENCE_PROVIDERS:
        raise PublicationConfigError(
            "reference_providers",
            f"must contain at most {_MAX_REFERENCE_PROVIDERS} providers",
        )
    result = {}
    ids = set()
    for identity in sorted(providers):
        raw = providers[identity]
        field = f"reference_providers.{identity}"
        _text(identity, field, 128)
        if not _IDENTIFIER.fullmatch(identity) or identity.casefold() in ids:
            raise PublicationConfigError(
                field, "must be a distinct portable provider identifier"
            )
        ids.add(identity.casefold())
        provider = _object(raw, field, {"kind"}, {"path"})
        kind = _choice(
            provider["kind"], field + ".kind", {"llm-wiki-cli", "contract-file"}
        )
        if kind == "llm-wiki-cli":
            _object(provider, field, {"kind"})
            result[identity] = {"kind": kind}
        else:
            _object(provider, field, {"kind", "path"})
            path = _relative_path(provider["path"], field + ".path")
            if not path.endswith(".json"):
                raise PublicationConfigError(
                    field + ".path", "must identify a JSON contract ending in .json"
                )
            _check_path(root, path, field + ".path", spellings)
            result[identity] = {"kind": kind, "path": path}
    return result


def _public_content_path(value: object, field: str, *, asset: bool = False) -> str:
    path = _relative_path(value, field)
    if any(
        part.casefold() in _METADATA_DIRECTORIES
        or part.casefold().startswith(".llm-wiki-")
        for part in path.split("/")
    ):
        raise PublicationConfigError(field, "must not name VCS or native metadata")
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in _PUBLIC_ASSET_EXTENSIONS:
        return path
    if not asset and path.endswith(".md") and "/" not in path and path != ".md":
        return path
    raise PublicationConfigError(
        field,
        "must identify a public media, PDF or text asset"
        if asset
        else "must identify a flat Markdown wiki page or public asset",
    )


def _content_source_path(
    path: str, content_root: str, architecture, field: str
) -> None:
    if content_root != "." and not path.startswith(content_root + "/"):
        raise PublicationConfigError(field, "must be within content.root")
    if architecture["baseline"] == "existing-wiki":
        native = architecture["root"]
        if native == "." or path == native or path.startswith(native + "/"):
            raise PublicationConfigError(field, "must be outside the native wiki")
    if any(
        part.casefold() in _METADATA_DIRECTORIES
        or part.casefold().startswith(".llm-wiki-")
        for part in path.split("/")
    ):
        raise PublicationConfigError(field, "must not import VCS or native metadata")


def _content_repository_url(value: object) -> str:
    field = "content.repository_url"
    url = _text(value, field, 2048)
    try:
        parts = urlsplit(url)
        host, port = parts.hostname, parts.port
        if (
            not host
            or "%" in host
            or port == 0
            or parts.username is not None
            or parts.password is not None
        ):
            raise ValueError
        if ":" in host:
            host = "[" + ipaddress.IPv6Address(host).compressed + "]"
        elif not re.fullmatch(
            r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*",
            host,
        ):
            raise ValueError
        origin = (
            "https://" + host + (":" + str(port) if port not in {None, 443} else "")
        )
        repository = parts.path.removeprefix("/")
        if (
            parts.scheme != "https"
            or parts.query
            or parts.fragment
            or not _REPOSITORY.fullmatch(repository)
            or repository.endswith(".git")
            or repository.split("/")[1] in {".", ".."}
            or url != origin + "/" + repository
        ):
            raise ValueError
    except (ValueError, UnicodeError) as exc:
        raise PublicationConfigError(
            field,
            "must be a canonical HTTPS repository URL without credentials, query or fragment",
        ) from exc
    return url


def _content_profile(value, root, architecture, topics, spellings):
    data = _object(
        value,
        "content",
        {"root"},
        {"assets", "adoptions", "removals", "repository_url"},
    )
    content_root = (
        "." if data["root"] == "." else _relative_path(data["root"], "content.root")
    )
    if content_root != ".":
        _check_path(root, content_root, "content.root", spellings)
    if root is not None:
        directory = root if content_root == "." else root / content_root
        if directory.exists() and not directory.is_dir():
            raise PublicationConfigError("content.root", "must identify a directory")
    result: dict[str, Any] = {"root": content_root}
    output_spellings = {}
    active_paths = {}
    for topic in topics:
        page = topic["wiki_page"]
        _public_content_path(page, "topics.wiki_page")
        _check_path(None, page, "topics.wiki_page", output_spellings)
        active_paths[portable_path_key(page.replace(" ", "-"))] = page
        if "source_document" in topic:
            source = topic["source_document"]
            _content_source_path(
                source, content_root, architecture, "topics.source_document"
            )
            if not source.endswith(".md"):
                raise PublicationConfigError(
                    "topics.source_document", "must identify Markdown ending in .md"
                )
    if "assets" in data:
        assets = []
        for index, raw in enumerate(
            _array(data["assets"], "content.assets", _MAX_CONTENT_ITEMS)
        ):
            field = f"content.assets[{index}]"
            entry = _object(raw, field, {"source_document", "wiki_path", "owner"})
            source = _relative_path(
                entry["source_document"], field + ".source_document"
            )
            _content_source_path(
                source, content_root, architecture, field + ".source_document"
            )
            _public_content_path(source, field + ".source_document", asset=True)
            _check_path(root, source, field + ".source_document", spellings)
            path = _public_content_path(
                entry["wiki_path"], field + ".wiki_path", asset=True
            )
            if (
                PurePosixPath(source).suffix.lower()
                != PurePosixPath(path).suffix.lower()
            ):
                raise PublicationConfigError(
                    field + ".wiki_path", "must retain the source asset extension"
                )
            key = portable_path_key(path.replace(" ", "-"))
            if key in active_paths:
                raise PublicationConfigError(
                    field + ".wiki_path", "collides with another public output"
                )
            for previous in active_paths.values():
                if path.startswith(previous + "/") or previous.startswith(path + "/"):
                    raise PublicationConfigError(
                        field + ".wiki_path", "overlaps another public output"
                    )
            _check_path(None, path, field + ".wiki_path", output_spellings)
            active_paths[key] = path
            assets.append(
                {
                    "source_document": source,
                    "wiki_path": path,
                    "owner": _text(entry["owner"], field + ".owner", 256),
                }
            )
        result["assets"] = assets
    operation_paths = set()
    for kind in ("adoptions", "removals"):
        if kind not in data:
            continue
        operations = []
        for index, raw in enumerate(
            _array(data[kind], "content." + kind, _MAX_CONTENT_ITEMS)
        ):
            field = f"content.{kind}[{index}]"
            entry = _object(raw, field, {"path", "expected_hash", "reason"})
            path = _public_content_path(entry["path"], field + ".path")
            key = portable_path_key(path.replace(" ", "-"))
            if key in operation_paths or (kind == "removals" and key in active_paths):
                raise PublicationConfigError(
                    field + ".path",
                    "duplicates or conflicts with public output ownership",
                )
            if key in active_paths and active_paths[key] != path:
                raise PublicationConfigError(
                    field + ".path", "must use the exact public output spelling"
                )
            if any(
                key.startswith(other + "/") or other.startswith(key + "/")
                for other in operation_paths | set(active_paths)
            ):
                raise PublicationConfigError(
                    field + ".path", "overlaps another public file coordinate"
                )
            expected = entry["expected_hash"]
            if expected is not None and (
                type(expected) is not str
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", expected)
            ):
                raise PublicationConfigError(
                    field + ".expected_hash",
                    "must be a canonical SHA-256 commitment or null",
                )
            _check_path(None, path, field + ".path", output_spellings)
            operation_paths.add(key)
            operations.append(
                {
                    "path": path,
                    "expected_hash": expected,
                    "reason": _text(entry["reason"], field + ".reason", 4096),
                }
            )
        result[kind] = operations
    if "repository_url" in data:
        result["repository_url"] = _content_repository_url(data["repository_url"])
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
        {"source_policy", "exclusions", "reference_providers", "content"},
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
    reference_providers = (
        _reference_providers(data["reference_providers"], root, spellings)
        if "reference_providers" in data
        else {}
    )
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
        seen_dependencies: set[tuple[str, str, object]] = set()
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
                raw_dep,
                dep_field,
                root,
                architecture_root,
                spellings,
                reference_providers,
            )
            dep_kind = next(
                key
                for key in ("architecture_page", "source_file", "reference")
                if key in dependency
            )
            scope = (
                tuple(dependency["command"])
                if dep_kind == "reference"
                else dependency.get("section")
            )
            dep_key = (dep_kind, dependency[dep_kind], scope)
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
    result = {
        "schema_version": PUBLICATION_CONFIG_SCHEMA_VERSION,
        "source_policy": source_policy,
        "architecture": {"baseline": baseline, "root": architecture_root},
        "target": {"kind": kind, "repository": repository},
        "enforcement": enforcement,
        "publish": False,
        "topics": topics,
        "exclusions": exclusions,
    }
    if "reference_providers" in data:
        result["reference_providers"] = reference_providers
    if "content" in data:
        result["content"] = _content_profile(
            data["content"], root, result["architecture"], topics, spellings
        )
    return result


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
