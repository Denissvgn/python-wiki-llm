"""Deterministic encoding, hashing, and concept-observation boundaries.

The module and entity builders operate only on an already evaluated inventory
and source-content hash. They do not scan source, invoke extractors, compute
live freshness, or write artifacts.
"""

from __future__ import annotations

import hashlib
import json
import math
import posixpath
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"

_SHA256_RE = re.compile(SHA256_PATTERN)
_WINDOWS_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")
_COMPONENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_UNKNOWN_REASON_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")

MODULE_OBSERVATION_SCOPE = "module"
ENTITY_OBSERVATION_SCOPE = "entity"

UNKNOWN_INSUFFICIENT_INVENTORY = "insufficient-inventory-detail"
UNKNOWN_UNSUPPORTED_LANGUAGE = "unsupported-language"
UNKNOWN_INVALID_INVENTORY = "invalid-inventory-shape"
UNKNOWN_ENTITY_NOT_FOUND = "entity-occurrence-not-found"

_SUPPORTED_OBSERVATION_LANGUAGES = frozenset(
    {"go", "haskell", "javascript", "python", "rust", "typescript"}
)
_LOCATION_ONLY_KEYS = frozenset({"line", "end_line", "decorator_line"})
_ENTITY_NONSTRUCTURAL_KEYS = _LOCATION_ONLY_KEYS | frozenset(
    {
        "calls",
        "data_effects",
        "description",
        "docstring",
    }
)
_MODULE_NONSTRUCTURAL_KEYS = _ENTITY_NONSTRUCTURAL_KEYS
_MODULE_ENTITY_FIELDS = (
    "name",
    "kind",
    "model_kind",
    "bases",
    "target",
)
_MODULE_FUNCTION_FIELDS = (
    "name",
    "kind",
    "signature",
    "params",
    "return_type",
    "is_async",
    "async",
    "decorators",
)
_MODULE_CONSTANT_FIELDS = ("name",)
_MODULE_CALL_FIELDS = ("name", "attr", "target")


@dataclass(frozen=True)
class ConceptObservationBasis:
    """One module/entity observation basis or an explicit unknown result.

    ``unknown_reason`` is service-level diagnostic state and is not a v1 core
    field. :meth:`to_evidence_payload` returns only fields accepted by the
    persisted :class:`knowledge_model.EvidenceBasis` contract.
    """

    scope: str
    source_path: str
    extractor_ref: str
    source_content_hash: str
    concept_observation_hash: str | None
    unknown_reason: str | None = None

    def __post_init__(self) -> None:
        _validate_scope(self.scope)
        _validate_source_path(self.source_path)
        _validate_extractor_ref(self.extractor_ref)
        _validate_hash(self.source_content_hash, "source_content_hash")
        if self.concept_observation_hash is None:
            if (
                not isinstance(self.unknown_reason, str)
                or _UNKNOWN_REASON_RE.fullmatch(self.unknown_reason) is None
            ):
                raise ValueError(
                    "unknown_reason must be a lowercase machine code when "
                    "concept_observation_hash is absent"
                )
        else:
            _validate_hash(
                self.concept_observation_hash,
                "concept_observation_hash",
            )
            if self.unknown_reason is not None:
                raise ValueError(
                    "unknown_reason must be absent when "
                    "concept_observation_hash is present"
                )

    @property
    def is_known(self) -> bool:
        """Return whether this basis carries a reproducible observation hash."""

        return self.concept_observation_hash is not None

    def to_evidence_payload(self) -> dict[str, str]:
        """Return the v1-compatible evidence-basis fields."""

        payload = {
            "scope": self.scope,
            "source_path": self.source_path,
            "extractor_ref": self.extractor_ref,
            "source_content_hash": self.source_content_hash,
        }
        if self.concept_observation_hash is not None:
            payload["concept_observation_hash"] = self.concept_observation_hash
        return payload


class _InventoryNormalizationError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def is_valid_sha256(value: object) -> bool:
    """Return whether *value* is a canonical ``sha256:<lowercase-hex>`` string."""

    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def canonical_json_text(value: Any) -> str:
    """Encode *value* as compact canonical JSON for hashing and ordering."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Return the UTF-8 bytes of :func:`canonical_json_text`."""

    return canonical_json_text(value).encode("utf-8")


