"""Documentation-run refresh services."""

from __future__ import annotations

from .dependencies import *
from .contracts import *
from .schema import *
from .workspace import *
from .integrity import *

def _capture_native_artifact_bytes(
    wiki_root: Path,
) -> dict[str, bytes | None]:
    snapshot: dict[str, bytes | None] = {}
    for name in sorted(_NATIVE_ARTIFACT_PATHS):
        path = wiki_root / name
        if path.is_symlink():
            raise DocumentationIntegrityError(
                f"Native refresh rejects a symlinked protected artifact: {path}"
            )
        if path.exists() and not path.is_file():
            raise DocumentationIntegrityError(
                f"Native refresh requires a regular protected artifact: {path}"
            )
        snapshot[name] = path.read_bytes() if path.is_file() else None
    return snapshot


def _rollback_native_artifact_bytes(
    wiki_root: Path,
    snapshot: Mapping[str, bytes | None],
    *,
    cause: BaseException,
) -> None:
    try:
        for name in sorted(_NATIVE_ARTIFACT_PATHS):
            path = wiki_root / name
            prior = snapshot.get(name)
            if path.is_symlink():
                raise DocumentationIntegrityError(
                    f"Cannot roll back a symlinked native artifact: {path}"
                )
            if prior is None:
                if path.exists():
                    if not path.is_file():
                        raise DocumentationIntegrityError(
                            "Cannot roll back a non-regular native artifact: "
                            f"{path}"
                        )
                    path.unlink()
                continue
            if path.exists() and not path.is_file():
                raise DocumentationIntegrityError(
                    f"Cannot roll back a non-regular native artifact: {path}"
                )
            write_bytes_atomic(path, prior)
        restored = _capture_native_artifact_bytes(wiki_root)
        if restored != dict(snapshot):
            raise DocumentationIntegrityError(
                "Native artifact rollback did not restore the captured bytes."
            )
    except (OSError, DocumentationIntegrityError) as rollback_exc:
        raise DocumentationIntegrityError(
            "Native projection refresh failed and protected-artifact rollback "
            f"also failed: {rollback_exc}"
        ) from cause


def _capture_exact_file_bytes(
    paths: Iterable[Path],
) -> dict[Path, bytes | None]:
    snapshot: dict[Path, bytes | None] = {}
    for path in sorted({Path(value) for value in paths}):
        if path.is_symlink():
            raise DocumentationIntegrityError(
                f"Native refresh rejects a symlinked controller file: {path}"
            )
        if path.exists() and not path.is_file():
            raise DocumentationIntegrityError(
                f"Native refresh requires a regular controller file: {path}"
            )
        snapshot[path] = path.read_bytes() if path.is_file() else None
    return snapshot


def _rollback_exact_file_bytes(
    snapshot: Mapping[Path, bytes | None],
    *,
    cause: BaseException,
) -> None:
    try:
        for path, prior in sorted(snapshot.items(), key=lambda item: str(item[0])):
            if path.is_symlink():
                raise DocumentationIntegrityError(
                    f"Cannot roll back a symlinked controller file: {path}"
                )
            if prior is None:
                if path.exists():
                    if not path.is_file():
                        raise DocumentationIntegrityError(
                            "Cannot roll back a non-regular controller file: "
                            f"{path}"
                        )
                    path.unlink()
                continue
            if path.exists() and not path.is_file():
                raise DocumentationIntegrityError(
                    f"Cannot roll back a non-regular controller file: {path}"
                )
            write_bytes_atomic(path, prior)
        restored = _capture_exact_file_bytes(snapshot)
        if restored != dict(snapshot):
            raise DocumentationIntegrityError(
                "Controller-file rollback did not restore the captured bytes."
            )
    except (OSError, DocumentationIntegrityError) as rollback_exc:
        raise DocumentationIntegrityError(
            "Native projection refresh failed and controller-file rollback "
            f"also failed: {rollback_exc}"
        ) from cause


def _rollback_native_refresh_transaction(
    wiki_root: Path,
    artifact_snapshot: Mapping[str, bytes | None],
    control_snapshot: Mapping[Path, bytes | None],
    *,
    cause: BaseException,
) -> None:
    failures: list[str] = []
    try:
        _rollback_native_artifact_bytes(
            wiki_root,
            artifact_snapshot,
            cause=cause,
        )
    except DocumentationIntegrityError as exc:
        failures.append(str(exc))
    try:
        _rollback_exact_file_bytes(control_snapshot, cause=cause)
    except DocumentationIntegrityError as exc:
        failures.append(str(exc))
    if failures:
        raise DocumentationIntegrityError(
            "Native refresh transaction rollback was incomplete: "
            + "; ".join(failures)
        ) from cause


def _refresh_prepared_native_projection(
    workspace_root: Path,
    *,
    run_id: str,
    wiki_root: Path,
    source_root: Path,
    trust_source_plugins: bool,
    helper_cache_root: Path | None,
    source_selection: str | Path | None,
) -> dict[str, Any]:
    before = capture_generated_ownership(wiki_root)
    artifact_snapshot = _capture_native_artifact_bytes(wiki_root)
    evidence_root = workspace_root / RUN_CONTROL_DIR / "evidence"
    control_snapshot = _capture_exact_file_bytes(
        (
            evidence_root / "native-refresh-baseline.json",
            evidence_root / "native-refresh.json",
        )
    )
    try:
        refresh = refresh_documentation_native_projection(
            source_root=source_root,
            wiki_root=wiki_root,
            trust_source_plugins=trust_source_plugins,
            helper_cache_dir=helper_cache_root,
            source_selection=source_selection,
        )
    except BaseException as exc:
        _rollback_native_artifact_bytes(
            wiki_root,
            artifact_snapshot,
            cause=exc,
        )
        if isinstance(exc, DocumentationNativeError):
            raise DocumentationIntegrityError(
                f"Cannot anchor the prepared native projection: {exc}"
            ) from exc
        raise
    try:
        after = capture_generated_ownership(wiki_root)
        _assert_native_only_ownership_change(before, after)
    except BaseException as exc:
        _rollback_native_artifact_bytes(
            wiki_root,
            artifact_snapshot,
            cause=exc,
        )
        raise
    try:
        verification_evaluation = _native_refresh_verification_evaluation(wiki_root)
        payload = _native_refresh_payload(
            run_id=run_id,
            phase="baseline",
            refresh=refresh,
            ownership_before=before,
            ownership_after=after,
            changed_wiki_paths=(),
            verification_evaluation=verification_evaluation,
        )
        _write_native_refresh_evidence(
            workspace_root,
            phase="baseline",
            payload=payload,
        )
        return payload
    except BaseException as exc:
        _rollback_native_refresh_transaction(
            wiki_root,
            artifact_snapshot,
            control_snapshot,
            cause=exc,
        )
        if isinstance(exc, OSError):
            raise DocumentationIntegrityError(
                f"Cannot finalize the prepared native projection: {exc}"
            ) from exc
        raise


