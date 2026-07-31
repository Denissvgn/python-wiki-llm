"""Documentation-run verify lifecycle."""

from __future__ import annotations

from .dependencies import *
from .contracts import *
from ._legacy import *

def verify_documentation_run(
    workspace: str | Path,
    *,
    advance: bool = True,
) -> DocumentationVerificationReport:
    """Run deterministic lifecycle checks and optionally advance review state."""

    workspace_root = _resolve_workspace_root_argument(workspace)
    run = load_documentation_run(workspace_root)
    checks: list[dict[str, Any]] = []
    limitations = list(run.verdict_limitations)
    try:
        checks.extend(_verify_read_only_inputs(workspace_root, run))
    except DocumentationIntegrityError as exc:
        checks.append({"check": "read_only_inputs", "ok": False, "message": str(exc)})

    generated_path = run.evidence.get("generated_ownership")
    if generated_path:
        generated_payload = _read_json(_workspace_path(workspace_root, generated_path))
        generated_diff = compare_generated_ownership(
            generated_payload.get("fingerprints", {}),
            workspace_root / run.paths["wiki"],
        )
        checks.append(
            {
                "check": "generated_ownership",
                "ok": not any(generated_diff.values()),
                "differences": generated_diff,
            }
        )

    readiness = _read_json(
        _workspace_path(workspace_root, run.evidence["semantic_readiness"])
    )
    checks.append(
        {
            "check": "semantic_readiness",
            "ok": bool(readiness.get("passed")),
            "status": readiness.get("status"),
            "missing_work_ids": readiness.get("missing_work_ids", []),
        }
    )
    for evidence_key, check_name in (("lint", "lint"), ("ci_check", "ci-check")):
        evidence_path = run.evidence.get(evidence_key)
        if not evidence_path:
            checks.append(
                {
                    "check": check_name,
                    "ok": False,
                    "message": "No lifecycle-owned checker evidence was recorded.",
                }
            )
            continue
        evidence_payload = _read_json(_workspace_path(workspace_root, evidence_path))
        checks.append(
            {
                "check": check_name,
                "ok": bool(evidence_payload.get("ok")),
                "status": evidence_payload.get("status"),
                "phase": evidence_payload.get("phase"),
                "evidence": evidence_path,
                "limited": bool(evidence_payload.get("limited", False)),
            }
        )
    if run.state in {"review", "publish_ready"}:
        try:
            _verify_user_docs_gate(workspace_root / run.paths["wiki"], run)
            checks.append({"check": "user_docs", "ok": True})
        except DocumentationRunError as exc:
            checks.append({"check": "user_docs", "ok": False, "message": str(exc)})
        review_ledger_path = run.evidence.get("review_ledger")
        review_ledger_state = "missing"
        review_ledger_ok = False
        if review_ledger_path:
            try:
                review_ledger = DocumentationReviewLedger.from_dict(
                    _read_json(_workspace_path(workspace_root, review_ledger_path))
                )
                review_ledger_state = review_ledger.state
                review_ledger_ok = (
                    review_ledger.state in {"awaiting_supervisor", "publish_ready"}
                    and not review_ledger.unresolved_findings
                )
            except DocumentationReviewError as exc:
                review_ledger_state = f"invalid: {exc}"
        checks.append(
            {
                "check": "independent_review",
                "ok": review_ledger_ok
                and not _has_unresolved_high_findings(run.unresolved_findings)
                and bool(run.evidence.get("review_result")),
                "ledger_state": review_ledger_state,
                "ledger": review_ledger_path,
                "unresolved_findings": run.unresolved_findings,
            }
        )

    site_check_path = run.evidence.get("site_check")
    if site_check_path:
        site_check = _read_json(_workspace_path(workspace_root, site_check_path))
        checks.append(
            {
                "check": "site_check",
                "ok": bool(site_check.get("ok")),
                "built_site_verified": bool(site_check.get("built_site_dir")),
                "link_mode": site_check.get("link_mode", ""),
            }
        )
    elif run.state in {"review", "publish_ready"}:
        checks.append(
            {
                "check": "site_check",
                "ok": False,
                "message": "No workspace export/site-check evidence has been recorded.",
            }
        )

    if run.baseline.get("freshness") != "verified_current":
        if "source_verified_publish_ready_unavailable" not in limitations:
            limitations.append("source_verified_publish_ready_unavailable")
    ok = all(bool(check.get("ok")) for check in checks)
    next_state = None
    if (
        ok
        and advance
        and run.state == "review"
        and run.baseline.get("freshness") == "verified_current"
    ):
        _approve_review_ledger(workspace_root, run, checks=checks)
        transition_documentation_run(run, "publish_ready")
        next_state = "publish_ready"
        save_documentation_run(workspace_root, run)
    elif not ok and any(
        check.get("check") in {"read_only_inputs", "generated_ownership"}
        and not check.get("ok")
        for check in checks
    ):
        _block_run_for_integrity(
            workspace_root,
            run,
            "Deterministic verification found a read-only or generated-ownership mutation.",
        )

    report = DocumentationVerificationReport(
        run_id=run.run_id,
        state=run.state,
        ok=ok,
        checks=tuple(checks),
        limitations=tuple(dict.fromkeys(limitations)),
        next_state=next_state,
    )
    verification_path = (
        workspace_root / RUN_CONTROL_DIR / "evidence" / "verification.json"
    )
    _write_json(verification_path, report.to_dict())
    if run.state != "blocked":
        run.evidence["verification"] = verification_path.relative_to(
            workspace_root
        ).as_posix()
        run.validation_results = [
            item
            for item in run.validation_results
            if item.get("check") != "documentation_verification"
        ]
        run.validation_results.append(
            {
                "check": "documentation_verification",
                "ok": ok,
                "evidence": run.evidence["verification"],
            }
        )
        save_documentation_run(workspace_root, run)
    return report


