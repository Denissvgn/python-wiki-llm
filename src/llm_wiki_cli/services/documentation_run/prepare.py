"""Documentation-run prepare services."""

from __future__ import annotations

from .dependencies import *
from .contracts import *
from .schema import *
from .workspace import *
from .integrity import *
from .refresh import *

def prepare_documentation_run(
    workspace: str | Path,
    *,
    baseline_strategy: str = "bootstrap_source",
    source_root: str | Path | None = None,
    input_wiki_root: str | Path | None = None,
    freshness_policy: str = "require-current",
    site_name: str,
    audiences: Iterable[str] | None = None,
    project_purpose: str | None = None,
    audience_intent: Mapping[str, str] | None = None,
    live_service_url: str | None = None,
    live_service_access_mode: str = "unspecified",
    live_service_observation_allowed: bool = False,
    helper_cache_root: str | Path | None = None,
    capture_root: str | Path | None = None,
    trust_source_plugins: bool = False,
    semantic_budget: int = 30,
    adjustment_loop_limit: int = 3,
    distribution_format: str = "mkdocs",
    link_mode: str = "http",
    knowledge_mode: str = "off",
    knowledge_public_repository_identity: str | None = None,
    refresh: bool = False,
) -> DocumentationRun:
    """Prepare a run with transactional rollback for initial creation and refresh."""

    refresh_transaction = _RefreshArchiveTransaction()
    initial_prepare_transaction = _InitialPrepareTransaction()
    try:
        run = _prepare_documentation_run_impl(
            workspace,
            baseline_strategy=baseline_strategy,
            source_root=source_root,
            input_wiki_root=input_wiki_root,
            freshness_policy=freshness_policy,
            site_name=site_name,
            audiences=audiences,
            project_purpose=project_purpose,
            audience_intent=audience_intent,
            live_service_url=live_service_url,
            live_service_access_mode=live_service_access_mode,
            live_service_observation_allowed=live_service_observation_allowed,
            helper_cache_root=helper_cache_root,
            capture_root=capture_root,
            trust_source_plugins=trust_source_plugins,
            semantic_budget=semantic_budget,
            adjustment_loop_limit=adjustment_loop_limit,
            distribution_format=distribution_format,
            link_mode=link_mode,
            knowledge_mode=knowledge_mode,
            knowledge_public_repository_identity=(
                knowledge_public_repository_identity
            ),
            refresh=refresh,
            refresh_transaction=refresh_transaction,
            initial_prepare_transaction=initial_prepare_transaction,
        )
        if refresh_transaction.active:
            _commit_refresh_archive(refresh_transaction)
        if initial_prepare_transaction.active:
            _commit_initial_prepare(initial_prepare_transaction)
        return run
    except BaseException as original:
        if refresh_transaction.active:
            try:
                _rollback_refresh_archive(refresh_transaction)
            except Exception as rollback_error:
                raise DocumentationIntegrityError(
                    "Explicit refresh failed and its prior run could not be restored; "
                    "the refresh transaction marker must be recovered before reuse: "
                    f"{rollback_error}"
                ) from original
        if initial_prepare_transaction.active:
            try:
                _rollback_initial_prepare(initial_prepare_transaction)
            except Exception as rollback_error:
                raise DocumentationIntegrityError(
                    "Initial documentation preparation failed and its lifecycle-owned "
                    "workspace artifacts could not be removed safely: "
                    f"{rollback_error}"
                ) from original
        raise


