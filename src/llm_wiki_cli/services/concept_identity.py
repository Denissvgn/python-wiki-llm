"""Pure stable-identity primitives for governed knowledge concepts.

The records in this module deliberately contain no filesystem behavior.  They
validate the small identity vocabulary used by a governance ledger, derive an
initial deterministic UID, detect registry collisions, and return immutable
move/alias updates.  Once an allocation is persisted, its ``uid`` is authority;
callers must carry it forward rather than deriving it again after a move.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, cast
from urllib.parse import quote, unquote, urlsplit

from .wiki_surface import (
    WikiSurfaceError,
    canonical_path,
    iter_page_kinds,
    mcp_uri,
    validate_exact_page_coordinate,
)


CONCEPT_UID_DOMAIN = "llm-wiki/concept-uid/v1"
CONCEPT_UID_HEX_LENGTH = 32

_MAX_BUNDLE_ID_LENGTH = 128
_MAX_CONCEPT_KIND_LENGTH = 128
_MAX_NATURAL_KEY_LENGTH = 512
_MAX_UID_LENGTH = 128

_BUNDLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_QUALIFIED_KIND_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9._-]*/[A-Za-z][A-Za-z0-9._-]*$"
)
_NATURAL_KEY_PREFIX_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_NATURAL_KEY_PAYLOAD_RE = re.compile(r"^[A-Za-z0-9%][A-Za-z0-9._~%+:/#@()=-]*$")
_PERCENT_ESCAPE_RE = re.compile(r"%([0-9A-Fa-f]{2})")
_INVALID_PERCENT_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_COLLISION_CODE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_COLLISION_COORDINATE_TYPE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_NATURAL_KEY_QUOTE_SAFE = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789._~+:/#@()=-"
)
_UID_RE = re.compile(
    rf"^lw:([a-z][a-z0-9-]{{0,31}}):([0-9a-f]{{{CONCEPT_UID_HEX_LENGTH}}})$"
)

_UID_TAG_BY_KIND = {
    "source-module": "module",
    "code-entity": "entity",
    "workflow": "workflow",
    "guide": "guide",
    "user-flow": "flow",
    "infrastructure-resource": "infrastructure",
    "api-contract": "api",
    "dependency-view": "dependency",
    "navigation-document": "navigation",
    "change-log-document": "change-log",
}


class ConceptIdentityError(ValueError):
    """Field-specific validation failure for stable concept identity."""

    def __init__(self, field: str, message: str, *, code: str = "invalid"):
        self.field = field
        self.message = message
        self.code = code
        super().__init__(f"{field}: {message}")


class AliasType(str, Enum):
    """The two coordinate namespaces that may retain historical aliases."""

    LOCATOR = "locator"
    NATURAL_KEY = "natural-key"


@dataclass(frozen=True)
class ConceptReference:
    """One current, regenerable concept coordinate before UID allocation."""

    locator: str
    concept_kind: str
    natural_key: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "locator", validate_locator(self.locator))
        object.__setattr__(
            self,
            "concept_kind",
            validate_concept_kind(self.concept_kind),
        )
        object.__setattr__(
            self,
            "natural_key",
            validate_natural_key(self.natural_key),
        )


@dataclass(frozen=True)
class ConceptAllocation:
    """A persisted UID bound to the concept's current coordinates."""

    uid: str
    concept_kind: str
    natural_key: str
    locator: str

    def __post_init__(self) -> None:
        uid = validate_concept_uid(self.uid)
        kind = validate_concept_kind(self.concept_kind)
        natural_key = validate_natural_key(self.natural_key)
        locator = validate_locator(self.locator)
        expected_tag = _uid_tag(kind)
        actual_tag = uid.split(":", 2)[1]
        if actual_tag != expected_tag:
            raise ConceptIdentityError(
                "uid",
                f"UID tag {actual_tag!r} does not match concept kind {kind!r}",
                code="uid-kind-mismatch",
            )
        object.__setattr__(self, "uid", uid)
        object.__setattr__(self, "concept_kind", kind)
        object.__setattr__(self, "natural_key", natural_key)
        object.__setattr__(self, "locator", locator)

    @property
    def reference(self) -> ConceptReference:
        """Return the allocation's current regenerable reference."""

        return ConceptReference(
            locator=self.locator,
            concept_kind=self.concept_kind,
            natural_key=self.natural_key,
        )