def formatted_json_text(value: Any) -> str:
    """Encode deterministic human-readable JSON with one trailing newline."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )


def formatted_json_bytes(value: Any) -> bytes:
    """Return UTF-8 deterministic JSON bytes with one trailing newline."""

    return formatted_json_text(value).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    """Return the canonical SHA-256 wire value for *value*."""

    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def hash_json(value: Any) -> str:
    """Hash the canonical JSON encoding of *value*."""

    return sha256_bytes(canonical_json_bytes(value))


def normalize_module_observation(
    file_data: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return the canonical structural module observation.

    Mapping keys are normalized by canonical JSON serialization while array
    order and multiplicity are retained. ``None`` means the supplied inventory
    is unsupported or malformed. Callers must separately establish that the
    inventory is complete; the mapping alone cannot prove extraction depth.
    """

    try:
        return _normalize_module_observation(file_data)
    except (_InventoryNormalizationError, RecursionError):
        return None


def normalize_entity_observation(
    file_data: Mapping[str, Any],
    entity_name: str,
    occurrence: int = 1,
) -> dict[str, Any] | None:
    """Return the structural observation for one same-name entity occurrence.

    ``occurrence`` is one-based within ``file_data["classes"]`` and is part of
    the hash input, so even byte-identical duplicate declarations remain
    distinct. ``None`` means the inventory is unsupported, malformed, or does
    not contain the requested occurrence.
    """

    _validate_entity_coordinate(entity_name, occurrence)
    try:
        return _normalize_entity_observation(file_data, entity_name, occurrence)
    except (_InventoryNormalizationError, RecursionError):
        return None


def module_observation_hash(
    file_data: Mapping[str, Any],
    *,
    inventory_complete: bool,
) -> str | None:
    """Hash a normalized module observation, or return ``None`` if unavailable.

    Completeness is explicit because it cannot be inferred safely from optional
    extractor fields. Prefer a basis builder when the unknown reason is needed.
    """

    _validate_inventory_complete(inventory_complete)
    if not inventory_complete:
        return None
    normalized = normalize_module_observation(file_data)
    return _hash_normalized_observation(normalized)


def entity_observation_hash(
    file_data: Mapping[str, Any],
    entity_name: str,
    occurrence: int = 1,
    *,
    inventory_complete: bool,
) -> str | None:
    """Hash one normalized entity observation, or return ``None``."""

    _validate_inventory_complete(inventory_complete)
    if not inventory_complete:
        return None
    normalized = normalize_entity_observation(
        file_data,
        entity_name,
        occurrence,
    )
    return _hash_normalized_observation(normalized)


def build_module_observation_basis(
    *,
    source_path: str,
    file_data: Mapping[str, Any] | None,
    source_content_hash: str,
    extractor_ref: str,
    inventory_complete: bool,
) -> ConceptObservationBasis:
    """Build a known module basis or an explicit unknown basis.

    ``inventory_complete`` must describe the already evaluated extraction run;
    this function never guesses deep/slim status from optional record fields.
    """

    _validate_basis_inputs(
        source_path,
        source_content_hash,
        extractor_ref,
        inventory_complete,
    )
    if not inventory_complete:
        return _unknown_basis(
            MODULE_OBSERVATION_SCOPE,
            source_path,
            source_content_hash,
            extractor_ref,
            UNKNOWN_INSUFFICIENT_INVENTORY,
        )

    try:
        normalized = _normalize_module_observation(file_data)
        observation_hash = hash_json(normalized)
    except _InventoryNormalizationError as exc:
        return _unknown_basis(
            MODULE_OBSERVATION_SCOPE,
            source_path,
            source_content_hash,
            extractor_ref,
            exc.reason,
        )
    except (RecursionError, TypeError, UnicodeEncodeError, ValueError):
        return _unknown_basis(
            MODULE_OBSERVATION_SCOPE,
            source_path,
            source_content_hash,
            extractor_ref,
            UNKNOWN_INVALID_INVENTORY,
        )

    return ConceptObservationBasis(
        scope=MODULE_OBSERVATION_SCOPE,
        source_path=source_path,
        extractor_ref=extractor_ref,
        source_content_hash=source_content_hash,
        concept_observation_hash=observation_hash,
    )


