"""Deterministic encoding, hashing, and concept-observation boundaries.

The module and entity builders operate only on an already evaluated inventory
and source-content hash. They do not scan source, invoke extractors, compute
live freshness, or write artifacts.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Any

from .normalization_diagnostics import MISSING_VALUE, NormalizationDiagnostic

from .validation import (
    require_bool,
    require_list,
    require_mapping,
    require_member,
    require_nonempty_text,
    require_positive_int,
    require_repository_relative_path,
    require_sha256,
    require_string,
)

SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"

_SHA256_RE = re.compile(SHA256_PATTERN)
_COMPONENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_UNKNOWN_REASON_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")

MODULE_OBSERVATION_SCOPE = "module"
ENTITY_OBSERVATION_SCOPE = "entity"
INFRASTRUCTURE_OBSERVATION_SCOPE = "infrastructure"

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
        "call_bindings",
        "python_constructor_dispatch",
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
    "target_truncated",
    "target_sha256",
    "type_params",
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
    "type_params",
)
_MODULE_CONSTANT_FIELDS = ("name",)
_MODULE_CALL_FIELDS = ("name", "attr", "target")


@dataclass(frozen=True)
class ConceptObservationBasis:
    """One source-backed concept observation basis or explicit unknown result.

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
    normalization_diagnostic: NormalizationDiagnostic | None = dataclass_field(default=None, repr=False, compare=False)

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
    def __init__(self, reason: str, *, pointer=None, rule=None, expected=None, value=None, exact=True):
        self.reason = reason
        self._detail = (pointer, rule, expected, value, exact)
        super().__init__(reason)

    @property
    def diagnostic(self) -> NormalizationDiagnostic | None:
        pointer, rule, expected, value, exact = self._detail
        if rule is None:
            return None
        return NormalizationDiagnostic.rejection(self.reason, pointer, rule, expected, value, exact=exact)


def _failure(pointer, rule, expected, value, *, reason=UNKNOWN_INVALID_INVENTORY, exact=True):
    return _InventoryNormalizationError(reason, pointer=pointer, rule=rule, expected=expected, value=value, exact=exact)


def _pointer(parent, field):
    return parent + "/" + str(field).replace("~", "~0").replace("/", "~1")


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
            diagnostic=exc.diagnostic,
        )
    except (RecursionError, TypeError, UnicodeEncodeError, ValueError):
        return _unknown_basis(
            MODULE_OBSERVATION_SCOPE,
            source_path,
            source_content_hash,
            extractor_ref,
            UNKNOWN_INVALID_INVENTORY,
            diagnostic=NormalizationDiagnostic(
                UNKNOWN_INVALID_INVENTORY, None, "structural-json-encoding",
                "finite encodable acyclic JSON within recursion limits", "unavailable", "not captured", False,
            ),
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
            diagnostic=exc.diagnostic, entity_name=entity_name, occurrence=occurrence,
        )
    except (RecursionError, TypeError, UnicodeEncodeError, ValueError):
        return _unknown_basis(
            ENTITY_OBSERVATION_SCOPE,
            source_path,
            source_content_hash,
            extractor_ref,
            UNKNOWN_INVALID_INVENTORY,
            diagnostic=NormalizationDiagnostic(
                UNKNOWN_INVALID_INVENTORY, None, "structural-json-encoding",
                "finite encodable acyclic JSON within recursion limits", "unavailable", "not captured", False,
            ), entity_name=entity_name, occurrence=occurrence,
        )

    return ConceptObservationBasis(
        scope=ENTITY_OBSERVATION_SCOPE,
        source_path=source_path,
        extractor_ref=extractor_ref,
        source_content_hash=source_content_hash,
        concept_observation_hash=observation_hash,
    )


def build_infrastructure_observation_basis(
    *,
    source_path: str,
    source_content_hash: str,
    observation_hash: str,
    extractor_ref: str,
) -> ConceptObservationBasis:
    """Build a known basis from one already normalized infrastructure record."""

    _validate_source_path(source_path)
    _validate_hash(source_content_hash, "source_content_hash")
    _validate_hash(observation_hash, "observation_hash")
    _validate_extractor_ref(extractor_ref)
    return ConceptObservationBasis(
        scope=INFRASTRUCTURE_OBSERVATION_SCOPE,
        source_path=source_path,
        extractor_ref=extractor_ref,
        source_content_hash=source_content_hash,
        concept_observation_hash=observation_hash,
    )


