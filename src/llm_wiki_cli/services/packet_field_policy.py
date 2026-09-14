"""Explicit field/key spaces for the frozen qualified-packet path policy.

This describes classification coverage, not a new wire schema or a sharing
admission policy. Semantic validation remains in context_packet. Open inventory
and legacy enrichment JSON are deliberate delegation boundaries; they retain
the existing structural-path/URI rules for their nested string fields.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class FieldPolicy:
    kind: str = "scalar"
    fields: Mapping[str, "FieldPolicy"] = field(default_factory=lambda: MappingProxyType({}))
    item: "FieldPolicy | None" = None
    key_policy: str = "schema-field"
    reason: str = ""


class UnclassifiedPacketField(ValueError):
    def __init__(self, pointer: tuple[str, ...]):
        self.pointer = pointer
        super().__init__("Packet field has no declared classification policy.")


SCALAR = FieldPolicy()
STRING_CLASSES = (
    "free_text_values", "opaque_values", "portable_identities", "public_uris",
    "repository_relative_paths",
)
STRUCTURAL_PATH_FIELDS = frozenset({"canonical_path", "file", "source_path"})
PUBLIC_URI_FIELDS = frozenset({"mcp_uri"})
REPOSITORY_KEY_SPACES = frozenset({
    ("response", "files"), ("response", "downgraded_files"),
    ("response", "source_priorities"),
})
REPOSITORY_LIST_SPACES = frozenset({("response", "omitted_files")})


def classify_string(pointer: tuple[str, ...]) -> str:
    """Classify a string after its fixed/delegated field space was admitted."""
    if pointer[:-1] in REPOSITORY_LIST_SPACES or pointer[-1:] and pointer[-1] in STRUCTURAL_PATH_FIELDS:
        return "repository_relative_paths"
    if pointer[-1:] and pointer[-1] in PUBLIC_URI_FIELDS:
        return "public_uris"
    if pointer == ("basis", "repository", "identity"):
        return "portable_identities"
    if pointer[:2] in {("delivery", "warnings"), ("response", "warnings"), ("delivery", "limitations")}:
        return "free_text_values"
    return "opaque_values"


def _record(names: str = "", **children: FieldPolicy) -> FieldPolicy:
    return FieldPolicy("record", MappingProxyType({**dict.fromkeys(names.split(), SCALAR), **children}))


def _list(item: FieldPolicy = SCALAR) -> FieldPolicy:
    return FieldPolicy("list", item=item)


def _mapping(item: FieldPolicy, *, keys: str) -> FieldPolicy:
    return FieldPolicy("mapping", item=item, key_policy=keys)


def _json(reason: str) -> FieldPolicy:
    return FieldPolicy("open-json", key_policy="opaque-source-key", reason=reason)


FILTERS = _record(
    "language module symbol entrypoint surface freshness evidence relationship_kind "
    "relationship_origin relationship_resolution relationship_direction"
)
BOUND = _record("total returned truncated")
SOURCE_BOUNDS = _record(files=BOUND)
FRESHNESS = _record("state reason live_comparison_performed hint")
ENDPOINT = _record(
    "kind target_class locator uid canonical_path source_path external_uri resource "
    "symbol normalized_target coordinate_state"
)
COVERAGE = _record(
    "analyzer observed emitted omitted limit truncated",
    limitations=_list(), limitation_bounds=BOUND,
)
CONCEPT = _record(
    "locator uid concept_kind title page_kind page_id canonical_path mcp_uri "
    "source_path role origin evidence verification lifecycle", freshness=FRESHNESS,
)
PAGE = _record("kind id title canonical_path source_path role mcp_uri")
RELATIONSHIP = _record(
    "graph kind direction origin resolution key",
    **{"from": ENDPOINT}, target=ENDPOINT,
    evidence=_record("state observed unique emitted omitted"), coverage=COVERAGE,
)
KNOWLEDGE = _record(
    "mode status availability reason selected freshness_evaluated",
    bounds=_record(concepts=BOUND, pages=BOUND, relationships=BOUND),
    fallback=_record("used reason", evidence=_list()),
    selection=_record(
        concepts=_list(CONCEPT), pages=_list(PAGE), relationships=_list(RELATIONSHIP),
        relationship_coverage=_record("availability reason schema_version", coverage=_list(COVERAGE)),
    ),
)
BASIS = _record(
    source_snapshot=_record("identity input_count"),
    repository=_record("state reason identity evaluated_revision working_tree"),
    knowledge=_record("state availability reason envelope_hash knowledge_index_hash surface_index_hash governance_hash"),
    generator=_record("component version context_protocol policy_digest"),
    freshness=_record(
        "state evaluated disclosure reason concept_count evaluation_digest",
        counts=_record("current nonsemantic-source-change source-changed source-missing basis-incompatible unknown"),
    ),
)
RECEIPT = _record(
    "policy_version policy_digest quarantined final_scan",
    field_counts=_record("free_text_values opaque_values portable_identities public_uris repository_relative_paths"),
    finding_counts=_record("accepted redacted rejected"), limitations=_list(),
)


def packet_policy(version: int) -> FieldPolicy:
    if version not in {1, 2}:
        raise ValueError("Unsupported qualified-packet field policy version.")
    request = _record(
        "protocol budget_tokens format prefer_fresh" + (" knowledge_mode" if version == 2 else ""),
        focus=_list(), filters=FILTERS,
    )
    response = _record(
        "protocol ok budget_tokens used_tokens format prefer_fresh truncated content",
        focus=_list(), filters=FILTERS, bounds=SOURCE_BOUNDS,
        warnings=_list(), omitted_files=_list(),
        files=_mapping(_json("Additive built-in source inventory contract."), keys="repository-relative-path"),
        downgraded_files=_mapping(SCALAR, keys="repository-relative-path"),
        source_priorities=_mapping(SCALAR, keys="repository-relative-path"),
        graphs=_json("Legacy source-query result contracts."),
        surface=_json("Registry-backed legacy surface-query result contract."),
        typed_graph=_json("Typed-graph query contract, including qualified relationship kinds."),
        knowledge=KNOWLEDGE if version == 2 else _json("Legacy native-knowledge enrichment contract."),
        ranking_policy=(
            _record("requested policy scope budget_pressure applied reason")
            if version == 2 else _record("name prefer_fresh scope freshness_evaluated budget_pressure applied filters_stale_content")
        ),
    )
    return _record(
        "schema_version packet_id", assurance=_record("level scope"),
        request=request, response=response, basis=BASIS,
        delivery=_record("truncated", bounds=SOURCE_BOUNDS, warnings=_list(), limitations=_list()),
        path_policy=RECEIPT,
    )


POLICIES = MappingProxyType({version: packet_policy(version) for version in (1, 2)})


def validate_field_coverage(value: Mapping[str, Any]) -> None:
    request = value.get("request")
    version = 2 if (
        value.get("schema_version") == "llm-wiki-qualified-context-packet/v2"
        or isinstance(request, Mapping) and request.get("protocol") == "llm-wiki-context/v2"
    ) else 1

    def visit(item: Any, policy: FieldPolicy, pointer: tuple[str, ...]) -> None:
        if policy.kind == "open-json":
            return  # Explicit additive namespace; value/path checks still run.
        if isinstance(item, Mapping):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise UnclassifiedPacketField(pointer)
                if policy.kind == "mapping":
                    child_policy = policy.item
                else:
                    child_policy = policy.fields.get(key)
                if child_policy is None:
                    raise UnclassifiedPacketField((*pointer, key))
                visit(child, child_policy, (*pointer, key))
        elif isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                if policy.item is None:
                    raise UnclassifiedPacketField(pointer)
                visit(child, policy.item, (*pointer, str(index)))

    visit(value, POLICIES[version], ())


def field_policy_manifest() -> dict[str, Any]:
    """Enumerate every fixed field and deliberately open key space for review."""
    versions: dict[str, list[dict[str, str]]] = {}
    for version, policy in POLICIES.items():
        entries: list[dict[str, str]] = []
        def visit(node: FieldPolicy, pointer: str) -> None:
            entry = {
                "pointer": pointer, "kind": node.kind, "key_policy": node.key_policy,
                "string_class": classify_string(tuple(pointer.split("/")[1:])),
            }
            if node.reason:
                entry["reason"] = node.reason
            entries.append(entry)
            for key, child in sorted(node.fields.items()):
                visit(child, f"{pointer}/{key}")
            if node.item is not None:
                visit(node.item, f"{pointer}/*")
        visit(policy, "")
        versions[f"llm-wiki-qualified-context-packet/v{version}"] = entries
    return {
        "schema_version": "llm-wiki-packet-field-declarations/v1",
        "receipt_excludes": ["schema_version", "packet_id", "path_policy"],
        "delegated_string_rules": {
            "structural_path_fields": sorted(STRUCTURAL_PATH_FIELDS),
            "public_uri_fields": sorted(PUBLIC_URI_FIELDS),
            "other_strings": "opaque_values",
        },
        "versions": versions,
    }