def build_entity_observation_basis(
    *,
    source_path: str,
    file_data: Mapping[str, Any] | None,
    entity_name: str,
    occurrence: int,
    source_content_hash: str,
    extractor_ref: str,
    inventory_complete: bool,
) -> ConceptObservationBasis:
    """Build a known entity basis or an explicit unknown basis."""

    _validate_basis_inputs(
        source_path,
        source_content_hash,
        extractor_ref,
        inventory_complete,
    )
    _validate_entity_coordinate(entity_name, occurrence)
    if not inventory_complete:
        return _unknown_basis(
            ENTITY_OBSERVATION_SCOPE,
            source_path,
            source_content_hash,
            extractor_ref,
            UNKNOWN_INSUFFICIENT_INVENTORY,
        )

    try:
        normalized = _normalize_entity_observation(
            file_data,
            entity_name,
            occurrence,
        )
        observation_hash = hash_json(normalized)
    except _InventoryNormalizationError as exc:
        return _unknown_basis(
            ENTITY_OBSERVATION_SCOPE,
            source_path,
            source_content_hash,
            extractor_ref,
            exc.reason,
        )
    except (RecursionError, TypeError, UnicodeEncodeError, ValueError):
        return _unknown_basis(
            ENTITY_OBSERVATION_SCOPE,
            source_path,
            source_content_hash,
            extractor_ref,
            UNKNOWN_INVALID_INVENTORY,
        )

    return ConceptObservationBasis(
        scope=ENTITY_OBSERVATION_SCOPE,
        source_path=source_path,
        extractor_ref=extractor_ref,
        source_content_hash=source_content_hash,
        concept_observation_hash=observation_hash,
    )


def _normalize_module_observation(
    file_data: Mapping[str, Any] | None,
) -> dict[str, Any]:
    language = _inventory_language(file_data)
    assert isinstance(file_data, Mapping)
    classes = _record_array(file_data, "classes", required=True)
    functions = _record_array(file_data, "functions", required=True)
    imports = _record_array(file_data, "imports", required=False)
    for record in imports:
        _validate_import_record(record)

    class_summaries: list[dict[str, Any]] = []
    seen_names: dict[str, int] = {}
    for record in classes:
        name = _record_name(record)
        _validate_module_entity_record(record)
        seen_names[name] = seen_names.get(name, 0) + 1
        summary = _copy_selected_fields(
            record,
            _MODULE_ENTITY_FIELDS,
            _MODULE_NONSTRUCTURAL_KEYS,
        )
        summary["occurrence"] = seen_names[name]
        class_summaries.append(summary)

    function_summaries: list[dict[str, Any]] = []
    for record in functions:
        _validate_callable_record(record)
        function_summaries.append(
            _copy_selected_fields(
                record,
                _MODULE_FUNCTION_FIELDS,
                _MODULE_NONSTRUCTURAL_KEYS,
            )
        )

    payload: dict[str, Any] = {
        "scope": MODULE_OBSERVATION_SCOPE,
        "language": language,
        "imports": _structural_copy(imports, _MODULE_NONSTRUCTURAL_KEYS),
        "classes": class_summaries,
        "functions": function_summaries,
    }
    if "module" in file_data:
        module_name = file_data["module"]
        if not isinstance(module_name, str) or not module_name.strip():
            raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
        payload["module"] = module_name

    if language in {"javascript", "typescript"}:
        exports = _json_array(file_data, "exports")
        _validate_string_array(exports)
        constants = _record_array(file_data, "constants", required=False)
        module_calls = _record_array(file_data, "module_calls", required=False)
        constant_summaries = []
        for record in constants:
            _validate_constant_record(record)
            constant_summaries.append(
                _copy_selected_fields(
                    record,
                    _MODULE_CONSTANT_FIELDS,
                    _MODULE_NONSTRUCTURAL_KEYS,
                )
            )
        payload["exports"] = _structural_copy(
            exports,
            _MODULE_NONSTRUCTURAL_KEYS,
        )
        payload["constants"] = constant_summaries
        call_summaries = []
        for record in module_calls:
            _validate_module_call_record(record)
            call_summaries.append(
                _copy_selected_fields(
                    record,
                    _MODULE_CALL_FIELDS,
                    _MODULE_NONSTRUCTURAL_KEYS,
                )
            )
        payload["module_calls"] = call_summaries

    return payload


