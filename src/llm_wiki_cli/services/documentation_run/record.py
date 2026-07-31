"""Documentation-run record lifecycle."""

from __future__ import annotations

from .dependencies import *
from .contracts import *
from ._legacy import *

def record_documentation_agent_result(
    workspace: str | Path,
    result: DocumentationAgentResult | Mapping[str, Any],
) -> DocumentationRun:
    """Validate, independently reconcile, and persist a worker result."""

    workspace_root = _resolve_workspace_root_argument(workspace)
    run = load_documentation_run(workspace_root)
    normalized = DocumentationAgentResult.from_dict(
        result.to_dict() if isinstance(result, DocumentationAgentResult) else result
    )
    if normalized.run_id != run.run_id:
        raise DocumentationSchemaError(
            "Agent result run_id does not match the workspace."
        )
    if normalized.stage != run.current_stage:
        raise DocumentationSchemaError(
            f"Agent result stage {normalized.stage!r} does not match active stage "
            f"{run.current_stage!r}."
        )
    attempt = run.stage_attempts.get(normalized.stage, 0)
    if attempt < 1:
        raise DocumentationSchemaError(
            "Agent result requires a previously recorded stage packet attempt."
        )
    result_dir = workspace_root / RUN_CONTROL_DIR / "results"
    result_path = result_dir / f"{normalized.stage}-{attempt:02d}.json"
    if result_path.exists():
        raise DocumentationSchemaError(
            "This stage-packet attempt already has a result; build a new packet "
            "before recording another result."
        )
    _verify_stage_dispatch_integrity(
        workspace_root,
        run,
        stage=normalized.stage,
        attempt=attempt,
    )
    if (
        normalized.reported_source_writes
        or normalized.reported_input_wiki_writes
        or normalized.reported_generated_block_edits
    ):
        _block_run_for_integrity(
            workspace_root,
            run,
            "Worker reported a forbidden source/input/generated mutation.",
        )
        raise DocumentationIntegrityError(
            "Agent result reports forbidden source, input-wiki, or generated-block writes."
        )

    try:
        integrity_checks = _verify_read_only_inputs(workspace_root, run)
    except DocumentationIntegrityError as exc:
        _block_run_for_integrity(workspace_root, run, str(exc))
        raise
    before_path = run.evidence.get(f"{normalized.stage}_before")
    if not before_path:
        raise DocumentationIntegrityError(
            "No pre-stage wiki baseline exists for result reconciliation."
        )
    before_payload = _read_json(_workspace_path(workspace_root, before_path))
    before_tree = TreeBaseline.from_dict(before_payload["tree"])
    wiki_root = workspace_root / run.paths["wiki"]
    current_tree = capture_tree_baseline(
        wiki_root, display=f"{normalized.stage}_wiki_after"
    )
    actual_changed = _changed_paths(before_tree, current_tree)
    if set(actual_changed) != set(normalized.changed_wiki_paths):
        _block_run_for_integrity(
            workspace_root,
            run,
            "Worker changed-path report does not match the workspace diff.",
        )
        raise DocumentationIntegrityError(
            "Agent changed_wiki_paths do not match independently derived changes: "
            f"reported={sorted(normalized.changed_wiki_paths)} actual={actual_changed}"
        )
    worklist = _read_json(
        _workspace_path(workspace_root, run.evidence["semantic_worklist"])
    )
    try:
        _validate_stage_changed_paths(
            normalized.stage,
            actual_changed,
            current_tree=current_tree,
            worklist=worklist,
            runtime_capture_paths=(
                str(capture["capture_path"])
                for capture in normalized.runtime_captures
                if isinstance(capture.get("capture_path"), str)
            ),
        )
    except DocumentationIntegrityError as exc:
        _block_run_for_integrity(workspace_root, run, str(exc))
        raise
    generated_diff = compare_generated_ownership(
        before_payload.get("generated_ownership", {}), wiki_root
    )
    if any(generated_diff.values()):
        _block_run_for_integrity(
            workspace_root,
            run,
            f"Generated ownership changed: {generated_diff}",
        )
        raise DocumentationIntegrityError(
            f"Agent modified CLI-owned generated content: {generated_diff}"
        )

    _preflight_documentation_native_evidence(
        workspace_root,
        run,
        normalized,
        actual_changed=actual_changed,
    )
    _validate_result_work_ids(
        normalized, worklist, stage=normalized.stage, wiki_root=wiki_root
    )
    if (
        normalized.stage == "review"
        and normalized.status == "complete"
        and not normalized.claims_evidence_pages
    ):
        raise DocumentationSchemaError(
            "Review results must cite at least one independently sampled canonical "
            "wiki evidence page."
        )
    try:
        reconciled_imported_edits = _reconcile_imported_page_edits(
            normalized,
            worklist,
            actual_changed=actual_changed,
            before_tree=before_tree,
            after_tree=current_tree,
            wiki_root=wiki_root,
        )
    except DocumentationIntegrityError as exc:
        _block_run_for_integrity(workspace_root, run, str(exc))
        raise
    phase = f"{normalized.stage}-{attempt:02d}"
    try:
        native_transaction = _capture_native_evidence_transaction(
            workspace_root,
            run,
            phase=phase,
        )
    except Exception as exc:
        integrity_exc = (
            exc
            if isinstance(exc, DocumentationIntegrityError)
            else DocumentationIntegrityError(
                "Cannot capture the documentation native-evidence transaction: "
                f"{exc}"
            )
        )
        _block_run_for_integrity(workspace_root, run, str(integrity_exc))
        if integrity_exc is exc:
            raise
        raise integrity_exc from exc
    try:
        native_refresh, refreshed_knowledge_view = (
            _refresh_and_reanchor_native_projection(
                workspace_root,
                run,
                phase=phase,
                changed_wiki_paths=actual_changed,
            )
        )
        reconciled_claims, reconciled_captures = (
            _reconcile_documentation_native_evidence(
                workspace_root,
                run,
                normalized,
                refreshed_knowledge_view=refreshed_knowledge_view,
            )
        )
    except Exception as exc:
        integrity_exc = (
            exc
            if isinstance(exc, DocumentationIntegrityError)
            else DocumentationIntegrityError(
                "Documentation native refresh or evidence reconciliation "
                f"failed: {exc}"
            )
        )
        try:
            _rollback_native_evidence_transaction(
                run,
                native_transaction,
                cause=integrity_exc,
            )
        except DocumentationIntegrityError as rollback_exc:
            _block_run_for_integrity(workspace_root, run, str(rollback_exc))
            raise rollback_exc from integrity_exc
        _block_run_for_integrity(workspace_root, run, str(integrity_exc))
        if integrity_exc is exc:
            raise
        raise integrity_exc from exc
    result_payload = {
        **normalized.to_dict(),
        "reconciliation": {
            "actual_changed_wiki_paths": actual_changed,
            "imported_page_edits": reconciled_imported_edits,
            "claim_evidence": reconciled_claims,
            "runtime_captures": reconciled_captures,
            "source_and_input_integrity": integrity_checks,
            "generated_ownership": generated_diff,
            "native_projection_refresh": (
                {
                    "status": native_refresh["status"],
                    "phase": native_refresh["phase"],
                    "evidence": (
                        f"{RUN_CONTROL_DIR}/evidence/native-refresh-"
                        f"{normalized.stage}-{attempt:02d}.json"
                    ),
                }
                if native_refresh is not None
                else None
            ),
            "verified_at": _utc_now(),
        },
    }
    _write_json(result_path, result_payload)
    _write_json(result_dir / f"{normalized.stage}.json", result_payload)
    run.evidence[f"{normalized.stage}_result"] = result_path.relative_to(
        workspace_root
    ).as_posix()
    result_stage_path = _stage_event_path(
        workspace_root,
        normalized.stage,
        attempt=attempt,
        event="result",
    )
    _write_json(
        result_stage_path,
        {
            "schema_version": DOCUMENTATION_RUN_SCHEMA_VERSION,
            "run_id": run.run_id,
            "stage": normalized.stage,
            "attempt": attempt,
            "status": normalized.status,
            "result": run.evidence[f"{normalized.stage}_result"],
            "result_hash": hash_bytes(result_path.read_bytes()),
            "recorded_at": _utc_now(),
        },
    )
    _merge_unique(run.work["reused"], normalized.reused_work_ids)
    _merge_unique(run.work["completed"], normalized.completed_work_ids)
    _merge_unique(run.work["deferred"], normalized.deferred_work_ids)
    if normalized.stage != "review":
        _merge_agent_findings(run, normalized.findings)

    if normalized.status == "blocked":
        _block_run_for_integrity(
            workspace_root,
            run,
            "Worker returned blocked status.",
            integrity=False,
        )
        return run
    if normalized.status == "partial":
        if normalized.stage == "wiki-enrichment":
            _reconcile_semantic_readiness(workspace_root, run, normalized, worklist)
        run.validation_results.append(
            {
                "check": f"{normalized.stage}_worker_status",
                "ok": False,
                "status": "partial",
                "evidence": run.evidence[f"{normalized.stage}_result"],
            }
        )
        save_documentation_run(workspace_root, run)
        return run
    if normalized.stage == "wiki-enrichment":
        readiness = _reconcile_semantic_readiness(
            workspace_root, run, normalized, worklist
        )
        if not readiness["passed"]:
            _block_run_for_integrity(
                workspace_root,
                run,
                "Semantic readiness gate did not pass.",
                integrity=False,
            )
            return run
        if not _run_wiki_validation_pair(
            workspace_root, run, phase=f"wiki-enrichment-{attempt:02d}"
        ):
            _block_run_for_integrity(
                workspace_root,
                run,
                "Post-enrichment lint/CI validation did not pass.",
                integrity=False,
            )
            return run
        transition_documentation_run(run, "user_docs")
    elif normalized.stage == "user-docs":
        _verify_user_docs_gate(wiki_root, run, normalized)
        if not _run_wiki_validation_pair(
            workspace_root, run, phase=f"user-docs-{attempt:02d}"
        ):
            _block_run_for_integrity(
                workspace_root,
                run,
                "Post-user-docs lint/CI validation did not pass.",
                integrity=False,
            )
            return run
        transition_documentation_run(run, "review")
    elif normalized.stage == "review":
        review_loop = _record_review_ledger_iteration(
            workspace_root,
            run,
            review_result=normalized,
            review_result_path=result_path,
        )
        if review_loop["decision"]["blocked"]:
            _block_run_for_integrity(
                workspace_root,
                run,
                review_loop["decision"]["rationale"],
                integrity=False,
            )
            return run
        run.validation_results.append(
            {
                "check": "independent_review",
                "ok": not _has_unresolved_high_findings(run.unresolved_findings),
                "evidence": run.evidence["review_ledger"],
                "requires_supervisor_reconciliation": review_loop["decision"][
                    "requires_supervisor_reconciliation"
                ],
            }
        )
        if review_loop["decision"]["action"] == "return_to_worker":
            adjustment_state = _review_adjustment_state(run.unresolved_findings)
            transition_documentation_run(run, adjustment_state)
    save_documentation_run(workspace_root, run)
    return run