def _normalize_module_observation(file_data: Mapping[str, Any] | None) -> dict[str, Any]:
    language = _inventory_language(file_data)
    assert isinstance(file_data, Mapping)
    classes = _record_array(file_data, "classes", required=True)
    functions = _record_array(file_data, "functions", required=True)
    imports = _record_array(file_data, "imports", required=False)
    for index, record in enumerate(imports):
        _validate_import_record(record, language=language, pointer=f"/imports/{index}")

    class_summaries: list[dict[str, Any]] = []
    seen_names: dict[str, int] = {}
    for index, record in enumerate(classes):
        pointer = f"/classes/{index}"
        name = _record_name(record, pointer)
        _validate_module_entity_record(record, pointer)
        seen_names[name] = seen_names.get(name, 0) + 1
        summary = _copy_selected_fields(record, _MODULE_ENTITY_FIELDS, _MODULE_NONSTRUCTURAL_KEYS, pointer)
        summary["occurrence"] = seen_names[name]
        class_summaries.append(summary)

    function_summaries: list[dict[str, Any]] = []
    for index, record in enumerate(functions):
        pointer = f"/functions/{index}"
        _validate_callable_record(record, pointer)
        function_summaries.append(_copy_selected_fields(record, _MODULE_FUNCTION_FIELDS, _MODULE_NONSTRUCTURAL_KEYS, pointer))

    payload: dict[str, Any] = {
        "scope": MODULE_OBSERVATION_SCOPE, "language": language,
        "imports": _structural_copy(imports, _MODULE_NONSTRUCTURAL_KEYS, pointer="/imports"),
        "classes": class_summaries, "functions": function_summaries,
    }
    if "module" in file_data:
        module_name = file_data["module"]
        if not isinstance(module_name, str) or not module_name.strip():
            raise _failure("/module", "nonempty-text", "nonblank string", module_name)
        payload["module"] = module_name

    if language in {"javascript", "typescript"}:
        exports = _json_array(file_data, "exports")
        _validate_string_array(exports, "/exports")
        constants = _record_array(file_data, "constants", required=False)
        module_calls = _record_array(file_data, "module_calls", required=False)
        constant_summaries = []
        for index, record in enumerate(constants):
            pointer = f"/constants/{index}"
            _validate_constant_record(record, pointer)
            constant_summaries.append(_copy_selected_fields(record, _MODULE_CONSTANT_FIELDS, _MODULE_NONSTRUCTURAL_KEYS, pointer))
        payload["exports"] = _structural_copy(exports, _MODULE_NONSTRUCTURAL_KEYS, pointer="/exports")
        payload["constants"] = constant_summaries
        call_summaries = []
        for index, record in enumerate(module_calls):
            pointer = f"/module_calls/{index}"
            _validate_module_call_record(record, pointer)
            call_summaries.append(_copy_selected_fields(record, _MODULE_CALL_FIELDS, _MODULE_NONSTRUCTURAL_KEYS, pointer))
        payload["module_calls"] = call_summaries
    return payload


def _normalize_entity_observation(file_data: Mapping[str, Any] | None, entity_name: str, occurrence: int) -> dict[str, Any]:
    language = _inventory_language(file_data)
    assert isinstance(file_data, Mapping)
    classes = _record_array(file_data, "classes", required=True)
    selected: Mapping[str, Any] | None = None
    seen = 0
    selected_pointer = "/classes"
    for index, record in enumerate(classes):
        name = _record_name(record, f"/classes/{index}")
        if name != entity_name:
            continue
        seen += 1
        if seen == occurrence:
            selected = record
            selected_pointer = f"/classes/{index}"
            break
    if selected is None:
        raise _failure("/classes", "entity-occurrence", "requested named one-based occurrence", classes,
                       reason=UNKNOWN_ENTITY_NOT_FOUND)
    _validate_entity_record(selected, selected_pointer)
    return {"scope": ENTITY_OBSERVATION_SCOPE, "language": language, "name": entity_name,
            "occurrence": occurrence,
            "declaration": _structural_copy(selected, _ENTITY_NONSTRUCTURAL_KEYS, pointer=selected_pointer)}


def _inventory_language(file_data: Mapping[str, Any] | None) -> str:
    if not isinstance(file_data, Mapping):
        raise _failure("", "object-required", "inventory object", file_data)
    language = file_data.get("language", MISSING_VALUE)
    if not isinstance(language, str) or not language:
        raise _failure("/language", "nonempty-text", "nonempty language string", language)
    if language not in _SUPPORTED_OBSERVATION_LANGUAGES:
        raise _failure("/language", "supported-language", "registered observation language", language,
                       reason=UNKNOWN_UNSUPPORTED_LANGUAGE)
    return language