def _normalize_entity_observation(
    file_data: Mapping[str, Any] | None,
    entity_name: str,
    occurrence: int,
) -> dict[str, Any]:
    language = _inventory_language(file_data)
    assert isinstance(file_data, Mapping)
    classes = _record_array(file_data, "classes", required=True)
    selected: Mapping[str, Any] | None = None
    seen = 0
    for record in classes:
        name = _record_name(record)
        if name != entity_name:
            continue
        seen += 1
        if seen == occurrence:
            selected = record
            break
    if selected is None:
        raise _InventoryNormalizationError(UNKNOWN_ENTITY_NOT_FOUND)
    _validate_entity_record(selected)

    return {
        "scope": ENTITY_OBSERVATION_SCOPE,
        "language": language,
        "name": entity_name,
        "occurrence": occurrence,
        "declaration": _structural_copy(
            selected,
            _ENTITY_NONSTRUCTURAL_KEYS,
        ),
    }


def _inventory_language(file_data: Mapping[str, Any] | None) -> str:
    if not isinstance(file_data, Mapping):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    language = file_data.get("language")
    if not isinstance(language, str) or not language:
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    if language not in _SUPPORTED_OBSERVATION_LANGUAGES:
        raise _InventoryNormalizationError(UNKNOWN_UNSUPPORTED_LANGUAGE)
    return language


def _record_array(
    file_data: Mapping[str, Any],
    field: str,
    *,
    required: bool,
) -> list[Mapping[str, Any]]:
    if field not in file_data:
        if required:
            raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
        return []
    value = file_data[field]
    if not isinstance(value, list):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    if not all(isinstance(item, Mapping) for item in value):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    return value


def _json_array(file_data: Mapping[str, Any], field: str) -> list[Any]:
    value = file_data.get(field, [])
    if not isinstance(value, list):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    return value


def _record_name(record: Mapping[str, Any]) -> str:
    name = record.get("name")
    if not isinstance(name, str) or not name:
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    return name


def _validate_module_entity_record(record: Mapping[str, Any]) -> None:
    _record_name(record)
    _validate_optional_strings(record, ("kind", "model_kind", "target"))
    _validate_optional_string_array(record, "bases")


def _validate_entity_record(record: Mapping[str, Any]) -> None:
    _validate_module_entity_record(record)
    for field in (
        "decorators",
        "deriving",
        "literal_values",
        "type_params",
    ):
        _validate_optional_string_array(record, field)

    attributes = _optional_record_array(record, "attributes")
    for attribute in attributes:
        _record_name(attribute)
        _validate_optional_strings(
            attribute,
            (
                "alias",
                "default",
                "default_factory",
                "serialization_alias",
                "tag",
                "type",
                "validation_alias",
                "value",
            ),
        )
        for field in (
            "annotated_metadata",
            "examples",
            "literal_values",
        ):
            _validate_optional_json_array(attribute, field)
        _validate_optional_mapping(attribute, "constraints")
        _validate_optional_record_array(attribute, "unknowns")
        _validate_optional_booleans(attribute, ("nullable", "required"))

    methods = _optional_record_array(record, "methods")
    for method in methods:
        _validate_callable_record(method)
        validator = _validate_optional_mapping(method, "validator")
        if validator is not None:
            _validate_optional_string_array(validator, "fields")
            _validate_optional_mapping(validator, "options")

    model_config = _optional_record_array(record, "model_config")
    for setting in model_config:
        _record_name(setting)
        _validate_optional_record_array(setting, "unknowns")


def _validate_callable_record(record: Mapping[str, Any]) -> None:
    _record_name(record)
    _validate_optional_strings(
        record,
        ("kind", "return_type", "signature"),
    )
    _validate_optional_booleans(record, ("async", "is_async"))
    _validate_optional_string_array(record, "decorators")
    params = _optional_record_array(record, "params")
    for param in params:
        if not isinstance(param.get("name"), str):
            raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
        _validate_optional_strings(param, ("default", "kind", "type"))


