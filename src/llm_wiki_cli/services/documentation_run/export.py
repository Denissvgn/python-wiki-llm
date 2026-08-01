"""Documentation-run export services."""

from __future__ import annotations

from .dependencies import *
from .contracts import *
from .schema import *
from .workspace import *
from .integrity import *
from .refresh import *
from .record import *
from .verify import *

def _run_authorized_builder(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    build: bool,
    builder_command: Iterable[str] | None,
) -> dict[str, Any]:
    if not build:
        return {
            "status": "not_authorized",
            "executed": False,
            "message": "Builder execution was not selected; deployment remains a handoff.",
        }
    if builder_command is None:
        if run.publication.get("format") != "mkdocs":
            return {
                "status": "deferred",
                "executed": False,
                "message": "No default builder is defined for this distribution format.",
            }
        if importlib.util.find_spec("mkdocs") is None:
            return {
                "status": "deferred",
                "executed": False,
                "message": "MkDocs is not installed; no dependency was installed implicitly.",
            }
        command = [
            sys.executable,
            "-m",
            "mkdocs",
            "build",
            "--strict",
            "-f",
            str(workspace_root / run.paths["site"] / "mkdocs.yml"),
        ]
    else:
        command = [str(value) for value in builder_command]
        if (
            not command
            or len(command) > 32
            or any(not value or "\n" in value or "\r" in value for value in command)
        ):
            raise DocumentationSchemaError(
                "builder_command must contain 1-32 non-empty argument strings."
            )
    built_root = workspace_root / run.paths["built_site"]
    built_site_before_present = os.path.lexists(built_root)
    built_site_before: TreeBaseline | None = None
    if built_site_before_present:
        try:
            built_site_before = capture_tree_baseline(
                built_root,
                display="built_site_before_builder",
            )
        except DocumentationPolicyError as exc:
            return {
                "status": "failed",
                "executed": False,
                "returncode": None,
                "command_kind": "mkdocs" if "mkdocs" in command else "custom",
                "message": (
                    "Cannot establish safe pre-build evidence for the built site: "
                    f"{exc}"
                ),
                "built_site_present": False,
                "built_site_changed": False,
                "built_site_before_tree_hash": None,
                "built_site_after_tree_hash": None,
            }
        try:
            _remove_built_site_before_builder(workspace_root, built_root)
        except DocumentationIntegrityError as exc:
            return {
                "status": "failed",
                "executed": False,
                "returncode": None,
                "command_kind": "mkdocs" if "mkdocs" in command else "custom",
                "message": f"Cannot safely clear prior built-site output: {exc}",
                "built_site_present": True,
                "built_site_recreated": False,
                "built_site_has_html": False,
                "built_site_changed": False,
                "built_site_before_tree_hash": built_site_before.tree_hash,
                "built_site_after_tree_hash": None,
                "built_site_before_file_count": built_site_before.file_count,
                "built_site_after_file_count": 0,
            }
    if os.path.lexists(built_root):
        raise DocumentationIntegrityError(
            "Built-site output still exists after guarded pre-build cleanup."
        )
    completed: subprocess.CompletedProcess[bytes] | None = None
    execution_error: str | None = None
    stdout_tail = ""
    stderr_tail = ""
    stdout_bytes = 0
    stderr_bytes = 0
    stdout_truncated = False
    stderr_truncated = False
    try:
        evidence_root = workspace_root / RUN_CONTROL_DIR / "evidence"
        with (
            tempfile.TemporaryFile(mode="w+b", dir=evidence_root) as stdout_stream,
            tempfile.TemporaryFile(mode="w+b", dir=evidence_root) as stderr_stream,
        ):
            completed = subprocess.run(  # noqa: S603 - caller-authorized argv
                command,
                cwd=workspace_root,
                stdout=stdout_stream,
                stderr=stderr_stream,
                check=False,
                timeout=600,
            )
            stdout_tail, stdout_bytes, stdout_truncated = _read_builder_output_tail(
                stdout_stream
            )
            stderr_tail, stderr_bytes, stderr_truncated = _read_builder_output_tail(
                stderr_stream
            )
    except (OSError, subprocess.SubprocessError) as exc:
        execution_error = str(exc)
    built_site_after: TreeBaseline | None = None
    output_error: str | None = None
    if os.path.lexists(built_root):
        try:
            built_site_after = capture_tree_baseline(
                built_root,
                display="built_site_after_builder",
            )
        except DocumentationPolicyError as exc:
            output_error = f"Built-site output failed safe fingerprinting: {exc}"
    built_site_has_html = bool(
        built_site_after is not None
        and any(
            PurePosixPath(path).suffix.casefold() == ".html"
            for path in built_site_after.file_hashes
        )
    )
    built_site_changed = built_site_after is not None and (
        built_site_before is None
        or built_site_before.tree_hash != built_site_after.tree_hash
    )
    built_site_has_files = bool(
        built_site_after is not None and built_site_after.file_count
    )
    ok = (
        completed is not None
        and completed.returncode == 0
        and built_site_has_files
        and built_site_has_html
        and output_error is None
    )
    message = execution_error or output_error
    if (
        completed is not None
        and completed.returncode == 0
        and not ok
        and message is None
    ):
        message = (
            "Builder exited successfully but did not create a new safe, non-empty "
            "built-site tree containing HTML during this invocation."
        )
    return {
        "status": "complete" if ok else "failed",
        "executed": True,
        "returncode": completed.returncode if completed is not None else None,
        "command_kind": "mkdocs" if "mkdocs" in command else "custom",
        "stdout": stdout_tail,
        "stderr": stderr_tail,
        "stdout_bytes": stdout_bytes,
        "stderr_bytes": stderr_bytes,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
        "message": message,
        "built_site_present": built_site_after is not None,
        "built_site_recreated": built_site_after is not None,
        "built_site_has_html": built_site_has_html,
        "built_site_changed": built_site_changed,
        "built_site_before_tree_hash": (
            built_site_before.tree_hash if built_site_before is not None else None
        ),
        "built_site_after_tree_hash": (
            built_site_after.tree_hash if built_site_after is not None else None
        ),
        "built_site_before_file_count": (
            built_site_before.file_count if built_site_before is not None else 0
        ),
        "built_site_after_file_count": (
            built_site_after.file_count if built_site_after is not None else 0
        ),
    }


