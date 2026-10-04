"""Captured source/semantic-section joins and pure durable reconciliation.

No source, Markdown, or ledger is reopened here. Absence needs an explicit
capture; omitted declarations and unselected inputs cannot prove deletion.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable

from .immutable import freeze
from .implementation_evidence import (
    DECLARATIONS_KEY,
    IMPLEMENTATION_KEY,
    validate_concept_implementation,
    validate_implementation_evidence,
)
from .maintenance_state import (
    MaintenanceError,
    canonical_hash,
    maintenance_core,
    new_identity,
    validate_maintenance_adoption,
    validate_maintenance_state,
)
from .python_implementation import comparison_id
from .knowledge_storage import digest
from .markdown_sections import parse_markdown_document
from .section_ownership import SectionOwnership, observe_page_sections


def captured_semantic_sections(
    markdown: str, page_locator: str, page_kind, *, raw_content: bytes | None = None
) -> dict:
    """Exact raw section bytes joined to existing normalized ownership locators."""
    encoding = "utf-8"
    raw = markdown.encode("utf-8") if raw_content is None else raw_content
    if not isinstance(raw, bytes):
        raise MaintenanceError(
            "prose-encoding-unavailable", "captured Markdown must be bytes"
        )
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        encoding = "cp1252"
        try:
            decoded = raw.decode(encoding)
        except UnicodeDecodeError as exc:
            raise MaintenanceError(
                "prose-encoding-unavailable",
                "captured Markdown encoding is unsupported",
            ) from exc

    def normalize(text):
        return text.replace("\r\n", "\n").replace("\r", "\n")

    if normalize(decoded) != normalize(markdown):
        raise MaintenanceError(
            "prose-encoding-unavailable",
            "Markdown text differs from its captured byte preimage",
        )
    markdown = decoded
    owned = observe_page_sections(markdown, page_locator, page_kind)
    document = parse_markdown_document(markdown, page_locator)
    offsets, raw_index = [0], 0
    while raw_index < len(markdown):
        raw_index += 2 if markdown[raw_index : raw_index + 2] == "\r\n" else 1
        offsets.append(raw_index)
    byte_offsets = [0]
    for character in markdown:
        byte_offsets.append(byte_offsets[-1] + len(character.encode(encoding)))
    spans = {section.locator: section for section in document.sections}
    result = {}
    for section in owned.sections:
        if (
            section.ownership is not SectionOwnership.SEMANTIC
            or section.locator not in spans
        ):
            continue
        span = spans[section.locator]
        selected = raw[
            byte_offsets[offsets[span.start]] : byte_offsets[offsets[span.end]]
        ]
        result[section.locator] = {
            "locator": section.locator,
            "prose_hash": digest(selected),
        }
    return result


def owner_key(coordinate, target) -> str:
    return canonical_hash({"coordinate": coordinate, "target": target})


@dataclass(frozen=True)
class MaintenanceCapture:
    by_owner: Mapping[str, dict[str, Any]]
    missing_source_paths: frozenset[str] = frozenset()
    known_absent_pages: frozenset[str] = frozenset()
    captured_paths: frozenset[str] = frozenset()
    complete_pages: frozenset[str] = frozenset()
    issues: tuple[dict[str, Any], ...] = ()
    source_backed_semantic_total: int = 0
    tracked_semantic_total: int = 0

    def __post_init__(self):
        object.__setattr__(self, "by_owner", freeze(dict(self.by_owner)))
        object.__setattr__(self, "issues", freeze(tuple(self.issues)))

    def to_payload(self) -> dict:
        return {
            "by_owner": deepcopy(self.by_owner),
            "missing_source_paths": sorted(self.missing_source_paths),
            "known_absent_pages": sorted(self.known_absent_pages),
            "captured_paths": sorted(self.captured_paths),
            "complete_pages": sorted(self.complete_pages),
            "issues": deepcopy(list(self.issues)),
            "source_backed_semantic_total": self.source_backed_semantic_total,
            "tracked_semantic_total": self.tracked_semantic_total,
        }


def _mapping_values(mapping):
    def get(key):
        return (
            mapping.get(key) if isinstance(mapping, Mapping) else getattr(mapping, key)
        )

    scope = "module" if get("scope") == "module" else "class"
    return {
        "source_path": get("source_path"),
        "qualified_owner": "__module__" if scope == "module" else get("entity_name"),
        "occurrence": 1 if scope == "module" else get("occurrence"),
    }, scope


def _unavailable(evidence, *, reason, source_hash):
    result = deepcopy(evidence)
    result.update(
        status="unavailable",
        unavailable_reason=reason,
        source_hash=source_hash,
        executable_hash=None,
        documentation_hash=None,
    )
    result["aggregation"] = {
        "complete_scope": False,
        "observations_total": 0,
        "observations_returned": 0,
        "truncated": False,
    }
    return validate_implementation_evidence(result)


def _current_evidence(concept, mapping, captures, hashes, selected, analysis_hash):
    coordinate, scope = _mapping_values(mapping)
    source = coordinate["source_path"]
    if source not in selected:
        return None, "source-not-captured"
    validated = validate_concept_implementation(concept)
    primary = validated.get(IMPLEMENTATION_KEY)
    gap = validated.get(DECLARATIONS_KEY)
    files = captures.get("files", {}) if isinstance(captures, Mapping) else {}
    captured = files.get(source, {})
    if (
        isinstance(captures, Mapping)
        and captures.get("schema_version") != "llm-wiki-implementation-observations/v1"
    ):
        raise MaintenanceError(
            "schema-invalid", "unsupported implementation capture envelope"
        )
    if captured:
        descriptor = captured.get("producer")
        if (
            descriptor is None
            or analysis_hash is None
            or descriptor.get("analysis_compatibility_hash") != analysis_hash
        ):
            return None, "unsupported-producer"
        if captured.get("source_hash") != hashes.get(source):
            raise MaintenanceError(
                "source-binding", "source sidecar differs from current byte commitment"
            )
        matched = [
            row["evidence"]
            for row in captured.get("observations", ())
            if row["evidence"]["coordinate"] == coordinate
            and row["evidence"]["scope"] == scope
        ]
        if len(matched) == 1:
            live = validate_implementation_evidence(matched[0])
            if (
                live["source_hash"] != hashes.get(source)
                or live["producer"] != descriptor
            ):
                raise MaintenanceError(
                    "producer-binding", "declaration differs from its captured file"
                )
            return live, live["unavailable_reason"]
        primary = None
    if primary is not None:
        if primary["coordinate"] != coordinate or primary["scope"] != scope:
            raise MaintenanceError(
                "coordinate-binding",
                "captured implementation differs from exact page mapping",
            )
        if (
            analysis_hash is None
            or primary["producer"]["analysis_compatibility_hash"] != analysis_hash
        ):
            return None, "unsupported-producer"
        if primary["source_hash"] != hashes.get(source):
            raise MaintenanceError(
                "source-binding",
                "captured implementation differs from source byte commitment",
            )
        return primary, primary["unavailable_reason"]
    if gap and gap["owner"] != {"coordinate": coordinate, "scope": scope}:
        raise MaintenanceError(
            "coordinate-binding", "implementation gap differs from exact page owner"
        )
    reason = gap["bounds"]["reason"] if gap else "legacy-evidence-absent"
    if captured:
        reason = captured.get("reason") or (
            "observation-limit"
            if captured.get("bounds", {}).get("truncated")
            else "ambiguous-owner"
        )
    descriptor = captured.get("producer") if isinstance(captured, Mapping) else None
    if (
        descriptor is None
        or analysis_hash is None
        or descriptor.get("analysis_compatibility_hash") != analysis_hash
    ):
        return None, "unsupported-producer"
    if captured.get("source_hash") != hashes.get(source):
        raise MaintenanceError(
            "source-binding", "unavailable capture differs from source byte commitment"
        )
    # A qualified captured file can describe an unavailable mapped declaration.
    # Zero counts here mean zero evaluated detail observations, not complete scope.
    evidence = {
        "schema_version": "llm-wiki-implementation-evidence/v1",
        "coordinate": coordinate,
        "scope": scope,
        "status": "unavailable",
        "producer": dict(descriptor),
        "comparison_id": comparison_id(descriptor),
        "source_hash": hashes.get(source),
        "executable_hash": None,
        "documentation_hash": None,
        "aggregation": {
            "complete_scope": False,
            "observations_total": 0,
            "observations_returned": 0,
            "truncated": False,
        },
        "unavailable_reason": reason or "ambiguous-owner",
    }
    return validate_implementation_evidence(evidence), reason


def captured_observations_from_knowledge(
    knowledge,
    *,
    content_by_page,
    page_source_mappings,
    captures=None,
    source_content_hashes=None,
    captured_paths=None,
    missing_source_paths=(),
    analysis_compatibility_hash=None,
    section_ownership=None,
    previous_state=None,
    known_absent_pages=(),
    raw_content_by_page=None,
) -> MaintenanceCapture:
    """Join actual current captures; unavailable old owners retain honest gaps.

    ``content_by_page`` supplies exact captured Markdown. Pages omitted from it
    remain unobserved unless separately listed in ``known_absent_pages``.
    Source absence similarly requires ``missing_source_paths``. No declaration
    disappears merely because the bounded sidecar omitted its row.
    """
    core = maintenance_core()
    hashes = dict(source_content_hashes or {})
    selected = frozenset(captured_paths if captured_paths is not None else hashes)
    missing = frozenset(missing_source_paths)
    absent_pages = frozenset(known_absent_pages)
    if missing & set(hashes) or absent_pages & set(content_by_page):
        raise MaintenanceError(
            "capture-contradiction",
            "input cannot be both present and explicitly absent",
        )
    old_state = (
        validate_maintenance_state(previous_state)
        if previous_state is not None
        else None
    )
    observations, issues, semantic_by_page, evidence_by_coordinate = {}, [], {}, {}
    semantic_keys = set()
    concepts = knowledge.concepts if hasattr(knowledge, "concepts") else knowledge
    for concept in concepts:
        if isinstance(concept, Mapping):
            path, locator, kind = (
                concept["document"]["canonical_path"],
                concept["locator"],
                concept["document"]["page_kind"],
            )
        else:
            path, locator, kind = (
                concept.document.canonical_path,
                concept.locator,
                concept.document.page_kind.value,
            )
        if path not in content_by_page:
            continue
        mapping = page_source_mappings.get(path)
        if mapping is not None and kind in {"modules", "entities"}:
            current_evidence, current_reason = _current_evidence(
                concept,
                mapping,
                captures,
                hashes,
                selected,
                analysis_compatibility_hash,
            )
            current_coordinate, _ = _mapping_values(mapping)
            if current_evidence is not None:
                evidence_by_coordinate[canonical_hash(current_coordinate)] = (
                    current_evidence
                )
        try:
            if raw_content_by_page is not None and path not in raw_content_by_page:
                raise MaintenanceError(
                    "prose-encoding-unavailable", "captured Markdown bytes are absent"
                )
            semantic = captured_semantic_sections(
                content_by_page[path],
                locator,
                kind,
                raw_content=raw_content_by_page[path]
                if raw_content_by_page is not None
                else None,
            )
        except MaintenanceError as exc:
            issues.append({"canonical_path": path, "reason": exc.code})
            continue
        semantic_by_page[path] = semantic
        if mapping is None or kind not in {"modules", "entities"}:
            continue
        coordinate, _ = _mapping_values(mapping)
        for section in semantic.values():
            semantic_keys.add(
                owner_key(
                    coordinate,
                    {
                        "canonical_path": path,
                        "section_locator": section["locator"],
                        "ownership": "semantic",
                    },
                )
            )
        evidence, reason = current_evidence, current_reason
        coordinate, scope = _mapping_values(mapping)
        if evidence is None:
            issues.append(
                {
                    "canonical_path": path,
                    "coordinate": coordinate,
                    "scope": scope,
                    "reason": reason,
                }
            )
            continue
        if reason is not None:
            issues.append(
                {
                    "canonical_path": path,
                    "coordinate": coordinate,
                    "scope": scope,
                    "reason": reason,
                }
            )
        evidence_by_coordinate[canonical_hash(coordinate)] = evidence
        for section in semantic.values():
            target = {
                "canonical_path": path,
                "section_locator": section["locator"],
                "ownership": "semantic",
            }
            observed = core.observation(evidence, section["prose_hash"], target=target)
            observations[owner_key(coordinate, target)] = observed
    if old_state is not None:
        for record_id, old in old_state["observations"].items():
            key = owner_key(old["coordinate"], old["target"])
            if key in observations:
                continue
            source, path = (
                old["coordinate"]["source_path"],
                old["target"]["canonical_path"],
            )
            page_semantics = semantic_by_page.get(path)
            target_exists = (
                page_semantics is not None
                and old["target"]["section_locator"] in page_semantics
            )
            confirmed_target_missing = path in absent_pages or (
                page_semantics is not None and not target_exists
            )
            target_presence = (
                "deleted" if confirmed_target_missing else old["target_presence"]
            )
            prose = (
                page_semantics[old["target"]["section_locator"]]["prose_hash"]
                if target_exists and page_semantics is not None
                else None
            )
            if source in missing:
                evidence = _unavailable(
                    old["implementation"], reason="missing-source", source_hash=None
                )
                presence = "deleted"
            elif canonical_hash(old["coordinate"]) in evidence_by_coordinate:
                evidence = evidence_by_coordinate[canonical_hash(old["coordinate"])]
                presence = old["presence"]
                if presence == "deleted":
                    evidence = _unavailable(
                        old["implementation"], reason="missing-source", source_hash=None
                    )
                if presence == "ambiguous":
                    evidence = _unavailable(
                        old["implementation"],
                        reason="ambiguous-owner",
                        source_hash=hashes.get(source),
                    )
            else:
                # Unknown current source/prose does not retain an active ack.
                # A historical producer may remain only in explicitly unavailable evidence.
                evidence = _unavailable(
                    old["implementation"],
                    reason="unsupported-producer",
                    source_hash=hashes.get(source) if source in selected else None,
                )
                presence = old["presence"]
                if presence == "deleted":
                    evidence = _unavailable(
                        old["implementation"], reason="missing-source", source_hash=None
                    )
                if presence == "ambiguous":
                    evidence = _unavailable(
                        old["implementation"],
                        reason="ambiguous-owner",
                        source_hash=hashes.get(source) if source in selected else None,
                    )
                issues.append(
                    {
                        "record_id": record_id,
                        "canonical_path": path,
                        "coordinate": old["coordinate"],
                        "reason": "current-owner-not-qualified",
                    }
                )
            observed = core.observation(
                evidence,
                prose,
                presence=presence,
                target=old["target"],
                target_presence=target_presence,
            )
            observations[key] = observed
    return MaintenanceCapture(
        observations,
        missing,
        absent_pages,
        selected,
        frozenset(content_by_page),
        tuple(issues),
        len(semantic_keys),
        len(semantic_keys & set(observations)),
    )


def _event(state, record_id, kind, **fields):
    return {
        "schema_version": "llm-wiki-maintenance-event/v1",
        "kind": kind,
        "record_id": record_id,
        "expected_state_hash": canonical_hash(state),
        **fields,
    }


def reconcile_pending_maintenance(
    previous_state,
    marker,
    capture: MaintenanceCapture,
    *,
    confirmed_transfers=(),
    ambiguous_transfers=(),
    allocate_id: Callable[[], str] = new_identity,
) -> dict:
    """Preserve history, apply explicit transfer proofs, and reopen captured work.

    The transaction owner captures/locks/rechecks inputs and persists newly
    allocated IDs once. Unchanged replay allocates nothing and changes no bytes.
    """
    guard = validate_maintenance_adoption(marker)
    core = maintenance_core()
    if not isinstance(capture, MaintenanceCapture):
        raise TypeError("capture must be an owned MaintenanceCapture")
    if previous_state is None:
        initial = {}
        for observed in capture.by_owner.values():
            if (
                observed["presence"] == observed["target_presence"] == "present"
                and observed["basis"]["source_hash"] is not None
                and observed["basis"]["prose_hash"] is not None
            ):
                record_id = allocate_id()
                if record_id in initial:
                    raise MaintenanceError(
                        "record-collision", "record allocator reused an opaque identity"
                    )
                initial[record_id] = deepcopy(observed)
        return core.initial_state(guard, initial)
    current = validate_maintenance_state(previous_state)
    if current["adoption_id"] != guard["adoption_id"] or current[
        "guard_hash"
    ] != canonical_hash(guard):
        raise MaintenanceError(
            "guard-mismatch", "immutable marker and durable owner disagree"
        )
    if not isinstance(capture, MaintenanceCapture):
        raise TypeError("capture must be an owned MaintenanceCapture")
    for transfer in confirmed_transfers:
        record_id = transfer["record_id"]
        observed = deepcopy(transfer["observation"])
        current = core.transition(
            current,
            _event(
                current,
                record_id,
                "confirm-move",
                observation=observed,
                confirmation=deepcopy(transfer["confirmation"]),
            ),
            observed["basis"],
        )
    unresolved_ids = {
        record_id
        for record_id, record in current["records"].items()
        if record["mapping"]["state"] == "ambiguous"
    }
    unresolved_keys = {
        owner_key(candidate["coordinate"], candidate["target"])
        for record_id in unresolved_ids
        for candidate in current["records"][record_id]["mapping"]["candidates"]
    }
    for transfer in ambiguous_transfers:
        record_id = transfer["record_id"]
        unresolved_ids.add(record_id)
        unresolved_keys.update(
            owner_key(candidate["coordinate"], candidate["target"])
            for candidate in transfer["candidates"]
        )
        observed = deepcopy(transfer["observation"])
        current = core.transition(
            current,
            _event(
                current,
                record_id,
                "ambiguous-move",
                observation=observed,
                candidates=deepcopy(transfer["candidates"]),
            ),
            observed["basis"],
        )
    incoming = deepcopy(capture.by_owner)
    existing = {
        owner_key(o["coordinate"], o["target"]): record_id
        for record_id, o in current["observations"].items()
    }
    for key in sorted(incoming):
        observed = incoming[key]
        record_id = existing.get(key)
        if record_id in unresolved_ids or key in unresolved_keys:
            continue
        if record_id is None:
            if observed["presence"] == observed["target_presence"] == "present":
                record_id = allocate_id()
                current = core.transition(
                    current,
                    _event(current, record_id, "register", observation=observed),
                    observed["basis"],
                )
                existing[key] = record_id
            continue
        old = current["observations"][record_id]
        if observed == old:
            continue
        if observed["presence"] == "deleted":
            current = core.transition(
                current,
                _event(current, record_id, "delete", observation=observed),
                observed["basis"],
            )
        elif old["presence"] != "present" or observed["presence"] != "present":
            # Resolution requires an explicit confirmed/ambiguous transfer.
            continue
        else:
            if (
                observed["target_presence"] == "deleted"
                and old["target_presence"] == "present"
            ):
                # Update shared source first; deleting only the section must
                # leave the peers' prose targets and histories intact.
                refreshed = core.observation(
                    observed["implementation"],
                    old["basis"]["prose_hash"],
                    target=old["target"],
                )
                if refreshed != old:
                    current = core.transition(
                        current,
                        _event(current, record_id, "observe", observation=refreshed),
                        refreshed["basis"],
                    )
                current = core.transition(
                    current,
                    _event(current, record_id, "delete-target", observation=observed),
                    observed["basis"],
                )
            else:
                current = core.transition(
                    current,
                    _event(current, record_id, "observe", observation=observed),
                    observed["basis"],
                )
    core.validate_state(current)
    return current


@dataclass(frozen=True)
class MaintenanceTransfers:
    confirmed: tuple[dict[str, Any], ...] = ()
    ambiguous: tuple[dict[str, Any], ...] = ()
    issues: tuple[dict[str, Any], ...] = ()

    def __post_init__(self):
        for name in ("confirmed", "ambiguous", "issues"):
            object.__setattr__(self, name, freeze(tuple(getattr(self, name))))


def maintenance_transfers_from_page_plan(
    previous_state,
    capture: MaintenanceCapture,
    page_plan,
    *,
    previous_raw_content_by_page,
) -> MaintenanceTransfers:
    """Use verified page owners and captured semantic sections, never names/hashes."""
    from urllib.parse import quote
    from .sync_transitions import PageTransitionPlan

    if page_plan is None:
        return MaintenanceTransfers()
    state = validate_maintenance_state(previous_state)
    if not isinstance(page_plan, PageTransitionPlan):
        raise TypeError("page_plan must be the verified PageTransitionPlan")
    confirmed, ambiguous, issues = [], [], []
    selected = set()
    for transition in page_plan.transitions:
        if transition.previous_owner is None or transition.old_path is None:
            continue
        old_coordinate, old_scope = _mapping_values(transition.previous_owner)
        new_coordinate, new_scope = _mapping_values(transition.owner)
        if old_scope != new_scope:
            continue
        if (
            old_coordinate == new_coordinate
            and transition.old_path == transition.final_path
        ):
            continue
        raw = (
            previous_raw_content_by_page.get(transition.old_path)
            if previous_raw_content_by_page is not None
            else None
        )
        if raw is None or transition.source_path is None:
            issues.append(
                {
                    "canonical_path": transition.old_path,
                    "reason": "previous-semantic-preimage-unavailable",
                }
            )
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw.decode("cp1252")
            except UnicodeDecodeError:
                issues.append(
                    {
                        "canonical_path": transition.old_path,
                        "reason": "prose-encoding-unavailable",
                    }
                )
                continue
        locator = "llm-wiki://" + quote(transition.old_path[:-3], safe="/-._~")
        old_sections = captured_semantic_sections(
            text,
            locator,
            "modules" if old_scope == "module" else "entities",
            raw_content=raw,
        )
        candidates = [
            deepcopy(value)
            for value in capture.by_owner.values()
            if value["coordinate"] == new_coordinate
            and value["target"]["canonical_path"] == transition.final_path
            and value["target_presence"] == "present"
        ]
        for record_id, old in state["observations"].items():
            if (
                old["coordinate"] != old_coordinate
                or old["target"]["canonical_path"] != transition.old_path
            ):
                continue
            if record_id in selected:
                raise MaintenanceError(
                    "move-unconfirmed",
                    "one durable owner has multiple page-transition claims",
                )
            selected.add(record_id)
            suffix = old["target"]["section_locator"].partition("#section/")[2]
            matches = [
                value
                for value in candidates
                if value["target"]["section_locator"].partition("#section/")[2]
                == suffix
            ]
            old_exists = old["target"]["section_locator"] in old_sections
            if (
                old_exists
                and len(matches) == 1
                and matches[0]["implementation"]["status"] == "available"
            ):
                incoming = matches[0]
                confirmation = {
                    "actor": {
                        "kind": "agent",
                        "actor_id": "agent-wiki-cli/sync",
                        "authority": "ordinary-maintenance",
                    },
                    "governance_effect": "none",
                    "from_coordinate": old_coordinate,
                    "to_coordinate": new_coordinate,
                    "from_target": deepcopy(old["target"]),
                    "to_target": deepcopy(incoming["target"]),
                    "from_basis_hash": canonical_hash(
                        state["records"][record_id]["last_present_basis"]
                    ),
                    "to_basis_hash": canonical_hash(incoming["basis"]),
                }
                confirmed.append(
                    {
                        "record_id": record_id,
                        "observation": incoming,
                        "confirmation": confirmation,
                    }
                )
            else:
                references = [
                    {"coordinate": value["coordinate"], "target": value["target"]}
                    for value in candidates
                ]
                if 2 <= len(references) <= 8:
                    evidence = _unavailable(
                        old["implementation"],
                        reason="ambiguous-owner",
                        source_hash=None,
                    )
                    observed = maintenance_core().observation(
                        evidence,
                        None,
                        presence="ambiguous",
                        target=old["target"],
                        target_presence=old["target_presence"],
                    )
                    ambiguous.append(
                        {
                            "record_id": record_id,
                            "observation": observed,
                            "candidates": references,
                        }
                    )
                else:
                    issues.append(
                        {
                            "record_id": record_id,
                            "canonical_path": transition.old_path,
                            "reason": "semantic-section-transfer-unconfirmed",
                        }
                    )
    # A plan may expose only newly created owners when source movement is
    # ambiguous. These are uncertainty candidates, never identity proof.
    new_owners = {
        _mapping_values(item.owner)[0]["source_path"]
        for item in page_plan.transitions
        if item.previous_owner is None
    }
    for record_id, old in state["observations"].items():
        if (
            record_id in selected
            or old["coordinate"]["source_path"] not in capture.missing_source_paths
            or old["implementation"]["scope"] == "module"
        ):
            continue
        suffix = old["target"]["section_locator"].partition("#section/")[2]
        candidates = [
            deepcopy(value)
            for value in capture.by_owner.values()
            if value["presence"] == value["target_presence"] == "present"
            and value["coordinate"]["source_path"] in new_owners
            and value["coordinate"]["qualified_owner"]
            == old["coordinate"]["qualified_owner"]
            and value["implementation"]["scope"] == old["implementation"]["scope"]
            and value["target"]["section_locator"].partition("#section/")[2] == suffix
        ]
        if not candidates:
            continue
        references = [
            {"coordinate": value["coordinate"], "target": value["target"]}
            for value in candidates
        ]
        if 2 <= len(references) <= 8:
            evidence = _unavailable(
                old["implementation"], reason="ambiguous-owner", source_hash=None
            )
            observed = maintenance_core().observation(
                evidence,
                None,
                presence="ambiguous",
                target=old["target"],
                target_presence="deleted"
                if old["target"]["canonical_path"] in capture.known_absent_pages
                else old["target_presence"],
            )
            ambiguous.append(
                {
                    "record_id": record_id,
                    "observation": observed,
                    "candidates": references,
                }
            )
        else:
            issues.append(
                {
                    "record_id": record_id,
                    "canonical_path": old["target"]["canonical_path"],
                    "reason": "source-owner-transfer-unconfirmed",
                }
            )
    return MaintenanceTransfers(tuple(confirmed), tuple(ambiguous), tuple(issues))