def _refresh_and_reanchor_native_projection(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    phase: str,
    changed_wiki_paths: Iterable[str],
) -> tuple[dict[str, Any] | None, KnowledgeReadView | None]:
    changed = tuple(sorted({str(path) for path in changed_wiki_paths}))
    if not any(path.casefold().endswith(".md") for path in changed):
        return None, None
    runtime_paths = _load_bound_runtime_policy(workspace_root, run)
    source_root = runtime_paths.get("source_root")
    source_is_current = run.baseline.get("freshness") == "verified_current"
    source_is_available = source_root is not None and source_root.is_dir()
    if not source_is_available or not source_is_current:
        if "native_knowledge_snapshot_only" not in run.verdict_limitations:
            run.verdict_limitations.append("native_knowledge_snapshot_only")
        save_documentation_run(workspace_root, run)
        return None, None

    assert source_root is not None
    selection_argument = _bound_source_selection_argument(run.policy)
    wiki_root = workspace_root / run.paths["wiki"]
    ownership_path = _workspace_path(
        workspace_root,
        run.evidence["generated_ownership"],
    )
    recorded_payload = _read_json(ownership_path)
    ownership_before = recorded_payload.get("fingerprints")
    if not isinstance(ownership_before, Mapping):
        raise DocumentationIntegrityError(
            "Generated ownership evidence is malformed before native refresh."
        )
    normalized_before = {
        str(key): str(value) for key, value in ownership_before.items()
    }
    pre_refresh_difference = compare_generated_ownership(
        normalized_before,
        wiki_root,
    )
    if any(pre_refresh_difference.values()):
        raise DocumentationIntegrityError(
            "Generated ownership changed before the controller native refresh: "
            f"{pre_refresh_difference}"
        )

    artifact_snapshot = _capture_native_artifact_bytes(wiki_root)
    evidence_root = workspace_root / RUN_CONTROL_DIR / "evidence"
    control_snapshot = _capture_exact_file_bytes(
        (
            evidence_root / f"native-refresh-{phase}.json",
            evidence_root / "native-refresh.json",
            ownership_path,
            documentation_run_path(workspace_root),
        )
    )
    run_evidence_before = dict(run.evidence)
    run_anchors_before = dict(run.integrity_anchors)
    run_limitations_before = list(run.verdict_limitations)
    run_updated_at_before = run.updated_at
    try:
        refresh = refresh_documentation_native_projection(
            source_root=source_root,
            wiki_root=wiki_root,
            trust_source_plugins=bool(
                run.policy.get("source_plugins_trusted", False)
            ),
            helper_cache_dir=runtime_paths.get("helper_cache_root"),
            source_selection=selection_argument,
        )
    except BaseException as exc:
        _rollback_native_artifact_bytes(
            wiki_root,
            artifact_snapshot,
            cause=exc,
        )
        if isinstance(exc, DocumentationNativeError):
            raise DocumentationIntegrityError(
                f"Controller native projection refresh failed: {exc}"
            ) from exc
        raise
    try:
        ownership_after = capture_generated_ownership(wiki_root)
        _assert_native_only_ownership_change(normalized_before, ownership_after)
    except BaseException as exc:
        _rollback_native_artifact_bytes(
            wiki_root,
            artifact_snapshot,
            cause=exc,
        )
        raise
    try:
        verification_evaluation = _native_refresh_verification_evaluation(wiki_root)
        refresh_payload = _native_refresh_payload(
            run_id=run.run_id,
            phase=phase,
            refresh=refresh,
            ownership_before=normalized_before,
            ownership_after=ownership_after,
            changed_wiki_paths=changed,
            verification_evaluation=verification_evaluation,
        )
        refresh_path = _write_native_refresh_evidence(
            workspace_root,
            phase=phase,
            payload=refresh_payload,
        )
        _write_json(ownership_path, {"fingerprints": ownership_after})
        run.evidence["native_refresh"] = refresh_path.relative_to(
            workspace_root
        ).as_posix()
        run.integrity_anchors["generated_ownership"] = hash_bytes(
            ownership_path.read_bytes()
        )
        if "native_knowledge_snapshot_only" in run.verdict_limitations:
            run.verdict_limitations.remove("native_knowledge_snapshot_only")
        _apply_native_verification_limitation(run, verification_evaluation)
        save_documentation_run(workspace_root, run)
        return refresh_payload, refresh.knowledge_view
    except BaseException as exc:
        run.evidence.clear()
        run.evidence.update(run_evidence_before)
        run.integrity_anchors.clear()
        run.integrity_anchors.update(run_anchors_before)
        run.verdict_limitations[:] = run_limitations_before
        run.updated_at = run_updated_at_before
        _rollback_native_refresh_transaction(
            wiki_root,
            artifact_snapshot,
            control_snapshot,
            cause=exc,
        )
        if isinstance(exc, OSError):
            raise DocumentationIntegrityError(
                f"Controller native refresh finalization failed: {exc}"
            ) from exc
        raise


def _write_native_refresh_evidence(
    workspace_root: Path,
    *,
    phase: str,
    payload: Mapping[str, Any],
) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", phase):
        raise DocumentationIntegrityError(
            "Native refresh phase must be a portable lowercase identifier."
        )
    evidence_root = workspace_root / RUN_CONTROL_DIR / "evidence"
    phase_path = evidence_root / f"native-refresh-{phase}.json"
    canonical_path = evidence_root / "native-refresh.json"
    _write_json(phase_path, payload)
    _write_json(canonical_path, payload)
    return canonical_path


def _assert_native_only_ownership_change(
    before: Mapping[str, str],
    after: Mapping[str, str],
) -> None:
    difference = {
        "added": set(after) - set(before),
        "removed": set(before) - set(after),
        "changed": {
            key for key in set(before) & set(after) if before[key] != after[key]
        },
    }
    receipt_changes = sorted(
        {
            key
            for values in difference.values()
            for key in values
            if key == VERIFICATION_RECEIPT_FILENAME
        }
    )
    if receipt_changes:
        raise DocumentationIntegrityError(
            "Native projection refresh must retain the disposable verification "
            "receipt for explicit post-refresh evaluation."
        )
    if (GOVERNANCE_FILENAME in before) != (GOVERNANCE_FILENAME in after):
        raise DocumentationIntegrityError(
            "Native projection refresh cannot create or remove the authoritative "
            "governance ledger; adoption and recovery require explicit authority."
        )
    unexpected = sorted(
        {
            key
            for values in difference.values()
            for key in values
            if key not in _NATIVE_REFRESH_MUTABLE_PATHS
        }
    )
    if unexpected:
        raise DocumentationIntegrityError(
            "Native projection refresh changed non-native generated ownership: "
            f"{unexpected}"
        )