def _record_array(file_data: Mapping[str, Any], field: str, *, required: bool, pointer="") -> list[Mapping[str, Any]]:
    if required and field not in file_data:
        raise _failure(_pointer(pointer, field), "required-field", "array of record objects", MISSING_VALUE)
    return _optional_record_array(file_data, field, pointer)


def _json_array(file_data: Mapping[str, Any], field: str) -> list[Any]:
    value = file_data.get(field, [])
    return require_list(value, error=_failure(_pointer("", field), "array-required", "array", value))


def _record_name(record: Mapping[str, Any], pointer="") -> str:
    value = record.get("name", MISSING_VALUE)
    return require_nonempty_text(value, error=_failure(_pointer(pointer, "name"), "nonempty-text", "nonblank string", value),
                                 reject_control_characters=False)


def _validate_module_entity_record(record: Mapping[str, Any], pointer="") -> None:
    _record_name(record, pointer)
    _validate_optional_strings(record, ("kind", "model_kind", "target"), pointer)
    _validate_optional_booleans(record, ("target_truncated",), pointer)
    if (record.get("target_truncated") or "target_sha256" in record) and not is_valid_sha256(record.get("target_sha256")):
        raise _failure(_pointer(pointer, "target_sha256"), "sha256-required", "complete definition digest", record.get("target_sha256", MISSING_VALUE))
    _validate_optional_string_array(record, "bases", pointer)
    _validate_optional_string_array(record, "type_params", pointer)


def _validate_entity_record(record: Mapping[str, Any], pointer="") -> None:
    _validate_module_entity_record(record, pointer)
    for field in ("decorators", "deriving", "literal_values", "type_params"):
        _validate_optional_string_array(record, field, pointer)
    attributes = _optional_record_array(record, "attributes", pointer)
    for index, attribute in enumerate(attributes):
        position = _pointer(_pointer(pointer, "attributes"), index)
        _record_name(attribute, position)
        _validate_optional_strings(attribute, (
            "alias", "default", "default_factory", "serialization_alias", "tag", "type", "validation_alias", "value",
        ), position)
        for field in ("annotated_metadata", "examples", "literal_values"):
            _validate_optional_json_array(attribute, field, position)
        _validate_optional_mapping(attribute, "constraints", position)
        _validate_optional_record_array(attribute, "unknowns", position)
        _validate_optional_booleans(attribute, ("nullable", "optional", "required"), position)
    methods = _optional_record_array(record, "methods", pointer)
    for index, method in enumerate(methods):
        position = _pointer(_pointer(pointer, "methods"), index)
        _validate_callable_record(method, position)
        validator = _validate_optional_mapping(method, "validator", position)
        if validator is not None:
            _validate_optional_string_array(validator, "fields", _pointer(position, "validator"))
            _validate_optional_mapping(validator, "options", _pointer(position, "validator"))
    model_config = _optional_record_array(record, "model_config", pointer)
    for index, setting in enumerate(model_config):
        position = _pointer(_pointer(pointer, "model_config"), index)
        _record_name(setting, position)
        _validate_optional_record_array(setting, "unknowns", position)


def _validate_callable_record(record: Mapping[str, Any], pointer="") -> None:
    _record_name(record, pointer)
    _validate_optional_strings(record, ("kind", "return_type", "signature"), pointer)
    _validate_optional_booleans(record, ("async", "is_async"), pointer)
    _validate_optional_string_array(record, "decorators", pointer)
    _validate_optional_string_array(record, "type_params", pointer)
    params = _optional_record_array(record, "params", pointer)
    for index, param in enumerate(params):
        position = _pointer(_pointer(pointer, "params"), index)
        if not isinstance(param.get("name"), str):
            raise _failure(_pointer(position, "name"), "string-required", "string", param.get("name", MISSING_VALUE))
        _validate_optional_strings(param, ("default", "kind", "type"), position)
        _validate_optional_booleans(param, ("optional", "rest"), position)