def _preflight_documentation_native_evidence(
    workspace_root: Path,
    run: DocumentationRun,
    result: DocumentationAgentResult,
    *,
    actual_changed: Iterable[str],
) -> None:
    """Reject malformed evidence before native refresh can mutate authority."""

    if result.runtime_captures and result.stage != "user-docs":
        raise DocumentationSchemaError(
            "Runtime capture provenance is accepted only in the user-docs stage."
        )

    evidence_pages = set(result.claims_evidence_pages)
    for claim in result.claim_evidence:
        canonical_page = str(claim["canonical_page"])
        if canonical_page not in evidence_pages:
            raise DocumentationSchemaError(
                "Claim evidence must cite its canonical page through "
                f"claims_evidence_pages: {claim['claim_id']}"
            )
        internal_ref = claim.get("internal_evidence_ref")
        if isinstance(internal_ref, str):
            path = _workspace_path(workspace_root, internal_ref)
            if path.is_symlink() or not path.is_file():
                raise DocumentationSchemaError(
                    f"Claim evidence internal reference is missing: {internal_ref}"
                )

    changed = {str(path) for path in actual_changed}
    for capture in result.runtime_captures:
        capture_path = capture.get("capture_path")
        if isinstance(capture_path, str) and capture_path not in changed:
            raise DocumentationSchemaError(
                "Persisted runtime captures must be independently visible in the "
                f"stage changed-path set: {capture_path}"
            )

    graph_limits = {
        int(graph["limit"])
        for claim in result.claim_evidence
        if isinstance((graph := claim.get("graph_query")), Mapping)
    }
    if len(graph_limits) > 1:
        raise DocumentationSchemaError(
            "All claim-evidence graph queries in one result must reuse one "
            "operation-scoped query limit."
        )

    try:
        preflight_runtime_capture_records(
            result.runtime_captures,
            wiki_root=workspace_root / run.paths["wiki"],
        )
    except DocumentationClaimEvidenceError as exc:
        raise DocumentationSchemaError(str(exc)) from exc


