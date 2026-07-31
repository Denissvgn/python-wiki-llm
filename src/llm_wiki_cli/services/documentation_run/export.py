"""Documentation-run export lifecycle."""

from __future__ import annotations

from .dependencies import *
from .contracts import *
from ._legacy import *
from .verify import *

def export_documentation_run(
    workspace: str | Path,
    *,
    build: bool = False,
    builder_command: Iterable[str] | None = None,
    knowledge_mode: str | None = None,
    knowledge_public_repository_identity: str | None = None,
) -> dict[str, Any]:
    """Export/check the user profile and write a reproducible local handoff."""

    from ..site_export import SiteExportError, check_site_mirror, export_site_mirror

    workspace_root = _resolve_workspace_root_argument(workspace)
    run = load_documentation_run(workspace_root)
    _verify_read_only_inputs(workspace_root, run)
    generated_path = run.evidence.get("generated_ownership")
    if not generated_path:
        raise DocumentationIntegrityError(
            "Workspace export requires generated-ownership evidence."
        )
    generated_payload = _read_json(_workspace_path(workspace_root, generated_path))
    generated_diff = compare_generated_ownership(
        generated_payload.get("fingerprints", {}),
        workspace_root / run.paths["wiki"],
    )
    if any(generated_diff.values()):
        raise DocumentationIntegrityError(
            f"Generated ownership changed before workspace export: {generated_diff}"
        )
    if run.state not in {"review", "publish_ready"}:
        raise DocumentationTransitionError(
            "Workspace export requires a completed user-docs stage and review state."
        )
    (
        selected_knowledge_mode,
        selected_public_repository_identity,
    ) = _assert_documentation_export_projection_policy(
        run,
        knowledge_mode=knowledge_mode,
        knowledge_public_repository_identity=(
            knowledge_public_repository_identity
        ),
    )
    wiki_root = workspace_root / run.paths["wiki"]
    site_root = workspace_root / run.paths["site"]
    built_root = workspace_root / run.paths["built_site"]
    publication_format = str(run.publication["format"])
    link_mode = str(run.publication["link_mode"])
    file_friendly = link_mode == "file"
    try:
        export_projection = _load_documentation_knowledge_projection(
            wiki_root,
            knowledge_mode=selected_knowledge_mode,
            knowledge_public_repository_identity=(
                selected_public_repository_identity
            ),
        )
        export_report = export_site_mirror(
            wiki_dir=wiki_root,
            out_dir=site_root,
            format=publication_format,
            front_matter=publication_format in {"mkdocs", "docusaurus"},
            file_friendly=file_friendly,
            profile="user",
            site_name=str(run.publication["site_name"]),
            knowledge_metadata=(
                "summary" if export_projection is not None else None
            ),
            knowledge_projection=export_projection,
        )
    except (DocumentationIntegrityError, SiteExportError) as exc:
        message = (
            "Standalone documentation export rejected the persisted native-knowledge "
            f"publication policy: {exc}"
        )
        _block_run_for_integrity(workspace_root, run, message)
        raise DocumentationIntegrityError(message) from exc
    export_projection_evidence = _documentation_projection_evidence(
        knowledge_mode=selected_knowledge_mode,
        knowledge_public_repository_identity=(
            selected_public_repository_identity
        ),
        projection=export_projection,
    )
    export_payload = export_report.to_dict()
    export_payload["knowledge_projection"] = export_projection_evidence
    export_path = workspace_root / RUN_CONTROL_DIR / "evidence" / "site-export.json"
    _write_json(export_path, export_payload)
    run.evidence["site_export"] = export_path.relative_to(workspace_root).as_posix()

    builder_evidence = _run_authorized_builder(
        workspace_root,
        run,
        build=build,
        builder_command=builder_command,
    )
    builder_path = workspace_root / RUN_CONTROL_DIR / "evidence" / "builder.json"
    _write_json(builder_path, builder_evidence)
    run.evidence["builder"] = builder_path.relative_to(workspace_root).as_posix()
    built_verified = builder_evidence.get("status") == "complete"
    try:
        check_projection = _load_documentation_knowledge_projection(
            wiki_root,
            knowledge_mode=selected_knowledge_mode,
            knowledge_public_repository_identity=(
                selected_public_repository_identity
            ),
        )
        check_projection_evidence = _documentation_projection_evidence(
            knowledge_mode=selected_knowledge_mode,
            knowledge_public_repository_identity=(
                selected_public_repository_identity
            ),
            projection=check_projection,
        )
        if (
            export_projection_evidence["source_knowledge_hash"]
            != check_projection_evidence["source_knowledge_hash"]
        ):
            raise DocumentationIntegrityError(
                "The native knowledge snapshot changed between export and check; "
                "the enriched output is stale and must be rebuilt."
            )
        check_report = check_site_mirror(
            wiki_dir=wiki_root,
            out_dir=site_root,
            built_site_dir=built_root if built_verified else None,
            link_mode=link_mode,
            format=publication_format,
            profile="user",
            site_name=str(run.publication["site_name"]),
            knowledge_metadata=(
                "summary" if check_projection is not None else None
            ),
            knowledge_projection=check_projection,
        )
    except (DocumentationIntegrityError, SiteExportError) as exc:
        message = (
            "Standalone documentation check rejected the persisted native-knowledge "
            f"publication policy: {exc}"
        )
        _block_run_for_integrity(workspace_root, run, message)
        raise DocumentationIntegrityError(message) from exc
    check_payload = check_report.to_dict()
    check_payload["knowledge_projection"] = check_projection_evidence
    if not built_verified:
        check_payload.setdefault("warnings", []).append(
            {
                "category": "built_site_not_verified",
                "message": (
                    "A builder was not run successfully; publication readiness remains "
                    "limited to the exported Markdown mirror."
                ),
            }
        )
    check_path = workspace_root / RUN_CONTROL_DIR / "evidence" / "site-check.json"
    _write_json(check_path, check_payload)
    run.evidence["site_check"] = check_path.relative_to(workspace_root).as_posix()
    if check_payload.get("issues"):
        site_loop = _record_site_review_findings(
            workspace_root,
            run,
            export_path=export_path,
            check_path=check_path,
            check_payload=check_payload,
        )
        if site_loop["decision"]["blocked"]:
            _block_run_for_integrity(
                workspace_root,
                run,
                site_loop["decision"]["rationale"],
                integrity=False,
            )
    if not built_verified and "built_site_not_verified" not in run.verdict_limitations:
        run.verdict_limitations.append("built_site_not_verified")
    elif built_verified and "built_site_not_verified" in run.verdict_limitations:
        run.verdict_limitations.remove("built_site_not_verified")
    save_documentation_run(workspace_root, run)

    verification = verify_documentation_run(workspace_root, advance=built_verified)
    run = load_documentation_run(workspace_root)
    final_report = _build_final_report(
        run,
        export_report=export_payload,
        builder_evidence=builder_evidence,
        site_check=check_payload,
        verification=verification.to_dict(),
    )
    final_json = workspace_root / RUN_CONTROL_DIR / "evidence" / "final-report.json"
    final_markdown = workspace_root / RUN_CONTROL_DIR / "evidence" / "final-report.md"
    _write_json(final_json, final_report)
    _write_workspace_text(
        workspace_root, final_markdown, _render_final_report(final_report)
    )
    run.evidence["final_report"] = final_json.relative_to(workspace_root).as_posix()
    save_documentation_run(workspace_root, run)
    return final_report

__all__ = (
    'export_documentation_run',
)