def _validate_import_record(record: Mapping[str, Any], *, language: str, pointer="") -> None:
    module = record.get("module", MISSING_VALUE)
    gap_type = record.get("type")
    gap_reasons = {"dynamic-import": "dynamic-import", "require": "dynamic-require"}
    unresolved_gap = (
        language in {"javascript", "typescript"} and module == ""
        and isinstance(gap_type, str) and gap_type in gap_reasons
        and record.get("resolution") == "unresolved" and record.get("reason") == gap_reasons[gap_type]
        and record.get("name") == "" and type(record.get("line")) is int and record["line"] > 0
        and ("scope" not in record or record["scope"] == "deferred")
    )
    if not isinstance(module, str) or (not module and not unresolved_gap):
        # Refine the location of a near-miss explicit gap without changing
        # its strict acceptance predicate or interpreting it as a dependency.
        if (language in {"javascript", "typescript"} and module == ""
                and isinstance(gap_type, str) and gap_type in gap_reasons):
            for field, expected in (("resolution", "unresolved"), ("reason", gap_reasons[gap_type]), ("name", "")):
                if record.get(field) != expected:
                    raise _failure(_pointer(pointer, field), "explicit-import-gap", f"literal {expected!r}", record.get(field, MISSING_VALUE))
            if type(record.get("line")) is not int or record["line"] <= 0:
                raise _failure(_pointer(pointer, "line"), "positive-integer", "positive integer (not boolean)", record.get("line", MISSING_VALUE))
            if "scope" in record and record["scope"] != "deferred":
                raise _failure(_pointer(pointer, "scope"), "explicit-import-gap", "deferred or omitted", record["scope"])
        raise _failure(_pointer(pointer, "module"), "import-module", "nonempty string or valid explicit unresolved-call gap", module)
    _validate_optional_strings(record, ("name", "type"), pointer)
    if "alias" in record and record["alias"] is not None:
        _validate_optional_strings(record, ("alias",), pointer)
    _validate_optional_booleans(record, ("qualified",), pointer)


def _validate_constant_record(record: Mapping[str, Any], pointer="") -> None:
    _record_name(record, pointer)
    _validate_optional_booleans(record, ("exported",), pointer)


def _validate_module_call_record(record: Mapping[str, Any], pointer="") -> None:
    name = record.get("attr") or record.get("name")
    if not isinstance(name, str) or not name:
        raise _failure(_pointer(pointer, "attr" if record.get("attr") else "name"),
                       "module-call-name", "nonempty attr or name string",
                       record.get("attr" if record.get("attr") else "name", MISSING_VALUE))
    _validate_optional_strings(record, ("attr", "name", "target"), pointer)


def _validate_optional_strings(record: Mapping[str, Any], fields: tuple[str, ...], pointer="") -> None:
    for field in fields:
        if field in record:
            require_string(record[field], error=_failure(_pointer(pointer, field), "string-required", "string", record[field]))


def _validate_optional_booleans(record: Mapping[str, Any], fields: tuple[str, ...], pointer="") -> None:
    for field in fields:
        if field in record:
            require_bool(record[field], error=_failure(_pointer(pointer, field), "boolean-required", "boolean", record[field]))


def _validate_string_array(value: list[Any], pointer="") -> None:
    # Shared scalar validation preserves acceptance, ordering and multiplicity.
    for index, item in enumerate(value):
        require_string(item, error=_failure(_pointer(pointer, index), "string-required", "string", item))


def _validate_optional_string_array(record: Mapping[str, Any], field: str, pointer="") -> None:
    if field in record:
        position = _pointer(pointer, field)
        _validate_string_array(
            require_list(record[field], error=_failure(position, "array-required", "string array", record[field])),
            position,
        )


def _validate_optional_json_array(record: Mapping[str, Any], field: str, pointer="") -> None:
    if field in record:
        require_list(record[field], error=_failure(_pointer(pointer, field), "array-required", "array", record[field]))


def _optional_record_array(record: Mapping[str, Any], field: str, pointer="") -> list[Mapping[str, Any]]:
    position = _pointer(pointer, field)
    value = require_list(record.get(field, []), error=_failure(position, "array-required", "array of record objects", record.get(field, [])))
    return [_record_object(item, _pointer(position, index)) for index, item in enumerate(value)]


def _record_object(value, pointer) -> Mapping[str, Any]:
    return require_mapping(value, error=_failure(pointer, "object-required", "record object", value))


def _validate_optional_record_array(record: Mapping[str, Any], field: str, pointer="") -> None:
    _optional_record_array(record, field, pointer)


def _validate_optional_mapping(record: Mapping[str, Any], field: str, pointer="") -> Mapping[str, Any] | None:
    if field not in record:
        return None
    return require_mapping(record[field], error=_failure(_pointer(pointer, field), "object-required", "object", record[field]))


def _copy_selected_fields(record: Mapping[str, Any], fields: tuple[str, ...], excluded_keys: frozenset[str], pointer="") -> dict[str, Any]:
    return {field: _structural_copy(record[field], excluded_keys, pointer=_pointer(pointer, field))
            for field in fields if field in record}