def _read_builder_output_tail(stream) -> tuple[str, int, bool]:
    stream.flush()
    total_bytes = stream.seek(0, os.SEEK_END)
    truncated = total_bytes > _MAX_BUILDER_LOG_BYTES
    stream.seek(max(0, total_bytes - _MAX_BUILDER_LOG_BYTES))
    data = stream.read(_MAX_BUILDER_LOG_BYTES)
    return data.decode("utf-8", errors="replace"), total_bytes, truncated


def _remove_built_site_before_builder(
    workspace_root: Path,
    built_root: Path,
) -> None:
    """Remove only the derived built-site root through qualified path guards."""

    root = Path(os.path.abspath(os.fspath(workspace_root)))
    target = Path(os.path.abspath(os.fspath(built_root)))
    if target != root / "_site":
        raise DocumentationIntegrityError(
            "Builder cleanup is restricted to the lifecycle-owned `_site` root."
        )
    if not os.path.lexists(target):
        return
    _assert_workspace_output_tree_safe(root, "_site")
    root_identity = _directory_identity(root)
    try:
        if _supports_descriptor_bound_workspace_writes():
            if not bool(getattr(shutil.rmtree, "avoids_symlink_attacks", False)):
                raise DocumentationIntegrityError(
                    "This platform lacks symlink-safe recursive directory removal."
                )
            _assert_safe_workspace_directory(root, target, "_site")
            shutil.rmtree(target)
        elif _uses_windows_guarded_path_writes():
            with guard_windows_directory_chain(root, ()):
                _assert_safe_workspace_directory(root, target, "_site")
                shutil.rmtree(target)
        else:
            raise DocumentationIntegrityError(
                "This platform lacks a qualified built-site removal guard."
            )
    except WindowsDirectoryGuardError as exc:
        raise DocumentationIntegrityError(
            f"Cannot pin the Windows workspace during built-site removal: {exc}"
        ) from exc
    except OSError as exc:
        raise DocumentationIntegrityError(
            f"Cannot remove prior built-site output: {exc}"
        ) from exc
    if _directory_identity(root) != root_identity:
        raise DocumentationIntegrityError(
            "Workspace root changed during built-site removal."
        )
    if os.path.lexists(target):
        raise DocumentationIntegrityError(
            "Prior built-site output remains after guarded removal."
        )