def _capture_native_evidence_transaction(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    phase: str,
) -> _NativeEvidenceTransaction:
    wiki_root = workspace_root / run.paths["wiki"]
    evidence_root = workspace_root / RUN_CONTROL_DIR / "evidence"
    control_paths = {
        evidence_root / f"native-refresh-{phase}.json",
        evidence_root / "native-refresh.json",
        documentation_run_path(workspace_root),
    }
    ownership = run.evidence.get("generated_ownership")
    if ownership:
        control_paths.add(_workspace_path(workspace_root, ownership))
    return _NativeEvidenceTransaction(
        wiki_root=wiki_root,
        artifact_snapshot=_capture_native_artifact_bytes(wiki_root),
        control_snapshot=_capture_exact_file_bytes(control_paths),
        run_state=copy.deepcopy(run.__dict__),
    )


def _rollback_native_evidence_transaction(
    run: DocumentationRun,
    transaction: _NativeEvidenceTransaction,
    *,
    cause: BaseException,
) -> None:
    run.__dict__.clear()
    run.__dict__.update(copy.deepcopy(transaction.run_state))
    _rollback_native_refresh_transaction(
        transaction.wiki_root,
        transaction.artifact_snapshot,
        transaction.control_snapshot,
        cause=cause,
    )


def _reconcile_documentation_native_evidence(
    workspace_root: Path,
    run: DocumentationRun,
    result: DocumentationAgentResult,
    *,
    refreshed_knowledge_view: KnowledgeReadView | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Recompute native claim coordinates and verify out-of-band captures."""

    if not result.claim_evidence and not result.runtime_captures:
        return [], []

    graph_limits = {
        int(graph["limit"])
        for claim in result.claim_evidence
        if isinstance((graph := claim.get("graph_query")), Mapping)
    }
    if len(graph_limits) > 1:
        raise DocumentationIntegrityError(
            "All claim-evidence graph queries in one result must reuse one "
            "operation-scoped query limit."
        )
    query_limit = next(iter(graph_limits), 20)
    wiki_root = workspace_root / run.paths["wiki"]

    service = None
    try:
        runtime_paths = _load_bound_runtime_policy(workspace_root, run)
        source_root = runtime_paths.get("source_root")
        source_is_current = run.baseline.get("freshness") == "verified_current"
        source_is_available = source_root is not None and source_root.is_dir()
        if source_root is not None and source_is_available and source_is_current:
            if refreshed_knowledge_view is not None:
                service = build_documentation_query_service_from_view(
                    wiki_root=wiki_root,
                    knowledge_view=refreshed_knowledge_view,
                    limit=query_limit,
                )
            else:
                service = build_live_documentation_query_service(
                    source_root=source_root,
                    wiki_root=wiki_root,
                    limit=query_limit,
                    read_only=True,
                    helper_cache_dir=runtime_paths.get("helper_cache_root"),
                    include_plugins=bool(
                        run.policy.get("source_plugins_trusted", False)
                    ),
                    require_live_freshness=True,
                )
        else:
            service = build_snapshot_documentation_query_service(
                wiki_root=wiki_root,
                limit=query_limit,
            )
    except (
        OSError,
        RecursionError,
        RuntimeError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as exc:
        raise DocumentationIntegrityError(
            "Cannot independently build the committed native view required "
            f"for evidence reconciliation: {exc}"
        ) from exc

    try:
        claims = (
            reconcile_claim_evidence_records(result.claim_evidence, service)
            if service is not None
            else ()
        )
        captures = reconcile_runtime_capture_records(
            result.runtime_captures,
            wiki_root=wiki_root,
            service=service,
        )
    except (DocumentationClaimEvidenceError, DocumentationQueryError) as exc:
        raise DocumentationIntegrityError(
            f"Documentation native evidence did not reconcile: {exc}"
        ) from exc
    return [dict(item) for item in claims], [dict(item) for item in captures]

__all__ = (
    'record_documentation_agent_result',
    '_preflight_documentation_native_evidence',
    '_capture_native_evidence_transaction',
    '_rollback_native_evidence_transaction',
    '_reconcile_documentation_native_evidence',
)