def _prepare_documentation_run_impl(
    workspace: str | Path,
    *,
    baseline_strategy: str = "bootstrap_source",
    source_root: str | Path | None = None,
    input_wiki_root: str | Path | None = None,
    freshness_policy: str = "require-current",
    site_name: str,
    audiences: Iterable[str] | None = None,
    project_purpose: str | None = None,
    audience_intent: Mapping[str, str] | None = None,
    live_service_url: str | None = None,
    live_service_access_mode: str = "unspecified",
    live_service_observation_allowed: bool = False,
    helper_cache_root: str | Path | None = None,
    capture_root: str | Path | None = None,
    trust_source_plugins: bool = False,
    semantic_budget: int = 30,
    adjustment_loop_limit: int = 3,
    distribution_format: str = "mkdocs",
    link_mode: str = "http",
    knowledge_mode: str = "off",
    knowledge_public_repository_identity: str | None = None,
    refresh: bool = False,
    refresh_transaction: _RefreshArchiveTransaction,
    initial_prepare_transaction: _InitialPrepareTransaction,
) -> DocumentationRun:
    """Prepare or idempotently resume an external documentation workspace.

    The function performs deterministic baseline work only.  It does not ask
    intake questions, run a model, execute the target application, install
    target instructions, or prepare missing extractor helpers.
    """

    if baseline_strategy not in SUPPORTED_BASELINE_STRATEGIES:
        raise DocumentationSchemaError(
            f"Unsupported baseline strategy: {baseline_strategy!r}"
        )
    if freshness_policy not in SUPPORTED_FRESHNESS_POLICIES:
        raise DocumentationSchemaError(
            f"Unsupported wiki freshness policy: {freshness_policy!r}"
        )
    if not site_name or site_name.strip() in {"", "LLM Wiki"}:
        raise DocumentationSchemaError(
            "External user documentation requires a non-default site name."
        )
    if semantic_budget < 0:
        raise DocumentationSchemaError("semantic_budget must not be negative.")
    if adjustment_loop_limit < 1:
        raise DocumentationSchemaError("adjustment_loop_limit must be positive.")
    if distribution_format not in {"mkdocs", "plain", "docusaurus"}:
        raise DocumentationSchemaError(
            f"Unsupported documentation distribution format: {distribution_format!r}"
        )
    if link_mode not in {"http", "file"}:
        raise DocumentationSchemaError("link_mode must be http or file.")
    (
        knowledge_mode,
        knowledge_public_repository_identity,
    ) = _validate_documentation_projection_policy(
        knowledge_mode,
        knowledge_public_repository_identity,
    )

    if baseline_strategy == "bootstrap_source":
        if source_root is None:
            raise DocumentationSchemaError(
                "bootstrap_source requires an explicit source_root."
            )
        if input_wiki_root is not None:
            raise DocumentationSchemaError(
                "bootstrap_source cannot also specify input_wiki_root."
            )
        if freshness_policy != "require-current":
            raise DocumentationSchemaError(
                "bootstrap_source always uses require-current source freshness."
            )
    else:
        if input_wiki_root is None:
            raise DocumentationSchemaError(
                "adopt_existing_wiki requires an explicit input_wiki_root."
            )
        if source_root is None and freshness_policy != "allow-unverified":
            raise DocumentationSchemaError(
                "Wiki-only adoption requires freshness_policy='allow-unverified'."
            )

    workspace_root = _resolve_workspace_root_argument(workspace)
    _recover_interrupted_refresh(workspace_root)
    policy = resolve_documentation_policy(
        workspace_root,
        source_root=source_root,
        input_wiki_root=input_wiki_root,
        helper_cache_root=helper_cache_root,
        capture_root=capture_root,
        trust_source_plugins=trust_source_plugins,
        live_service_url=live_service_url,
        live_service_access_mode=live_service_access_mode,
        live_service_observation_allowed=live_service_observation_allowed,
    )
    intake = DocumentationIntakeBrief.from_values(
        project_purpose=project_purpose,
        audiences=audiences,
        audience_intent=audience_intent,
        live_service_url=live_service_url,
        live_service_access_mode=live_service_access_mode,
        live_service_observation_allowed=live_service_observation_allowed,
    )

    _assert_existing_workspace_layout_safe(workspace_root)
    run_path = documentation_run_path(workspace_root)
    if run_path.is_file() and not refresh:
        existing = load_documentation_run(workspace_root)
        _load_bound_runtime_policy(workspace_root, existing)
        _verify_initial_integrity_anchors(workspace_root, existing)
        _assert_resume_compatible(
            workspace_root,
            existing,
            policy=policy,
            baseline_strategy=baseline_strategy,
            intake=intake,
            site_name=site_name.strip(),
            freshness_policy=freshness_policy,
            semantic_budget=semantic_budget,
            adjustment_loop_limit=adjustment_loop_limit,
            distribution_format=distribution_format,
            link_mode=link_mode,
            knowledge_mode=knowledge_mode,
            knowledge_public_repository_identity=(
                knowledge_public_repository_identity
            ),
        )
        return existing
    initial_prepare = not run_path.is_file()
    initial_root_identity: tuple[int, int, int] | None = None
    if initial_prepare:
        initial_root_identity = _assert_new_documentation_workspace_empty(
            workspace_root
        )
    continuation_snapshot: _RefreshContinuationSnapshot | None = None
    continuation_archive: str | None = None
    if run_path.is_file() and refresh:
        prior_run = load_documentation_run(workspace_root)
        _load_bound_runtime_policy(workspace_root, prior_run)
        continuation_snapshot = _capture_refresh_continuation(workspace_root, prior_run)
        continuation_archive = _archive_owned_run(
            workspace_root,
            prior_run,
            transaction=refresh_transaction,
        )

    _create_workspace_layout(
        workspace_root,
        initial_transaction=(initial_prepare_transaction if initial_prepare else None),
        existing_root_identity=initial_root_identity,
    )
    _write_runtime_policy(workspace_root, policy)
    source_baseline = None
    source_baseline_path: Path | None = None
    source = {
        "available": False,
        "display_identifier": "source_unavailable",
        "revision": "source_unavailable",
        "revision_kind": "unavailable",
    }
    if policy.source_root is not None:
        source_baseline = source_tree_baseline(policy.source_root)
        source = source_identity(policy.source_root, source_baseline)
        source_baseline_path = _workspace_path(
            workspace_root, f"{RUN_CONTROL_DIR}/evidence/source-baseline.json"
        )
        _write_json(source_baseline_path, source_baseline.to_dict())

    skills = _export_documentation_skills(workspace_root)
    run_id = _new_run_id()
    created_at = _utc_now()
    baseline: dict[str, Any]
    imported_pages: list[Mapping[str, Any]] = []
    bootstrap_summary: dict[str, Any] = {}
    wiki_input_evidence: dict[str, Any] | None = None
    workspace_refresh_evidence: dict[str, Any] | None = None
    continuation_evidence: dict[str, Any] | None = None
    native_refresh_evidence: dict[str, Any] | None = None
    continuation_paths: tuple[str, ...] = ()
    wiki_root = workspace_root / "wiki"

    if baseline_strategy == "bootstrap_source":
        from ..bootstrap_runtime import execute_bootstrap

        result = execute_bootstrap(
            BootstrapRequest(
                source_root=policy.source_root or "",
                wiki_root=wiki_root,
                depth="full",
                overwrite=False,
                source_adapter=True,
                helper_cache_dir=str(policy.helper_cache_root)
                if policy.helper_cache_root is not None
                else None,
                trust_source_plugins=policy.trust_source_plugins,
            )
        )
        bootstrap_summary = _portable_bootstrap_summary(
            result.to_dict(), workspace_root=workspace_root
        )
        _write_json(
            workspace_root / RUN_CONTROL_DIR / "evidence" / "bootstrap.json",
            bootstrap_summary,
        )
        baseline = {
            "strategy": "bootstrap_source",
            "freshness_policy": "require-current",
            "freshness": "verified_current",
            "source_revision": source["revision"],
            "input_wiki": None,
        }
    else:
        from ..documentation_wiki_input import (
            _adopt_documentation_wiki_snapshot_with_runtime,
        )

        snapshot = _adopt_documentation_wiki_snapshot_with_runtime(
            policy.input_wiki_root or "",
            wiki_root,
            source_root=policy.source_root,
            freshness_policy=freshness_policy,
            trust_source_plugins=policy.trust_source_plugins,
            helper_cache_dir=policy.helper_cache_root,
        )
        wiki_input_evidence = snapshot.to_dict()
        imported_pages = list(
            getattr(snapshot, "semantic_pages", None)
            or wiki_input_evidence.get("semantic_pages", [])
        )
        _write_json(
            workspace_root / RUN_CONTROL_DIR / "evidence" / "wiki-input.json",
            wiki_input_evidence,
        )
        snapshot_freshness = str(
            getattr(snapshot, "freshness", None)
            or wiki_input_evidence.get("freshness", "unverified")
        )
        refresh_decision = wiki_input_evidence.get("refresh_decision")
        if snapshot.workspace_refresh_required:
            if policy.source_root is None:
                raise DocumentationSchemaError(
                    "Workspace-only snapshot refresh requires an explicit source root."
                )
            from ..bootstrap_runtime import (
                _execute_documentation_workspace_refresh,
            )

            refresh_before = capture_tree_baseline(
                wiki_root,
                display="workspace_wiki_before_refresh",
            )
            imported_semantic_text = {
                relative: (wiki_root / relative).read_text(encoding="utf-8")
                for relative in snapshot.semantic_markdown_paths
                if (wiki_root / relative).is_file()
            }
            refresh_result = _execute_documentation_workspace_refresh(
                BootstrapRequest(
                    source_root=policy.source_root,
                    wiki_root=wiki_root,
                    depth="full",
                    overwrite=True,
                    source_adapter=True,
                    helper_cache_dir=str(policy.helper_cache_root)
                    if policy.helper_cache_root is not None
                    else None,
                    trust_source_plugins=policy.trust_source_plugins,
                ),
                workspace_root=workspace_root,
            )
            preserved_semantic_paths = _preserve_imported_semantic_markdown(
                wiki_root,
                imported_semantic_text,
            )
            bootstrap_summary = _portable_bootstrap_summary(
                refresh_result.to_dict(), workspace_root=workspace_root
            )
            refresh_after = capture_tree_baseline(
                wiki_root,
                display="workspace_wiki_after_refresh",
            )
            workspace_refresh_evidence = {
                "schema_version": DOCUMENTATION_RUN_SCHEMA_VERSION,
                "run_id": run_id,
                "status": "complete",
                "scope": "workspace_snapshot_only",
                "input_wiki_mutated": False,
                "source_revision": source["revision"],
                "initial_snapshot_hash": wiki_input_evidence.get(
                    "initial_snapshot_hash",
                    wiki_input_evidence.get("snapshot_tree_hash"),
                ),
                "before_tree_hash": refresh_before.tree_hash,
                "after_tree_hash": refresh_after.tree_hash,
                "changed_paths": _changed_paths(refresh_before, refresh_after),
                "preserved_semantic_paths": preserved_semantic_paths,
                "bootstrap": bootstrap_summary,
                "completed_at": _utc_now(),
            }
            _write_json(
                workspace_root
                / RUN_CONTROL_DIR
                / "evidence"
                / "workspace-refresh.json",
                workspace_refresh_evidence,
            )
            snapshot_freshness = "verified_current"
            refresh_decision = "workspace_only_completed"
        baseline = {
            "strategy": "adopt_existing_wiki",
            "freshness_policy": freshness_policy,
            "freshness": snapshot_freshness,
            "source_revision": source.get("revision", "source_unavailable"),
            "input_wiki": {
                "display_identifier": "input_wiki",
                "input_tree_hash": wiki_input_evidence.get("input_tree_hash"),
                "initial_snapshot_hash": wiki_input_evidence.get(
                    "initial_snapshot_hash",
                    wiki_input_evidence.get("snapshot_tree_hash"),
                ),
                "manifest_version": wiki_input_evidence.get("manifest_version"),
                "surface_schema_version": wiki_input_evidence.get(
                    "surface_schema_version"
                ),
                "compatibility": wiki_input_evidence.get("compatibility"),
                "refresh_decision": refresh_decision,
            },
        }

    if (
        continuation_snapshot is not None
        and continuation_archive is not None
        and source.get("available") is True
        and _source_identity_changed(continuation_snapshot, source)
    ):
        continuation_records, continuation_payload = _restore_refresh_continuation(
            wiki_root,
            continuation_snapshot,
        )
        imported_pages.extend(continuation_records)
        continuation_paths = tuple(
            str(path) for path in continuation_payload["preserved_semantic_paths"]
        )
        continuation_evidence = {
            "schema_version": "llm-wiki-documentation-continuation/v1",
            "run_id": run_id,
            "status": "complete",
            "reason": "source_revision_changed",
            "prior_run_id": continuation_snapshot.prior_run_id,
            "prior_source_revision": continuation_snapshot.prior_source_revision,
            "source_revision": source["revision"],
            "archive_path": continuation_archive,
            "prior_wiki_tree_hash": continuation_snapshot.prior_wiki_tree_hash,
            **continuation_payload,
            "completed_at": _utc_now(),
        }
        _write_json(
            workspace_root / RUN_CONTROL_DIR / "evidence" / "continuation.json",
            continuation_evidence,
        )

    if source_baseline is not None:
        difference = compare_tree_baseline(source_baseline, policy.source_root or "")
        if not difference.ok:
            raise DocumentationIntegrityError(
                "Source tree changed while preparing the deterministic baseline: "
                f"{difference.to_dict()}"
            )

    if (
        policy.source_root is not None
        and baseline.get("freshness") == "verified_current"
    ):
        native_refresh_evidence = _refresh_prepared_native_projection(
            workspace_root,
            run_id=run_id,
            wiki_root=wiki_root,
            source_root=policy.source_root,
            trust_source_plugins=policy.trust_source_plugins,
            helper_cache_root=policy.helper_cache_root,
        )

    wiki_baseline = capture_tree_baseline(wiki_root, display="workspace_wiki")
    generated_baseline = capture_generated_ownership(wiki_root)
    _write_json(
        workspace_root / RUN_CONTROL_DIR / "evidence" / "wiki-baseline.json",
        wiki_baseline.to_dict(),
    )
    generated_ownership_path = (
        workspace_root / RUN_CONTROL_DIR / "evidence" / "generated-ownership.json"
    )
    _write_json(generated_ownership_path, {"fingerprints": generated_baseline})
    integrity_anchors = {
        "generated_ownership": hash_bytes(generated_ownership_path.read_bytes()),
    }
    if source_baseline_path is not None:
        integrity_anchors["source_baseline"] = hash_bytes(
            source_baseline_path.read_bytes()
        )

    worklist = build_documentation_worklist(
        wiki_root,
        imported_pages=imported_pages,
        unsupported_sources=bootstrap_summary.get("unsupported_sources", {}),
        dependency_metrics=bootstrap_summary.get("dependencies", {}),
        p1_budget=semantic_budget,
    )
    worklist_payload = worklist.to_dict()
    if continuation_paths:
        _mark_continuation_pages_needing_grounding(worklist_payload, continuation_paths)
    _write_json(
        workspace_root / RUN_CONTROL_DIR / "evidence" / "semantic-worklist.json",
        worklist_payload,
    )
    calibration_census = build_flow_evidence_census(
        str(wiki_root),
        source_root=policy.source_root,
        source_revision=str(source.get("revision", "source_unavailable")),
        source_fingerprint=str(source.get("content_fingerprint", "unknown")),
        dependency_evidence=bootstrap_summary.get("dependency_evidence", {}),
        tool_revision=__version__,
        allow_surface_fallback=True,
    )
    calibration_shadow = build_p0_calibration_shadow(
        worklist_payload,
        calibration_census,
    )
    _write_json(
        workspace_root / RUN_CONTROL_DIR / "evidence" / "p0-calibration-census.json",
        calibration_census,
    )
    _write_json(
        workspace_root / RUN_CONTROL_DIR / "evidence" / "p0-calibration-shadow.json",
        calibration_shadow,
    )
    readiness = _initial_readiness_ledger(run_id, worklist_payload)
    _write_json(
        workspace_root / RUN_CONTROL_DIR / "evidence" / "semantic-readiness.json",
        readiness,
    )

    limitations = []
    if source_root is None:
        limitations.append("source_unavailable")
    if baseline.get("freshness") != "verified_current":
        limitations.append("source_verified_publish_ready_unavailable")
    if native_refresh_evidence is None:
        limitations.append("native_knowledge_snapshot_only")
    else:
        verification = native_refresh_evidence.get("verification_receipt", {})
        evaluation = (
            verification.get("evaluation")
            if isinstance(verification, Mapping)
            else None
        )
        limitation = (
            evaluation.get("limitation")
            if isinstance(evaluation, Mapping)
            else None
        )
        if isinstance(limitation, str):
            limitations.append(limitation)
    run = DocumentationRun(
        run_id=run_id,
        state="baseline_ready",
        baseline_strategy=baseline_strategy,
        created_at=created_at,
        updated_at=created_at,
        intake=intake,
        source=source,
        baseline=baseline,
        paths=workspace_paths(),
        policy=policy.to_portable_dict(),
        publication={
            "site_name": site_name.strip(),
            "format": distribution_format,
            "link_mode": link_mode,
            "deployment": "handoff_only",
            "knowledge_mode": knowledge_mode,
            "knowledge_public_repository_identity": (
                knowledge_public_repository_identity
            ),
        },
        skills=skills,
        semantic_budget=semantic_budget,
        adjustment_loop_limit=adjustment_loop_limit,
        integrity_anchors=integrity_anchors,
        evidence={
            "source_baseline": f"{RUN_CONTROL_DIR}/evidence/source-baseline.json"
            if source_baseline is not None
            else "",
            "bootstrap": f"{RUN_CONTROL_DIR}/evidence/bootstrap.json"
            if baseline_strategy == "bootstrap_source"
            else "",
            "wiki_input": f"{RUN_CONTROL_DIR}/evidence/wiki-input.json"
            if wiki_input_evidence is not None
            else "",
            "workspace_refresh": f"{RUN_CONTROL_DIR}/evidence/workspace-refresh.json"
            if workspace_refresh_evidence is not None
            else "",
            "continuation": f"{RUN_CONTROL_DIR}/evidence/continuation.json"
            if continuation_evidence is not None
            else "",
            "native_refresh": f"{RUN_CONTROL_DIR}/evidence/native-refresh.json"
            if native_refresh_evidence is not None
            else "",
            "wiki_baseline": f"{RUN_CONTROL_DIR}/evidence/wiki-baseline.json",
            "generated_ownership": (
                f"{RUN_CONTROL_DIR}/evidence/generated-ownership.json"
            ),
            "semantic_worklist": f"{RUN_CONTROL_DIR}/evidence/semantic-worklist.json",
            "semantic_readiness": (
                f"{RUN_CONTROL_DIR}/evidence/semantic-readiness.json"
            ),
            "p0_calibration_census": (
                f"{RUN_CONTROL_DIR}/evidence/p0-calibration-census.json"
            ),
            "p0_calibration_shadow": (
                f"{RUN_CONTROL_DIR}/evidence/p0-calibration-shadow.json"
            ),
        },
        current_stage=None,
        verdict_limitations=limitations,
    )
    _write_json(
        workspace_root / RUN_CONTROL_DIR / "stages" / "01-baseline.json",
        {
            "schema_version": DOCUMENTATION_RUN_SCHEMA_VERSION,
            "run_id": run_id,
            "stage": "baseline",
            "status": "complete",
            "baseline_strategy": baseline_strategy,
            "source": source,
            "baseline": baseline,
            "worklist_hash": _sha256_json(worklist_payload),
        },
    )
    save_documentation_run(workspace_root, run)
    if not _run_wiki_validation_pair(workspace_root, run, phase="baseline"):
        _block_run_for_integrity(
            workspace_root,
            run,
            "Deterministic baseline lint/CI validation did not pass.",
            integrity=False,
        )
    return run

__all__ = (
    'prepare_documentation_run',
    '_prepare_documentation_run_impl',
)