@dataclass(frozen=True)
class IdentityAlias:
    """One historical locator or natural key owned by a persisted UID."""

    alias_type: AliasType | str
    value: str
    uid: str

    def __post_init__(self) -> None:
        alias_type = validate_alias_type(self.alias_type)
        uid = validate_concept_uid(self.uid)
        value = validate_alias_value(alias_type, self.value)
        object.__setattr__(self, "alias_type", alias_type)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "uid", uid)


@dataclass(frozen=True, order=True)
class IdentityCollision:
    """One deterministic registry conflict found without resolving it."""

    code: str
    coordinate_type: str
    value: str
    uids: tuple[str, ...]

    def __post_init__(self) -> None:
        code = _machine_text(self.code, "collision.code", maximum=64)
        coordinate_type = _machine_text(
            self.coordinate_type,
            "collision.coordinate_type",
            maximum=64,
        )
        value = _machine_text(self.value, "collision.value", maximum=2048)
        if _COLLISION_CODE_RE.fullmatch(code) is None:
            raise ConceptIdentityError(
                "collision.code",
                "must be a lowercase machine code",
            )
        if _COLLISION_COORDINATE_TYPE_RE.fullmatch(coordinate_type) is None:
            raise ConceptIdentityError(
                "collision.coordinate_type",
                "must be a lowercase machine code",
            )
        supplied_uids = _typed_tuple(self.uids, str, "collision.uids")
        if not supplied_uids:
            raise ConceptIdentityError(
                "collision.uids",
                "must contain at least one UID",
            )
        uids = tuple(sorted(validate_concept_uid(uid) for uid in supplied_uids))
        if len(set(uids)) != len(uids):
            raise ConceptIdentityError(
                "collision.uids",
                "must not contain duplicate UIDs",
            )
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "coordinate_type", coordinate_type)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "uids", uids)


class IdentityCollisionError(ConceptIdentityError):
    """Raised when allocations or aliases do not form a unique registry."""

    def __init__(self, collisions: Sequence[IdentityCollision]):
        ordered = tuple(sorted(collisions))
        if not ordered:
            raise ValueError("collisions must not be empty")
        self.collisions = ordered
        first = ordered[0]
        owners = ", ".join(first.uids) if first.uids else "none"
        super().__init__(
            f"{first.coordinate_type}.{first.value}",
            f"{first.code} (owners: {owners})",
            code=first.code,
        )


@dataclass(frozen=True)
class IdentityUpdate:
    """A replacement allocation and the complete canonical alias collection."""

    allocation: ConceptAllocation
    aliases: tuple[IdentityAlias, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.allocation, ConceptAllocation):
            raise TypeError("allocation must be a ConceptAllocation")
        aliases = _typed_tuple(self.aliases, IdentityAlias, "aliases")
        seen_records: set[tuple[str, str, str]] = set()
        owners_by_coordinate: dict[tuple[str, str], str] = {}
        for alias in aliases:
            alias_type = cast(AliasType, alias.alias_type)
            coordinate = (
                alias_type.value,
                identity_coordinate_key(alias_type, alias.value),
            )
            record = (*coordinate, alias.uid)
            if record in seen_records:
                raise ConceptIdentityError(
                    "aliases",
                    "must not contain duplicate alias records",
                    code="duplicate-alias",
                )
            seen_records.add(record)
            previous_owner = owners_by_coordinate.setdefault(
                coordinate,
                alias.uid,
            )
            if previous_owner != alias.uid:
                raise ConceptIdentityError(
                    "aliases",
                    "one alias coordinate must not have multiple owners",
                    code="alias-collision",
                )
            current_value = (
                self.allocation.locator
                if alias.alias_type is AliasType.LOCATOR
                else self.allocation.natural_key
            )
            if identity_coordinate_key(
                alias.alias_type,
                alias.value,
            ) == identity_coordinate_key(alias.alias_type, current_value):
                raise ConceptIdentityError(
                    "aliases",
                    "must not repeat the allocation's current coordinate",
                    code="alias-current-collision",
                )
        object.__setattr__(self, "aliases", _sorted_aliases(aliases))