def _build_final_report(
    run: DocumentationRun,
    *,
    export_report: Mapping[str, Any],
    builder_evidence: Mapping[str, Any],
    site_check: Mapping[str, Any],
    verification: Mapping[str, Any],
) -> dict[str, Any]:
    verification_ok = bool(verification.get("ok"))
    builder_complete = builder_evidence.get("status") == "complete"
    built_site_check_ok = (
        builder_complete
        and bool(site_check.get("ok"))
        and bool(site_check.get("built_site_dir"))
    )
    current_publish_ready = (
        run.state == "publish_ready" and built_site_check_ok and verification_ok
    )
    export_projection = export_report.get("knowledge_projection")
    check_projection = site_check.get("knowledge_projection")
    export_projection_hash = (
        export_projection.get("source_knowledge_hash")
        if isinstance(export_projection, Mapping)
        else None
    )
    check_projection_hash = (
        check_projection.get("source_knowledge_hash")
        if isinstance(check_projection, Mapping)
        else None
    )
    export_projection_freshness = (
        export_projection.get("freshness")
        if isinstance(export_projection, Mapping)
        else None
    )
    check_projection_freshness = (
        check_projection.get("freshness")
        if isinstance(check_projection, Mapping)
        else None
    )
    if current_publish_ready:
        verdict = "publish_ready"
    elif verification_ok:
        verdict = "local_artifact_ready_with_limitations"
    else:
        verdict = "blocked"
    return {
        "schema_version": DOCUMENTATION_FINAL_REPORT_SCHEMA_VERSION,
        "run_id": run.run_id,
        "state": run.state,
        "verdict": verdict,
        "source": {
            "available": bool(run.source.get("available")),
            "display_identifier": run.source.get("display_identifier"),
            "revision": run.source.get("revision"),
            "source_verified": run.baseline.get("freshness") == "verified_current",
        },
        "baseline": run.baseline,
        "intake": {
            "project_purpose": run.intake.project_purpose,
            "audiences": list(run.intake.audiences),
            "provenance": run.intake.provenance,
            "recorded_once": True,
        },
        "skills": [
            {
                "id": skill["id"],
                "package_version": skill["package_version"],
                "hash": skill["hash"],
            }
            for skill in run.skills
        ],
        "coverage": {
            "reused_work_ids": list(run.work["reused"]),
            "completed_work_ids": list(run.work["completed"]),
            "deferred_work_ids": list(run.work["deferred"]),
            "blocked_work_ids": list(run.work["blocked"]),
        },
        "budgets": {
            "semantic_p1_items": run.semantic_budget,
            "maximum_adjustment_loops": run.adjustment_loop_limit,
        },
        "evidence": {
            key: value for key, value in sorted(run.evidence.items()) if value
        },
        "execution_route": {
            "requested_profile": "wiki_update_economy",
            "default_tier": "low-cost",
            "actual_runner_selection_owned_by": "external_host",
            "concrete_selection_recorded_by_core": False,
        },
        "unresolved_findings": run.unresolved_findings,
        "validation": {
            "verification": verification,
            "site_export_ok": bool(export_report.get("ok", True)),
            "site_check_ok": bool(site_check.get("ok")),
            "built_site_check_ok": built_site_check_ok,
            "builder_status": builder_evidence.get("status"),
            "current_publish_ready": current_publish_ready,
            "knowledge_projection": {
                "mode": run.publication.get("knowledge_mode", "off"),
                "export_source_knowledge_hash": export_projection_hash,
                "check_source_knowledge_hash": check_projection_hash,
                "source_knowledge_hashes_match": (
                    export_projection_hash == check_projection_hash
                ),
                "freshness": export_projection_freshness,
                "check_freshness": check_projection_freshness,
                "freshness_disclosures_match": (
                    export_projection_freshness == check_projection_freshness
                ),
                "freshness_scope": "snapshot-only",
                "canonical_body_media_review": "separate-required",
            },
        },
        "limitations": list(dict.fromkeys(run.verdict_limitations)),
        "distribution": {
            **run.publication,
            "canonical_wiki": "wiki",
            "derived_mirror": "site",
            "built_site": "_site" if built_site_check_ok else None,
            "remote_deployment_performed": False,
        },
        "deployment_handoff": {
            "kind": "local_only",
            "instructions": (
                "Review the final report and publish the `_site` directory with a "
                "separately authorized deployment workflow."
                if built_site_check_ok
                else "Install/select a trusted builder, rerun `llm-wiki docs export --build`, then review `_site`."
            ),
        },
        "resume": {
            "status_command": "llm-wiki docs status --workspace <workspace> --format json",
            "verify_command": "llm-wiki docs verify --workspace <workspace> --format json",
        },
        "generated_at": _utc_now(),
    }


def _render_final_report(report: Mapping[str, Any]) -> str:
    source = report.get("source", {})
    distribution = report.get("distribution", {})
    coverage = report.get("coverage", {})
    limitations = list(report.get("limitations", []))
    validation = report.get("validation", {})
    projection = (
        validation.get("knowledge_projection")
        if isinstance(validation, Mapping)
        else None
    )
    native_freshness = (
        projection.get("freshness")
        if isinstance(projection, Mapping) and projection.get("mode") != "off"
        else None
    )
    lines = [
        "# Documentation Run Final Report",
        "",
        f"- Run: `{report.get('run_id', '')}`",
        f"- Verdict: `{report.get('verdict', '')}`",
        f"- State: `{report.get('state', '')}`",
        f"- Source available: `{str(source.get('available', False)).lower()}`",
        f"- Source verified: `{str(source.get('source_verified', False)).lower()}`",
        f"- Distribution: `{distribution.get('format', '')}` / `{distribution.get('link_mode', '')}`",
        "- Remote deployment performed: `false`",
    ]
    if isinstance(native_freshness, str):
        lines.append(f"- Freshness: {native_freshness}")
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- Reused: {len(coverage.get('reused_work_ids', []))}",
            f"- Completed: {len(coverage.get('completed_work_ids', []))}",
            f"- Deferred: {len(coverage.get('deferred_work_ids', []))}",
            f"- Blocked: {len(coverage.get('blocked_work_ids', []))}",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend(f"- `{limitation}`" for limitation in limitations)
    if not limitations:
        lines.append("- None recorded.")
    lines.extend(
        [
            "",
            "## Deployment handoff",
            "",
            str(report.get("deployment_handoff", {}).get("instructions", "")),
            "",
        ]
    )
    return "\n".join(lines)


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
    '_run_authorized_builder',
    '_read_builder_output_tail',
    '_remove_built_site_before_builder',
    '_build_final_report',
    '_render_final_report',
    'export_documentation_run',
)
