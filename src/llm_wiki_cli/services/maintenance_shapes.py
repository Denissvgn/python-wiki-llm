"""Strict maintenance payload shapes without a JSON Schema runtime dependency."""

from __future__ import annotations
import re
from .knowledge_storage import canonical_bytes, digest
from .validation import require_exact_fields


def canonical_hash(value):
    return digest(canonical_bytes(value))


def _shape_fields(value, **kwargs):
    return require_exact_fields(value, **kwargs)


class MaintenanceError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.field = "maintenance"
        self.message = message
        super().__init__(code + ": " + message)


def require(condition, code, message):
    if not condition:
        raise MaintenanceError(code, message)


def shape_1(value, path):
    require(type(value) is str, "schema-invalid", path + ": invalid string type")
    require(
        re.fullmatch("^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$", value) is not None,
        "schema-invalid",
        path + ": invalid value syntax",
    )


def shape_3(value, path):
    require(type(value) is int, "schema-invalid", path + ": invalid integer type")
    require(value == 1, "schema-invalid", path + ": unsupported constant")


def shape_2(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "implementation_evidence",
            "maintenance_state",
            "ordinary_acknowledgment",
        ),
        required=(
            "implementation_evidence",
            "maintenance_state",
            "ordinary_acknowledgment",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "implementation_evidence" in value:
        shape_3(value["implementation_evidence"], path + ".implementation_evidence")
    if "maintenance_state" in value:
        shape_3(value["maintenance_state"], path + ".maintenance_state")
    if "ordinary_acknowledgment" in value:
        shape_3(value["ordinary_acknowledgment"], path + ".ordinary_acknowledgment")


def shape_4(value, path):
    require(type(value) is int, "schema-invalid", path + ": invalid integer type")
    require(value == 7, "schema-invalid", path + ": unsupported constant")


def shape_5(value, path):
    require(
        value == "llm-wiki-maintenance-adoption/v1",
        "schema-invalid",
        path + ": unsupported constant",
    )


def shape_0(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=("adoption_id", "features", "min_manifest_version", "schema_version"),
        required=("schema_version", "adoption_id", "min_manifest_version", "features"),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "adoption_id" in value:
        shape_1(value["adoption_id"], path + ".adoption_id")
    if "features" in value:
        shape_2(value["features"], path + ".features")
    if "min_manifest_version" in value:
        shape_4(value["min_manifest_version"], path + ".min_manifest_version")
    if "schema_version" in value:
        shape_5(value["schema_version"], path + ".schema_version")


def shape_7(value, path):
    require(type(value) is str, "schema-invalid", path + ": invalid string type")
    require(
        re.fullmatch("^sha256:[0-9a-f]{64}$", value) is not None,
        "schema-invalid",
        path + ": invalid value syntax",
    )


def shape_9(value, path):
    require(type(value) is int, "schema-invalid", path + ": invalid integer type")
    require(value >= 1, "schema-invalid", path + ": number exceeds bound")
    require(value <= 1000000, "schema-invalid", path + ": number exceeds bound")


def shape_10(value, path):
    require(type(value) is str, "schema-invalid", path + ": invalid string type")
    require(len(value) >= 1, "schema-invalid", path + ": length exceeds bound")
    require(len(value) <= 4096, "schema-invalid", path + ": length exceeds bound")


def shape_8(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=("occurrence", "qualified_owner", "source_path"),
        required=("source_path", "qualified_owner", "occurrence"),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "occurrence" in value:
        shape_9(value["occurrence"], path + ".occurrence")
    if "qualified_owner" in value:
        shape_10(value["qualified_owner"], path + ".qualified_owner")
    if "source_path" in value:
        shape_10(value["source_path"], path + ".source_path")


def shape_12(value, path):
    require(value is None, "schema-invalid", path + ": invalid null type")


def shape_11(value, path):
    accepted = False
    for validator in (
        shape_7,
        shape_12,
    ):
        try:
            validator(value, path)
            accepted = True
            break
        except MaintenanceError:
            pass
    require(
        accepted, "schema-invalid", path + ": value does not match any supported shape"
    )


def shape_13(value, path):
    require(
        value in ["module", "class", "callable"],
        "schema-invalid",
        path + ": unsupported enum value",
    )


def shape_15(value, path):
    require(value == "semantic", "schema-invalid", path + ": unsupported constant")


def shape_14(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=("canonical_path", "ownership", "section_locator"),
        required=("canonical_path", "section_locator", "ownership"),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "canonical_path" in value:
        shape_10(value["canonical_path"], path + ".canonical_path")
    if "ownership" in value:
        shape_15(value["ownership"], path + ".ownership")
    if "section_locator" in value:
        shape_10(value["section_locator"], path + ".section_locator")


def shape_6(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "comparison_id",
            "coordinate",
            "documentation_hash",
            "executable_hash",
            "producer_hash",
            "prose_hash",
            "scope",
            "source_hash",
            "target",
        ),
        required=(
            "coordinate",
            "source_hash",
            "executable_hash",
            "documentation_hash",
            "prose_hash",
            "comparison_id",
            "producer_hash",
            "target",
            "scope",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "comparison_id" in value:
        shape_7(value["comparison_id"], path + ".comparison_id")
    if "coordinate" in value:
        shape_8(value["coordinate"], path + ".coordinate")
    if "documentation_hash" in value:
        shape_11(value["documentation_hash"], path + ".documentation_hash")
    if "executable_hash" in value:
        shape_11(value["executable_hash"], path + ".executable_hash")
    if "producer_hash" in value:
        shape_7(value["producer_hash"], path + ".producer_hash")
    if "prose_hash" in value:
        shape_11(value["prose_hash"], path + ".prose_hash")
    if "scope" in value:
        shape_13(value["scope"], path + ".scope")
    if "source_hash" in value:
        shape_11(value["source_hash"], path + ".source_hash")
    if "target" in value:
        shape_14(value["target"], path + ".target")


def shape_17(value, path):
    require(type(value) is str, "schema-invalid", path + ": invalid string type")
    require(len(value) >= 1, "schema-invalid", path + ": length exceeds bound")
    require(len(value) <= 128, "schema-invalid", path + ": length exceeds bound")


def shape_18(value, path):
    require(type(value) is int, "schema-invalid", path + ": invalid integer type")
    require(value >= 0, "schema-invalid", path + ": number exceeds bound")
    require(value <= 1000000000, "schema-invalid", path + ": number exceeds bound")


def shape_23(value, path):
    require(type(value) is bool, "schema-invalid", path + ": invalid boolean type")


def shape_24(value, path):
    require(type(value) is int, "schema-invalid", path + ": invalid integer type")
    require(value >= 0, "schema-invalid", path + ": number exceeds bound")
    require(value <= 128, "schema-invalid", path + ": number exceeds bound")


def shape_22(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "complete_scope",
            "observations_returned",
            "observations_total",
            "truncated",
        ),
        required=(
            "complete_scope",
            "observations_total",
            "observations_returned",
            "truncated",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "complete_scope" in value:
        shape_23(value["complete_scope"], path + ".complete_scope")
    if "observations_returned" in value:
        shape_24(value["observations_returned"], path + ".observations_returned")
    if "observations_total" in value:
        shape_18(value["observations_total"], path + ".observations_total")
    if "truncated" in value:
        shape_23(value["truncated"], path + ".truncated")


def shape_26(value, path):
    require(type(value) is str, "schema-invalid", path + ": invalid string type")
    require(len(value) >= 1, "schema-invalid", path + ": length exceeds bound")
    require(len(value) <= 32, "schema-invalid", path + ": length exceeds bound")


def shape_27(value, path):
    require(type(value) is str, "schema-invalid", path + ": invalid string type")
    require(len(value) >= 1, "schema-invalid", path + ": length exceeds bound")
    require(len(value) <= 64, "schema-invalid", path + ": length exceeds bound")


def shape_25(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "algorithm",
            "analysis_compatibility_hash",
            "language",
            "parser",
            "parser_version",
        ),
        required=(
            "language",
            "algorithm",
            "parser",
            "parser_version",
            "analysis_compatibility_hash",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "algorithm" in value:
        shape_17(value["algorithm"], path + ".algorithm")
    if "analysis_compatibility_hash" in value:
        shape_7(
            value["analysis_compatibility_hash"], path + ".analysis_compatibility_hash"
        )
    if "language" in value:
        shape_26(value["language"], path + ".language")
    if "parser" in value:
        shape_27(value["parser"], path + ".parser")
    if "parser_version" in value:
        shape_27(value["parser_version"], path + ".parser_version")


def shape_28(value, path):
    require(
        value == "llm-wiki-implementation-evidence/v1",
        "schema-invalid",
        path + ": unsupported constant",
    )


def shape_29(value, path):
    require(
        value in ["available", "unavailable"],
        "schema-invalid",
        path + ": unsupported enum value",
    )


def shape_30(value, path):
    require(
        value
        in [
            None,
            "missing-source",
            "unsupported-language",
            "unsupported-syntax",
            "unsupported-producer",
            "ambiguous-owner",
            "legacy-evidence-absent",
            "observation-limit",
            "object-limit",
        ],
        "schema-invalid",
        path + ": unsupported enum value",
    )


def shape_21(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "aggregation",
            "comparison_id",
            "coordinate",
            "documentation_hash",
            "executable_hash",
            "producer",
            "schema_version",
            "scope",
            "source_hash",
            "status",
            "unavailable_reason",
        ),
        required=(
            "schema_version",
            "coordinate",
            "scope",
            "status",
            "producer",
            "comparison_id",
            "source_hash",
            "executable_hash",
            "documentation_hash",
            "aggregation",
            "unavailable_reason",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "aggregation" in value:
        shape_22(value["aggregation"], path + ".aggregation")
    if "comparison_id" in value:
        shape_7(value["comparison_id"], path + ".comparison_id")
    if "coordinate" in value:
        shape_8(value["coordinate"], path + ".coordinate")
    if "documentation_hash" in value:
        shape_11(value["documentation_hash"], path + ".documentation_hash")
    if "executable_hash" in value:
        shape_11(value["executable_hash"], path + ".executable_hash")
    if "producer" in value:
        shape_25(value["producer"], path + ".producer")
    if "schema_version" in value:
        shape_28(value["schema_version"], path + ".schema_version")
    if "scope" in value:
        shape_13(value["scope"], path + ".scope")
    if "source_hash" in value:
        shape_11(value["source_hash"], path + ".source_hash")
    if "status" in value:
        shape_29(value["status"], path + ".status")
    if "unavailable_reason" in value:
        shape_30(value["unavailable_reason"], path + ".unavailable_reason")


def shape_31(value, path):
    require(
        value in ["present", "deleted", "ambiguous"],
        "schema-invalid",
        path + ": unsupported enum value",
    )


def shape_32(value, path):
    require(
        value in ["present", "deleted"],
        "schema-invalid",
        path + ": unsupported enum value",
    )


def shape_20(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "basis",
            "coordinate",
            "implementation",
            "presence",
            "target",
            "target_presence",
        ),
        required=(
            "coordinate",
            "presence",
            "implementation",
            "basis",
            "target",
            "target_presence",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "basis" in value:
        shape_6(value["basis"], path + ".basis")
    if "coordinate" in value:
        shape_8(value["coordinate"], path + ".coordinate")
    if "implementation" in value:
        shape_21(value["implementation"], path + ".implementation")
    if "presence" in value:
        shape_31(value["presence"], path + ".presence")
    if "target" in value:
        shape_14(value["target"], path + ".target")
    if "target_presence" in value:
        shape_32(value["target_presence"], path + ".target_presence")


def shape_19(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    require(len(value) <= 100000, "schema-invalid", path + ": length exceeds bound")
    require(set(()) <= set(value), "schema-invalid", path + ": required field absent")
    for key, item in value.items():
        require(type(key) is str, "schema-invalid", path + ": non-string key")
        shape_20(item, path + "." + key)


def shape_38(value, path):
    require(type(value) is str, "schema-invalid", path + ": invalid string type")
    require(len(value) >= 1, "schema-invalid", path + ": length exceeds bound")
    require(len(value) <= 256, "schema-invalid", path + ": length exceeds bound")


def shape_39(value, path):
    require(
        value == "ordinary-maintenance",
        "schema-invalid",
        path + ": unsupported constant",
    )


def shape_40(value, path):
    require(
        value in ["agent", "human"], "schema-invalid", path + ": unsupported enum value"
    )


def shape_37(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=("actor_id", "authority", "kind"),
        required=("kind", "actor_id", "authority"),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "actor_id" in value:
        shape_38(value["actor_id"], path + ".actor_id")
    if "authority" in value:
        shape_39(value["authority"], path + ".authority")
    if "kind" in value:
        shape_40(value["kind"], path + ".kind")


def shape_41(value, path):
    require(value == "none", "schema-invalid", path + ": unsupported constant")


def shape_36(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "acknowledgment_id",
            "actor",
            "basis",
            "basis_hash",
            "governance_effect",
            "record_id",
        ),
        required=(
            "acknowledgment_id",
            "record_id",
            "basis",
            "basis_hash",
            "actor",
            "governance_effect",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "acknowledgment_id" in value:
        shape_7(value["acknowledgment_id"], path + ".acknowledgment_id")
    if "actor" in value:
        shape_37(value["actor"], path + ".actor")
    if "basis" in value:
        shape_6(value["basis"], path + ".basis")
    if "basis_hash" in value:
        shape_7(value["basis_hash"], path + ".basis_hash")
    if "governance_effect" in value:
        shape_41(value["governance_effect"], path + ".governance_effect")
    if "record_id" in value:
        shape_17(value["record_id"], path + ".record_id")


def shape_35(value, path):
    require(type(value) is list, "schema-invalid", path + ": invalid array type")
    require(len(value) <= 128, "schema-invalid", path + ": length exceeds bound")
    for index, item in enumerate(value):
        shape_36(item, path + "[" + str(index) + "]")


def shape_42(value, path):
    require(type(value) is list, "schema-invalid", path + ": invalid array type")
    require(len(value) >= 1, "schema-invalid", path + ": length exceeds bound")
    require(len(value) <= 1024, "schema-invalid", path + ": length exceeds bound")
    require(
        len({canonical_hash(item) for item in value}) == len(value),
        "schema-invalid",
        path + ": duplicate collection value",
    )
    for index, item in enumerate(value):
        shape_8(item, path + "[" + str(index) + "]")


def shape_45(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=("coordinate", "target"),
        required=("coordinate", "target"),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "coordinate" in value:
        shape_8(value["coordinate"], path + ".coordinate")
    if "target" in value:
        shape_14(value["target"], path + ".target")


def shape_44(value, path):
    require(type(value) is list, "schema-invalid", path + ": invalid array type")
    require(len(value) <= 8, "schema-invalid", path + ": length exceeds bound")
    require(
        len({canonical_hash(item) for item in value}) == len(value),
        "schema-invalid",
        path + ": duplicate collection value",
    )
    for index, item in enumerate(value):
        shape_45(item, path + "[" + str(index) + "]")


def shape_46(value, path):
    accepted = False
    for validator in (
        shape_8,
        shape_12,
    ):
        try:
            validator(value, path)
            accepted = True
            break
        except MaintenanceError:
            pass
    require(
        accepted, "schema-invalid", path + ": value does not match any supported shape"
    )


def shape_47(value, path):
    accepted = False
    for validator in (
        shape_14,
        shape_12,
    ):
        try:
            validator(value, path)
            accepted = True
            break
        except MaintenanceError:
            pass
    require(
        accepted, "schema-invalid", path + ": value does not match any supported shape"
    )


def shape_48(value, path):
    require(
        value in ["resolved", "deleted", "ambiguous"],
        "schema-invalid",
        path + ": unsupported enum value",
    )


def shape_43(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=("candidates", "previous_coordinate", "previous_target", "state"),
        required=("state", "previous_coordinate", "candidates", "previous_target"),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "candidates" in value:
        shape_44(value["candidates"], path + ".candidates")
    if "previous_coordinate" in value:
        shape_46(value["previous_coordinate"], path + ".previous_coordinate")
    if "previous_target" in value:
        shape_47(value["previous_target"], path + ".previous_target")
    if "state" in value:
        shape_48(value["state"], path + ".state")


def shape_49(value, path):
    require(type(value) is list, "schema-invalid", path + ": invalid array type")
    require(len(value) <= 16, "schema-invalid", path + ": length exceeds bound")
    require(
        len({canonical_hash(item) for item in value}) == len(value),
        "schema-invalid",
        path + ": duplicate collection value",
    )
    for index, item in enumerate(value):
        shape_17(item, path + "[" + str(index) + "]")


def shape_50(value, path):
    require(
        value in ["pending", "acknowledged"],
        "schema-invalid",
        path + ": unsupported enum value",
    )


def shape_51(value, path):
    require(type(value) is list, "schema-invalid", path + ": invalid array type")
    require(len(value) >= 1, "schema-invalid", path + ": length exceeds bound")
    require(len(value) <= 1024, "schema-invalid", path + ": length exceeds bound")
    require(
        len({canonical_hash(item) for item in value}) == len(value),
        "schema-invalid",
        path + ": duplicate collection value",
    )
    for index, item in enumerate(value):
        shape_14(item, path + "[" + str(index) + "]")


def shape_34(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "acknowledgment_history",
            "coordinate_history",
            "current_acknowledgment_id",
            "last_present_basis",
            "mapping",
            "reasons",
            "record_id",
            "status",
            "target_history",
        ),
        required=(
            "record_id",
            "coordinate_history",
            "last_present_basis",
            "status",
            "reasons",
            "mapping",
            "acknowledgment_history",
            "current_acknowledgment_id",
            "target_history",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "acknowledgment_history" in value:
        shape_35(value["acknowledgment_history"], path + ".acknowledgment_history")
    if "coordinate_history" in value:
        shape_42(value["coordinate_history"], path + ".coordinate_history")
    if "current_acknowledgment_id" in value:
        shape_11(
            value["current_acknowledgment_id"], path + ".current_acknowledgment_id"
        )
    if "last_present_basis" in value:
        shape_6(value["last_present_basis"], path + ".last_present_basis")
    if "mapping" in value:
        shape_43(value["mapping"], path + ".mapping")
    if "reasons" in value:
        shape_49(value["reasons"], path + ".reasons")
    if "record_id" in value:
        shape_1(value["record_id"], path + ".record_id")
    if "status" in value:
        shape_50(value["status"], path + ".status")
    if "target_history" in value:
        shape_51(value["target_history"], path + ".target_history")


def shape_33(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    require(len(value) <= 100000, "schema-invalid", path + ": length exceeds bound")
    require(set(()) <= set(value), "schema-invalid", path + ": required field absent")
    for key, item in value.items():
        require(type(key) is str, "schema-invalid", path + ": non-string key")
        shape_34(item, path + "." + key)


def shape_52(value, path):
    require(
        value == "llm-wiki-maintenance-state/v1",
        "schema-invalid",
        path + ": unsupported constant",
    )


def shape_16(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "adoption_id",
            "generation",
            "guard_hash",
            "observations",
            "records",
            "schema_version",
        ),
        required=(
            "schema_version",
            "adoption_id",
            "guard_hash",
            "generation",
            "observations",
            "records",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "adoption_id" in value:
        shape_17(value["adoption_id"], path + ".adoption_id")
    if "generation" in value:
        shape_18(value["generation"], path + ".generation")
    if "guard_hash" in value:
        shape_7(value["guard_hash"], path + ".guard_hash")
    if "observations" in value:
        shape_19(value["observations"], path + ".observations")
    if "records" in value:
        shape_33(value["records"], path + ".records")
    if "schema_version" in value:
        shape_52(value["schema_version"], path + ".schema_version")


def shape_54(value, path):
    require(type(value) is list, "schema-invalid", path + ": invalid array type")
    require(len(value) >= 2, "schema-invalid", path + ": length exceeds bound")
    require(len(value) <= 8, "schema-invalid", path + ": length exceeds bound")
    require(
        len({canonical_hash(item) for item in value}) == len(value),
        "schema-invalid",
        path + ": duplicate collection value",
    )
    for index, item in enumerate(value):
        shape_45(item, path + "[" + str(index) + "]")


def shape_55(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "actor",
            "from_basis_hash",
            "from_coordinate",
            "from_target",
            "governance_effect",
            "to_basis_hash",
            "to_coordinate",
            "to_target",
        ),
        required=(
            "actor",
            "from_basis_hash",
            "to_basis_hash",
            "from_coordinate",
            "to_coordinate",
            "governance_effect",
            "from_target",
            "to_target",
        ),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "actor" in value:
        shape_37(value["actor"], path + ".actor")
    if "from_basis_hash" in value:
        shape_7(value["from_basis_hash"], path + ".from_basis_hash")
    if "from_coordinate" in value:
        shape_8(value["from_coordinate"], path + ".from_coordinate")
    if "from_target" in value:
        shape_14(value["from_target"], path + ".from_target")
    if "governance_effect" in value:
        shape_41(value["governance_effect"], path + ".governance_effect")
    if "to_basis_hash" in value:
        shape_7(value["to_basis_hash"], path + ".to_basis_hash")
    if "to_coordinate" in value:
        shape_8(value["to_coordinate"], path + ".to_coordinate")
    if "to_target" in value:
        shape_14(value["to_target"], path + ".to_target")


def shape_56(value, path):
    require(
        value
        in [
            "observe",
            "sync",
            "acknowledge",
            "delete",
            "confirm-move",
            "ambiguous-move",
            "register",
            "delete-target",
        ],
        "schema-invalid",
        path + ": unsupported enum value",
    )


def shape_57(value, path):
    require(
        value == "llm-wiki-maintenance-event/v1",
        "schema-invalid",
        path + ": unsupported constant",
    )


def shape_53(value, path):
    require(type(value) is dict, "schema-invalid", path + ": invalid object type")
    _shape_fields(
        value,
        allowed=(
            "actor",
            "basis",
            "candidates",
            "confirmation",
            "expected_state_hash",
            "kind",
            "observation",
            "record_id",
            "schema_version",
        ),
        required=("schema_version", "kind", "record_id", "expected_state_hash"),
        mapping_error=MaintenanceError("schema-invalid", path + ": expected object"),
        missing_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": missing " + ", ".join(keys)
        ),
        unknown_error=lambda keys: MaintenanceError(
            "schema-invalid", path + ": unexpected " + ", ".join(keys)
        ),
    )
    if "actor" in value:
        shape_37(value["actor"], path + ".actor")
    if "basis" in value:
        shape_6(value["basis"], path + ".basis")
    if "candidates" in value:
        shape_54(value["candidates"], path + ".candidates")
    if "confirmation" in value:
        shape_55(value["confirmation"], path + ".confirmation")
    if "expected_state_hash" in value:
        shape_7(value["expected_state_hash"], path + ".expected_state_hash")
    if "kind" in value:
        shape_56(value["kind"], path + ".kind")
    if "observation" in value:
        shape_20(value["observation"], path + ".observation")
    if "record_id" in value:
        shape_17(value["record_id"], path + ".record_id")
    if "schema_version" in value:
        shape_57(value["schema_version"], path + ".schema_version")


VALIDATORS = {
    "maintenance-adoption-v1": shape_0,
    "maintenance-basis-v1": shape_6,
    "maintenance-state-v1": shape_16,
    "maintenance-event-v1": shape_53,
}
