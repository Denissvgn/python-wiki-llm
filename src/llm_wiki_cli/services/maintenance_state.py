"""Pure durable maintenance authority and explicit source/prose review transitions.

All inputs come from a caller-owned captured basis. This service performs no
filesystem I/O, parsing, generation, storage adoption, or human governance
mutation. The operation owner supplies the implementation validator and holds
the shared writer lock around capture and manifest-last publication.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import re
from typing import Any
from urllib.parse import quote, unquote
from uuid import UUID, uuid4

from .knowledge_storage import canonical_bytes, digest
from .validation import require_repository_relative_path
from .maintenance_shapes import MaintenanceError, VALIDATORS, require


def canonical_hash(value: object) -> str:
    """Canonical maintenance commitments include the storage protocol LF."""
    return digest(canonical_bytes(value))


LIMITS = {
    "observations_per_object": 128,
    "object_bytes": 65_536,
    "pending_records": 100_000,
    "state_bytes": 67_108_864,
    "source_selector_bytes": 4_096,
    "indexed_catalog_bytes": 65_536,
}

EVENT_FIELDS = {
    "register": {"observation"},
    "observe": {"observation"},
    "sync": set(),
    "acknowledge": {"actor", "basis"},
    "delete": {"observation"},
    "delete-target": {"observation"},
    "confirm-move": {"observation", "confirmation"},
    "ambiguous-move": {"observation", "candidates"},
}


def new_identity() -> str:
    """Allocate once in the operation owner; persist and replay this identity."""
    return str(uuid4())


def _identity(value: str) -> None:
    try:
        parsed = UUID(value)
    except (ValueError, TypeError, AttributeError) as exc:
        raise MaintenanceError(
            "identity-invalid", "identity must be canonical UUIDv4"
        ) from exc
    require(
        parsed.version == 4 and str(parsed) == value,
        "identity-invalid",
        "identity must be canonical UUIDv4",
    )


def _portable(value: Any, field: str) -> str:
    error = MaintenanceError(
        "coordinate-invalid", field + " must be portable and relative"
    )
    return require_repository_relative_path(
        value,
        text_error=error,
        posix_error=error,
        normalized_error=error,
        absolute_error=error,
        separator_error=error,
        control_error=error,
        reject_delete_character=True,
        portability_error=error,
    )


def _finite(value: Any, depth: int = 0, active: set[int] | None = None) -> None:
    require(depth <= 64, "state-limit", "maintenance value nesting exceeds 64")
    if value is None or type(value) in {str, bool, int}:
        return
    require(
        type(value) in {dict, list},
        "schema-invalid",
        "maintenance accepts only strict JSON types",
    )
    active = set() if active is None else active
    require(id(value) not in active, "schema-invalid", "maintenance value is cyclic")
    active.add(id(value))
    if type(value) is dict:
        require(
            all(type(key) is str for key in value),
            "schema-invalid",
            "maintenance keys must be strings",
        )
        children = value.values()
    else:
        children = value
    for child in children:
        _finite(child, depth + 1, active)
    active.remove(id(value))


class MaintenanceCore:
    """Pure transitions with the installed implementation contract as authority."""

    def __init__(self, evidence_validator: Callable[[dict[str, Any]], object]):
        if not callable(evidence_validator):
            raise TypeError(
                "evidence_validator must be the implementation contract validator"
            )
        self.evidence_validator = evidence_validator

    def validate_schema(self, name: str, value: Any) -> None:
        _finite(value)
        VALIDATORS[name](value, name)
        if name == "maintenance-event-v1":
            require(
                set(value)
                == {"schema_version", "kind", "record_id", "expected_state_hash"}
                | EVENT_FIELDS[value["kind"]],
                "schema-invalid",
                "event fields do not match its explicit operation",
            )
            _identity(value["record_id"])
        elif name == "maintenance-adoption-v1":
            _identity(value["adoption_id"])
        elif name == "maintenance-state-v1":
            _identity(value["adoption_id"])
            for record_id in value["records"]:
                _identity(record_id)

    def validate_evidence(self, value: dict[str, Any]) -> None:
        _finite(value)
        require(
            len(canonical_bytes(value)) <= LIMITS["object_bytes"],
            "object-limit",
            "implementation evidence exceeds 64 KiB",
        )
        try:
            self.evidence_validator(value)
        except (TypeError, ValueError) as exc:
            raise MaintenanceError("implementation-invalid", str(exc)) from exc
        self._coordinate(value["coordinate"])

    def _coordinate(self, value: dict[str, Any]) -> None:
        require(
            type(value) is dict
            and set(value) == {"source_path", "qualified_owner", "occurrence"},
            "coordinate-invalid",
            "declaration coordinate has invalid fields",
        )
        source = _portable(value["source_path"], "source path")
        owner = value["qualified_owner"]
        require(
            type(owner) is str
            and bool(owner)
            and all(part.isidentifier() for part in owner.split("."))
            and not any(ord(c) < 32 or ord(c) == 127 for c in owner),
            "coordinate-invalid",
            "qualified owner must be explicit nonempty text",
        )
        require(
            type(value["occurrence"]) is int and 1 <= value["occurrence"] <= 1_000_000,
            "coordinate-invalid",
            "occurrence must be a bounded positive integer",
        )
        require(
            len(f"{source}:{owner}#{value['occurrence']}".encode("utf-8"))
            <= LIMITS["source_selector_bytes"],
            "selector-limit",
            "complete declaration selector exceeds 4 KiB",
        )

    def _target(self, target: dict[str, Any]) -> None:
        require(
            type(target) is dict
            and set(target) == {"canonical_path", "section_locator", "ownership"},
            "target-invalid",
            "semantic target has invalid fields",
        )
        path = _portable(target["canonical_path"], "target page")
        locator = target["section_locator"]
        require(
            path.endswith(".md")
            and type(locator) is str
            and target["ownership"] == "semantic",
            "target-invalid",
            "target must be a captured semantic Markdown section",
        )
        prefix = "llm-wiki://" + quote(path[:-3], safe="/-._~") + "#section/"
        require(
            locator.startswith(prefix), "target-invalid", "target binds another page"
        )
        for component in locator[len(prefix) :].split("/"):
            title, mark, ordinal = component.rpartition("~")
            require(
                bool(mark and title)
                and re.fullmatch(r"[1-9][0-9]*", ordinal) is not None
                and quote(unquote(title), safe="-._~") == title,
                "target-invalid",
                "section locator has invalid heading or sibling occurrence",
            )
        require(
            max(len(path.encode("utf-8")), len(locator.encode("utf-8")))
            <= LIMITS["source_selector_bytes"],
            "selector-limit",
            "semantic target exceeds 4 KiB",
        )

    def basis_for(
        self,
        evidence: dict[str, Any],
        prose_hash: str | None,
        target: dict[str, Any] | None,
    ) -> dict[str, Any]:
        self.validate_evidence(evidence)
        result = {
            "coordinate": deepcopy(evidence["coordinate"]),
            "scope": evidence["scope"],
            "target": deepcopy(target),
            **{
                name: evidence[name]
                for name in (
                    "source_hash",
                    "executable_hash",
                    "documentation_hash",
                    "comparison_id",
                )
            },
            "producer_hash": canonical_hash(evidence["producer"]),
            "prose_hash": prose_hash,
        }
        self.validate_schema("maintenance-basis-v1", result)
        self._target(result["target"])
        return result

    def observation(
        self,
        evidence: dict[str, Any],
        prose_hash: str | None,
        *,
        presence="present",
        target: dict[str, Any] | None,
        target_presence="present",
    ) -> dict[str, Any]:
        selected = target
        return {
            "coordinate": deepcopy(evidence["coordinate"]),
            "target": deepcopy(selected),
            "presence": presence,
            "target_presence": target_presence,
            "implementation": deepcopy(evidence),
            "basis": self.basis_for(evidence, prose_hash, selected),
        }

    def _validate_observation(self, value: dict[str, Any]) -> None:
        self.validate_evidence(value["implementation"])
        self._target(value["target"])
        if value["target_presence"] == "deleted":
            require(
                value["basis"]["prose_hash"] is None,
                "target-binding",
                "missing semantic target cannot carry a current prose digest",
            )
        require(
            value["target"] == value["basis"]["target"],
            "target-binding",
            "observed page/section and byte basis differ",
        )
        require(
            value["coordinate"]
            == value["implementation"]["coordinate"]
            == value["basis"]["coordinate"],
            "coordinate-binding",
            "observation coordinates disagree",
        )
        require(
            value["basis"]
            == self.basis_for(
                value["implementation"], value["basis"]["prose_hash"], value["target"]
            ),
            "basis-binding",
            "source/executable/documentation/producer bindings disagree",
        )
        if value["presence"] != "present":
            require(
                value["implementation"]["status"] == "unavailable",
                "evidence-invalid",
                "missing/ambiguous owner cannot claim available evidence",
            )
        if value["presence"] == "deleted":
            require(
                value["implementation"]["unavailable_reason"] == "missing-source"
                and value["implementation"]["source_hash"] is None,
                "evidence-invalid",
                "deleted owner must retain an explicit missing-source basis",
            )
        if value["presence"] == "ambiguous":
            require(
                value["implementation"]["unavailable_reason"] == "ambiguous-owner",
                "evidence-invalid",
                "ambiguous mapping must not hide its unknown declaration owner",
            )

    def validate_state(self, state: dict[str, Any]) -> None:
        self.validate_schema("maintenance-state-v1", state)
        require(
            len(canonical_bytes(state)) <= LIMITS["state_bytes"],
            "state-limit",
            "canonical maintenance state exceeds 64 MiB",
        )
        require(
            set(state["records"]) == set(state["observations"]),
            "owner-missing",
            "record and observation owners differ",
        )
        require(
            sum((record["status"] == "pending" for record in state["records"].values()))
            <= LIMITS["pending_records"],
            "record-limit",
            "pending record limit exceeded",
        )
        coordinates = set()
        shared_implementation: dict[str, Any] = {}
        source_presence: dict[str, set[str]] = {}
        for record_id, record in state["records"].items():
            current = state["observations"][record_id]
            self._validate_observation(current)
            require(
                record_id == record["record_id"],
                "record-binding",
                "opaque record id differs from owner key",
            )
            for coordinate in record["coordinate_history"]:
                self._coordinate(coordinate)
            for target in record["target_history"]:
                self._target(target)
            require(
                current["coordinate"] in record["coordinate_history"],
                "coordinate-binding",
                "current coordinate missing from retained history",
            )
            require(
                current["target"] in record["target_history"],
                "target-binding",
                "current semantic target missing from retained history",
            )
            coordinate_key = canonical_hash(current["coordinate"])
            states = source_presence.setdefault(coordinate_key, set())
            states.add(current["presence"])
            require(
                not ("deleted" in states and states != {"deleted"}),
                "partial-source-deletion",
                "source deletion cannot leave another section's declaration observation present or ambiguous",
            )
            key = canonical_hash(
                {"coordinate": current["coordinate"], "target": current["target"]}
            )
            require(
                key not in coordinates,
                "coordinate-collision",
                "declaration and semantic target pair belongs to two records",
            )
            coordinates.add(key)
            if current["presence"] == "present":
                if coordinate_key in shared_implementation:
                    require(
                        shared_implementation[coordinate_key]
                        == current["implementation"],
                        "shared-implementation-mismatch",
                        "sections of one declaration cannot invent different source execution observations",
                    )
                shared_implementation[coordinate_key] = current["implementation"]
            self._coordinate(record["last_present_basis"]["coordinate"])
            self._target(record["last_present_basis"]["target"])
            mapping = record["mapping"]
            if mapping["previous_target"] is not None:
                self._target(mapping["previous_target"])
            expected_mapping = {
                "present": "resolved",
                "deleted": "deleted",
                "ambiguous": "ambiguous",
            }[current["presence"]]
            require(
                mapping["state"] == expected_mapping,
                "mapping-invalid",
                "presence and mapping state disagree",
            )
            require(
                (len(mapping["candidates"]) >= 2) == (mapping["state"] == "ambiguous"),
                "mapping-invalid",
                "ambiguous mapping must retain candidates",
            )
            for candidate in mapping["candidates"]:
                self._coordinate(candidate["coordinate"])
                self._target(candidate["target"])
            if current["presence"] == "present":
                require(
                    record["last_present_basis"] == current["basis"],
                    "basis-binding",
                    "last present basis differs from current present observation",
                )
            acknowledgments = {}
            for ack in record["acknowledgment_history"]:
                self._target(ack["basis"]["target"])
                require(
                    ack["basis"]["target"] in record["target_history"]
                    and ack["basis"]["coordinate"] in record["coordinate_history"],
                    "ack-binding",
                    "historical acknowledgment belongs to another declaration/semantic section",
                )
                require(
                    all(
                        (
                            ack["basis"][name] is not None
                            for name in (
                                "source_hash",
                                "executable_hash",
                                "documentation_hash",
                                "prose_hash",
                            )
                        )
                    ),
                    "ack-binding",
                    "historical acknowledgment lacks its captured source/prose basis",
                )
                require(
                    ack["record_id"] == record_id
                    and ack["basis_hash"] == canonical_hash(ack["basis"]),
                    "ack-binding",
                    "acknowledgment binds the wrong record or byte basis",
                )
                payload = {k: v for k, v in ack.items() if k != "acknowledgment_id"}
                require(
                    ack["acknowledgment_id"] == canonical_hash(payload),
                    "ack-binding",
                    "acknowledgment identity is corrupt",
                )
                require(
                    ack["acknowledgment_id"] not in acknowledgments,
                    "ack-binding",
                    "duplicate acknowledgment history",
                )
                acknowledgments[ack["acknowledgment_id"]] = ack
            if record["status"] == "acknowledged":
                selected = acknowledgments.get(record["current_acknowledgment_id"])
                require(
                    current["presence"] == "present"
                    and current["target_presence"] == "present"
                    and (current["implementation"]["status"] == "available")
                    and (current["basis"]["prose_hash"] is not None)
                    and (selected is not None)
                    and (selected["basis"] == current["basis"])
                    and (not record["reasons"]),
                    "stale-acknowledgment",
                    "acknowledged state lacks its exact current known source/prose basis",
                )
            else:
                require(
                    record["current_acknowledgment_id"] is None
                    and bool(record["reasons"]),
                    "pending-invalid",
                    "pending work cannot lose its reason or retain an active acknowledgment",
                )

    def initial_state(
        self, guard: dict[str, Any], observations: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Explicit adoption bootstrap records pending/unreviewed, never historical approval."""
        self.validate_schema("maintenance-adoption-v1", guard)
        records = {}
        for record_id, value in observations.items():
            require(
                value["presence"] == "present",
                "bootstrap-invalid",
                "bootstrap must start from a captured present observation",
            )
            records[record_id] = {
                "record_id": record_id,
                "coordinate_history": [deepcopy(value["coordinate"])],
                "target_history": [deepcopy(value["target"])],
                "last_present_basis": deepcopy(value["basis"]),
                "status": "pending",
                "reasons": ["unreviewed"],
                "mapping": {
                    "state": "resolved",
                    "previous_coordinate": None,
                    "previous_target": None,
                    "candidates": [],
                },
                "acknowledgment_history": [],
                "current_acknowledgment_id": None,
            }
        state = {
            "schema_version": "llm-wiki-maintenance-state/v1",
            "adoption_id": guard["adoption_id"],
            "guard_hash": canonical_hash(guard),
            "generation": 0,
            "observations": deepcopy(observations),
            "records": records,
        }
        self.validate_state(state)
        return state

    def _ack(
        self, record_id: str, actor: dict[str, Any], basis: dict[str, Any]
    ) -> dict[str, Any]:
        value = {
            "record_id": record_id,
            "actor": deepcopy(actor),
            "basis": deepcopy(basis),
            "basis_hash": canonical_hash(basis),
            "governance_effect": "none",
        }
        return {"acknowledgment_id": canonical_hash(value), **value}

    def transition(
        self,
        state: dict[str, Any],
        event: dict[str, Any],
        current_basis: dict[str, Any],
    ) -> dict[str, Any]:
        """Pure maintenance transition. The caller supplies independently captured current basis."""
        self.validate_state(state)
        self.validate_schema("maintenance-event-v1", event)
        self.validate_schema("maintenance-basis-v1", current_basis)
        record_id, kind = (event["record_id"], event["kind"])
        if kind == "register":
            require(
                event["expected_state_hash"] == canonical_hash(state),
                "state-changed",
                "captured maintenance owner changed before registration",
            )
            require(
                record_id not in state["records"],
                "record-collision",
                "opaque record id is already owned, including retained deleted work",
            )
            incoming = event["observation"]
            self._validate_observation(incoming)
            require(
                incoming["presence"] == "present"
                and incoming["target_presence"] == "present"
                and (incoming["basis"] == current_basis)
                and (current_basis["source_hash"] is not None)
                and (current_basis["prose_hash"] is not None),
                "registration-invalid",
                "registration requires a captured present declaration and semantic prose target",
            )
            for existing in state["observations"].values():
                if existing["coordinate"] == incoming["coordinate"]:
                    require(
                        existing["target"] != incoming["target"],
                        "coordinate-collision",
                        "declaration and semantic target already have an owner",
                    )
                    if existing["presence"] == "present":
                        require(
                            existing["implementation"] == incoming["implementation"],
                            "shared-implementation-mismatch",
                            "new section cannot invent another source execution observation",
                        )
            created = self.initial_state(
                {
                    "schema_version": "llm-wiki-maintenance-adoption/v1",
                    "adoption_id": state["adoption_id"],
                    "min_manifest_version": 7,
                    "features": {
                        "implementation_evidence": 1,
                        "maintenance_state": 1,
                        "ordinary_acknowledgment": 1,
                    },
                },
                {record_id: incoming},
            )["records"][record_id]
            result = deepcopy(state)
            result["records"][record_id] = created
            result["observations"][record_id] = deepcopy(incoming)
            result["generation"] += 1
            self.validate_state(result)
            return result
        require(
            record_id in state["records"], "owner-missing", "event has no durable owner"
        )
        record, current = (
            state["records"][record_id],
            state["observations"][record_id],
        )
        acknowledgment: dict[str, Any] = {}
        if kind == "acknowledge":
            require(
                current_basis == current["basis"] == event["basis"]
                and current["presence"] == "present"
                and (current["target_presence"] == "present")
                and (current["implementation"]["status"] == "available")
                and all(
                    (
                        current_basis[name] is not None
                        for name in (
                            "source_hash",
                            "executable_hash",
                            "documentation_hash",
                            "prose_hash",
                        )
                    )
                ),
                "stale-acknowledgment",
                "acknowledgment requires exact current source/prose/executable/producer bindings",
            )
            acknowledgment = self._ack(record_id, event["actor"], current_basis)
            if (
                record["status"] == "acknowledged"
                and record["current_acknowledgment_id"]
                == acknowledgment["acknowledgment_id"]
            ):
                return deepcopy(state)
        require(
            event["expected_state_hash"] == canonical_hash(state),
            "state-changed",
            "captured maintenance owner changed before transition",
        )
        if kind == "sync":
            require(
                current_basis == current["basis"],
                "basis-changed",
                "sync cannot invent a current basis",
            )
            return deepcopy(state)
        result = deepcopy(state)
        target = result["records"][record_id]
        if kind == "acknowledge":
            if not any(
                (
                    ack["acknowledgment_id"] == acknowledgment["acknowledgment_id"]
                    for ack in target["acknowledgment_history"]
                )
            ):
                target["acknowledgment_history"].append(acknowledgment)
            target.update(
                status="acknowledged",
                reasons=[],
                current_acknowledgment_id=acknowledgment["acknowledgment_id"],
            )
        else:
            incoming = event["observation"]
            self._validate_observation(incoming)
            require(
                incoming["basis"] == current_basis,
                "basis-changed",
                "event observation differs from independently captured basis",
            )
            if kind in {"observe", "delete", "delete-target", "ambiguous-move"}:
                require(
                    incoming["coordinate"] == current["coordinate"],
                    "coordinate-binding",
                    "unconfirmed coordinate replacement is forbidden",
                )
                require(
                    incoming["target"] == current["target"],
                    "target-binding",
                    "unconfirmed page/section replacement is forbidden",
                )
            if kind == "observe":
                require(
                    incoming["presence"] == current["presence"] == "present",
                    "mapping-invalid",
                    "ordinary observation cannot resolve a missing owner",
                )
                if incoming == current:
                    return deepcopy(state)
                require(
                    incoming["target_presence"] != "deleted"
                    or current["target_presence"] == "deleted",
                    "target-binding",
                    "removing a semantic section requires the explicit delete-target event",
                )
                compatible_scope = (
                    incoming["implementation"]["scope"]
                    == current["implementation"]["scope"]
                )
                compatible_producer = (
                    incoming["basis"]["comparison_id"]
                    == current["basis"]["comparison_id"]
                )
                available_pair = (
                    incoming["implementation"]["status"]
                    == current["implementation"]["status"]
                    == "available"
                )
                if (
                    compatible_scope
                    and compatible_producer
                    and available_pair
                    and (
                        incoming["basis"]["source_hash"]
                        == current["basis"]["source_hash"]
                    )
                ):
                    require(
                        incoming["basis"]["executable_hash"]
                        == current["basis"]["executable_hash"]
                        and incoming["basis"]["documentation_hash"]
                        == current["basis"]["documentation_hash"],
                        "identical-source-observation-mismatch",
                        "identical scoped source under a compatible producer cannot have divergent syntax/documentation digests",
                    )
                reasons = []
                if (
                    current["target_presence"] == "deleted"
                    and incoming["target_presence"] == "present"
                ):
                    reasons.append("target-restored")
                if incoming["basis"]["source_hash"] != current["basis"]["source_hash"]:
                    reasons.append("source-basis-changed")
                if incoming["basis"]["prose_hash"] != current["basis"]["prose_hash"]:
                    reasons.append("prose-changed")
                same_comparison = (
                    incoming["basis"]["comparison_id"]
                    == current["basis"]["comparison_id"]
                )
                both_available = (
                    incoming["implementation"]["status"]
                    == current["implementation"]["status"]
                    == "available"
                )
                if not compatible_scope:
                    reasons.append("scope-incompatible")
                if not same_comparison:
                    reasons.append("producer-incompatible")
                if (
                    both_available
                    and same_comparison
                    and compatible_scope
                    and (
                        incoming["basis"]["executable_hash"]
                        != current["basis"]["executable_hash"]
                    )
                ):
                    reasons.append("executable-syntax-changed")
                if not both_available:
                    reasons.append("implementation-unavailable")
                target["reasons"] = sorted(
                    set(
                        target["reasons"]
                        + reasons
                        + (["observation-changed"] if not reasons else [])
                    )
                )
            elif kind == "delete-target":
                require(
                    incoming["presence"] == current["presence"] == "present"
                    and incoming["target_presence"] == "deleted"
                    and (incoming["basis"]["prose_hash"] is None)
                    and (incoming["implementation"] == current["implementation"]),
                    "target-binding",
                    "section deletion retains captured source execution and explicit absent prose",
                )
                target["reasons"] = sorted(set(target["reasons"] + ["target-deleted"]))
            elif kind == "delete":
                require(
                    incoming["presence"] == "deleted",
                    "mapping-invalid",
                    "deletion must retain explicit missing-source observation",
                )
                target["mapping"] = {
                    "state": "deleted",
                    "previous_coordinate": deepcopy(current["coordinate"]),
                    "previous_target": deepcopy(current["target"]),
                    "candidates": [],
                }
                target["reasons"] = sorted(set(target["reasons"] + ["source-deleted"]))
            elif kind == "ambiguous-move":
                require(
                    incoming["presence"] == "ambiguous",
                    "mapping-invalid",
                    "ambiguous move must retain an unresolved observation",
                )
                target["mapping"] = {
                    "state": "ambiguous",
                    "previous_coordinate": deepcopy(current["coordinate"]),
                    "previous_target": deepcopy(current["target"]),
                    "candidates": deepcopy(event["candidates"]),
                }
                target["reasons"] = sorted(set(target["reasons"] + ["move-unresolved"]))
            elif kind == "confirm-move":
                confirmation = event["confirmation"]
                require(
                    incoming["presence"] == "present"
                    and incoming["implementation"]["status"] == "available"
                    and (confirmation["from_coordinate"] == current["coordinate"])
                    and (confirmation["to_coordinate"] == incoming["coordinate"])
                    and (confirmation["from_target"] == current["target"])
                    and (confirmation["to_target"] == incoming["target"])
                    and (
                        confirmation["from_basis_hash"]
                        == canonical_hash(target["last_present_basis"])
                    )
                    and (
                        confirmation["to_basis_hash"] == canonical_hash(current_basis)
                    ),
                    "move-unconfirmed",
                    "confirmed mapping lacks its exact old/new captured declaration bindings",
                )
                if target["mapping"]["state"] == "ambiguous":
                    require(
                        {
                            "coordinate": incoming["coordinate"],
                            "target": incoming["target"],
                        }
                        in target["mapping"]["candidates"],
                        "move-unconfirmed",
                        "target was not one of the unresolved candidates",
                    )
                target["mapping"] = {
                    "state": "resolved",
                    "previous_coordinate": deepcopy(current["coordinate"]),
                    "previous_target": deepcopy(current["target"]),
                    "candidates": [],
                }
                if incoming["coordinate"] not in target["coordinate_history"]:
                    target["coordinate_history"].append(
                        deepcopy(incoming["coordinate"])
                    )
                if incoming["target"] not in target["target_history"]:
                    target["target_history"].append(deepcopy(incoming["target"]))
                target["reasons"] = sorted(
                    set(target["reasons"] + ["confirmed-move-basis-changed"])
                )
            result["observations"][record_id] = deepcopy(incoming)
            if incoming["presence"] == "present":
                target["last_present_basis"] = deepcopy(current_basis)
            target.update(status="pending", current_acknowledgment_id=None)
            if kind == "delete":
                for peer_id, peer in list(result["observations"].items()):
                    if (
                        peer_id == record_id
                        or peer["coordinate"] != current["coordinate"]
                    ):
                        continue
                    peer_record = result["records"][peer_id]
                    result["observations"][peer_id] = self.observation(
                        incoming["implementation"],
                        peer["basis"]["prose_hash"],
                        presence="deleted",
                        target=peer["target"],
                        target_presence=peer["target_presence"],
                    )
                    peer_record.update(
                        status="pending",
                        current_acknowledgment_id=None,
                        reasons=sorted(
                            set(peer_record["reasons"] + ["source-deleted"])
                        ),
                        mapping={
                            "state": "deleted",
                            "previous_coordinate": deepcopy(peer["coordinate"]),
                            "previous_target": deepcopy(peer["target"]),
                            "candidates": [],
                        },
                    )
            if (
                kind == "observe"
                and incoming["implementation"] != current["implementation"]
            ):
                for peer_id, peer in list(result["observations"].items()):
                    if (
                        peer_id == record_id
                        or peer["coordinate"] != current["coordinate"]
                        or peer["presence"] != "present"
                    ):
                        continue
                    updated = self.observation(
                        incoming["implementation"],
                        peer["basis"]["prose_hash"],
                        target=peer["target"],
                        target_presence=peer["target_presence"],
                    )
                    peer_record = result["records"][peer_id]
                    peer_reasons = []
                    if updated["basis"]["source_hash"] != peer["basis"]["source_hash"]:
                        peer_reasons.append("source-basis-changed")
                    same_comparison = (
                        updated["basis"]["comparison_id"]
                        == peer["basis"]["comparison_id"]
                    )
                    same_scope = (
                        updated["implementation"]["scope"]
                        == peer["implementation"]["scope"]
                    )
                    both_available = (
                        updated["implementation"]["status"]
                        == peer["implementation"]["status"]
                        == "available"
                    )
                    if not same_comparison:
                        peer_reasons.append("producer-incompatible")
                    if not same_scope:
                        peer_reasons.append("scope-incompatible")
                    if not both_available:
                        peer_reasons.append("implementation-unavailable")
                    if (
                        same_comparison
                        and both_available
                        and same_scope
                        and (
                            updated["basis"]["executable_hash"]
                            != peer["basis"]["executable_hash"]
                        )
                    ):
                        peer_reasons.append("executable-syntax-changed")
                    peer_record.update(
                        status="pending",
                        current_acknowledgment_id=None,
                        reasons=sorted(
                            set(
                                peer_record["reasons"]
                                + peer_reasons
                                + (["observation-changed"] if not peer_reasons else [])
                            )
                        ),
                        last_present_basis=deepcopy(updated["basis"]),
                    )
                    result["observations"][peer_id] = updated
        result["generation"] += 1
        self.validate_state(result)
        return result


_CORE: MaintenanceCore | None = None


def maintenance_core() -> MaintenanceCore:
    """Use the installed implementation contract, never a model-only callback."""
    global _CORE
    if _CORE is None:
        from .implementation_evidence import validate_implementation_evidence

        _CORE = MaintenanceCore(validate_implementation_evidence)
    return _CORE


def _detached(value: object) -> dict[str, Any]:
    try:
        result = deepcopy(value)
    except (TypeError, ValueError, RecursionError) as exc:
        raise MaintenanceError(
            "schema-invalid", "maintenance owner must contain strict JSON"
        ) from exc
    require(
        type(result) is dict, "schema-invalid", "maintenance owner must be an object"
    )
    assert isinstance(result, dict)
    return result


def validate_maintenance_state(value: object) -> dict[str, Any]:
    result = _detached(value)
    maintenance_core().validate_state(result)
    return result


def validate_maintenance_adoption(value: object) -> dict[str, Any]:
    result = _detached(value)
    maintenance_core().validate_schema("maintenance-adoption-v1", result)
    return result


def maintenance_state_hash(value: object) -> str:
    return canonical_hash(validate_maintenance_state(value))


state_hash = maintenance_state_hash
