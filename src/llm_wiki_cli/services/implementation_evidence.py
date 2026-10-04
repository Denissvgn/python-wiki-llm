"""Pure, bounded persistence and comparison of captured implementation syntax.

These observations describe syntax within one declaration scope. They do not
establish dependency, runtime behavior, or authored documentation correctness.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import re
from types import MappingProxyType

from . import python_implementation as pi

IMPLEMENTATION_KEY = "llm-wiki/implementation"
DECLARATIONS_KEY = "llm-wiki/implementation-declarations"
DECLARATIONS_SCHEMA = "llm-wiki-implementation-declarations/v1"
SCOPES = frozenset({"module", "class", "callable"})
ANALYSIS_SCOPES = frozenset({"snapshot", "selected-source", "full-inventory"})
UNAVAILABLE_REASONS = frozenset(
    {
        "missing-source",
        "unsupported-language",
        "unsupported-syntax",
        "unsupported-producer",
        "ambiguous-owner",
        "legacy-evidence-absent",
        "observation-limit",
        "object-limit",
    }
)
REASONS = UNAVAILABLE_REASONS | frozenset(
    {
        "matching-executable-syntax",
        "executable-syntax-changed",
        "live-evaluation-not-performed",
        "source-not-captured",
        "owner-not-observed",
        "producer-incompatible",
        "scope-incompatible",
        "implementation-unavailable",
        "identical-source-observation-mismatch",
        "invalid-captured-evidence",
    }
)
LIMITATIONS = (
    "captured-executable-syntax-only",
    "dependencies-and-runtime-behavior-not-evaluated",
    "authored-prose-correctness-not-evaluated",
)
SUMMARY_FIELDS = frozenset(
    {
        "state",
        "reason",
        "scope",
        "analysis_scope",
        "live_comparison_performed",
        "source_changed",
        "documentation_changed",
        "truncated",
        "limitations",
    }
)
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _object(value, fields, label):
    if not isinstance(value, Mapping) or set(value) != set(fields):
        raise ValueError(f"{label}: fields must match the closed contract")
    return dict(value)


def _int(value, maximum, label, minimum=0):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{label}: invalid integer")
    return value


def _bool(value, label):
    if type(value) is not bool:
        raise ValueError(f"{label}: must be boolean")
    return value


def _hash(value, label, nullable=False):
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise ValueError(f"{label}: invalid SHA-256 commitment")
    return value


def _copy(value):
    # This also refuses NaN, non-JSON values and invalid UTF-8 scalars.
    return json.loads(pi.canonical_bytes(value))


def _freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value):
    if isinstance(value, Mapping):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


def validate_coordinate(value, scope=None):
    row = _object(value, {"source_path", "qualified_owner", "occurrence"}, "coordinate")
    _int(row["occurrence"], 1_000_000, "coordinate.occurrence", 1)
    if not isinstance(row["source_path"], str) or not isinstance(
        row["qualified_owner"], str
    ):
        raise ValueError("coordinate: path and owner must be strings")
    inferred = scope or (
        "module" if row["qualified_owner"] == "__module__" else "callable"
    )
    if inferred not in SCOPES or not pi.coordinate_supported(row, inferred):
        raise ValueError("coordinate: unsupported path, owner or selector size")
    return row


def coordinate_key(value):
    row = validate_coordinate(value)
    return f"{row['source_path']}:{row['qualified_owner']}#{row['occurrence']}"


def _supported_producer(row):
    return (
        row["language"] == "python"
        and row["algorithm"] == pi.ALGORITHM
        and row["parser"] == "cpython-ast"
        and re.fullmatch(
            r"3\.(?:10|11|12|13|14)\.(?:0|[1-9][0-9]*)", row["parser_version"]
        )
        is not None
    )


def validate_implementation_evidence(value) -> dict:
    row = _object(
        value,
        {
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
        },
        "implementation",
    )
    if (
        row["schema_version"] != pi.EVIDENCE_SCHEMA
        or row["scope"] not in SCOPES
        or row["status"] not in {"available", "unavailable"}
    ):
        raise ValueError("implementation: unsupported schema, scope or status")
    row["coordinate"] = validate_coordinate(row["coordinate"], row["scope"])
    descriptor = _object(
        row["producer"],
        {
            "language",
            "algorithm",
            "parser",
            "parser_version",
            "analysis_compatibility_hash",
        },
        "producer",
    )
    for name, maximum in (
        ("language", 32),
        ("algorithm", 128),
        ("parser", 64),
        ("parser_version", 64),
    ):
        text = descriptor[name]
        if (
            not isinstance(text, str)
            or not 0 < len(text) <= maximum
            or any(ord(c) < 32 for c in text)
        ):
            raise ValueError("producer: invalid descriptor")
    _hash(
        descriptor["analysis_compatibility_hash"],
        "producer.analysis_compatibility_hash",
    )
    row["producer"] = descriptor
    if row["comparison_id"] != pi.comparison_id(descriptor):
        raise ValueError("comparison_id: differs from producer identity")
    for key in ("source_hash", "executable_hash", "documentation_hash"):
        _hash(row[key], key, True)
    aggregation = _object(
        row["aggregation"],
        {"complete_scope", "observations_total", "observations_returned", "truncated"},
        "aggregation",
    )
    _bool(aggregation["complete_scope"], "aggregation.complete_scope")
    _bool(aggregation["truncated"], "aggregation.truncated")
    total = _int(aggregation["observations_total"], 1_000_000_000, "aggregation.total")
    returned = _int(
        aggregation["observations_returned"],
        pi.MAX_OBSERVATIONS,
        "aggregation.returned",
    )
    if returned > total or aggregation["truncated"] != (returned < total):
        raise ValueError("aggregation: inconsistent count or truncation")
    row["aggregation"] = aggregation
    reason = row["unavailable_reason"]
    if row["status"] == "available":
        if (
            not _supported_producer(descriptor)
            or reason is not None
            or any(
                row[k] is None
                for k in ("source_hash", "executable_hash", "documentation_hash")
            )
            or not aggregation["complete_scope"]
        ):
            raise ValueError(
                "implementation: available evidence requires supported complete non-null commitments"
            )
    elif (
        reason not in UNAVAILABLE_REASONS
        or row["executable_hash"] is not None
        or row["documentation_hash"] is not None
        or aggregation["complete_scope"]
    ):
        raise ValueError(
            "implementation: unavailable evidence cannot assert syntax digests"
        )
    if reason == "missing-source" and row["source_hash"] is not None:
        raise ValueError("implementation: missing source cannot assert a source hash")
    if len(pi.canonical_bytes(row)) > pi.MAX_OBJECT_BYTES:
        raise ValueError("implementation: object exceeds 64 KiB")
    return _copy(row)


def _owner(value):
    row = _object(value, {"coordinate", "scope"}, "owner")
    if row["scope"] not in {"module", "class"}:
        raise ValueError(
            "owner: declaration collections belong to module or class concepts"
        )
    row["coordinate"] = validate_coordinate(row["coordinate"], row["scope"])
    return row


def _bounds(value):
    row = _object(
        value, {"total", "returned", "truncated", "omitted", "reason"}, "bounds"
    )
    returned = _int(row["returned"], pi.MAX_OBSERVATIONS, "bounds.returned")
    _bool(row["truncated"], "bounds.truncated")
    if row["reason"] is not None and row["reason"] not in UNAVAILABLE_REASONS:
        raise ValueError("bounds: unknown reason")
    if row["total"] is None:
        if row["omitted"] is not None or returned != 0 or row["reason"] is None:
            raise ValueError(
                "bounds: unknown owner counts require an empty explicit gap"
            )
        if row["truncated"] != (row["reason"] in {"observation-limit", "object-limit"}):
            raise ValueError("bounds: unknown bounded owner must disclose truncation")
        return row
    total = _int(row["total"], 1_000_000_000, "bounds.total")
    _int(row["omitted"], 1_000_000_000, "bounds.omitted")
    if (
        returned > total
        or row["omitted"] != total - returned
        or row["truncated"] != (returned < total)
    ):
        raise ValueError("bounds: count or truncation differs")
    if row["truncated"] and row["reason"] not in {"observation-limit", "object-limit"}:
        raise ValueError("bounds: omitted observations require a bounded reason")
    return row


def _row(value):
    row = _object(value, {"evidence", "line", "lineage"}, "observation")
    row["evidence"] = validate_implementation_evidence(row["evidence"])
    if row["line"] is not None:
        _int(row["line"], 2**63 - 1, "observation.line", 1)
    if (
        not isinstance(row["lineage"], (list, tuple))
        or len(row["lineage"]) > pi.MAX_OBSERVATIONS
    ):
        raise ValueError("observation.lineage: requires bounded array")
    lineage = []
    seen = {coordinate_key(row["evidence"]["coordinate"])}
    source = row["evidence"]["coordinate"]["source_path"]
    owner = row["evidence"]["coordinate"]["qualified_owner"]
    for item in row["lineage"]:
        parent = _object(item, {"coordinate", "scope"}, "lineage")
        parent["coordinate"] = validate_coordinate(
            parent["coordinate"], parent["scope"]
        )
        key = coordinate_key(parent["coordinate"])
        name = parent["coordinate"]["qualified_owner"]
        if (
            key in seen
            or parent["coordinate"]["source_path"] != source
            or (name != "__module__" and not owner.startswith(name + "."))
        ):
            raise ValueError("lineage: duplicate, cross-source or unrelated ancestor")
        if not lineage and name != "__module__":
            raise ValueError("lineage: first ancestor must be module")
        if (
            lineage
            and not name.startswith(lineage[-1]["coordinate"]["qualified_owner"] + ".")
            and lineage[-1]["scope"] != "module"
        ):
            raise ValueError("lineage: ancestors must be ordered")
        seen.add(key)
        lineage.append(parent)
    if (row["evidence"]["scope"] == "module") != (not lineage):
        raise ValueError(
            "lineage: module has no parents and declarations require module ancestor"
        )
    row["lineage"] = lineage
    return row


def validate_implementation_declarations(value) -> dict:
    result = _object(
        value, {"schema_version", "owner", "observations", "bounds"}, "declarations"
    )
    if result["schema_version"] != DECLARATIONS_SCHEMA:
        raise ValueError("declarations: unsupported schema")
    owner = result["owner"] = _owner(result["owner"])
    bounds = result["bounds"] = _bounds(result["bounds"])
    if (
        not isinstance(result["observations"], (tuple, list))
        or len(result["observations"]) != bounds["returned"]
    ):
        raise ValueError("declarations: returned count differs from rows")
    rows = result["observations"] = [_row(v) for v in result["observations"]]
    keys = set()
    owner_key = coordinate_key(owner["coordinate"])
    for row in rows:
        evidence = row["evidence"]
        key = coordinate_key(evidence["coordinate"])
        if (
            key in keys
            or evidence["coordinate"]["source_path"]
            != owner["coordinate"]["source_path"]
        ):
            raise ValueError("declarations: duplicate or cross-source declaration")
        keys.add(key)
        if owner["scope"] == "class" and not any(p == owner for p in row["lineage"]):
            raise ValueError(
                "declarations: class descendants require exact parent occurrence"
            )
        if owner["scope"] == "module" and evidence["scope"] == "module":
            raise ValueError("declarations: primary module must not be duplicated")
        if key == owner_key:
            raise ValueError("declarations: primary owner must not be duplicated")
    if rows:
        first = rows[0]["evidence"]
        if any(
            r["evidence"]["source_hash"] != first["source_hash"]
            or r["evidence"]["producer"] != first["producer"]
            for r in rows
        ):
            raise ValueError("declarations: source and producer must share one capture")
    if len(pi.canonical_bytes(result)) > pi.MAX_OBJECT_BYTES:
        raise ValueError("declarations: object exceeds 64 KiB")
    return _copy(result)


def analysis_hash_from_producer(producer) -> str | None:
    """Reconstruct the recorded issuer identity from committed component records."""
    from .analysis_compatibility import component_record

    tool = producer.get("tool") if isinstance(producer, Mapping) else producer.tool
    extractors = (
        producer.get("extractors", ())
        if isinstance(producer, Mapping)
        else producer.extractors
    )
    components = [tool, *extractors]
    selected = {}
    for component in components:
        name = (
            component.get("id")
            if isinstance(component, Mapping)
            else component.component_id
        )
        if name in {"agent-wiki-cli", "llm-wiki/extractor/python"}:
            record = component_record(component)
            if record is None or name in selected:
                return None
            selected[name] = {k: record[k] for k in ("implementation", "runtime")}
    if set(selected) != {"agent-wiki-cli", "llm-wiki/extractor/python"}:
        return None
    return (
        "sha256:"
        + hashlib.sha256(
            pi.canonical_bytes(
                {
                    "schema_version": "llm-wiki-implementation-analysis/v1",
                    "components": selected,
                    "configuration": pi.CONFIGURATION,
                }
            )
        ).hexdigest()
    )


def _concept_parts(concept):
    if isinstance(concept, Mapping):
        return concept.get("extensions", {}), concept["document"], concept["locator"]
    return (
        concept.extensions,
        {
            "page_kind": concept.document.page_kind.value,
            "canonical_path": concept.document.canonical_path,
        },
        concept.locator,
    )


def validate_concept_implementation(
    concept, *, producer=None, source_content_hashes=None, mapping=None
) -> dict:
    extensions, document, _ = _concept_parts(concept)
    primary = (
        validate_implementation_evidence(extensions[IMPLEMENTATION_KEY])
        if IMPLEMENTATION_KEY in extensions
        else None
    )
    supplemental = (
        validate_implementation_declarations(extensions[DECLARATIONS_KEY])
        if DECLARATIONS_KEY in extensions
        else None
    )
    if primary is None and supplemental is None:
        return {}
    if primary is not None:
        owner = {"coordinate": primary["coordinate"], "scope": primary["scope"]}
    else:
        assert supplemental is not None
        owner = supplemental["owner"]
    kind = document["page_kind"]
    if kind not in {"modules", "entities"} or owner["scope"] != (
        "module" if kind == "modules" else "class"
    ):
        raise ValueError(
            "implementation: evidence must match documented module/class scope"
        )
    if supplemental and supplemental["owner"] != owner:
        raise ValueError("implementation: supplemental owner differs from primary")
    if mapping is not None:

        def attr(key):
            return (
                mapping.get(key)
                if isinstance(mapping, Mapping)
                else getattr(mapping, key)
            )

        if attr("scope") != ("module" if kind == "modules" else "entity"):
            raise ValueError("implementation: mapped declaration scope differs")
        expected = {
            "source_path": attr("source_path"),
            "qualified_owner": "__module__"
            if kind == "modules"
            else attr("entity_name"),
            "occurrence": 1 if kind == "modules" else attr("occurrence"),
        }
        if owner["coordinate"] != expected:
            raise ValueError("implementation: exact mapped source owner differs")
    rows = ([primary] if primary else []) + (
        [r["evidence"] for r in supplemental["observations"]] if supplemental else []
    )
    if primary and any(
        r["source_hash"] != primary["source_hash"]
        or r["producer"] != primary["producer"]
        for r in rows
    ):
        raise ValueError("implementation: primary and declarations disagree on capture")
    detail_rows = supplemental["observations"] if supplemental else ()
    _validate_detail_lineages(
        {coordinate_key(r["coordinate"]): r for r in rows},
        {coordinate_key(r["evidence"]["coordinate"]): r for r in detail_rows},
        owner=owner,
    )
    expected_analysis = (
        analysis_hash_from_producer(producer) if producer is not None else None
    )
    for row in rows:
        if producer is not None and (
            expected_analysis is None
            or row["producer"]["analysis_compatibility_hash"] != expected_analysis
        ):
            raise ValueError(
                "implementation: producer does not match enclosing captured analysis"
            )
        if source_content_hashes is not None:
            expected = source_content_hashes.get(row["coordinate"]["source_path"])
            if row["source_hash"] != expected or (
                expected is None and row["unavailable_reason"] != "missing-source"
            ):
                raise ValueError(
                    "implementation: source hash differs from current committed source"
                )
    return {
        **({IMPLEMENTATION_KEY: primary} if primary else {}),
        **({DECLARATIONS_KEY: supplemental} if supplemental else {}),
    }


def _validate_detail_lineages(observations, details, *, owner=None, complete=True):
    for row in details.values():
        for index, parent in enumerate(row["lineage"]):
            key = coordinate_key(parent["coordinate"])
            observed = observations.get(key)
            if observed is None:
                if parent["scope"] == "module":
                    # Canonical __module__#1 identifies the captured file even
                    # when a selected class read excludes its module page.
                    continue
                if not complete:
                    continue
                if owner and owner["scope"] == "class":
                    owner_index = next(
                        i for i, item in enumerate(row["lineage"]) if item == owner
                    )
                    if index < owner_index:
                        # Ancestors above a selected class are outside that
                        # projection; exact class occurrence owns descendants.
                        continue
                raise ValueError(
                    "lineage: non-module ancestor is absent from captured declarations"
                )
            if observed["scope"] != parent["scope"]:
                raise ValueError(
                    "lineage: parent scope differs from captured declaration"
                )
            if key in details and details[key]["lineage"] != row["lineage"][:index]:
                raise ValueError(
                    "lineage: parent ancestry differs from captured declaration"
                )


def validate_implementation_collection(concepts, *, producer=None, complete=True):
    """Crosscheck redundant primaries and detail ancestry in a full collection."""
    observations, details = {}, {}
    for concept in concepts:
        validated = validate_concept_implementation(concept, producer=producer)
        primary = validated.get(IMPLEMENTATION_KEY)
        supplemental = validated.get(DECLARATIONS_KEY)
        rows = ([primary] if primary else []) + (
            [r["evidence"] for r in supplemental["observations"]]
            if supplemental
            else []
        )
        for row in rows:
            key = coordinate_key(row["coordinate"])
            if key in observations and observations[key] != row:
                raise ValueError(
                    "implementation: contradictory observations for one captured coordinate"
                )
            observations[key] = row
        for row in supplemental["observations"] if supplemental else ():
            key = coordinate_key(row["evidence"]["coordinate"])
            if key in details and details[key] != row:
                raise ValueError("implementation: contradictory copied line or lineage")
            details[key] = row
    _validate_detail_lineages(observations, details, complete=complete)


def project_concept_implementations(
    observations, mappings, *, producer, source_content_hashes
) -> dict:
    """Project exact already captured owners after manifest mapping finalization."""
    if observations is None:
        return {}
    if (
        not isinstance(observations, Mapping)
        or observations.get("schema_version") != pi.SCHEMA
        or not isinstance(observations.get("files"), Mapping)
    ):
        raise ValueError("implementation capture: unsupported envelope")
    expected_analysis = analysis_hash_from_producer(producer)
    result = {}
    for path, mapping in mappings.items():
        captured = observations["files"].get(mapping.source_path)
        if captured is None:
            continue
        if not isinstance(captured, Mapping) or captured.get(
            "source_hash"
        ) != source_content_hashes.get(mapping.source_path):
            raise ValueError("implementation capture: source commitment differs")
        if mapping.scope not in {"module", "entity"}:
            continue
        owner = {
            "coordinate": {
                "source_path": mapping.source_path,
                "qualified_owner": "__module__"
                if mapping.scope == "module"
                else mapping.entity_name,
                "occurrence": 1 if mapping.scope == "module" else mapping.occurrence,
            },
            "scope": "module" if mapping.scope == "module" else "class",
        }
        try:
            _owner(owner)
        except ValueError:
            # A mapping with an unknown occurrence is never guessed.
            continue
        rows = [_row(v) for v in captured.get("observations", ())]
        if (
            len(rows) > pi.MAX_OBSERVATIONS
            or len(pi.canonical_bytes(captured)) > pi.MAX_OBJECT_BYTES
        ):
            raise ValueError("implementation capture: exceeds bounds")
        for row in rows:
            e = row["evidence"]
            if (
                e["source_hash"] != captured["source_hash"]
                or e["producer"] != captured.get("producer")
                or e["producer"]["analysis_compatibility_hash"] != expected_analysis
            ):
                raise ValueError(
                    "implementation capture: unqualified source or producer"
                )
        matched = [
            r
            for r in rows
            if r["evidence"]["coordinate"] == owner["coordinate"]
            and r["evidence"]["scope"] == owner["scope"]
        ]
        if len(matched) > 1:
            raise ValueError("implementation capture: ambiguous owner")
        primary = matched[0]["evidence"] if matched else None
        selected = [
            r
            for r in rows
            if r not in matched
            and (owner["scope"] == "module" or owner in r["lineage"])
        ]
        if primary is None:
            if selected:
                raise ValueError(
                    "implementation capture: descendants cannot precede an unretained owner"
                )
            total = omitted = None
            if captured.get("reason") in UNAVAILABLE_REASONS:
                reason = captured["reason"]
            elif captured.get("bounds", {}).get("truncated"):
                reason = (
                    "observation-limit"
                    if captured.get("bounds", {}).get("returned") == pi.MAX_OBSERVATIONS
                    else "object-limit"
                )
            else:
                reason = captured.get("reason") or "ambiguous-owner"
            truncated = reason in {"observation-limit", "object-limit"}
        else:
            total = max(primary["aggregation"]["observations_total"], len(selected))
            omitted = total - len(selected)
            truncated = omitted > 0
            reason = captured.get("reason")
            if truncated:
                reason = (
                    "object-limit"
                    if captured.get("bounds", {}).get("reason")
                    == "object-or-observation-limit"
                    else "observation-limit"
                )
        supplement = {
            "schema_version": DECLARATIONS_SCHEMA,
            "owner": owner,
            "observations": selected,
            "bounds": {
                "total": total,
                "returned": len(selected),
                "truncated": truncated,
                "omitted": omitted,
                "reason": reason,
            },
        }
        while len(pi.canonical_bytes(supplement)) > pi.MAX_OBJECT_BYTES and selected:
            assert total is not None
            selected.pop()
            supplement["bounds"].update(
                returned=len(selected),
                omitted=total - len(selected),
                truncated=True,
                reason="object-limit",
            )
        exts = {DECLARATIONS_KEY: validate_implementation_declarations(supplement)}
        if primary:
            exts[IMPLEMENTATION_KEY] = primary
        result[path] = exts
    return result


@dataclass(frozen=True)
class ImplementationComparison:
    state: str
    reason: str
    coordinate: Mapping | None = None
    scope: str | None = None
    analysis_scope: str = "snapshot"
    live_comparison_performed: bool = False
    source_changed: bool | None = None
    documentation_changed: bool | None = None
    recorded: Mapping | None = None
    live: Mapping | None = None
    truncated: bool = False
    limitations: tuple[str, ...] = LIMITATIONS

    def __post_init__(self):
        for name in ("coordinate", "recorded", "live"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))
        object.__setattr__(self, "limitations", tuple(self.limitations))
        validate_implementation_summary({k: getattr(self, k) for k in SUMMARY_FIELDS})

    def to_payload(self) -> dict:
        return {name: _thaw(getattr(self, name)) for name in self.__dataclass_fields__}


@dataclass(frozen=True)
class ImplementationReport:
    by_locator: Mapping[str, ImplementationComparison]
    by_coordinate: Mapping[str, ImplementationComparison]
    analysis_scope: str = "snapshot"

    def __post_init__(self):
        object.__setattr__(self, "by_locator", MappingProxyType(dict(self.by_locator)))
        object.__setattr__(
            self, "by_coordinate", MappingProxyType(dict(self.by_coordinate))
        )

    def to_payload(self) -> dict:
        return {
            "analysis_scope": self.analysis_scope,
            "by_locator": {k: v.to_payload() for k, v in self.by_locator.items()},
            "by_coordinate": {k: v.to_payload() for k, v in self.by_coordinate.items()},
        }


def validate_implementation_summary(value: object) -> dict:
    row = _object(value, SUMMARY_FIELDS, "implementation summary")
    if (
        row["state"] not in {"changed", "unchanged", "unavailable"}
        or row["reason"] not in REASONS
        or row["scope"] not in SCOPES | {None}
        or row["analysis_scope"] not in ANALYSIS_SCOPES
    ):
        raise ValueError("implementation summary: unsupported state, reason or scope")
    for key in ("live_comparison_performed", "truncated"):
        _bool(row[key], key)
    for key in ("source_changed", "documentation_changed"):
        if row[key] is not None:
            _bool(row[key], key)
    if (
        not isinstance(row["limitations"], (list, tuple))
        or tuple(row["limitations"]) != LIMITATIONS
    ):
        raise ValueError("implementation summary: fixed limitations required")
    if row["state"] != "unavailable":
        expected = (
            "matching-executable-syntax"
            if row["state"] == "unchanged"
            else "executable-syntax-changed"
        )
        if (
            row["reason"] != expected
            or row["analysis_scope"] == "snapshot"
            or not row["live_comparison_performed"]
            or row["scope"] is None
            or row["source_changed"] is None
            or row["documentation_changed"] is None
        ):
            raise ValueError(
                "implementation summary: verdict requires qualified live comparison"
            )
        if (row["state"] == "changed" or row["documentation_changed"]) and row[
            "source_changed"
        ] is not True:
            raise ValueError(
                "implementation summary: changed syntax/docstrings require changed source bytes"
            )
    elif (
        row["reason"] in {"matching-executable-syntax", "executable-syntax-changed"}
        or row["live_comparison_performed"]
        or row["documentation_changed"] is not None
    ):
        raise ValueError(
            "implementation summary: unavailable cannot assert executable comparison"
        )
    if row["analysis_scope"] == "snapshot" and (
        row["reason"] != "live-evaluation-not-performed"
        or row["source_changed"] is not None
        or row["documentation_changed"] is not None
    ):
        raise ValueError("implementation summary: snapshot has no live verdict")
    row["limitations"] = list(row["limitations"])
    return _copy(row)


def compact_implementation_summary(value: ImplementationComparison | Mapping) -> dict:
    payload = (
        value.to_payload() if isinstance(value, ImplementationComparison) else value
    )
    return validate_implementation_summary({k: payload[k] for k in SUMMARY_FIELDS})


def _analysis_scope(value):
    value = "selected-source" if value == "selected" else value
    if value not in ANALYSIS_SCOPES:
        raise ValueError("unsupported implementation analysis scope")
    return value


def compare_implementation_observations(
    recorded,
    live,
    *,
    analysis_scope="snapshot",
    coordinate=None,
    scope=None,
    expected_analysis_hash=None,
    source_captured=True,
    source_present=True,
    truncated=False,
) -> ImplementationComparison:
    analysis_scope = _analysis_scope(analysis_scope)
    for name, flag in (
        ("source_captured", source_captured),
        ("source_present", source_present),
        ("truncated", truncated),
    ):
        _bool(flag, name)
    left = validate_implementation_evidence(recorded) if recorded is not None else None
    truncated = truncated or bool(left and left["aggregation"]["truncated"])
    selected_coord = left["coordinate"] if left else coordinate
    selected_scope = left["scope"] if left else scope

    def unavailable(reason, right=None, source_changed=None):
        return ImplementationComparison(
            "unavailable",
            reason,
            selected_coord,
            selected_scope,
            analysis_scope,
            False,
            source_changed,
            None,
            left,
            right,
            truncated,
        )

    if analysis_scope == "snapshot":
        return unavailable("live-evaluation-not-performed")
    if left is None:
        return unavailable("legacy-evidence-absent")
    if not source_captured:
        return unavailable("source-not-captured")
    if not source_present:
        return unavailable("missing-source")
    if live is None:
        return unavailable("owner-not-observed")
    try:
        right = validate_implementation_evidence(live)
    except (ValueError, TypeError, UnicodeError):
        return unavailable("invalid-captured-evidence")
    truncated = truncated or right["aggregation"]["truncated"]
    changed = (
        (left["source_hash"] != right["source_hash"])
        if left["source_hash"] is not None and right["source_hash"] is not None
        else None
    )
    if left["scope"] != right["scope"]:
        return unavailable("scope-incompatible", right, changed)
    if left["coordinate"] != right["coordinate"]:
        return unavailable(
            "ambiguous-owner",
            right,
            changed
            if left["coordinate"]["source_path"] == right["coordinate"]["source_path"]
            else None,
        )
    if left["status"] != "available" or right["status"] != "available":
        return unavailable("implementation-unavailable", right, changed)
    if (
        not isinstance(expected_analysis_hash, str)
        or not _HASH.fullmatch(expected_analysis_hash)
        or left["comparison_id"] != right["comparison_id"]
        or right["producer"]["analysis_compatibility_hash"] != expected_analysis_hash
    ):
        return unavailable("producer-incompatible", right, changed)
    executable_changed = left["executable_hash"] != right["executable_hash"]
    doc_changed = left["documentation_hash"] != right["documentation_hash"]
    if not changed and (executable_changed or doc_changed):
        return unavailable("identical-source-observation-mismatch", right, changed)
    return ImplementationComparison(
        "changed" if executable_changed else "unchanged",
        "executable-syntax-changed"
        if executable_changed
        else "matching-executable-syntax",
        selected_coord,
        selected_scope,
        analysis_scope,
        True,
        changed,
        doc_changed,
        left,
        right,
        truncated
        or left["aggregation"]["truncated"]
        or right["aggregation"]["truncated"],
    )


def compare_knowledge_implementation(
    knowledge_or_concepts,
    implementation_observations,
    *,
    analysis_scope="snapshot",
    captured_paths=None,
    source_content_hashes=None,
    analysis_compatibility_hash=None,
    missing_source_paths=None,
) -> ImplementationReport:
    analysis_scope = _analysis_scope(analysis_scope)
    concepts = tuple(
        knowledge_or_concepts.concepts
        if hasattr(knowledge_or_concepts, "concepts")
        else knowledge_or_concepts
    )
    validate_implementation_collection(concepts, complete=False)
    files = (
        implementation_observations.get("files", {})
        if isinstance(implementation_observations, Mapping)
        and implementation_observations.get("schema_version") == pi.SCHEMA
        else {}
    )
    captured = set(captured_paths) if captured_paths is not None else set(files)
    missing = set(missing_source_paths or ())
    by_locator, by_coordinate = {}, {}
    for concept in concepts:
        extensions, _, locator = _concept_parts(concept)
        validated = validate_concept_implementation(concept)
        primary = validated.get(IMPLEMENTATION_KEY)
        supplemental = validated.get(DECLARATIONS_KEY)
        rows = ([primary] if primary else []) + (
            [r["evidence"] for r in supplemental["observations"]]
            if supplemental
            else []
        )
        if not rows:
            gap_reason = supplemental["bounds"]["reason"] if supplemental else None
            gap_owner = supplemental["owner"] if supplemental else None
            gap_truncated = bool(supplemental and supplemental["bounds"]["truncated"])
            if gap_reason and gap_owner is not None:
                gap = ImplementationComparison(
                    "unavailable",
                    "live-evaluation-not-performed"
                    if analysis_scope == "snapshot"
                    else gap_reason,
                    gap_owner["coordinate"],
                    gap_owner["scope"],
                    analysis_scope,
                    truncated=gap_truncated,
                )
                by_locator[locator] = gap
                by_coordinate[coordinate_key(gap_owner["coordinate"])] = gap
            else:
                by_locator[locator] = compare_implementation_observations(
                    None, None, analysis_scope=analysis_scope
                )
        for recorded in rows:
            source = recorded["coordinate"]["source_path"]
            capture = files.get(source, {})
            live = None
            raw_rows = (
                capture.get("observations", ()) if isinstance(capture, Mapping) else ()
            )
            candidates = [
                r.get("evidence")
                for r in raw_rows
                if isinstance(r, Mapping)
                and isinstance(r.get("evidence"), Mapping)
                and r["evidence"].get("coordinate") == recorded["coordinate"]
                and r["evidence"].get("scope") == recorded["scope"]
            ]
            if len(candidates) == 1:
                live = candidates[0]
            result = compare_implementation_observations(
                recorded,
                live,
                analysis_scope=analysis_scope,
                expected_analysis_hash=analysis_compatibility_hash,
                source_captured=source in captured,
                source_present=source not in missing,
                truncated=bool(supplemental and supplemental["bounds"]["truncated"]),
            )
            if (
                analysis_scope != "snapshot"
                and source in captured
                and source not in missing
            ):
                if len(candidates) > 1:
                    result = ImplementationComparison(
                        "unavailable",
                        "ambiguous-owner",
                        recorded["coordinate"],
                        recorded["scope"],
                        analysis_scope,
                        recorded=recorded,
                    )
                elif live is None:
                    gap_reason = (
                        capture.get("reason") if isinstance(capture, Mapping) else None
                    )
                    live_bounded = bool(
                        isinstance(capture, Mapping)
                        and capture.get("bounds", {}).get("truncated")
                    )
                    if gap_reason in UNAVAILABLE_REASONS or live_bounded:
                        result = ImplementationComparison(
                            "unavailable",
                            gap_reason
                            if gap_reason in UNAVAILABLE_REASONS
                            else "observation-limit",
                            recorded["coordinate"],
                            recorded["scope"],
                            analysis_scope,
                            recorded=recorded,
                            truncated=live_bounded or result.truncated,
                        )
            if (
                analysis_scope != "snapshot"
                and live is not None
                and (
                    capture.get("source_hash") != live.get("source_hash")
                    or capture.get("producer") != live.get("producer")
                    or (
                        source_content_hashes is not None
                        and source_content_hashes.get(source) != live.get("source_hash")
                    )
                )
            ):
                result = ImplementationComparison(
                    "unavailable",
                    "invalid-captured-evidence",
                    recorded["coordinate"],
                    recorded["scope"],
                    analysis_scope,
                    recorded=recorded,
                )
            key = coordinate_key(recorded["coordinate"])
            if key in by_coordinate and by_coordinate[key].recorded != result.recorded:
                raise ValueError(
                    "implementation: contradictory recorded observations for one coordinate"
                )
            by_coordinate[key] = result
            if recorded is primary:
                by_locator[locator] = result
        if primary is None and locator not in by_locator:
            by_locator[locator] = compare_implementation_observations(
                None, None, analysis_scope=analysis_scope
            )
    return ImplementationReport(by_locator, by_coordinate, analysis_scope)


def select_implementation_comparison(
    report: ImplementationReport, selector: str
) -> ImplementationComparison:
    if selector in report.by_locator:
        return report.by_locator[selector]
    if selector in report.by_coordinate:
        return report.by_coordinate[selector]
    matches = [
        value
        for key, value in report.by_coordinate.items()
        if key.rsplit("#", 1)[0] == selector
        or (value.coordinate and value.coordinate["qualified_owner"] == selector)
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches and ":" in selector:
        selected_source = selector.rsplit(":", 1)[0]
        bounded = [
            v
            for v in report.by_coordinate.values()
            if v.truncated
            and v.coordinate
            and v.coordinate["source_path"] == selected_source
        ]
        if bounded:
            reason = (
                "live-evaluation-not-performed"
                if report.analysis_scope == "snapshot"
                else "observation-limit"
            )
            return ImplementationComparison(
                "unavailable",
                reason,
                analysis_scope=report.analysis_scope,
                truncated=True,
            )
    reason = (
        "live-evaluation-not-performed"
        if report.analysis_scope == "snapshot"
        else ("ambiguous-owner" if matches else "owner-not-observed")
    )
    return ImplementationComparison(
        "unavailable", reason, analysis_scope=report.analysis_scope
    )


def validate_implementation_comparison(value: object) -> dict:
    """Validate a report's shape/consistency, never attest its capture issuer.

    Live issuer and read-scope bindings remain the receiving boundary's duty.
    In particular, a claimed producer in ``live`` is not an independent basis.
    """
    result = _object(
        value,
        SUMMARY_FIELDS | {"coordinate", "recorded", "live"},
        "implementation comparison",
    )
    summary = validate_implementation_summary({k: result[k] for k in SUMMARY_FIELDS})
    result.update(summary)
    coordinate = result["coordinate"]
    if coordinate is not None:
        if result["scope"] is None:
            raise ValueError("implementation comparison: coordinate requires a scope")
        result["coordinate"] = validate_coordinate(coordinate, result["scope"])
    left = (
        validate_implementation_evidence(result["recorded"])
        if result["recorded"] is not None
        else None
    )
    right = (
        validate_implementation_evidence(result["live"])
        if result["live"] is not None
        else None
    )
    result.update(recorded=left, live=right)
    if (
        any(
            observation and observation["aggregation"]["truncated"]
            for observation in (left, right)
        )
        and not result["truncated"]
    ):
        raise ValueError(
            "implementation comparison: included observation truncation must be disclosed"
        )
    if left is not None and (
        result["coordinate"] != left["coordinate"] or result["scope"] != left["scope"]
    ):
        raise ValueError(
            "implementation comparison: selected coordinate/scope differs from recorded evidence"
        )
    if result["analysis_scope"] == "snapshot":
        if right is not None:
            raise ValueError(
                "implementation comparison: snapshot cannot carry a live observation"
            )
        return _copy(result)
    if right is not None:
        coordinate_matches = result["coordinate"] == right["coordinate"]
        scope_matches = result["scope"] == right["scope"]
        if not scope_matches and result["reason"] != "scope-incompatible":
            raise ValueError(
                "implementation comparison: live scope differs without explicit incompatible reason"
            )
        if not coordinate_matches and result["reason"] not in {
            "ambiguous-owner",
            "scope-incompatible",
        }:
            raise ValueError(
                "implementation comparison: live coordinate differs without explicit ambiguity"
            )
        if result["reason"] == "scope-incompatible" and scope_matches:
            raise ValueError(
                "implementation comparison: scope incompatibility requires different scopes"
            )
    if result["state"] in {"changed", "unchanged"}:
        if (
            left is None
            or right is None
            or left["status"] != "available"
            or right["status"] != "available"
            or left["comparison_id"] != right["comparison_id"]
        ):
            raise ValueError(
                "implementation comparison: verdict requires compatible available observations"
            )
        source_changed = left["source_hash"] != right["source_hash"]
        executable_changed = left["executable_hash"] != right["executable_hash"]
        doc_changed = left["documentation_hash"] != right["documentation_hash"]
        if not source_changed and (executable_changed or doc_changed):
            raise ValueError(
                "implementation comparison: identical source has contradictory syntax commitments"
            )
        if (
            result["state"] != ("changed" if executable_changed else "unchanged")
            or result["source_changed"] != source_changed
            or result["documentation_changed"] != doc_changed
        ):
            raise ValueError(
                "implementation comparison: verdict or hash deltas differ from observations"
            )
    elif left is not None and right is not None:
        same_source_owner = (
            left["coordinate"]["source_path"] == right["coordinate"]["source_path"]
        )
        source_delta = (
            (left["source_hash"] != right["source_hash"])
            if same_source_owner
            and left["source_hash"] is not None
            and right["source_hash"] is not None
            else None
        )
        if result["source_changed"] != source_delta:
            raise ValueError(
                "implementation comparison: unavailable raw source delta differs"
            )
        contradiction = (
            left["status"] == right["status"] == "available"
            and left["coordinate"] == right["coordinate"]
            and left["scope"] == right["scope"]
            and left["comparison_id"] == right["comparison_id"]
            and source_delta is False
            and (
                left["executable_hash"] != right["executable_hash"]
                or left["documentation_hash"] != right["documentation_hash"]
            )
        )
        if (
            result["reason"] == "identical-source-observation-mismatch"
            and not contradiction
        ):
            raise ValueError(
                "implementation comparison: contradiction diagnostic requires contradictory commitments"
            )
        if (
            contradiction
            and result["reason"] != "identical-source-observation-mismatch"
        ):
            raise ValueError(
                "implementation comparison: contradictory commitments require explicit diagnostic"
            )
    elif result["source_changed"] is not None:
        raise ValueError(
            "implementation comparison: raw source delta requires two observations"
        )
    return _copy(result)