def _validate_import_record(record: Mapping[str, Any]) -> None:
    module = record.get("module")
    if not isinstance(module, str) or not module:
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    _validate_optional_strings(record, ("name", "type"))
    if "alias" in record and record["alias"] is not None:
        _validate_optional_strings(record, ("alias",))
    _validate_optional_booleans(record, ("qualified",))


def _validate_constant_record(record: Mapping[str, Any]) -> None:
    _record_name(record)
    _validate_optional_booleans(record, ("exported",))


def _validate_module_call_record(record: Mapping[str, Any]) -> None:
    name = record.get("attr") or record.get("name")
    if not isinstance(name, str) or not name:
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    _validate_optional_strings(record, ("attr", "name", "target"))


def _validate_optional_strings(
    record: Mapping[str, Any],
    fields: tuple[str, ...],
) -> None:
    if any(field in record and not isinstance(record[field], str) for field in fields):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)


def _validate_optional_booleans(
    record: Mapping[str, Any],
    fields: tuple[str, ...],
) -> None:
    if any(field in record and not isinstance(record[field], bool) for field in fields):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)


def _validate_string_array(value: list[Any]) -> None:
    if not all(isinstance(item, str) for item in value):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)


def _validate_optional_string_array(
    record: Mapping[str, Any],
    field: str,
) -> None:
    if field not in record:
        return
    value = record[field]
    if not isinstance(value, list):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    _validate_string_array(value)


def _validate_optional_json_array(
    record: Mapping[str, Any],
    field: str,
) -> None:
    if field in record and not isinstance(record[field], list):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)


def _optional_record_array(
    record: Mapping[str, Any],
    field: str,
) -> list[Mapping[str, Any]]:
    if field not in record:
        return []
    value = record[field]
    if not isinstance(value, list) or not all(
        isinstance(item, Mapping) for item in value
    ):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    return value


def _validate_optional_record_array(
    record: Mapping[str, Any],
    field: str,
) -> None:
    _optional_record_array(record, field)


def _validate_optional_mapping(
    record: Mapping[str, Any],
    field: str,
) -> Mapping[str, Any] | None:
    if field not in record:
        return None
    value = record[field]
    if not isinstance(value, Mapping):
        raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
    return value


def _copy_selected_fields(
    record: Mapping[str, Any],
    fields: tuple[str, ...],
    excluded_keys: frozenset[str],
) -> dict[str, Any]:
    return {
        field: _structural_copy(record[field], excluded_keys)
        for field in fields
        if field in record
    }


def _structural_copy(
    value: Any,
    excluded_keys: frozenset[str],
    active: set[int] | None = None,
) -> Any:
    if active is None:
        active = set()
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in active:
            raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
        active.add(identity)
        try:
            if not all(isinstance(key, str) for key in value):
                raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
            return {
                key: _structural_copy(value[key], excluded_keys, active)
                for key in sorted(value)
                if key not in excluded_keys
            }
        finally:
            active.remove(identity)
    if isinstance(value, list):
        identity = id(value)
        if identity in active:
            raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)
        active.add(identity)
        try:
            return [_structural_copy(item, excluded_keys, active) for item in value]
        finally:
            active.remove(identity)
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise _InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)


def _hash_normalized_observation(normalized: dict[str, Any] | None) -> str | None:
    if normalized is None:
        return None
    try:
        return hash_json(normalized)
    except (RecursionError, TypeError, UnicodeEncodeError, ValueError):
        return None


def _unknown_basis(
    scope: str,
    source_path: str,
    source_content_hash: str,
    extractor_ref: str,
    reason: str,
) -> ConceptObservationBasis:
    return ConceptObservationBasis(
        scope=scope,
        source_path=source_path,
        extractor_ref=extractor_ref,
        source_content_hash=source_content_hash,
        concept_observation_hash=None,
        unknown_reason=reason,
    )