def _native_refresh_payload(
    *,
    run_id: str,
    phase: str,
    refresh: DocumentationNativeRefresh,
    ownership_before: Mapping[str, str],
    ownership_after: Mapping[str, str],
    changed_wiki_paths: Iterable[str],
    verification_evaluation: Mapping[str, Any],
) -> dict[str, Any]:
    from ..knowledge_observability import knowledge_freshness_disclosure

    if refresh.knowledge_view is None:
        raise DocumentationIntegrityError(
            "Native refresh evidence requires its live evaluated knowledge view."
        )
    artifacts = {}
    for label, artifact in (
        ("surface", refresh.commit.surface_index),
        ("knowledge", refresh.commit.knowledge_index),
        ("manifest", refresh.commit.manifest),
    ):
        artifacts[label] = {
            "path": artifact.relative_path,
            "state": artifact.state.value,
            "sha256": artifact.content_hash,
        }
    return {
        "schema_version": "llm-wiki-documentation-native-refresh/v2",
        "run_id": run_id,
        "phase": phase,
        "status": "complete",
        "freshness": knowledge_freshness_disclosure(refresh.knowledge_view),
        "freshness_evaluated": refresh.knowledge_view.freshness_evaluated,
        "changed": refresh.changed,
        "changed_wiki_paths": sorted({str(path) for path in changed_wiki_paths}),
        "artifacts": artifacts,
        "artifact_hashes_before": dict(
            sorted(refresh.artifact_hashes_before.items())
        ),
        "artifact_hashes_after": dict(
            sorted(refresh.artifact_hashes_after.items())
        ),
        "ownership_before": dict(sorted(ownership_before.items())),
        "ownership_after": dict(sorted(ownership_after.items())),
        "artifact_ownership": {
            ".llm-wiki-manifest.json": {
                "classification": "generated-projection",
                "owner": "documentation-supervisor",
            },
            ".llm-wiki-surface.json": {
                "classification": "generated-projection",
                "owner": "documentation-supervisor",
            },
            KNOWLEDGE_INDEX_FILENAME: {
                "classification": "generated-projection",
                "owner": "documentation-supervisor",
            },
            GOVERNANCE_FILENAME: {
                "classification": "authoritative-adopted-ledger",
                "owner": "repository-governance-owner",
                "supervisor_action": "reconcile-existing-only",
            },
            VERIFICATION_RECEIPT_FILENAME: {
                "classification": "disposable-machine-receipt",
                "owner": "application-checker",
                "supervisor_action": "retain-and-evaluate-only",
            },
        },
        "governance_reconciliation": _native_artifact_transition(
            ownership_before,
            ownership_after,
            GOVERNANCE_FILENAME,
            absent_status="not-adopted",
            changed_status="reconciled-changed",
        ),
        "verification_receipt": {
            **_native_artifact_transition(
                ownership_before,
                ownership_after,
                VERIFICATION_RECEIPT_FILENAME,
                absent_status="absent",
                changed_status="forbidden-mutation",
            ),
            "policy": "retain-and-limit",
            "checker_execution": "not-authorized",
            "evaluation": dict(verification_evaluation),
        },
        "review_authority": {
            "external_agent_result": "not-native-human-review",
            "human_review_mutation": "not-authorized",
        },
        "completed_at": _utc_now(),
    }


def _native_artifact_transition(
    before: Mapping[str, str],
    after: Mapping[str, str],
    path: str,
    *,
    absent_status: str,
    changed_status: str,
) -> dict[str, Any]:
    before_hash = before.get(path)
    after_hash = after.get(path)
    if before_hash is None and after_hash is None:
        status = absent_status
    elif before_hash == after_hash:
        status = "unchanged"
    else:
        status = changed_status
    return {
        "path": path,
        "before_sha256": before_hash,
        "after_sha256": after_hash,
        "status": status,
    }


def _native_refresh_verification_evaluation(wiki_root: Path) -> dict[str, Any]:
    receipt_path = wiki_root / VERIFICATION_RECEIPT_FILENAME
    if not receipt_path.exists() and not receipt_path.is_symlink():
        return {
            "status": "absent",
            "availability": "absent",
            "reason": "verification-receipt-not-present",
            "valid": None,
            "recorded_result": None,
            "passed": None,
            "invalidation_reasons": [],
            "limitation": None,
        }
    try:
        from ..knowledge_consumption import load_knowledge_read_view

        view = load_knowledge_read_view(
            wiki_root,
            snapshot_only=True,
            include_machine_verification=True,
        )
        evaluated = view.machine_verification
        availability = evaluated.availability.value
        valid = evaluated.valid
        passed = evaluated.passed
        recorded_result = evaluated.recorded_result
        reasons = list(evaluated.invalidation_reasons)
        reason = evaluated.reason
    except (OSError, RecursionError, TypeError, UnicodeError, ValueError):
        return {
            "status": "retained-invalid",
            "availability": "invalid",
            "reason": "verification-receipt-evaluation-failed",
            "valid": False,
            "recorded_result": None,
            "passed": None,
            "invalidation_reasons": [],
            "limitation": "native_verification_receipt_invalid",
        }

    if availability == "recorded" and valid is True and passed is True:
        status = "current-passed"
        limitation = None
    elif availability == "recorded" and valid is True:
        status = "current-failed"
        limitation = "native_verification_receipt_failed"
    elif availability == "recorded":
        status = "retained-stale"
        limitation = "native_verification_receipt_stale"
    else:
        status = "retained-invalid"
        limitation = "native_verification_receipt_invalid"
    return {
        "status": status,
        "availability": availability,
        "reason": reason,
        "valid": valid,
        "recorded_result": recorded_result,
        "passed": passed,
        "invalidation_reasons": reasons,
        "limitation": limitation,
    }


def _apply_native_verification_limitation(
    run: DocumentationRun,
    evaluation: Mapping[str, Any],
) -> None:
    known = {
        "native_verification_receipt_failed",
        "native_verification_receipt_invalid",
        "native_verification_receipt_stale",
    }
    run.verdict_limitations[:] = [
        item for item in run.verdict_limitations if item not in known
    ]
    limitation = evaluation.get("limitation")
    if isinstance(limitation, str):
        run.verdict_limitations.append(limitation)