def validate_bundle_id(value: object) -> str:
    """Validate a stored, checkout-independent bundle identifier."""

    text = _machine_text(value, "bundle_id", maximum=_MAX_BUNDLE_ID_LENGTH)
    if (
        _BUNDLE_ID_RE.fullmatch(text) is None
        or text.casefold() in {"unknown", "none", "null"}
        or _looks_absolute_path(text)
        or _contains_uri_userinfo(text)
    ):
        raise ConceptIdentityError(
            "bundle_id",
            "must be a normalized machine identifier without paths or credentials",
        )
    return text


def validate_concept_kind(value: object) -> str:
    """Validate a core lowercase kind or a qualified extension kind."""

    text = _machine_text(
        value,
        "concept_kind",
        maximum=_MAX_CONCEPT_KIND_LENGTH,
    )
    if text not in _UID_TAG_BY_KIND and _QUALIFIED_KIND_RE.fullmatch(text) is None:
        raise ConceptIdentityError(
            "concept_kind",
            "must be a supported core kind or a qualified namespace/name",
        )
    return text


def validate_natural_key(value: object) -> str:
    """Validate one normalized, non-prose concept natural key.

    Natural keys use ``namespace:payload`` form.  Payloads are compact ASCII
    machine coordinates; non-ASCII symbols can be represented with canonical
    uppercase percent escapes.  Absolute paths, dot segments, URL-like values,
    credential-bearing authorities, controls, whitespace, and backslashes are
    rejected.
    """

    text = _machine_text(
        value,
        "natural_key",
        maximum=_MAX_NATURAL_KEY_LENGTH,
    )
    prefix, separator, payload = text.partition(":")
    if (
        not separator
        or _NATURAL_KEY_PREFIX_RE.fullmatch(prefix) is None
        or _NATURAL_KEY_PAYLOAD_RE.fullmatch(payload) is None
    ):
        raise ConceptIdentityError(
            "natural_key",
            "must use normalized namespace:machine-coordinate form",
        )
    if _INVALID_PERCENT_RE.search(payload):
        raise ConceptIdentityError(
            "natural_key",
            "contains an invalid percent escape",
        )
    for match in _PERCENT_ESCAPE_RE.finditer(payload):
        if match.group(1) != match.group(1).upper():
            raise ConceptIdentityError(
                "natural_key",
                "percent escapes must use uppercase hexadecimal",
            )
    try:
        decoded = unquote(payload, encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ConceptIdentityError(
            "natural_key",
            "contains an invalid UTF-8 percent escape",
        ) from exc
    _safe_decoded_coordinate(decoded, "natural_key")
    if quote(decoded, safe=_NATURAL_KEY_QUOTE_SAFE) != payload:
        raise ConceptIdentityError(
            "natural_key",
            "must use canonical percent encoding only for non-ASCII characters",
        )
    if (
        _URI_SCHEME_RE.match(decoded)
        or _contains_uri_userinfo(decoded)
        or _contains_coordinate_userinfo(decoded)
    ):
        raise ConceptIdentityError(
            "natural_key",
            "must not contain a URL or credential-bearing authority",
        )
    if _looks_absolute_path(decoded):
        raise ConceptIdentityError(
            "natural_key",
            "must not contain an absolute path",
        )
    if "\\" in decoded:
        raise ConceptIdentityError(
            "natural_key",
            "must use forward slashes",
        )
    path_part = decoded.split("#", 1)[0]
    if "/" in path_part:
        segments = path_part.split("/")
        if (
            any(segment in {"", ".", ".."} for segment in segments)
            or path_part.endswith("/")
        ):
            raise ConceptIdentityError(
                "natural_key",
                "contains a non-normalized path",
            )
    if decoded in {".", ".."}:
        raise ConceptIdentityError(
            "natural_key",
            "must not be a dot path",
        )
    return text


def validate_locator(value: object) -> str:
    """Validate an exact canonical Markdown route or ``llm-wiki`` URI."""

    text = _machine_text(value, "locator", maximum=_MAX_NATURAL_KEY_LENGTH)
    if _contains_uri_userinfo(text) or _looks_absolute_path(text):
        raise ConceptIdentityError(
            "locator",
            "must not contain an absolute path or credential-bearing authority",
        )
    try:
        normalized = validate_exact_page_coordinate(text)
    except WikiSurfaceError as exc:
        raise ConceptIdentityError(
            "locator",
            "must be an exact canonical wiki path or llm-wiki URI",
        ) from exc
    if normalized != text:
        raise ConceptIdentityError("locator", "must already be normalized")
    return normalized


def validate_concept_uid(value: object) -> str:
    """Validate the persisted stable UID wire format."""

    text = _machine_text(value, "uid", maximum=_MAX_UID_LENGTH)
    if _UID_RE.fullmatch(text) is None:
        raise ConceptIdentityError(
            "uid",
            (
                "must use lw:<kind-tag>:"
                f"<{CONCEPT_UID_HEX_LENGTH} lowercase hexadecimal characters>"
            ),
        )
    return text


def validate_alias_type(value: AliasType | str) -> AliasType:
    """Return a validated alias namespace."""

    try:
        return value if isinstance(value, AliasType) else AliasType(value)
    except (TypeError, ValueError) as exc:
        raise ConceptIdentityError(
            "alias_type",
            "must be 'locator' or 'natural-key'",
        ) from exc


def validate_alias_value(alias_type: AliasType | str, value: object) -> str:
    """Validate an alias according to its coordinate namespace."""

    selected = validate_alias_type(alias_type)
    if selected is AliasType.LOCATOR:
        return validate_locator(value)
    return validate_natural_key(value)


def identity_coordinate_key(
    alias_type: AliasType | str,
    value: object,
) -> str:
    """Return a collision key shared by equivalent locator spellings.

    Canonical Markdown paths and their canonical ``llm-wiki://`` resource URI
    identify the same page.  The ledger may retain either spelling as history,
    but they cannot be owned by different concepts or repeated as distinct
    aliases.
    """

    selected = validate_alias_type(alias_type)
    normalized = validate_alias_value(selected, value)
    if selected is not AliasType.LOCATOR or normalized.startswith("llm-wiki://"):
        return normalized
    for entry in iter_page_kinds():
        if not entry.requires_page_id:
            if normalized == canonical_path(entry.kind):
                return mcp_uri(entry.kind)
            continue
        directory = entry.directory
        assert directory is not None
        prefix = f"{directory}/"
        if normalized.startswith(prefix) and normalized.endswith(".md"):
            page_id = normalized[len(prefix) : -len(".md")]
            return mcp_uri(entry.kind, page_id)
    # ``validate_alias_value`` already proved this is a page coordinate.
    raise AssertionError("validated locator was absent from the surface registry")


def derive_concept_uid(
    bundle_id: object,
    concept_kind: object,
    natural_key: object,
) -> str:
    """Derive the deterministic initial UID for one validated natural key.

    This function is for first allocation only.  A persisted UID must be
    retained when its locator or natural key changes.
    """

    bundle = validate_bundle_id(bundle_id)
    kind = validate_concept_kind(concept_kind)
    key = validate_natural_key(natural_key)
    encoded = json.dumps(
        {
            "bundle_id": bundle,
            "concept_kind": kind,
            "domain": CONCEPT_UID_DOMAIN,
            "natural_key": key,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:CONCEPT_UID_HEX_LENGTH]
    return f"lw:{_uid_tag(kind)}:{digest}"


def allocate_concept(
    bundle_id: object,
    reference: ConceptReference,
    *,
    allocations: Iterable[ConceptAllocation] = (),
    aliases: Iterable[IdentityAlias] = (),
) -> ConceptAllocation:
    """Return an existing exact identity or allocate a deterministic new UID.

    Matching a current coordinate or historical alias is idempotent.  This
    helper never changes an existing allocation; callers use
    :func:`move_allocation` after explicit/supported move evidence.
    """

    if not isinstance(reference, ConceptReference):
        raise TypeError("reference must be a ConceptReference")
    bundle = validate_bundle_id(bundle_id)
    current, historical = validate_identity_registry(allocations, aliases)
    candidates: set[str] = set()
    by_uid = {allocation.uid: allocation for allocation in current}
    reference_locator_key = identity_coordinate_key(
        AliasType.LOCATOR,
        reference.locator,
    )
    for allocation in current:
        if (
            allocation.natural_key == reference.natural_key
            or identity_coordinate_key(
                AliasType.LOCATOR,
                allocation.locator,
            )
            == reference_locator_key
        ):
            candidates.add(allocation.uid)
    for alias in historical:
        if (
            alias.alias_type is AliasType.NATURAL_KEY
            and alias.value == reference.natural_key
        ) or (
            alias.alias_type is AliasType.LOCATOR
            and identity_coordinate_key(alias.alias_type, alias.value)
            == reference_locator_key
        ):
            candidates.add(alias.uid)
    if len(candidates) > 1:
        collision = IdentityCollision(
            code="reference-collision",
            coordinate_type="reference",
            value=f"{reference.natural_key}|{reference.locator}",
            uids=tuple(sorted(candidates)),
        )
        raise IdentityCollisionError((collision,))
    if candidates:
        allocation = by_uid[next(iter(candidates))]
        if allocation.concept_kind != reference.concept_kind:
            raise ConceptIdentityError(
                "concept_kind",
                "reference resolves to an allocation with a different concept kind",
                code="concept-kind-conflict",
            )
        return allocation

    uid = derive_concept_uid(
        bundle,
        reference.concept_kind,
        reference.natural_key,
    )
    if uid in by_uid:
        raise IdentityCollisionError(
            (
                IdentityCollision(
                    code="uid-derivation-collision",
                    coordinate_type="uid",
                    value=uid,
                    uids=(uid,),
                ),
            )
        )
    return ConceptAllocation(
        uid=uid,
        concept_kind=reference.concept_kind,
        natural_key=reference.natural_key,
        locator=reference.locator,
    )


def find_identity_collisions(
    allocations: Iterable[ConceptAllocation],
    aliases: Iterable[IdentityAlias] = (),
) -> tuple[IdentityCollision, ...]:
    """Return every deterministic UID/current-coordinate/alias conflict."""

    current = _typed_tuple(
        allocations,
        ConceptAllocation,
        "allocations",
    )
    historical = _typed_tuple(aliases, IdentityAlias, "aliases")
    collisions: list[IdentityCollision] = []

    allocations_by_uid: defaultdict[str, list[ConceptAllocation]] = defaultdict(list)
    current_coordinates: dict[
        AliasType, defaultdict[str, list[ConceptAllocation]]
    ] = {
        AliasType.NATURAL_KEY: defaultdict(list),
        AliasType.LOCATOR: defaultdict(list),
    }
    for allocation in current:
        allocations_by_uid[allocation.uid].append(allocation)
        current_coordinates[AliasType.NATURAL_KEY][allocation.natural_key].append(
            allocation
        )
        current_coordinates[AliasType.LOCATOR][
            identity_coordinate_key(AliasType.LOCATOR, allocation.locator)
        ].append(allocation)

    for uid, records in allocations_by_uid.items():
        if len(records) > 1:
            collisions.append(
                IdentityCollision(
                    code="duplicate-uid",
                    coordinate_type="uid",
                    value=uid,
                    uids=(uid,),
                )
            )
    for alias_type, values in current_coordinates.items():
        for value, records in values.items():
            uids = tuple(sorted({record.uid for record in records}))
            if len(uids) > 1:
                collisions.append(
                    IdentityCollision(
                        code=f"{alias_type.value}-collision",
                        coordinate_type=alias_type.value,
                        value=value,
                        uids=uids,
                    )
                )

    aliases_by_coordinate: defaultdict[
        tuple[AliasType, str], list[IdentityAlias]
    ] = defaultdict(list)
    known_uids = set(allocations_by_uid)
    for alias in historical:
        alias_type = cast(AliasType, alias.alias_type)
        aliases_by_coordinate[
            (
                alias_type,
                identity_coordinate_key(alias_type, alias.value),
            )
        ].append(alias)
        if alias.uid not in known_uids:
            collisions.append(
                IdentityCollision(
                    code="alias-missing-allocation",
                    coordinate_type=alias_type.value,
                    value=alias.value,
                    uids=(alias.uid,),
                )
            )

    for (alias_type, value), records in aliases_by_coordinate.items():
        owners = tuple(sorted({record.uid for record in records}))
        if len(records) > 1 and len(owners) == 1:
            collisions.append(
                IdentityCollision(
                    code="duplicate-alias",
                    coordinate_type=alias_type.value,
                    value=value,
                    uids=owners,
                )
            )
        elif len(owners) > 1:
            collisions.append(
                IdentityCollision(
                    code="alias-collision",
                    coordinate_type=alias_type.value,
                    value=value,
                    uids=owners,
                )
            )
        current_owners = {
            allocation.uid
            for allocation in current_coordinates[alias_type].get(value, ())
        }
        conflicting = tuple(sorted(current_owners - set(owners)))
        if conflicting:
            collisions.append(
                IdentityCollision(
                    code="alias-current-collision",
                    coordinate_type=alias_type.value,
                    value=value,
                    uids=tuple(sorted(set(owners) | current_owners)),
                )
            )

    return tuple(sorted(set(collisions)))


def validate_identity_registry(
    allocations: Iterable[ConceptAllocation],
    aliases: Iterable[IdentityAlias] = (),
) -> tuple[tuple[ConceptAllocation, ...], tuple[IdentityAlias, ...]]:
    """Validate uniqueness and return canonical immutable registry records."""

    current = _typed_tuple(allocations, ConceptAllocation, "allocations")
    historical = _typed_tuple(aliases, IdentityAlias, "aliases")
    collisions = find_identity_collisions(current, historical)
    if collisions:
        raise IdentityCollisionError(collisions)
    return (
        tuple(
            sorted(
                current,
                key=lambda item: (
                    item.uid,
                    item.concept_kind,
                    item.natural_key,
                    item.locator,
                ),
            )
        ),
        _sorted_aliases(historical),
    )


def aliases_for_move(
    allocation: ConceptAllocation,
    new_reference: ConceptReference,
    *,
    aliases: Iterable[IdentityAlias] = (),
) -> tuple[IdentityAlias, ...]:
    """Retain prior natural key/locator values as immutable aliases."""

    if not isinstance(allocation, ConceptAllocation):
        raise TypeError("allocation must be a ConceptAllocation")
    if not isinstance(new_reference, ConceptReference):
        raise TypeError("new_reference must be a ConceptReference")
    if allocation.concept_kind != new_reference.concept_kind:
        raise ConceptIdentityError(
            "concept_kind",
            "a move cannot change concept kind",
            code="concept-kind-change",
        )
    historical = _typed_tuple(aliases, IdentityAlias, "aliases")
    result = [
        alias
        for alias in historical
        if not (
            alias.uid == allocation.uid
            and (
                (
                    alias.alias_type is AliasType.NATURAL_KEY
                    and alias.value == new_reference.natural_key
                )
                or (
                    alias.alias_type is AliasType.LOCATOR
                    and identity_coordinate_key(alias.alias_type, alias.value)
                    == identity_coordinate_key(
                        AliasType.LOCATOR,
                        new_reference.locator,
                    )
                )
            )
        )
    ]
    if allocation.natural_key != new_reference.natural_key:
        result.append(
            IdentityAlias(
                AliasType.NATURAL_KEY,
                allocation.natural_key,
                allocation.uid,
            )
        )
    if identity_coordinate_key(
        AliasType.LOCATOR,
        allocation.locator,
    ) != identity_coordinate_key(AliasType.LOCATOR, new_reference.locator):
        result.append(
            IdentityAlias(
                AliasType.LOCATOR,
                allocation.locator,
                allocation.uid,
            )
        )
    return _deduplicated_aliases(result)


def move_allocation(
    allocation: ConceptAllocation,
    new_reference: ConceptReference,
    *,
    allocations: Iterable[ConceptAllocation] = (),
    aliases: Iterable[IdentityAlias] = (),
) -> IdentityUpdate:
    """Carry a UID to new coordinates and retain both prior aliases."""

    if not isinstance(allocation, ConceptAllocation):
        raise TypeError("allocation must be a ConceptAllocation")
    supplied = _typed_tuple(allocations, ConceptAllocation, "allocations")
    if all(item.uid != allocation.uid for item in supplied):
        supplied = (*supplied, allocation)
    current, historical = validate_identity_registry(supplied, aliases)
    existing = {item.uid: item for item in current}.get(allocation.uid)
    if existing is not None and existing != allocation:
        raise ConceptIdentityError(
            "allocation",
            "does not match the registry record for its UID",
            code="allocation-mismatch",
        )
    retained = aliases_for_move(
        allocation,
        new_reference,
        aliases=historical,
    )
    updated = ConceptAllocation(
        uid=allocation.uid,
        concept_kind=new_reference.concept_kind,
        natural_key=new_reference.natural_key,
        locator=new_reference.locator,
    )
    registry = tuple(item for item in current if item.uid != allocation.uid) + (
        updated,
    )
    _, validated_aliases = validate_identity_registry(registry, retained)
    return IdentityUpdate(allocation=updated, aliases=validated_aliases)


def add_identity_alias(
    allocation: ConceptAllocation,
    alias_type: AliasType | str,
    value: object,
    *,
    allocations: Iterable[ConceptAllocation] = (),
    aliases: Iterable[IdentityAlias] = (),
) -> IdentityUpdate:
    """Add one explicit alias idempotently after full collision validation."""

    if not isinstance(allocation, ConceptAllocation):
        raise TypeError("allocation must be a ConceptAllocation")
    supplied = _typed_tuple(allocations, ConceptAllocation, "allocations")
    if all(item.uid != allocation.uid for item in supplied):
        supplied = (*supplied, allocation)
    current, historical = validate_identity_registry(supplied, aliases)
    existing = {item.uid: item for item in current}.get(allocation.uid)
    if existing is not None and existing != allocation:
        raise ConceptIdentityError(
            "allocation",
            "does not match the registry record for its UID",
            code="allocation-mismatch",
        )
    selected = validate_alias_type(alias_type)
    normalized = validate_alias_value(selected, value)
    current_value = (
        allocation.locator
        if selected is AliasType.LOCATOR
        else allocation.natural_key
    )
    normalized_key = identity_coordinate_key(selected, normalized)
    current_key = identity_coordinate_key(selected, current_value)
    updated_aliases = tuple(
        alias
        for alias in historical
        if not (
            alias.uid == allocation.uid
            and alias.alias_type is selected
            and identity_coordinate_key(alias.alias_type, alias.value)
            == current_key
        )
    )
    if normalized_key != current_key:
        updated_aliases = _deduplicated_aliases(
            (
                *updated_aliases,
                IdentityAlias(selected, normalized, allocation.uid),
            )
        )
    registry = tuple(item for item in current if item.uid != allocation.uid) + (
        allocation,
    )
    _, validated_aliases = validate_identity_registry(registry, updated_aliases)
    return IdentityUpdate(allocation=allocation, aliases=validated_aliases)


def _uid_tag(concept_kind: str) -> str:
    return _UID_TAG_BY_KIND.get(concept_kind, "concept")


def _machine_text(value: object, field: str, *, maximum: int) -> str:
    if not isinstance(value, str) or not value:
        raise ConceptIdentityError(field, "must be a non-empty string")
    if len(value) > maximum:
        raise ConceptIdentityError(field, f"must contain at most {maximum} characters")
    if value != value.strip() or any(character.isspace() for character in value):
        raise ConceptIdentityError(field, "must not contain whitespace")
    if unicodedata.normalize("NFC", value) != value:
        raise ConceptIdentityError(field, "must use Unicode NFC normalization")
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ConceptIdentityError(field, "must not contain control or format characters")
    return value


def _safe_decoded_coordinate(value: str, field: str) -> None:
    if not value:
        raise ConceptIdentityError(field, "must contain a non-empty coordinate")
    if unicodedata.normalize("NFC", value) != value:
        raise ConceptIdentityError(field, "decoded value must use Unicode NFC normalization")
    if any(
        character.isspace()
        or unicodedata.category(character).startswith("C")
        for character in value
    ):
        raise ConceptIdentityError(
            field,
            "decoded value must not contain whitespace, controls, or format characters",
        )


def _looks_absolute_path(value: str) -> bool:
    return (
        value.startswith(("/", "\\\\", "//"))
        or _WINDOWS_ABSOLUTE_RE.match(value) is not None
    )


def _contains_uri_userinfo(value: str) -> bool:
    if "://" not in value:
        return False
    try:
        parsed = urlsplit(value)
        return parsed.username is not None or parsed.password is not None
    except ValueError:
        return True


def _contains_coordinate_userinfo(value: str) -> bool:
    path_part = value.split("#", 1)[0]
    first_segment = path_part.split("/", 1)[0]
    if "@" not in first_segment:
        return False
    userinfo, host = first_segment.rsplit("@", 1)
    return bool(
        userinfo
        and host
        and (
            ":" in userinfo
            or "." in host
            or ":" in host
        )
    )


_RecordT = TypeVar("_RecordT")


def _typed_tuple(
    values: Iterable[_RecordT],
    expected_type: type[_RecordT],
    field: str,
) -> tuple[_RecordT, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field} must be an iterable of {expected_type.__name__}")
    try:
        result = tuple(values)
    except TypeError as exc:
        raise TypeError(
            f"{field} must be an iterable of {expected_type.__name__}"
        ) from exc
    for index, value in enumerate(result):
        if not isinstance(value, expected_type):
            raise TypeError(
                f"{field}[{index}] must be a {expected_type.__name__}"
            )
    return result


def _sorted_aliases(values: Iterable[IdentityAlias]) -> tuple[IdentityAlias, ...]:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                cast(AliasType, item.alias_type).value,
                item.value,
                item.uid,
            ),
        )
    )


def _deduplicated_aliases(
    values: Iterable[IdentityAlias],
) -> tuple[IdentityAlias, ...]:
    by_key = {
        (
            cast(AliasType, item.alias_type).value,
            identity_coordinate_key(
                cast(AliasType, item.alias_type),
                item.value,
            ),
            item.uid,
        ): item
        for item in values
    }
    return _sorted_aliases(by_key.values())


__all__ = [
    "AliasType",
    "CONCEPT_UID_DOMAIN",
    "CONCEPT_UID_HEX_LENGTH",
    "ConceptAllocation",
    "ConceptIdentityError",
    "ConceptReference",
    "IdentityAlias",
    "IdentityCollision",
    "IdentityCollisionError",
    "IdentityUpdate",
    "add_identity_alias",
    "aliases_for_move",
    "allocate_concept",
    "derive_concept_uid",
    "find_identity_collisions",
    "identity_coordinate_key",
    "move_allocation",
    "validate_alias_type",
    "validate_alias_value",
    "validate_bundle_id",
    "validate_concept_kind",
    "validate_concept_uid",
    "validate_identity_registry",
    "validate_locator",
    "validate_natural_key",
]