def _validate_basis_inputs(
    source_path: object,
    source_content_hash: object,
    extractor_ref: object,
    inventory_complete: object,
) -> None:
    _validate_source_path(source_path)
    _validate_hash(source_content_hash, "source_content_hash")
    _validate_extractor_ref(extractor_ref)
    _validate_inventory_complete(inventory_complete)


def _validate_inventory_complete(inventory_complete: object) -> None:
    if not isinstance(inventory_complete, bool):
        raise TypeError("inventory_complete must be a boolean")


def _validate_scope(scope: object) -> None:
    if scope not in {MODULE_OBSERVATION_SCOPE, ENTITY_OBSERVATION_SCOPE}:
        raise ValueError("scope must be 'module' or 'entity'")


def _validate_source_path(source_path: object) -> None:
    if not isinstance(source_path, str) or not source_path:
        raise ValueError("source_path must be a non-empty repository-relative path")
    if (
        source_path != source_path.strip()
        or any(ord(char) < 0x20 for char in source_path)
        or source_path.startswith("/")
        or _WINDOWS_DRIVE_PREFIX_RE.match(source_path)
        or "\\" in source_path
    ):
        raise ValueError("source_path must be a repository-relative POSIX path")
    parts = source_path.split("/")
    if (
        any(part in {"", ".", ".."} for part in parts)
        or posixpath.normpath(source_path) != source_path
    ):
        raise ValueError("source_path must be a normalized repository-relative path")


def _validate_extractor_ref(extractor_ref: object) -> None:
    if (
        not isinstance(extractor_ref, str)
        or _COMPONENT_ID_RE.fullmatch(extractor_ref) is None
    ):
        raise ValueError("extractor_ref must be a normalized producer component ID")


def _validate_hash(value: object, field: str) -> None:
    if not is_valid_sha256(value):
        raise ValueError(
            f"{field} must be 'sha256:' followed by 64 lowercase hexadecimal digits"
        )


def _validate_entity_coordinate(entity_name: object, occurrence: object) -> None:
    if not isinstance(entity_name, str) or not entity_name:
        raise ValueError("entity_name must be a non-empty string")
    if (
        isinstance(occurrence, bool)
        or not isinstance(occurrence, int)
        or occurrence < 1
    ):
        raise ValueError("occurrence must be a positive integer")


def without_line_metadata(value: Any) -> Any:
    """Return inventory data with line-only metadata removed."""

    if isinstance(value, dict):
        return {
            key: without_line_metadata(item)
            for key, item in sorted(value.items())
            if key != "line"
        }
    if isinstance(value, list):
        return [without_line_metadata(item) for item in value]
    return value


def semantic_hash_for_file(file_data: dict[str, Any]) -> str:
    """Fingerprint extracted file semantics while ignoring line shifts."""

    normalized = without_line_metadata(file_data)
    # Manifest v4 historically hashed json.dumps()'s ASCII-escaped compact
    # representation. Preserve that commitment until a versioned migration.
    legacy_bytes = json.dumps(
        normalized,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256_bytes(legacy_bytes)


def hash_file(path: Path) -> str:
    """Hash raw file bytes, returning ``""`` when the file cannot be read."""

    try:
        return sha256_bytes(path.read_bytes())
    except OSError:
        return ""


__all__ = [
    "ENTITY_OBSERVATION_SCOPE",
    "MODULE_OBSERVATION_SCOPE",
    "SHA256_PATTERN",
    "UNKNOWN_ENTITY_NOT_FOUND",
    "UNKNOWN_INSUFFICIENT_INVENTORY",
    "UNKNOWN_INVALID_INVENTORY",
    "UNKNOWN_UNSUPPORTED_LANGUAGE",
    "ConceptObservationBasis",
    "build_entity_observation_basis",
    "build_module_observation_basis",
    "canonical_json_bytes",
    "canonical_json_text",
    "entity_observation_hash",
    "formatted_json_bytes",
    "formatted_json_text",
    "hash_file",
    "hash_json",
    "is_valid_sha256",
    "module_observation_hash",
    "normalize_entity_observation",
    "normalize_module_observation",
    "semantic_hash_for_file",
    "sha256_bytes",
    "without_line_metadata",
]