def source_identity(source_root: str | Path, baseline: TreeBaseline) -> dict[str, Any]:
    root = Path(source_root).expanduser().resolve()
    revision = None
    try:
        result = subprocess.run(  # noqa: S603 - fixed read-only git query
            ["git", "-C", str(root), "rev-parse", "HEAD"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        revision = result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        revision = None
    return {
        "available": True,
        "display_identifier": "source",
        "revision": revision or f"content:{baseline.tree_hash}",
        "content_fingerprint": baseline.tree_hash,
        "revision_kind": "git" if revision else "content",
    }


def _assert_resume_compatible(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    policy: DocumentationMutationPolicy,
    baseline_strategy: str,
    intake: DocumentationIntakeBrief,
    site_name: str,
    freshness_policy: str,
    semantic_budget: int,
    adjustment_loop_limit: int,
    distribution_format: str,
    link_mode: str,
    knowledge_mode: str,
    knowledge_public_repository_identity: str | None,
) -> None:
    if run.baseline_strategy != baseline_strategy:
        raise DocumentationRunError(
            "Prepared workspace uses a different baseline strategy; choose a new "
            "workspace or request an explicit refresh."
        )
    if run.publication.get("site_name") != site_name:
        raise DocumentationRunError(
            "Prepared workspace uses a different site name; choose a new workspace "
            "or request an explicit refresh."
        )
    if run.publication.get("format") != distribution_format:
        raise DocumentationRunError(
            "Prepared workspace uses a different distribution format; request an "
            "explicit refresh or choose a new workspace."
        )
    if run.publication.get("link_mode") != link_mode:
        raise DocumentationRunError(
            "Prepared workspace uses a different link mode; request an explicit "
            "refresh or choose a new workspace."
        )
    recorded_knowledge_mode = run.publication.get("knowledge_mode", "off")
    recorded_public_identity = run.publication.get(
        "knowledge_public_repository_identity"
    )
    if (
        recorded_knowledge_mode != knowledge_mode
        or recorded_public_identity != knowledge_public_repository_identity
    ):
        raise DocumentationRunError(
            "Prepared workspace uses a different native-knowledge publication "
            "policy; request an explicit refresh (including --knowledge-mode off "
            "for a deliberate un-enriched fallback) or choose a new workspace."
        )
    if run.semantic_budget != semantic_budget:
        raise DocumentationRunError(
            "Prepared workspace uses a different semantic budget; request an explicit "
            "refresh or choose a new workspace."
        )
    if run.adjustment_loop_limit != adjustment_loop_limit:
        raise DocumentationRunError(
            "Prepared workspace uses a different adjustment-loop limit; request an "
            "explicit refresh or choose a new workspace."
        )
    if run.baseline.get("freshness_policy") != freshness_policy and (
        baseline_strategy == "adopt_existing_wiki"
    ):
        raise DocumentationRunError(
            "Prepared workspace uses a different existing-wiki freshness policy."
        )
    _assert_intake_compatible(run.intake, intake)
    _assert_runtime_roots_compatible(workspace_root, policy)
    recorded_trust = bool(run.policy.get("source_plugins_trusted", False))
    if recorded_trust != policy.trust_source_plugins:
        raise DocumentationRunError(
            "Prepared workspace uses a different source-plugin trust decision; request "
            "an explicit refresh or choose a new workspace."
        )
    current_portable_policy = policy.to_portable_dict()
    if (
        run.policy.get("source_selection")
        != current_portable_policy.get("source_selection")
        or run.policy.get("source_selection_origin")
        != current_portable_policy.get("source_selection_origin")
    ):
        raise DocumentationRunError(
            "Prepared workspace uses a different source selection; request an "
            "explicit refresh or choose a new workspace."
        )

    source_evidence = run.evidence.get("source_baseline")
    if source_evidence and policy.source_root is not None:
        payload = _read_json(_workspace_path(workspace_root, source_evidence))
        difference = _compare_bound_source_baseline(
            TreeBaseline.from_dict(payload),
            policy.source_root,
            current_portable_policy,
        )
        if not difference.ok:
            raise DocumentationRunError(
                "Source content changed since prepare; use an explicit refresh or a "
                f"new workspace. Differences: {difference.to_dict()}"
            )
    plugin_evidence = run.evidence.get("source_plugins_baseline")
    if recorded_trust and policy.source_root is not None:
        if not plugin_evidence:
            raise DocumentationRunError(
                "Prepared workspace lacks trusted source-plugin integrity evidence; "
                "request an explicit refresh or choose a new workspace."
            )
        plugin_difference = _compare_bound_source_plugin_baseline(
            TreeBaseline.from_dict(
                _read_json(_workspace_path(workspace_root, plugin_evidence))
            ),
            policy.source_root,
        )
        if not plugin_difference.ok:
            raise DocumentationRunError(
                "Trusted source plugins changed since prepare; use an explicit "
                "refresh or a new workspace. Differences: "
                f"{plugin_difference.to_dict()}"
            )
    input_baseline = run.baseline.get("input_wiki")
    if isinstance(input_baseline, dict) and policy.input_wiki_root is not None:
        try:
            current_tree_hash = _adopted_input_wiki_tree_hash(policy.input_wiki_root)
        except DocumentationIntegrityError as exc:
            raise DocumentationRunError(
                "Input wiki cannot be safely rechecked; use an explicit re-import "
                "or a new workspace."
            ) from exc
        if current_tree_hash != input_baseline.get("input_tree_hash"):
            raise DocumentationRunError(
                "Input wiki changed since prepare; use an explicit re-import or a "
                "new workspace."
            )


def _assert_intake_compatible(
    recorded: DocumentationIntakeBrief,
    supplied: DocumentationIntakeBrief,
) -> None:
    if (
        supplied.project_purpose != "unspecified"
        and supplied.project_purpose != recorded.project_purpose
    ):
        raise DocumentationRunError(
            "Prepared workspace already contains a different project-purpose answer."
        )
    if (
        supplied.audiences != ("unspecified",)
        and supplied.audiences != recorded.audiences
    ):
        raise DocumentationRunError(
            "Prepared workspace already contains different audience answers."
        )
    supplied_address = supplied.live_service.get("address")
    recorded_address = recorded.live_service.get("address")
    if supplied_address != "unspecified" and supplied_address != recorded_address:
        raise DocumentationRunError(
            "Prepared workspace already contains a different live-service answer."
        )
    for audience, supplied_intent in supplied.audience_intent.items():
        if supplied_intent == "unspecified":
            continue
        if supplied_intent != recorded.audience_intent.get(audience):
            raise DocumentationRunError(
                "Prepared workspace already contains different audience-intent answers."
            )
    supplied_mode = supplied.live_service.get("access_mode")
    recorded_mode = recorded.live_service.get("access_mode")
    if supplied_mode != "unspecified" and supplied_mode != recorded_mode:
        raise DocumentationRunError(
            "Prepared workspace already contains a different live-service access mode."
        )
    if supplied.live_service.get(
        "observation_allowed"
    ) and not recorded.live_service.get("observation_allowed"):
        raise DocumentationRunError(
            "Prepared workspace did not record live-service observation permission."
        )


def _assert_runtime_roots_compatible(
    workspace_root: Path, policy: DocumentationMutationPolicy
) -> None:
    payload = _read_json(workspace_root / RUN_CONTROL_DIR / POLICY_FILENAME)
    expected = {
        "workspace_root": str(policy.workspace_root),
        "source_root": str(policy.source_root) if policy.source_root else None,
        "input_wiki_root": str(policy.input_wiki_root)
        if policy.input_wiki_root
        else None,
        "helper_cache_root": str(policy.helper_cache_root)
        if policy.helper_cache_root
        else None,
        "capture_root": str(policy.capture_root) if policy.capture_root else None,
    }
    for key, value in expected.items():
        if payload.get("runtime_paths", {}).get(key) != value:
            raise DocumentationRunError(
                f"Prepared workspace runtime path changed for {key}; use a new workspace."
            )


def _capture_refresh_continuation(
    workspace_root: Path,
    run: DocumentationRun,
) -> _RefreshContinuationSnapshot:
    """Capture only prior imported or reconciled agent-owned Markdown.

    Explicit refresh is allowed to observe a changed source, but it must not use
    that authorization to carry protected generated edits into the next run.
    The current wiki and result evidence are therefore inventoried without
    following links and generated ownership must still match the recorded
    baseline before anything is archived.
    """

    wiki_root = _workspace_path(workspace_root, run.paths["wiki"])
    wiki_tree = capture_tree_baseline(wiki_root, display="prior_workspace_wiki")
    ownership_relative = run.evidence.get("generated_ownership")
    if not ownership_relative:
        raise DocumentationIntegrityError(
            "Explicit refresh cannot preserve semantic Markdown without prior "
            "generated-ownership evidence."
        )
    ownership_payload = _read_json(_workspace_path(workspace_root, ownership_relative))
    recorded_fingerprints = ownership_payload.get("fingerprints")
    if not isinstance(recorded_fingerprints, Mapping) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in recorded_fingerprints.items()
    ):
        raise DocumentationIntegrityError(
            "Prior generated-ownership evidence is malformed."
        )
    generated_difference = compare_generated_ownership(recorded_fingerprints, wiki_root)
    if any(generated_difference.values()):
        raise DocumentationIntegrityError(
            "Explicit refresh refuses to preserve a wiki with changed generated "
            f"ownership: {generated_difference}"
        )

    candidates = _refresh_continuation_candidate_paths(workspace_root, run)
    portable_candidates = _portable_path_tuple(sorted(candidates))
    old_generated_descriptions = _prior_generated_descriptions(wiki_root)
    pages: dict[str, dict[str, Any]] = {}
    for relative in portable_candidates:
        if not relative.casefold().endswith(".md"):
            continue
        expected_hash = wiki_tree.file_hashes.get(relative)
        if expected_hash is None:
            continue
        path = _workspace_path(wiki_root, relative)
        try:
            mode = path.lstat().st_mode
            data = path.read_bytes()
        except OSError as exc:
            raise DocumentationIntegrityError(
                f"Cannot safely capture prior semantic page {relative!r}: {exc}"
            ) from exc
        if not stat.S_ISREG(mode) or path.is_symlink():
            raise DocumentationIntegrityError(
                f"Prior semantic page must be a regular file: {relative}"
            )
        if hash_bytes(data) != expected_hash:
            raise DocumentationIntegrityError(
                f"Prior semantic page changed while refresh was capturing it: {relative}"
            )
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentationIntegrityError(
                f"Prior semantic page is not valid UTF-8: {relative}"
            ) from exc
        pages[relative] = {
            "text": text,
            "reasons": sorted(candidates[relative]),
            "prior_page_hash": expected_hash,
            "old_generated_description": old_generated_descriptions.get(relative),
        }

    final_difference = compare_tree_baseline(wiki_tree, wiki_root)
    if not final_difference.ok:
        raise DocumentationIntegrityError(
            "Prior wiki changed while refresh continuation was being captured: "
            f"{final_difference.to_dict()}"
        )
    return _RefreshContinuationSnapshot(
        prior_run_id=run.run_id,
        prior_source_revision=str(run.source.get("revision", "source_unavailable")),
        prior_source_fingerprint=(
            str(run.source["content_fingerprint"])
            if run.source.get("content_fingerprint")
            else None
        ),
        prior_wiki_tree_hash=wiki_tree.tree_hash,
        pages=pages,
    )


def _refresh_continuation_candidate_paths(
    workspace_root: Path,
    run: DocumentationRun,
) -> dict[str, set[str]]:
    candidates: dict[str, set[str]] = {}
    results_root = workspace_root / RUN_CONTROL_DIR / "results"
    if results_root.is_dir():
        results_tree = capture_tree_baseline(
            results_root, display="prior_agent_results"
        )
        for relative, expected_hash in sorted(results_tree.file_hashes.items()):
            if not relative.casefold().endswith(".json"):
                continue
            result_path = _workspace_path(results_root, relative)
            if hash_bytes(result_path.read_bytes()) != expected_hash:
                raise DocumentationIntegrityError(
                    "Prior agent result changed while refresh was reading it: "
                    f"{relative}"
                )
            payload = _read_json(result_path)
            if payload.get("run_id") != run.run_id:
                raise DocumentationIntegrityError(
                    f"Prior agent result belongs to a different run: {relative}"
                )
            reconciliation = payload.get("reconciliation")
            if not isinstance(reconciliation, Mapping):
                continue
            changed_paths = reconciliation.get("actual_changed_wiki_paths", [])
            if not isinstance(changed_paths, list) or any(
                not isinstance(path, str) for path in changed_paths
            ):
                raise DocumentationIntegrityError(
                    f"Prior agent result has malformed changed paths: {relative}"
                )
            for raw_path in changed_paths:
                path = _portable_path(
                    raw_path, field_name="prior agent changed wiki path"
                )
                candidates.setdefault(path, set()).add("reconciled_agent_result")

    wiki_input_relative = run.evidence.get("wiki_input")
    if wiki_input_relative:
        wiki_input = _read_json(_workspace_path(workspace_root, wiki_input_relative))
        semantic_pages = wiki_input.get("semantic_pages", [])
        if not isinstance(semantic_pages, list):
            raise DocumentationIntegrityError(
                "Prior input-wiki semantic page evidence is malformed."
            )
        for record in semantic_pages:
            if not isinstance(record, Mapping):
                raise DocumentationIntegrityError(
                    "Prior input-wiki semantic page evidence must contain objects."
                )
            raw_path = record.get("canonical_path")
            if not isinstance(raw_path, str):
                raise DocumentationIntegrityError(
                    "Prior input-wiki semantic page is missing canonical_path."
                )
            path = _portable_path(raw_path, field_name="prior imported semantic page")
            candidates.setdefault(path, set()).add("imported_semantic_page")
    return candidates


def _prior_generated_descriptions(wiki_root: Path) -> dict[str, str]:
    """Map generated module/entity descriptions from the prior manifest."""

    manifest_path = wiki_root / ".llm-wiki-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return {}
    manifest = _read_json(manifest_path)
    sources = manifest.get("sources", {})
    if not isinstance(sources, Mapping):
        return {}
    descriptions: dict[str, str] = {}
    for source_record in sources.values():
        if not isinstance(source_record, Mapping):
            continue
        generated = source_record.get("generated_semantics", {})
        if not isinstance(generated, Mapping):
            continue
        module_page = source_record.get("module_page")
        module_semantics = generated.get("module", {})
        if isinstance(module_page, str) and isinstance(module_semantics, Mapping):
            description = module_semantics.get("description")
            if isinstance(description, str):
                descriptions[f"modules/{module_page}.md"] = description
        entities = generated.get("entities", {})
        if not isinstance(entities, Mapping):
            continue
        page_by_name: dict[str, str] = {}
        entity_pages = source_record.get("entity_pages", {})
        if isinstance(entity_pages, Mapping):
            page_by_name.update(
                {
                    str(name): str(page)
                    for name, page in entity_pages.items()
                    if isinstance(name, str) and isinstance(page, str)
                }
            )
        occurrences = source_record.get("entity_page_occurrences", [])
        if isinstance(occurrences, list):
            for occurrence in occurrences:
                if not isinstance(occurrence, Mapping):
                    continue
                name = occurrence.get("name")
                page = occurrence.get("page")
                if isinstance(name, str) and isinstance(page, str):
                    page_by_name.setdefault(name, page)
        for name, semantics in entities.items():
            if not isinstance(name, str) or not isinstance(semantics, Mapping):
                continue
            description = semantics.get("description")
            page = page_by_name.get(name)
            if isinstance(description, str) and page:
                descriptions[f"entities/{page}.md"] = description
    return descriptions


def _source_identity_changed(
    snapshot: _RefreshContinuationSnapshot,
    current: Mapping[str, Any],
) -> bool:
    current_revision = str(current.get("revision", "source_unavailable"))
    current_fingerprint = current.get("content_fingerprint")
    return (
        snapshot.prior_source_revision != current_revision
        or snapshot.prior_source_fingerprint
        != (str(current_fingerprint) if current_fingerprint else None)
    )


def _restore_refresh_continuation(
    wiki_root: Path,
    snapshot: _RefreshContinuationSnapshot,
) -> tuple[list[Mapping[str, Any]], dict[str, Any]]:
    """Merge prior agent-owned surfaces onto a new deterministic wiki."""

    refreshed_tree = capture_tree_baseline(
        wiki_root, display="refreshed_workspace_wiki_before_continuation"
    )
    records: list[Mapping[str, Any]] = []
    prior_page_hashes: dict[str, str] = {}
    preserved_page_hashes: dict[str, str] = {}
    semantic_hashes: dict[str, str] = {}
    for relative, record in sorted(snapshot.pages.items()):
        target = _workspace_path(wiki_root, relative)
        current = ""
        if os.path.lexists(target):
            try:
                mode = target.lstat().st_mode
            except OSError as exc:
                raise DocumentationIntegrityError(
                    f"Cannot inspect refreshed continuation target {relative!r}: {exc}"
                ) from exc
            if not stat.S_ISREG(mode) or target.is_symlink():
                raise DocumentationIntegrityError(
                    f"Refreshed continuation target must be a regular file: {relative}"
                )
            current = target.read_text(encoding="utf-8")
        merged = _merge_refresh_semantic_page(relative, record, current)
        if merged is None:
            continue
        merged_text, preserved_semantic = merged
        if merged_text != current:
            write_text_output(target, merged_text)
        final_bytes = target.read_bytes()
        final_hash = hash_bytes(final_bytes)
        prior_page_hashes[relative] = str(record["prior_page_hash"])
        preserved_page_hashes[relative] = final_hash
        semantic_hashes[relative] = hash_bytes(preserved_semantic.encode("utf-8"))
        records.append(
            {
                "canonical_path": relative,
                "sha256": final_hash,
                "compatible": True,
                "compatibility": "refresh_continuation",
                "imported_classification": "needs_grounding",
                "grounding_status": "unknown",
                "preserved_from_run_id": snapshot.prior_run_id,
                "preserved_after_source_revision_change": True,
            }
        )

    after_tree = capture_tree_baseline(
        wiki_root, display="refreshed_workspace_wiki_after_continuation"
    )
    actual_changed = set(_changed_paths(refreshed_tree, after_tree))
    allowed_changed = set(preserved_page_hashes)
    unexpected = sorted(actual_changed - allowed_changed)
    if unexpected:
        raise DocumentationIntegrityError(
            "Refresh continuation changed paths outside its preserved semantic set: "
            f"{unexpected}"
        )
    preserved_paths = sorted(preserved_page_hashes)
    return records, {
        "candidate_semantic_paths": sorted(snapshot.pages),
        "preserved_semantic_paths": preserved_paths,
        "prior_page_hashes": prior_page_hashes,
        "preserved_page_hashes": preserved_page_hashes,
        "preserved_semantic_hash": _sha256_json(semantic_hashes),
    }


def _merge_refresh_semantic_page(
    relative: str,
    record: Mapping[str, Any],
    current: str,
) -> tuple[str, str] | None:
    prior = str(record.get("text", ""))
    reasons = {
        str(reason) for reason in record.get("reasons", []) if isinstance(reason, str)
    }
    imported = "imported_semantic_page" in reasons

    if relative == "index.md" and current:
        from ..markdown_sections import preserve_index_custom_sections

        merged = preserve_index_custom_sections(prior, current)
        if merged == current:
            return None
        return _ensure_final_newline(merged), _semantic_owner_markdown(prior)

    if relative.startswith("guides/"):
        semantic_document = _without_generated_markdown_sections(prior)
        if not _semantic_owner_markdown(semantic_document):
            return None
        return _ensure_final_newline(semantic_document), semantic_document

    heading = _refresh_owned_heading(relative)
    if heading is None:
        return None
    prior_section = _level_two_markdown_section(prior, heading)
    if prior_section is None:
        return None
    prior_body = _level_two_section_body(prior_section)
    if not _is_preservable_semantic_body(prior_body):
        return None
    old_generated = record.get("old_generated_description")
    if (
        not imported
        and heading == "Description"
        and isinstance(old_generated, str)
        and _normalise_semantic_comparison(prior_body)
        == _normalise_semantic_comparison(old_generated)
    ):
        return None

    current_section = _level_two_markdown_section(current, heading) if current else None
    if current_section is not None:
        start, end, _ = current_section
        merged = current[:start] + prior_section[2] + current[end:]
    else:
        title = next(
            (line for line in prior.splitlines() if line.startswith("# ")),
            f"# {PurePosixPath(relative).stem}",
        )
        if current:
            separator = "" if current.endswith("\n\n") else "\n"
            merged = current + separator + prior_section[2]
        else:
            merged = f"{title}\n\n{prior_section[2]}"
    return _ensure_final_newline(merged), prior_section[2]


def _refresh_owned_heading(relative: str) -> str | None:
    if relative.startswith(("modules/", "entities/")):
        return "Description"
    if relative.startswith("flows/"):
        return "Behavior"
    if relative in {"api-contracts.md", "dependencies.md", "load-order.md"}:
        return "Notes"
    return None


def _level_two_markdown_section(
    markdown: str,
    heading: str,
) -> tuple[int, int, str] | None:
    match = re.search(
        rf"(?ms)^##[ \t]+{re.escape(heading)}[ \t]*\r?\n.*?(?=^##[ \t]+|\Z)",
        markdown,
    )
    if match is None:
        return None
    return match.start(), match.end(), match.group(0)


def _level_two_section_body(section: tuple[int, int, str]) -> str:
    lines = section[2].splitlines()
    return "\n".join(lines[1:]).strip()


def _normalise_semantic_comparison(value: str) -> str:
    return " ".join(value.replace("\r", "").split()).casefold()


def _is_preservable_semantic_body(value: str) -> bool:
    normalized = _normalise_semantic_comparison(value)
    if not normalized or normalized in {"-", "—"}:
        return False
    return not any(
        marker in normalized
        for marker in (
            "_auto-generated from `",
            "replace this placeholder",
            "no detailed chain extracted",
        )
    )


def _without_generated_markdown_sections(markdown: str) -> str:
    semantic = markdown
    for _, generated in _generated_sections(markdown):
        semantic = semantic.replace(generated, "")
    return _ensure_final_newline(semantic.strip()) if semantic.strip() else ""


def _ensure_final_newline(value: str) -> str:
    return value.rstrip() + "\n"


def _mark_continuation_pages_needing_grounding(
    worklist: dict[str, Any],
    preserved_paths: tuple[str, ...],
) -> None:
    expected = set(_portable_path_tuple(list(preserved_paths)))
    found: set[str] = set()
    items = worklist.get("items", [])
    if not isinstance(items, list):
        raise DocumentationIntegrityError("Semantic worklist items are malformed.")
    for item in items:
        if not isinstance(item, dict) or item.get("canonical_path") not in expected:
            continue
        path = str(item["canonical_path"])
        found.add(path)
        original_classification = item.get("imported_classification")
        signals = {
            str(signal)
            for signal in item.get("signals", [])
            if isinstance(signal, str) and not signal.startswith("imported:")
        }
        if original_classification not in {None, "needs_grounding"}:
            signals.add(f"continuation:also_{original_classification}")
        signals.update(
            {"imported:needs_grounding", "continuation:source_revision_changed"}
        )
        context = {
            str(value)
            for value in item.get("suggested_context", [])
            if isinstance(value, str) and value != "evidence:wiki-input.json"
        }
        context.add("evidence:continuation.json")
        checks = {
            str(value)
            for value in item.get("acceptance_checks", [])
            if isinstance(value, str)
        }
        checks.add(
            "Re-ground preserved semantic claims against the refreshed source revision or defer them explicitly."
        )
        item.update(
            {
                "status": "open",
                "signals": sorted(signals),
                "suggested_context": sorted(context),
                "acceptance_checks": sorted(checks),
                "imported_classification": "needs_grounding",
                "reuse_eligible": True,
                "grounding_status": "unknown",
                "deferred": False,
                "deferral_reason": None,
            }
        )
    missing = sorted(expected - found)
    if missing:
        raise DocumentationIntegrityError(
            "Preserved continuation pages are missing from the semantic worklist: "
            f"{missing}"
        )
    counts = worklist.get("counts")
    if isinstance(counts, dict):
        counts["by_status"] = {
            status: sum(
                isinstance(item, Mapping) and item.get("status") == status
                for item in items
            )
            for status in ("deferred", "open", "reused")
        }
        counts["deferred"] = sum(
            isinstance(item, Mapping) and item.get("deferred") is True for item in items
        )


def _commit_initial_prepare(transaction: _InitialPrepareTransaction) -> None:
    transaction.clear()


def _rollback_initial_prepare(transaction: _InitialPrepareTransaction) -> None:
    if not transaction.active:
        return
    workspace_root = transaction.workspace_root
    root_identity = transaction.root_identity
    if workspace_root is None or root_identity is None:
        raise DocumentationIntegrityError("Invalid initial-prepare transaction state.")

    if _directory_identity(workspace_root) != root_identity:
        raise DocumentationIntegrityError(
            "Initial-prepare workspace root changed identity before rollback."
        )
    try:
        root_entries = sorted(entry.name for entry in os.scandir(workspace_root))
    except OSError as exc:
        raise DocumentationIntegrityError(
            f"Cannot inspect initial-prepare workspace rollback state: {exc}"
        ) from exc
    unexpected = sorted(set(root_entries) - set(_INITIAL_PREPARE_OWNED_ROOTS))
    if unexpected:
        raise DocumentationIntegrityError(
            "Initial-prepare rollback found an unexpected workspace entry and "
            f"refused to delete it: {unexpected[0]}"
        )

    # Reject injected redirects and special files before deleting any owned tree.
    _assert_existing_workspace_layout_safe(workspace_root)
    for relative in _INITIAL_PREPARE_OWNED_ROOTS:
        target = workspace_root / relative
        if not os.path.lexists(target):
            continue
        entry_stat = target.lstat()
        is_reparse = bool(getattr(entry_stat, "st_reparse_tag", 0)) or bool(
            getattr(entry_stat, "st_file_attributes", 0) & 0x400
        )
        if (
            not stat.S_ISDIR(entry_stat.st_mode)
            or stat.S_ISLNK(entry_stat.st_mode)
            or is_reparse
        ):
            raise DocumentationIntegrityError(
                "Initial-prepare rollback target is not a regular owned directory: "
                f"{relative}"
            )
        try:
            shutil.rmtree(target)
        except OSError as exc:
            raise DocumentationIntegrityError(
                f"Cannot remove initial-prepare workspace artifact {relative}: {exc}"
            ) from exc
        if _directory_identity(workspace_root) != root_identity:
            raise DocumentationIntegrityError(
                "Initial-prepare workspace root changed during rollback."
            )

    try:
        remaining = sorted(entry.name for entry in os.scandir(workspace_root))
    except OSError as exc:
        raise DocumentationIntegrityError(
            f"Cannot verify initial-prepare workspace rollback: {exc}"
        ) from exc
    if remaining:
        raise DocumentationIntegrityError(
            "Initial-prepare workspace was not empty after owned-artifact cleanup: "
            f"{remaining[0]}"
        )
    if transaction.preserve_root:
        if _directory_identity(workspace_root) != root_identity:
            raise DocumentationIntegrityError(
                "Initially empty workspace root changed during rollback."
            )
    else:
        try:
            workspace_root.rmdir()
        except OSError as exc:
            raise DocumentationIntegrityError(
                f"Cannot remove the newly created documentation workspace: {exc}"
            ) from exc
    transaction.clear()


def _archive_owned_run(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    transaction: _RefreshArchiveTransaction,
) -> str:
    control = workspace_root / RUN_CONTROL_DIR
    history = control / "history"
    if os.path.lexists(history):
        _assert_safe_workspace_directory(workspace_root, history, "history")
    else:
        history.mkdir(parents=False, exist_ok=False)
        _assert_safe_workspace_directory(workspace_root, history, "history")
    archive = history / f"{run.run_id}-{_archive_timestamp()}"
    archive.mkdir(parents=True, exist_ok=False)
    _assert_safe_workspace_directory(
        workspace_root,
        archive,
        archive.relative_to(workspace_root).as_posix(),
    )
    transaction.workspace_root = workspace_root
    transaction.archive = archive
    transaction.prior_run_id = run.run_id
    transaction.phase = "archiving"
    _write_refresh_transaction_marker(transaction)
    for relative in ("stages", "packets", "results", "evidence", "skills"):
        source = control / relative
        if source.exists():
            source.replace(archive / relative)
    run_path = control / RUN_FILENAME
    if run_path.exists():
        run_path.replace(archive / RUN_FILENAME)
    # Keep the old policy in place until the archive is complete so transaction
    # marker writes remain policy-bound. The new preparation atomically replaces
    # it, while the archived copy remains available for rollback.
    policy_path = control / POLICY_FILENAME
    if policy_path.exists():
        shutil.copy2(policy_path, archive / POLICY_FILENAME)
    for relative in ("wiki", "site", "_site"):
        source = workspace_root / relative
        if source.exists():
            source.replace(archive / relative)
    transaction.phase = "building"
    _write_refresh_transaction_marker(transaction)
    return archive.relative_to(workspace_root).as_posix()


def _refresh_transaction_path(workspace_root: Path) -> Path:
    return workspace_root / RUN_CONTROL_DIR / REFRESH_TRANSACTION_FILENAME


def _write_refresh_transaction_marker(
    transaction: _RefreshArchiveTransaction,
) -> None:
    if not transaction.active or transaction.phase not in {
        "archiving",
        "building",
        "committed",
        "rolled_back",
    }:
        raise DocumentationIntegrityError("Invalid refresh transaction state.")
    workspace_root = transaction.workspace_root
    archive = transaction.archive
    prior_run_id = transaction.prior_run_id
    if workspace_root is None or archive is None or prior_run_id is None:
        raise DocumentationIntegrityError("Invalid refresh transaction state.")
    _write_json(
        _refresh_transaction_path(workspace_root),
        {
            "schema_version": "llm-wiki-documentation-refresh-transaction/v1",
            "prior_run_id": prior_run_id,
            "archive_path": archive.relative_to(workspace_root).as_posix(),
            "phase": transaction.phase,
        },
    )


def _commit_refresh_archive(transaction: _RefreshArchiveTransaction) -> None:
    previous_phase = transaction.phase
    transaction.phase = "committed"
    try:
        _write_refresh_transaction_marker(transaction)
    except Exception:
        transaction.phase = previous_phase
        raise
    workspace_root = transaction.workspace_root
    if workspace_root is None:
        raise DocumentationIntegrityError("Invalid refresh transaction state.")
    try:
        _remove_refresh_transaction_marker(workspace_root)
    except DocumentationIntegrityError:
        # The durable committed marker is sufficient. A later prepare removes it
        # after confirming that no rollback is required.
        pass
    transaction.workspace_root = None
    transaction.archive = None


def _recover_interrupted_refresh(workspace_root: Path) -> None:
    marker = _refresh_transaction_path(workspace_root)
    if not os.path.lexists(marker):
        return
    try:
        payload = _read_json(marker)
    except DocumentationRunError as exc:
        raise DocumentationIntegrityError(
            "Cannot recover malformed refresh transaction evidence."
        ) from exc
    expected = {"schema_version", "prior_run_id", "archive_path", "phase"}
    if set(payload) != expected or payload.get("schema_version") != (
        "llm-wiki-documentation-refresh-transaction/v1"
    ):
        raise DocumentationIntegrityError(
            "Refresh transaction marker has an unsupported schema."
        )
    prior_run_id = payload.get("prior_run_id")
    phase = payload.get("phase")
    if not isinstance(prior_run_id, str) or phase not in {
        "archiving",
        "building",
        "committed",
        "rolled_back",
    }:
        raise DocumentationIntegrityError("Refresh transaction marker is malformed.")
    archive_relative = _portable_path(
        str(payload.get("archive_path", "")), field_name="refresh archive path"
    )
    archive = _workspace_path(workspace_root, archive_relative)
    expected_history = workspace_root / RUN_CONTROL_DIR / "history"
    try:
        archive.relative_to(expected_history)
    except ValueError as exc:
        raise DocumentationIntegrityError(
            "Refresh transaction archive must remain under control history."
        ) from exc
    if phase == "committed":
        _remove_refresh_transaction_marker(workspace_root)
        return
    if phase == "rolled_back":
        if not (workspace_root / RUN_CONTROL_DIR / RUN_FILENAME).is_file():
            raise DocumentationIntegrityError(
                "Rolled-back refresh marker has no restored prior run."
            )
        if os.path.lexists(archive):
            try:
                archive.rmdir()
            except OSError as exc:
                raise DocumentationIntegrityError(
                    "Rolled-back refresh archive is unexpectedly non-empty."
                ) from exc
        _remove_refresh_transaction_marker(workspace_root)
        return
    transaction = _RefreshArchiveTransaction(
        workspace_root=workspace_root,
        archive=archive,
        prior_run_id=prior_run_id,
        phase=phase,
    )
    _rollback_refresh_archive(transaction)


def _rollback_refresh_archive(transaction: _RefreshArchiveTransaction) -> None:
    if not transaction.active or transaction.phase not in {"archiving", "building"}:
        return
    workspace_root = transaction.workspace_root
    archive = transaction.archive
    if workspace_root is None or archive is None:
        raise DocumentationIntegrityError("Invalid refresh transaction state.")
    control = workspace_root / RUN_CONTROL_DIR
    entries = (
        (archive / "stages", control / "stages", False),
        (archive / "packets", control / "packets", False),
        (archive / "results", control / "results", False),
        (archive / "evidence", control / "evidence", False),
        (archive / "skills", control / "skills", False),
        (archive / RUN_FILENAME, control / RUN_FILENAME, False),
        (archive / POLICY_FILENAME, control / POLICY_FILENAME, True),
        (archive / "wiki", workspace_root / "wiki", False),
        (archive / "site", workspace_root / "site", False),
        (archive / "_site", workspace_root / "_site", False),
    )
    building = transaction.phase == "building"
    for archived, destination, copied_policy in entries:
        archived_exists = os.path.lexists(archived)
        destination_exists = os.path.lexists(destination)
        # During a retried rollback an absent archive entry means that entry was
        # already restored before the prior process stopped. Never delete it.
        if building and archived_exists and destination_exists:
            _remove_refresh_owned_path(workspace_root, destination)
            destination_exists = False
        if not archived_exists:
            continue
        if destination_exists:
            if copied_policy and archived.read_bytes() == destination.read_bytes():
                archived.unlink()
                continue
            raise DocumentationIntegrityError(
                f"Refresh rollback destination already exists: {destination}"
            )
        archived.replace(destination)
    previous_phase = transaction.phase
    transaction.phase = "rolled_back"
    try:
        _write_refresh_transaction_marker(transaction)
    except Exception:
        transaction.phase = previous_phase
        raise
    if os.path.lexists(archive):
        try:
            archive.rmdir()
        except OSError as exc:
            raise DocumentationIntegrityError(
                f"Refresh archive is not empty after rollback: {archive}: {exc}"
            ) from exc
    _remove_refresh_transaction_marker(workspace_root)
    transaction.workspace_root = None
    transaction.archive = None


def _remove_refresh_owned_path(workspace_root: Path, target: Path) -> None:
    try:
        target.relative_to(workspace_root)
        entry_stat = target.lstat()
    except (OSError, ValueError) as exc:
        raise DocumentationIntegrityError(
            f"Cannot safely remove partial refresh artifact {target}: {exc}"
        ) from exc
    is_reparse = bool(getattr(entry_stat, "st_reparse_tag", 0)) or bool(
        getattr(entry_stat, "st_file_attributes", 0) & 0x400
    )
    if stat.S_ISLNK(entry_stat.st_mode) or is_reparse:
        raise DocumentationIntegrityError(
            f"Partial refresh artifact is a link or reparse point: {target}"
        )
    if stat.S_ISDIR(entry_stat.st_mode):
        shutil.rmtree(target)
    elif stat.S_ISREG(entry_stat.st_mode):
        target.unlink()
    else:
        raise DocumentationIntegrityError(
            f"Partial refresh artifact is not regular: {target}"
        )


def _remove_refresh_transaction_marker(workspace_root: Path) -> None:
    marker = _refresh_transaction_path(workspace_root)
    if not os.path.lexists(marker):
        return
    target_stat = marker.lstat()
    is_reparse = bool(getattr(target_stat, "st_reparse_tag", 0)) or bool(
        getattr(target_stat, "st_file_attributes", 0) & 0x400
    )
    if not stat.S_ISREG(target_stat.st_mode) or is_reparse:
        raise DocumentationIntegrityError(
            "Refresh transaction marker must remain a regular file."
        )
    control = workspace_root / RUN_CONTROL_DIR
    if _supports_descriptor_bound_workspace_writes():
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        descriptor = os.open(control, flags)
        try:
            os.unlink(REFRESH_TRANSACTION_FILENAME, dir_fd=descriptor)
            _fsync_directory_after_replace(descriptor)
        finally:
            os.close(descriptor)
    elif _uses_windows_guarded_path_writes():
        try:
            with guard_windows_directory_chain(workspace_root, (RUN_CONTROL_DIR,)):
                marker.unlink()
        except WindowsDirectoryGuardError as exc:
            raise DocumentationIntegrityError(
                f"Cannot remove the guarded refresh marker: {exc}"
            ) from exc
    else:
        raise DocumentationIntegrityError(
            "Cannot safely remove a refresh transaction marker on this platform."
        )


def _preserve_imported_semantic_markdown(
    wiki_root: Path,
    imported_text: Mapping[str, str],
) -> list[str]:
    """Keep imported semantic prose available after a workspace-only refresh.

    The deterministic bootstrap owns navigation and generated sections.  When a
    legacy or differently structured page cannot be merged by that generator,
    retain its non-generated prose in the same canonical page under an explicit
    imported-baseline heading.  The adopted input remains untouched and the
    later semantic worklist still decides whether the prose is reusable.
    """

    preserved: list[str] = []
    for relative in sorted(imported_text):
        target = _workspace_path(wiki_root, relative)
        original_semantic = _semantic_owner_markdown(imported_text[relative])
        if not original_semantic:
            continue
        current = target.read_text(encoding="utf-8") if target.is_file() else ""
        if original_semantic in current:
            continue
        separator = "" if not current or current.endswith("\n\n") else "\n"
        merged = (
            current
            + separator
            + "## Imported semantic baseline\n\n"
            + original_semantic.rstrip()
            + "\n"
        )
        write_text_output(target, merged)
        preserved.append(relative)
    return preserved


def _semantic_owner_markdown(text: str) -> str:
    semantic = text
    for _, generated in _generated_sections(text):
        semantic = semantic.replace(generated, "")
    lines = semantic.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()

__all__ = (
    '_capture_native_artifact_bytes',
    '_rollback_native_artifact_bytes',
    '_capture_exact_file_bytes',
    '_rollback_exact_file_bytes',
    '_rollback_native_refresh_transaction',
    '_refresh_prepared_native_projection',
    '_refresh_and_reanchor_native_projection',
    '_write_native_refresh_evidence',
    '_assert_native_only_ownership_change',
    '_native_refresh_payload',
    '_native_artifact_transition',
    '_native_refresh_verification_evaluation',
    '_apply_native_verification_limitation',
    'source_identity',
    '_assert_resume_compatible',
    '_assert_intake_compatible',
    '_assert_runtime_roots_compatible',
    '_capture_refresh_continuation',
    '_refresh_continuation_candidate_paths',
    '_prior_generated_descriptions',
    '_source_identity_changed',
    '_restore_refresh_continuation',
    '_merge_refresh_semantic_page',
    '_refresh_owned_heading',
    '_level_two_markdown_section',
    '_level_two_section_body',
    '_normalise_semantic_comparison',
    '_is_preservable_semantic_body',
    '_without_generated_markdown_sections',
    '_ensure_final_newline',
    '_mark_continuation_pages_needing_grounding',
    '_commit_initial_prepare',
    '_rollback_initial_prepare',
    '_archive_owned_run',
    '_refresh_transaction_path',
    '_write_refresh_transaction_marker',
    '_commit_refresh_archive',
    '_recover_interrupted_refresh',
    '_rollback_refresh_archive',
    '_remove_refresh_owned_path',
    '_remove_refresh_transaction_marker',
    '_preserve_imported_semantic_markdown',
    '_semantic_owner_markdown',
)