# Only schema-owned keys are shown in diagnostics. Arbitrary keys may contain
# secrets; their values still participate fully in the original structural hash.
_POINTER_FIELDS = frozenset({
    "name", "kind", "model_kind", "bases", "target", "signature", "params", "return_type", "is_async", "async",
    "decorators", "module", "type", "alias", "qualified", "resolution", "reason", "scope", "attributes", "methods",
    "default", "default_factory", "serialization_alias", "tag", "validation_alias", "value", "annotated_metadata",
    "examples", "literal_values", "constraints", "unknowns", "nullable", "optional", "required", "validator", "fields",
    "options", "model_config", "deriving", "type_params", "exported", "attr", "rest", "target_truncated", "target_sha256",
})


def _structural_copy(value: Any, excluded_keys: frozenset[str], active: set[int] | None = None,
                     *, pointer="", exact=True) -> Any:
    if active is None:
        active = set()
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in active:
            raise _failure(pointer, "acyclic-json", "acyclic JSON value", value, exact=exact)
        active.add(identity)
        try:
            if not all(isinstance(key, str) for key in value):
                raise _failure(pointer, "string-object-keys", "JSON object with string keys", value, exact=exact)
            return {key: _structural_copy(value[key], excluded_keys, active,
                                         pointer=_pointer(pointer, key) if exact and key in _POINTER_FIELDS else pointer,
                                         exact=exact and key in _POINTER_FIELDS)
                    for key in sorted(value) if key not in excluded_keys}
        finally:
            active.remove(identity)
    if isinstance(value, list):
        identity = id(value)
        if identity in active:
            raise _failure(pointer, "acyclic-json", "acyclic JSON value", value, exact=exact)
        active.add(identity)
        try:
            return [_structural_copy(item, excluded_keys, active, pointer=_pointer(pointer, index) if exact else pointer, exact=exact)
                    for index, item in enumerate(value)]
        finally:
            active.remove(identity)
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise _failure(pointer, "finite-json-value", "finite JSON scalar, object or array", value, exact=exact)


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
    *, diagnostic: NormalizationDiagnostic | None = None, entity_name=None, occurrence=None,
) -> ConceptObservationBasis:
    return ConceptObservationBasis(
        scope=scope,
        source_path=source_path,
        extractor_ref=extractor_ref,
        source_content_hash=source_content_hash,
        concept_observation_hash=None,
        unknown_reason=reason,
        normalization_diagnostic=(diagnostic.at_source(source_path, scope, extractor_ref, entity_name, occurrence)
                                  if diagnostic is not None else None),
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
    require_bool(
        inventory_complete,
        error=TypeError("inventory_complete must be a boolean"),
    )


def _validate_scope(scope: object) -> None:
    require_member(
        scope,
        {
            MODULE_OBSERVATION_SCOPE,
            ENTITY_OBSERVATION_SCOPE,
            INFRASTRUCTURE_OBSERVATION_SCOPE,
        },
        error=ValueError(
            "scope must be 'module', 'entity', or 'infrastructure'"
        ),
    )


def _validate_source_path(source_path: object) -> None:
    require_repository_relative_path(
        source_path,
        text_error=ValueError(
            "source_path must be a non-empty repository-relative path"
        ),
        posix_error=ValueError(
            "source_path must be a repository-relative POSIX path"
        ),
        normalized_error=ValueError(
            "source_path must be a normalized repository-relative path"
        ),
    )


def _validate_extractor_ref(extractor_ref: object) -> None:
    parsed = require_string(
        extractor_ref,
        error=ValueError(
            "extractor_ref must be a normalized producer component ID"
        ),
    )
    if _COMPONENT_ID_RE.fullmatch(parsed) is None:
        raise ValueError("extractor_ref must be a normalized producer component ID")


def _validate_hash(value: object, field: str) -> None:
    require_sha256(
        value,
        digest_error=ValueError(
            f"{field} must be 'sha256:' followed by 64 lowercase hexadecimal digits"
        ),
    )


def _validate_entity_coordinate(entity_name: object, occurrence: object) -> None:
    require_nonempty_text(
        entity_name,
        error=ValueError("entity_name must be a non-empty string"),
        reject_control_characters=False,
    )
    require_positive_int(
        occurrence,
        invalid_error=ValueError("occurrence must be a positive integer"),
    )


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
    "INFRASTRUCTURE_OBSERVATION_SCOPE",
    "MODULE_OBSERVATION_SCOPE",
    "SHA256_PATTERN",
    "UNKNOWN_ENTITY_NOT_FOUND",
    "UNKNOWN_INSUFFICIENT_INVENTORY",
    "UNKNOWN_INVALID_INVENTORY",
    "UNKNOWN_UNSUPPORTED_LANGUAGE",
    "ConceptObservationBasis",
    "build_entity_observation_basis",
    "build_infrastructure_observation_basis",
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