def _documentation_projection_policy(
    run: DocumentationRun,
) -> tuple[str, str | None]:
    return _validate_documentation_projection_policy(
        run.publication.get("knowledge_mode", "off"),
        run.publication.get("knowledge_public_repository_identity"),
    )


def _assert_documentation_export_projection_policy(
    run: DocumentationRun,
    *,
    knowledge_mode: str | None,
    knowledge_public_repository_identity: str | None,
) -> tuple[str, str | None]:
    recorded_mode, recorded_identity = _documentation_projection_policy(run)
    if knowledge_mode is not None and knowledge_mode != recorded_mode:
        raise DocumentationRunError(
            "Export knowledge mode differs from the prepared run contract; rerun "
            "docs prepare with --refresh and the intended --knowledge-mode."
        )
    if (
        knowledge_public_repository_identity is not None
        and knowledge_public_repository_identity != recorded_identity
    ):
        raise DocumentationRunError(
            "Export public repository identity differs from the prepared run "
            "contract; rerun docs prepare with --refresh and the intended "
            "--knowledge-public-repository-identity."
        )
    return recorded_mode, recorded_identity


def _load_documentation_knowledge_projection(
    wiki_root: Path,
    *,
    knowledge_mode: str,
    knowledge_public_repository_identity: str | None,
):
    if knowledge_mode == "off":
        return None

    from ..knowledge_consumption import load_knowledge_read_view
    from ..knowledge_projection import project_knowledge

    try:
        view = load_knowledge_read_view(
            wiki_root,
            snapshot_only=True,
            include_machine_verification=True,
        )
        projection = project_knowledge(
            view,
            profile=knowledge_mode,
            public_repository_identity=knowledge_public_repository_identity,
        )
    except (OSError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise DocumentationIntegrityError(
            "The selected native-knowledge publication projection could not be "
            f"validated: {exc}. No un-enriched fallback was performed; explicitly "
            "rerun docs prepare with --refresh --knowledge-mode off to choose "
            "that fallback."
        ) from exc

    freshness_records = [
        concept.get("freshness")
        for concept in projection.concepts.values()
        if isinstance(concept, Mapping)
    ]
    if any(
        not isinstance(freshness, Mapping)
        or freshness.get("state") != "not-evaluated"
        or freshness.get("evaluated") is not False
        or freshness.get("live_comparison_performed") is not False
        for freshness in freshness_records
    ):
        raise DocumentationIntegrityError(
            "Standalone documentation export requires a snapshot-only native "
            "projection with freshness preserved as not-evaluated."
        )
    return projection


def _documentation_projection_evidence(
    *,
    knowledge_mode: str,
    knowledge_public_repository_identity: str | None,
    projection,
) -> dict[str, Any]:
    return {
        "mode": knowledge_mode,
        "knowledge_metadata": "off" if projection is None else "summary",
        "profile": projection.profile.value if projection is not None else None,
        "public_repository_identity": knowledge_public_repository_identity,
        "projection_schema_version": (
            projection.schema_version if projection is not None else None
        ),
        "source_knowledge_hash": (
            projection.source_knowledge_hash if projection is not None else None
        ),
        "freshness_scope": "snapshot-only",
        "freshness_evaluated": False,
        "warnings": list(projection.warnings) if projection is not None else [],
        "canonical_body_media_review": "separate-required",
        "derived_output": "disposable-rebuildable",
    }

__all__ = (
    'verify_documentation_run',
    '_documentation_projection_policy',
    '_assert_documentation_export_projection_policy',
    '_load_documentation_knowledge_projection',
    '_documentation_projection_evidence',
)
