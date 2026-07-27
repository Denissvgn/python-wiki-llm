"""Explicit durable-knowledge governance and verification commands.

The governance ledger is the non-rebuildable authority.  Mutations are
prepared from a validated artifact snapshot and committed while holding the
governance lock.  Their disposable projection is refreshed in the same
operation except for an explicitly staged move whose target will exist only
after the next sync.  Verification is separate and never runs while metadata
is merely being loaded.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from ..services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    ValidatedKnowledgeArtifacts,
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
    validate_knowledge_artifacts,
)
from ..services.knowledge_governance import (
    ACTOR_KINDS,
    ALIAS_LOCATOR,
    ALIAS_NATURAL_KEY,
    GOVERNANCE_EXTENSION_KEY,
    GOVERNANCE_FILENAME,
    MAX_EVENT_LIMIT,
    GovernanceActor,
    GovernanceError,
    GovernanceLedger,
    add_alias,
    add_review_event,
    apply_governance_projection,
    concept_references_from_knowledge,
    current_review_evidence,
    evaluate_review_event,
    governance_bundle_id_from_knowledge,
    governance_lock,
    load_governance,
    move_concept,
    reconcile_concepts,
    review_scope_hash,
    save_governance,
    set_lifecycle,
    strip_governance_projection,
    validate_governance_ledger,
)
from ..services.knowledge_index import serialize_knowledge_index
from ..services.io import first_unsafe_path_component
from ..services.knowledge_loader import (
    KnowledgeMismatchPolicy,
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from ..services.knowledge_model import (
    KnowledgeIndex,
    KnowledgeLoadState,
    Lifecycle,
)
from ..services.sync_manifest import MANIFEST_FILENAME, SyncManifest
from ..services.verification_contracts import (
    VerificationResult,
    build_artifact_verification_context,
    verify,
    verify_and_write_receipt,
)
from ..services.wiki_surface_index import SURFACE_INDEX_FILENAME


_RECOVERABLE_PROJECTION_CODES = frozenset(
    {
        "governance-live-hash-mismatch",
        "governance-projection-mismatch",
        "governance-projection-missing",
    }
)


@dataclass(frozen=True)
class _ArtifactSnapshot:
    surface_bytes: bytes
    knowledge_bytes: bytes
    manifest_bytes: bytes
    manifest: SyncManifest
    validated: ValidatedKnowledgeArtifacts


LedgerMutation = Callable[
    [GovernanceLedger, KnowledgeIndex],
    GovernanceLedger,
]


def _wiki_root(value: str | Path) -> Path:
    root = Path(value)
    if first_unsafe_path_component(root) is not None:
        raise GovernanceError(
            "wiki_dir",
            "must not contain traversal, symbolic-link, or reparse-point components",
        )
    if root.is_symlink():
        raise GovernanceError(
            "wiki_dir",
            "must be an existing directory, not a symbolic link",
        )
    if not root.is_dir():
        raise GovernanceError("wiki_dir", "must be an existing directory")
    return root


def _read_bytes(path: Path, field: str) -> bytes:
    if path.is_symlink():
        raise GovernanceError(field, "must be a regular file, not a symbolic link")
    if not path.is_file():
        raise GovernanceError(field, "is required before managing knowledge")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise GovernanceError(field, "could not be read") from exc


def _validated_artifact_snapshot(
    wiki_dir: Path,
    *,
    allow_governance_recovery: bool,
) -> _ArtifactSnapshot:
    """Load a coherent current artifact snapshot.

    Governance-only mismatch is tolerated for mutation recovery because the
    command will rebuild the projection from the authoritative ledger.  Every
    other mismatch, including Markdown drift and marker mismatch, fails before
    any write.
    """

    try:
        state = load_knowledge_state(
            wiki_dir,
            policy=KnowledgeMismatchPolicy.REJECT,
        )
    except KnowledgeStateLoadError as exc:
        issue_codes = {issue.code for issue in exc.issues}
        if (
            not allow_governance_recovery
            or not issue_codes
            or not issue_codes.issubset(_RECOVERABLE_PROJECTION_CODES)
        ):
            raise
    else:
        if (
            state.status is not KnowledgeLoadState.VALID
            or state.knowledge is None
            or state.manifest_basis is None
        ):
            raise GovernanceError(
                "knowledge",
                "a complete committed knowledge snapshot is required",
            )

    return _committed_artifact_snapshot(wiki_dir)


def _committed_artifact_snapshot(wiki_dir: Path) -> _ArtifactSnapshot:
    """Read artifacts committed by their manifest without checking live Markdown.

    This narrower read is used by the staged move workflow.  A page rename is
    expected to make the live Markdown snapshot stale before the following
    sync, but the last committed artifacts must still be internally coherent.
    """

    surface_path = wiki_dir / SURFACE_INDEX_FILENAME
    knowledge_path = wiki_dir / KNOWLEDGE_INDEX_FILENAME
    manifest_path = wiki_dir / MANIFEST_FILENAME
    surface_bytes = _read_bytes(surface_path, SURFACE_INDEX_FILENAME)
    knowledge_bytes = _read_bytes(knowledge_path, KNOWLEDGE_INDEX_FILENAME)
    manifest_bytes = _read_bytes(manifest_path, MANIFEST_FILENAME)
    manifest = SyncManifest.load(wiki_dir)
    validated = validate_knowledge_artifacts(
        surface_index_bytes=surface_bytes,
        knowledge_index_bytes=knowledge_bytes,
        manifest=manifest,
    )
    marker = manifest.artifact_hashes
    if marker is None:
        raise GovernanceError(
            "manifest.artifact_hashes",
            "must commit the current knowledge artifacts",
        )
    marker_values = (
        marker.surface_index_hash,
        marker.knowledge_index_hash,
        marker.evaluated_envelope_hash,
        marker.governance_hash,
    )
    actual_values = (
        validated.surface_index_hash,
        validated.knowledge_index_hash,
        validated.evaluated_envelope_hash,
        validated.governance_hash,
    )
    if marker_values != actual_values:
        raise GovernanceError(
            "manifest.artifact_hashes",
            "does not commit the current artifact snapshot",
            code="governance-conflict",
        )
    return _ArtifactSnapshot(
        surface_bytes=surface_bytes,
        knowledge_bytes=knowledge_bytes,
        manifest_bytes=manifest_bytes,
        manifest=manifest,
        validated=validated,
    )


def _assert_snapshot_unchanged(
    wiki_dir: Path,
    snapshot: _ArtifactSnapshot,
) -> None:
    observed = (
        _read_bytes(wiki_dir / SURFACE_INDEX_FILENAME, SURFACE_INDEX_FILENAME),
        _read_bytes(wiki_dir / KNOWLEDGE_INDEX_FILENAME, KNOWLEDGE_INDEX_FILENAME),
        _read_bytes(wiki_dir / MANIFEST_FILENAME, MANIFEST_FILENAME),
    )
    expected = (
        snapshot.surface_bytes,
        snapshot.knowledge_bytes,
        snapshot.manifest_bytes,
    )
    if observed != expected:
        raise GovernanceError(
            "knowledge",
            "artifacts changed while the governance mutation was prepared",
            code="governance-conflict",
        )


def _load_required_ledger(wiki_dir: Path):
    try:
        return load_governance(wiki_dir)
    except FileNotFoundError as exc:
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            "is absent; run 'llm-wiki knowledge init' first",
        ) from exc


def _assert_bundle_continuity(
    snapshot: _ArtifactSnapshot,
    ledger: GovernanceLedger,
) -> None:
    expected = governance_bundle_id_from_knowledge(
        snapshot.validated.knowledge
    )
    if expected is not None and ledger.bundle_id != expected:
        raise GovernanceError(
            "bundle_id",
            "does not match the prior committed governance bundle",
            code="governance-bundle-mismatch",
        )


def _projected_commit_plan(
    wiki_dir: Path,
    snapshot: _ArtifactSnapshot,
    ledger: GovernanceLedger,
):
    base = strip_governance_projection(snapshot.validated.knowledge)
    projected = apply_governance_projection(base, ledger)
    return build_knowledge_commit_plan(
        wiki_dir,
        surface_index_bytes=snapshot.surface_bytes,
        knowledge_index_bytes=serialize_knowledge_index(projected).encode("utf-8"),
        manifest=snapshot.manifest,
    )


def _mutation_preview_payload(
    action: str,
    ledger: GovernanceLedger,
    *,
    changed: bool,
    dry_run: bool,
    projection: str = "current",
) -> dict[str, object]:
    return {
        "action": action,
        "bundle_id": ledger.bundle_id,
        "changed": changed,
        "concept_count": len(ledger.concepts),
        "dry_run": dry_run,
        "governance_hash": ledger.content_hash(),
        "projection": projection,
    }


def _print_payload(payload: Mapping[str, object]) -> None:
    print(json.dumps(dict(payload), sort_keys=True))


def _prepare_existing_mutation(
    wiki_dir: Path,
    mutation: LedgerMutation,
) -> tuple[_ArtifactSnapshot, object, GovernanceLedger, object]:
    loaded = _load_required_ledger(wiki_dir)
    snapshot = _validated_artifact_snapshot(
        wiki_dir,
        allow_governance_recovery=True,
    )
    _assert_bundle_continuity(snapshot, loaded.ledger)
    updated = mutation(loaded.ledger, snapshot.validated.knowledge)
    plan = _projected_commit_plan(wiki_dir, snapshot, updated)
    return snapshot, loaded, updated, plan


def _run_existing_mutation(
    wiki_dir: Path,
    *,
    action: str,
    dry_run: bool,
    mutation: LedgerMutation,
) -> None:
    if dry_run:
        _snapshot, loaded, updated, plan = _prepare_existing_mutation(
            wiki_dir,
            mutation,
        )
        changed = loaded.ledger != updated or plan.changed
        _print_payload(
            _mutation_preview_payload(
                action,
                updated,
                changed=changed,
                dry_run=True,
            )
        )
        return

    with governance_lock(wiki_dir):
        snapshot, loaded, updated, plan = _prepare_existing_mutation(
            wiki_dir,
            mutation,
        )
        _assert_snapshot_unchanged(wiki_dir, snapshot)
        write_result = save_governance(
            wiki_dir,
            updated,
            expected_hash=loaded.content_hash,
        )
        commit_result = commit_knowledge_artifacts(plan)
    _print_payload(
        _mutation_preview_payload(
            action,
            updated,
            changed=write_result.changed or commit_result.changed,
            dry_run=False,
        )
    )


def _init_ledger(
    wiki_dir: Path,
    *,
    bundle_id: str | None,
) -> tuple[_ArtifactSnapshot, GovernanceLedger, str | None, GovernanceLedger]:
    path = wiki_dir / GOVERNANCE_FILENAME
    ledger_present = path.exists() or path.is_symlink()
    if ledger_present:
        loaded = load_governance(wiki_dir)
        if bundle_id is not None and loaded.ledger.bundle_id != bundle_id:
            raise GovernanceError(
                "bundle_id",
                "does not match the existing governance bundle",
                code="governance-bundle-mismatch",
            )
        ledger = loaded.ledger
        expected_hash: str | None = loaded.content_hash
    else:
        ledger = (
            GovernanceLedger.empty()
            if bundle_id is None
            else validate_governance_ledger(
                GovernanceLedger(bundle_id=bundle_id)
            )
        )
        expected_hash = None

    snapshot = _validated_artifact_snapshot(
        wiki_dir,
        allow_governance_recovery=ledger_present,
    )
    if ledger_present:
        _assert_bundle_continuity(snapshot, ledger)
    updated = reconcile_concepts(
        ledger,
        concept_references_from_knowledge(
            strip_governance_projection(snapshot.validated.knowledge)
        ),
    )
    return snapshot, ledger, expected_hash, updated


def _run_init(args) -> None:
    wiki_dir = _wiki_root(args.wiki_dir)
    if args.dry_run:
        snapshot, prior, _expected_hash, updated = _init_ledger(
            wiki_dir,
            bundle_id=args.bundle_id,
        )
        plan = _projected_commit_plan(wiki_dir, snapshot, updated)
        _print_payload(
            _mutation_preview_payload(
                "init",
                updated,
                changed=prior != updated or plan.changed,
                dry_run=True,
            )
        )
        return

    with governance_lock(wiki_dir):
        snapshot, prior, expected_hash, updated = _init_ledger(
            wiki_dir,
            bundle_id=args.bundle_id,
        )
        plan = _projected_commit_plan(wiki_dir, snapshot, updated)
        _assert_snapshot_unchanged(wiki_dir, snapshot)
        write_result = save_governance(
            wiki_dir,
            updated,
            expected_hash=expected_hash,
        )
        commit_result = commit_knowledge_artifacts(plan)
    _print_payload(
        _mutation_preview_payload(
            "init",
            updated,
            changed=(
                prior != updated
                or write_result.changed
                or commit_result.changed
            ),
            dry_run=False,
        )
    )


def _lifecycle_mutation(
    *,
    uid: str,
    state: str,
    actor_kind: str,
    actor_id: str,
    authored_at: str,
    successor_uid: str | None,
    reason: str,
) -> LedgerMutation:
    actor = GovernanceActor(kind=actor_kind, actor_id=actor_id)

    def mutate(ledger: GovernanceLedger, _knowledge: KnowledgeIndex):
        return set_lifecycle(
            ledger,
            uid,
            state,
            actor=actor,
            authored_at=authored_at,
            successor_uid=successor_uid,
            reason=reason,
        )

    return mutate


def _run_lifecycle(
    args,
    *,
    state_override: str | None = None,
    action_override: str | None = None,
) -> None:
    state = state_override or args.state
    successor_uid = getattr(args, "successor_uid", None)
    if state == Lifecycle.SUPERSEDED.value and successor_uid is None:
        raise GovernanceError(
            "successor_uid",
            "is required when superseding a concept",
        )
    _run_existing_mutation(
        _wiki_root(args.wiki_dir),
        action=action_override or f"lifecycle-{state}",
        dry_run=args.dry_run,
        mutation=_lifecycle_mutation(
            uid=args.uid,
            state=state,
            actor_kind=args.actor_kind,
            actor_id=args.actor_id,
            authored_at=args.authored_at,
            successor_uid=successor_uid,
            reason=args.reason,
        ),
    )


def _run_move(args) -> None:
    wiki_dir = _wiki_root(args.wiki_dir)

    def prepare():
        loaded = _load_required_ledger(wiki_dir)
        snapshot = _committed_artifact_snapshot(wiki_dir)
        _assert_bundle_continuity(snapshot, loaded.ledger)
        updated = mutate(loaded.ledger)
        try:
            plan = _projected_commit_plan(
                wiki_dir,
                snapshot,
                updated,
            )
        except GovernanceError as exc:
            if exc.code not in {
                "governance-missing-uid",
                "governance-allocation-conflict",
            }:
                raise
            plan = None
        return snapshot, loaded, updated, plan

    def mutate(ledger: GovernanceLedger):
        return move_concept(
            ledger,
            args.uid,
            locator=args.locator,
            natural_key=args.natural_key,
        )

    if args.dry_run:
        _snapshot, loaded, updated, plan = prepare()
        _print_payload(
            _mutation_preview_payload(
                "move",
                updated,
                changed=loaded.ledger != updated or (
                    plan.changed if plan is not None else False
                ),
                dry_run=True,
                projection=("current" if plan is not None else "pending-sync"),
            )
        )
        return

    with governance_lock(wiki_dir):
        snapshot, loaded, updated, plan = prepare()
        _assert_snapshot_unchanged(wiki_dir, snapshot)
        write_result = save_governance(
            wiki_dir,
            updated,
            expected_hash=loaded.content_hash,
        )
        commit_result = (
            commit_knowledge_artifacts(plan) if plan is not None else None
        )
    _print_payload(
        _mutation_preview_payload(
            "move",
            updated,
            changed=write_result.changed or (
                commit_result.changed if commit_result is not None else False
            ),
            dry_run=False,
            projection=("current" if plan is not None else "pending-sync"),
        )
    )


def _run_alias(args) -> None:
    def mutate(ledger: GovernanceLedger, _knowledge: KnowledgeIndex):
        return add_alias(ledger, args.uid, args.alias_type, args.value)

    _run_existing_mutation(
        _wiki_root(args.wiki_dir),
        action="alias",
        dry_run=args.dry_run,
        mutation=mutate,
    )


def _concept_for_uid(
    ledger: GovernanceLedger,
    knowledge: KnowledgeIndex,
    uid: str,
):
    allocation = ledger.concepts.get(uid)
    if allocation is None:
        raise GovernanceError("uid", "does not identify an allocated concept")
    concept = next(
        (
            item
            for item in knowledge.concepts
            if item.locator == allocation.locator
        ),
        None,
    )
    if concept is None:
        raise GovernanceError(
            "uid",
            "identifies a concept absent from the current knowledge snapshot",
            code="concept-missing",
        )
    return concept


def _run_review(args) -> None:
    if args.reviewer_kind != "human":
        raise GovernanceError(
            "reviewer_kind",
            "governance review events require an explicit human reviewer",
        )

    def mutate(ledger: GovernanceLedger, knowledge: KnowledgeIndex):
        concept = _concept_for_uid(ledger, knowledge, args.uid)
        evidence = current_review_evidence(concept)
        if evidence is None:
            raise GovernanceError(
                "evidence",
                "the current concept evidence basis is incompatible with review",
                code="basis-incompatible",
            )
        return add_review_event(
            ledger,
            args.uid,
            section_locator=args.section,
            scope_hash=review_scope_hash(knowledge, args.section),
            evidence=evidence,
            reviewer=GovernanceActor(
                kind=args.reviewer_kind,
                actor_id=args.reviewer_id,
            ),
            method=args.method,
            method_version=args.method_version,
            authored_at=args.authored_at,
        )

    _run_existing_mutation(
        _wiki_root(args.wiki_dir),
        action="review",
        dry_run=args.dry_run,
        mutation=mutate,
    )


def _status_payload(
    ledger: GovernanceLedger,
    knowledge: KnowledgeIndex,
    *,
    event_limit: int,
) -> dict[str, object]:
    active_locators = {concept.locator for concept in knowledge.concepts}
    aliases_by_uid: dict[str, list[dict[str, str]]] = {
        uid: [] for uid in ledger.concepts
    }
    for alias in ledger.aliases.values():
        aliases_by_uid[alias.uid].append(
            {"type": alias.alias_type, "value": alias.value}
        )
    lifecycle_by_uid: dict[str, list[object]] = {
        uid: [] for uid in ledger.concepts
    }
    for event in ledger.lifecycle_events.values():
        lifecycle_by_uid[event.concept_uid].append(event)
    reviews_by_uid: dict[str, list[object]] = {
        uid: [] for uid in ledger.concepts
    }
    for event in ledger.review_events.values():
        reviews_by_uid[event.concept_uid].append(event)

    concepts: list[dict[str, object]] = []
    for uid, allocation in sorted(ledger.concepts.items()):
        uid_lifecycle_events = lifecycle_by_uid[uid]
        predecessor_ids = {
            event.previous_event_id
            for event in uid_lifecycle_events
            if event.previous_event_id is not None
        }
        terminal = next(
            (
                event
                for event in uid_lifecycle_events
                if event.event_id not in predecessor_ids
            ),
            None,
        )
        state = terminal.to_state if terminal is not None else Lifecycle.UNKNOWN
        reviews = sorted(
            reviews_by_uid[uid],
            key=lambda item: (item.authored_at, item.event_id),
        )
        evaluations = [
            evaluate_review_event(event, ledger, knowledge) for event in reviews
        ]
        lifecycle_events = sorted(
            uid_lifecycle_events,
            key=lambda item: (item.authored_at, item.event_id),
        )
        selected_lifecycle_events = lifecycle_events[-event_limit:]
        selected_reviews = reviews[-event_limit:]
        selected_evaluations = evaluations[-event_limit:]
        concepts.append(
            {
                "uid": uid,
                "locator": allocation.locator,
                "natural_key": allocation.natural_key,
                "concept_kind": allocation.concept_kind,
                "present": allocation.locator in active_locators,
                "lifecycle": state.value,
                "successor_uid": (
                    terminal.successor_uid if terminal is not None else None
                ),
                "aliases": sorted(
                    aliases_by_uid[uid],
                    key=lambda item: (item["type"], item["value"]),
                ),
                "lifecycle_events": [
                    {
                        "event_id": event.event_id,
                        "from": event.from_state.value,
                        "to": event.to_state.value,
                        "authored_at": event.authored_at,
                    }
                    for event in selected_lifecycle_events
                ],
                "lifecycle_event_count": len(lifecycle_events),
                "lifecycle_event_coverage": {
                    "total": len(lifecycle_events),
                    "returned": len(selected_lifecycle_events),
                    "limit": event_limit,
                    "truncated": (
                        len(selected_lifecycle_events) < len(lifecycle_events)
                    ),
                },
                "reviews": [
                    {
                        "event_id": evaluation.event_id,
                        "section_locator": event.section_locator,
                        "reviewer": event.reviewer.to_payload(),
                        "method": {
                            "id": event.method,
                            "version": event.method_version,
                        },
                        "authored_at": event.authored_at,
                        "state": evaluation.state,
                        "reasons": list(evaluation.reasons),
                    }
                    for event, evaluation in zip(
                        selected_reviews,
                        selected_evaluations,
                        strict=True,
                    )
                ],
                "review_event_count": len(reviews),
                "review_event_coverage": {
                    "total": len(reviews),
                    "returned": len(selected_reviews),
                    "limit": event_limit,
                    "truncated": len(selected_reviews) < len(reviews),
                },
            }
        )
    return {
        "state": "governed",
        "bundle_id": ledger.bundle_id,
        "governance_hash": ledger.content_hash(),
        "concept_count": len(concepts),
        "concepts": concepts,
        "event_limit": event_limit,
    }


def _run_status(args) -> None:
    if args.event_limit > MAX_EVENT_LIMIT:
        raise GovernanceError(
            "event_limit",
            f"must not exceed {MAX_EVENT_LIMIT}",
        )
    wiki_dir = _wiki_root(args.wiki_dir)
    state = load_knowledge_state(
        wiki_dir,
        policy=KnowledgeMismatchPolicy.REJECT,
    )
    path = wiki_dir / GOVERNANCE_FILENAME
    if not (path.exists() or path.is_symlink()):
        payload: dict[str, object] = {
            "state": "ungoverned",
            "knowledge_state": state.status.value,
        }
    else:
        if state.knowledge is None:
            raise GovernanceError(
                "knowledge",
                "a governed ledger requires a valid knowledge projection",
            )
        loaded = load_governance(wiki_dir)
        payload = _status_payload(
            loaded.ledger,
            state.knowledge,
            event_limit=args.event_limit,
        )
        payload["knowledge_state"] = state.status.value
    if args.format == "json":
        _print_payload(payload)
        return
    if payload["state"] == "ungoverned":
        print(f"Knowledge governance: ungoverned ({payload['knowledge_state']})")
        return
    print(
        "Knowledge governance: "
        f"{payload['bundle_id']} — {payload['concept_count']} concepts "
        f"({payload['governance_hash']})"
    )
    for concept in payload["concepts"]:
        print(
            f"{concept['uid']} {concept['lifecycle']} "
            f"{concept['locator']}"
        )


def _scope_locator_for_uid(
    knowledge: KnowledgeIndex,
    uid: str | None,
) -> str | None:
    if uid is None:
        return None
    for concept in knowledge.concepts:
        summary = concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
        if isinstance(summary, Mapping) and summary.get("uid") == uid:
            return concept.locator
    raise GovernanceError(
        "uid",
        "does not identify a current governed concept",
        code="concept-missing",
    )


def _run_verify(args) -> None:
    wiki_dir = _wiki_root(args.wiki_dir)
    state = load_knowledge_state(
        wiki_dir,
        policy=KnowledgeMismatchPolicy.REJECT,
    )
    if (
        state.status is not KnowledgeLoadState.VALID
        or state.knowledge is None
        or state.manifest_basis is None
        or state.manifest_basis.artifact_hashes is None
    ):
        raise GovernanceError(
            "knowledge",
            "a complete valid knowledge snapshot is required",
        )
    marker = state.manifest_basis.artifact_hashes
    scope_locator = _scope_locator_for_uid(state.knowledge, args.uid)
    context = build_artifact_verification_context(
        state.knowledge,
        knowledge_hash=marker.knowledge_index_hash,
        surface_index_hash=marker.surface_index_hash,
        evaluated_envelope_hash=marker.evaluated_envelope_hash,
        governance_hash=marker.governance_hash,
        scope_locator=scope_locator,
    )
    receipt = (
        verify(context, args.checker)
        if args.dry_run
        else verify_and_write_receipt(
            wiki_dir,
            context,
            args.checker,
        )
    )
    _print_payload(
        {
            "action": "verify",
            "dry_run": args.dry_run,
            "knowledge_hash": receipt.knowledge_hash,
            "result": receipt.result.value,
            "scope_uid": receipt.scope_uid,
            "checks": [
                {
                    "id": check.checker_id,
                    "version": check.checker_version,
                    "result": check.result.value,
                    "diagnostic_count": len(check.diagnostics),
                }
                for check in receipt.checks
            ],
        }
    )
    if receipt.result is VerificationResult.FAILED:
        raise SystemExit(1)


def run(args) -> None:
    action = args.knowledge_action
    if action == "init":
        _run_init(args)
    elif action == "status":
        _run_status(args)
    elif action == "move":
        _run_move(args)
    elif action == "alias":
        _run_alias(args)
    elif action == "lifecycle":
        lifecycle_action = args.lifecycle_action
        if lifecycle_action == "set":
            _run_lifecycle(args)
        elif lifecycle_action == "deprecate":
            _run_lifecycle(
                args,
                state_override=Lifecycle.DEPRECATED.value,
                action_override="deprecate",
            )
        elif lifecycle_action == "supersede":
            _run_lifecycle(
                args,
                state_override=Lifecycle.SUPERSEDED.value,
                action_override="supersede",
            )
        else:  # pragma: no cover - argparse owns this invariant.
            raise GovernanceError("lifecycle_action", "is not supported")
    elif action == "deprecate":
        _run_lifecycle(
            args,
            state_override=Lifecycle.DEPRECATED.value,
            action_override="deprecate",
        )
    elif action == "supersede":
        _run_lifecycle(
            args,
            state_override=Lifecycle.SUPERSEDED.value,
            action_override="supersede",
        )
    elif action == "review":
        _run_review(args)
    elif action == "verify":
        _run_verify(args)
    else:  # pragma: no cover - argparse owns this invariant.
        raise GovernanceError("knowledge_action", "is not supported")


__all__ = [
    "ACTOR_KINDS",
    "ALIAS_LOCATOR",
    "ALIAS_NATURAL_KEY",
    "run",
]
