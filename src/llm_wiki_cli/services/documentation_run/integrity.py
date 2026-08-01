"""Documentation-run integrity services."""

from __future__ import annotations

from .dependencies import *
from .contracts import *
from .schema import *
from .workspace import *

def capture_generated_ownership(wiki_root: str | Path) -> dict[str, str]:
    """Fingerprint CLI-owned JSON files and generated Markdown sections."""

    root = Path(wiki_root).expanduser().resolve()
    fingerprints: dict[str, str] = {}
    for name in (
        ".llm-wiki-manifest.json",
        ".llm-wiki-surface.json",
        KNOWLEDGE_INDEX_FILENAME,
        GOVERNANCE_FILENAME,
        VERIFICATION_RECEIPT_FILENAME,
    ):
        path = root / name
        if path.is_symlink():
            raise DocumentationIntegrityError(
                f"Native ownership inventory rejects symlinked content: {path}"
            )
        if path.is_file():
            fingerprints[name] = hash_bytes(path.read_bytes())
    for path in sorted(root.rglob("*.md")):
        if path.is_symlink() or not path.is_file():
            raise DocumentationIntegrityError(
                f"Wiki ownership inventory rejects non-regular content: {path}"
            )
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        for section_id, section in _generated_sections(text):
            fingerprints[f"{rel}#{section_id}"] = hash_bytes(section.encode("utf-8"))
    return fingerprints


def compare_generated_ownership(
    baseline: Mapping[str, str], wiki_root: str | Path
) -> dict[str, list[str]]:
    current = capture_generated_ownership(wiki_root)
    before = dict(baseline)
    return {
        "added": sorted(set(current) - set(before)),
        "removed": sorted(set(before) - set(current)),
        "changed": sorted(
            key for key in set(before) & set(current) if before[key] != current[key]
        ),
    }


def _export_documentation_skills(workspace_root: Path) -> list[dict[str, Any]]:
    bundled = {skill.skill_id: skill for skill in list_bundled_skills()}
    missing = [
        skill_id for skill_id in DEFAULT_DOCUMENTATION_SKILLS if skill_id not in bundled
    ]
    if missing:
        raise DocumentationRunError(
            f"Required bundled documentation skill is missing: {missing[0]}"
        )
    destination = workspace_root / RUN_CONTROL_DIR / "skills"
    report = export_skills(
        destination,
        skills=list(DEFAULT_DOCUMENTATION_SKILLS),
        force=True,
    )
    if not report.ok:
        raise DocumentationRunError(
            f"Could not export documentation skills: {report.issues}"
        )
    result = []
    for skill_id in DEFAULT_DOCUMENTATION_SKILLS:
        skill = bundled[skill_id]
        expected_hash = _hash_skill_tree(
            (
                relative,
                read_md(skill.path / relative).encode("utf-8"),
            )
            for relative in skill.files
        )
        relative_path = f"{RUN_CONTROL_DIR}/skills/{skill_id}"
        actual_hash = _hash_exported_skill(workspace_root, relative_path)
        if actual_hash != expected_hash:
            raise DocumentationRunError(
                "Exported documentation skill differs from its canonical "
                f"bundled content: {skill_id}"
            )
        result.append(
            {
                "id": skill_id,
                "package_version": __version__,
                "hash": actual_hash,
                "path": relative_path,
            }
        )
    return result


def _initial_readiness_ledger(
    run_id: str, worklist: Mapping[str, Any]
) -> dict[str, Any]:
    items = [item for item in worklist.get("items", []) if isinstance(item, dict)]
    return {
        "schema_version": DOCUMENTATION_SEMANTIC_READINESS_SCHEMA_VERSION,
        "run_id": run_id,
        "status": "pending_agent_reconciliation",
        "passed": False,
        "p0": {
            "required": [item["id"] for item in items if item.get("priority") == "P0"],
            "reused": [],
            "completed": [],
            "deferred": [],
        },
        "p1": {
            "budget": int(worklist.get("policy", {}).get("p1_budget", 0)),
            "selected": [
                item["id"]
                for item in items
                if item.get("priority") == "P1" and not item.get("deferred")
            ],
            "reused": [],
            "completed": [],
            "deferred": [],
        },
        "unsupported_coverage": [],
        "generator_defects": [],
        "imported_page_accounting": {},
        "imported_page_edits": [],
        "claims_evidence_pages": [],
        "evidence_by_work": {},
        "deferral_rationales": {},
        "updated_at": _utc_now(),
    }


def _capture_control_integrity_snapshot(
    workspace_root: Path,
    run: DocumentationRun,
) -> dict[str, Any]:
    """Hash immutable supervisor-owned inputs used by a stage packet.

    This is a defense-in-depth receipt, not a boundary against an actor that can
    replace every control artifact and its receipt. Hosts must still keep the
    control directory outside worker write permissions.
    """

    artifact_paths: dict[str, str] = {
        "runtime_policy": f"{RUN_CONTROL_DIR}/{POLICY_FILENAME}",
        "baseline_stage": f"{RUN_CONTROL_DIR}/stages/01-baseline.json",
    }
    for key in _CONTROL_SNAPSHOT_EVIDENCE_KEYS:
        relative = run.evidence.get(key, "")
        if relative:
            artifact_paths[f"evidence.{key}"] = relative

    artifacts: dict[str, dict[str, str]] = {}
    for label, relative in sorted(artifact_paths.items()):
        path = _workspace_path(workspace_root, relative)
        if not path.is_file() or path.is_symlink():
            raise DocumentationIntegrityError(
                f"Required supervisor control artifact is not a regular file: {relative}"
            )
        artifacts[label] = {
            "path": relative,
            "hash": hash_bytes(path.read_bytes()),
        }

    skill_trees: dict[str, dict[str, str]] = {}
    for raw in run.skills:
        skill_id = str(raw["id"])
        relative = str(raw["path"])
        actual_hash = _hash_exported_skill(workspace_root, relative)
        expected_hash = str(raw["hash"])
        if actual_hash != expected_hash:
            raise DocumentationIntegrityError(
                f"Exported documentation skill changed before dispatch: {skill_id}"
            )
        skill_trees[skill_id] = {
            "path": relative,
            "hash": actual_hash,
        }
    return {
        "schema_version": "llm-wiki-documentation-control-snapshot/v1",
        "artifacts": artifacts,
        "skills": skill_trees,
    }


def _verify_stage_dispatch_integrity(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    stage: str,
    attempt: int,
) -> None:
    """Reconcile a stage result with the exact supervisor dispatch receipt."""

    expected_before = f"{RUN_CONTROL_DIR}/evidence/{stage}-{attempt:02d}-before.json"
    expected_packet = f"{RUN_CONTROL_DIR}/packets/{stage}-{attempt:02d}.json"
    if run.evidence.get(f"{stage}_before") != expected_before:
        raise DocumentationIntegrityError(
            "Run state no longer references the canonical pre-stage evidence."
        )
    if run.evidence.get(f"{stage}_packet") != expected_packet:
        raise DocumentationIntegrityError(
            "Run state no longer references the canonical stage packet."
        )

    before_path = _workspace_path(workspace_root, expected_before)
    packet_path = _workspace_path(workspace_root, expected_packet)
    event_path = _stage_event_path(
        workspace_root,
        stage,
        attempt=attempt,
        event="packet",
    )
    for artifact in (before_path, packet_path, event_path):
        if not artifact.is_file() or artifact.is_symlink():
            raise DocumentationIntegrityError(
                f"Stage dispatch evidence is missing or redirected: {artifact.name}"
            )

    event = _read_json(event_path)
    _require_exact_fields(
        event,
        allowed={
            "schema_version",
            "run_id",
            "stage",
            "attempt",
            "status",
            "packet",
            "packet_hash",
            "pre_stage_evidence",
            "pre_stage_evidence_hash",
            "control_snapshot_hash",
            "run_hash",
            "recorded_at",
        },
        required={
            "schema_version",
            "run_id",
            "stage",
            "attempt",
            "status",
            "packet",
            "packet_hash",
            "pre_stage_evidence",
            "pre_stage_evidence_hash",
            "control_snapshot_hash",
            "run_hash",
            "recorded_at",
        },
        label="stage dispatch receipt",
    )
    expected_event_values = {
        "schema_version": DOCUMENTATION_RUN_SCHEMA_VERSION,
        "run_id": run.run_id,
        "stage": stage,
        "attempt": attempt,
        "status": "packet_ready",
        "packet": expected_packet,
        "pre_stage_evidence": expected_before,
    }
    for key, expected in expected_event_values.items():
        if event.get(key) != expected:
            raise DocumentationIntegrityError(
                f"Stage dispatch receipt field {key!r} was changed."
            )
    if event.get("packet_hash") != hash_bytes(packet_path.read_bytes()):
        raise DocumentationIntegrityError(
            "Stage packet bytes no longer match its receipt."
        )
    if event.get("pre_stage_evidence_hash") != hash_bytes(before_path.read_bytes()):
        raise DocumentationIntegrityError(
            "Pre-stage evidence bytes no longer match the dispatch receipt."
        )
    run_path = _workspace_path(workspace_root, f"{RUN_CONTROL_DIR}/{RUN_FILENAME}")
    if event.get("run_hash") != hash_bytes(run_path.read_bytes()):
        raise DocumentationIntegrityError(
            "Run control state changed after the stage packet was dispatched."
        )

    before = _read_json(before_path)
    _require_exact_fields(
        before,
        allowed={
            "tree",
            "generated_ownership",
            "control_snapshot",
            "control_snapshot_hash",
            "captured_at",
        },
        required={
            "tree",
            "generated_ownership",
            "control_snapshot",
            "control_snapshot_hash",
            "captured_at",
        },
        label="pre-stage evidence",
    )
    snapshot = before.get("control_snapshot")
    if not isinstance(snapshot, Mapping):
        raise DocumentationIntegrityError("Pre-stage control snapshot is malformed.")
    snapshot_payload = dict(snapshot)
    snapshot_hash = _sha256_json(snapshot_payload)
    if (
        before.get("control_snapshot_hash") != snapshot_hash
        or event.get("control_snapshot_hash") != snapshot_hash
    ):
        raise DocumentationIntegrityError(
            "Pre-stage control snapshot hash no longer matches its receipts."
        )
    current_snapshot = _capture_control_integrity_snapshot(workspace_root, run)
    if current_snapshot != snapshot_payload:
        raise DocumentationIntegrityError(
            "Supervisor-owned control artifacts changed after packet dispatch."
        )

    packet = _read_json(packet_path)
    if (
        packet.get("schema_version") != DOCUMENTATION_AGENT_PACKET_SCHEMA_VERSION
        or packet.get("run_id") != run.run_id
        or packet.get("stage") != stage
    ):
        raise DocumentationIntegrityError(
            "Stage packet identity no longer matches the active run."
        )
    supervisor_integrity = packet.get("supervisor_integrity")
    if not isinstance(supervisor_integrity, Mapping) or dict(supervisor_integrity) != {
        "pre_stage_evidence": expected_before,
        "pre_stage_evidence_hash": event["pre_stage_evidence_hash"],
        "control_snapshot_hash": snapshot_hash,
    }:
        raise DocumentationIntegrityError(
            "Stage packet supervisor-integrity projection was changed."
        )
    _assert_no_forbidden_packet_fields(packet, label="persisted agent packet")


def _hash_exported_skill(workspace_root: Path, relative: str) -> str:
    root = _workspace_path(workspace_root, relative)
    if not root.is_dir() or root.is_symlink():
        raise DocumentationIntegrityError(
            f"Exported documentation skill is not a regular directory: {relative}"
        )
    descendants = list(root.rglob("*"))
    for path in descendants:
        if path.is_symlink():
            raise DocumentationIntegrityError(
                f"Exported documentation skill contains a link: {relative}"
            )
    files = [path for path in descendants if path.is_file()]
    if not files:
        raise DocumentationIntegrityError(
            f"Exported documentation skill contains no files: {relative}"
        )
    return _hash_skill_tree(
        (path.relative_to(root).as_posix(), path.read_bytes()) for path in files
    )


def _hash_skill_tree(entries: Iterable[tuple[str, bytes]]) -> str:
    """Hash a skill tree by case-sensitive POSIX relative-name order."""
    digest = hashlib.sha256()
    for relative, content in sorted(entries, key=lambda entry: entry[0]):
        if "\0" in relative or b"\0" in content:
            raise DocumentationIntegrityError(
                "Documentation skill paths and content must not contain NUL bytes."
            )
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _assert_packet_stage(run: DocumentationRun, stage: str) -> None:
    allowed_states = {
        "wiki-enrichment": {"baseline_ready", "wiki_enrichment"},
        "user-docs": {"user_docs"},
        "review": {"review"},
    }
    effective_state = run.resume_state if run.state == "blocked" else run.state
    if effective_state not in allowed_states[stage]:
        raise DocumentationTransitionError(
            f"Stage {stage!r} cannot start from run state {run.state!r}."
        )
    if stage == "user-docs":
        readiness_path = run.evidence.get("semantic_readiness")
        if not readiness_path:
            raise DocumentationTransitionError(
                "User-docs stage requires a semantic readiness ledger."
            )


def _stage_contract(stage: str) -> dict[str, Any]:
    return {
        "wiki-enrichment": {
            "objective": (
                "Ground, preserve, or improve the canonical wiki's agent-owned semantic "
                "surfaces while accounting for every required and imported work item."
            ),
            "definition_of_done": [
                "Every P0 item is completed, reused, or evidence-backed deferred.",
                "The configured P1 budget is completed, reused, or explicitly deferred.",
                "Every imported semantic page is accounted for without style-only rewriting.",
                "Generator defects and unsupported evidence remain explicit.",
                "No source, input-wiki, or generated-owner content changes.",
            ],
            "skills": ["wiki-semantic-enhance"],
            "allowed_writes": [
                "wiki agent-owned semantic prose",
                "wiki/bootstrap-remainder.md",
                f"{RUN_CONTROL_DIR}/results/wiki-enrichment.json",
            ],
        },
        "user-docs": {
            "objective": (
                "Author evidence-linked human documentation for the recorded audiences "
                "from the semantically ready canonical wiki."
            ),
            "definition_of_done": [
                "The canonical wiki contains a grounded overview and at least one audience guide.",
                "Primary factual sections link to canonical wiki evidence.",
                "Unverified imported claims are excluded or visibly deferred.",
                "Usage capture is performed only when separately authorized and safe.",
                "Derived site output is not hand-edited.",
            ],
            "skills": [
                "user-docs-author",
                "onboarding-guide",
                "usage-examples",
                "publish-docs",
            ],
            "allowed_writes": [
                "wiki/index.md agent-owned prose",
                "wiki/guides/**",
                "wiki/deferred-docs.md",
                f"{RUN_CONTROL_DIR}/results/user-docs.json",
            ],
        },
        "review": {
            "objective": (
                "Independently reconcile important user-facing claims, deterministic "
                "findings, and filesystem ownership before publication handoff."
            ),
            "definition_of_done": [
                "Important claims are sampled against available evidence.",
                "Every finding has a stable status and evidence-backed rationale.",
                "No unresolved high-severity correctness or safety finding remains.",
                "Source, input-wiki, and generated ownership are intact.",
            ],
            "skills": ["doc-review"],
            "allowed_writes": [
                f"{RUN_CONTROL_DIR}/results/review.json",
            ],
        },
    }[stage]


def _verify_initial_integrity_anchors(
    workspace_root: Path,
    run: DocumentationRun,
) -> None:
    """Bind mutable baseline files to hashes persisted in the run contract."""

    expected_anchor_keys = {"generated_ownership"}
    if run.source.get("available") is True:
        expected_anchor_keys.add("source_baseline")
    if set(run.integrity_anchors) != expected_anchor_keys:
        raise DocumentationIntegrityError(
            "Documentation run is missing its immutable baseline integrity anchors; "
            "start a new run or perform an explicit refresh."
        )

    for key in sorted(expected_anchor_keys):
        relative = run.evidence.get(key)
        if not relative:
            raise DocumentationIntegrityError(
                f"Documentation run lost required {key} evidence."
            )
        path = _workspace_path(workspace_root, relative)
        if not path.is_file() or path.is_symlink():
            raise DocumentationIntegrityError(
                f"Anchored baseline evidence is missing or redirected: {relative}"
            )
        actual_hash = hash_bytes(path.read_bytes())
        if actual_hash != run.integrity_anchors[key]:
            raise DocumentationIntegrityError(
                f"Anchored {key.replace('_', '-')} evidence changed after prepare."
            )

    if run.source.get("available") is True:
        source_path = _workspace_path(workspace_root, run.evidence["source_baseline"])
        source_payload = _read_json(source_path)
        _require_exact_fields(
            source_payload,
            allowed={
                "root_display",
                "tree_hash",
                "file_count",
                "file_hashes",
                "excluded_directories",
            },
            required={
                "root_display",
                "tree_hash",
                "file_count",
                "file_hashes",
                "excluded_directories",
            },
            label="anchored source baseline",
        )
        file_hashes = source_payload.get("file_hashes")
        file_count = source_payload.get("file_count")
        excluded = source_payload.get("excluded_directories")
        if (
            source_payload.get("root_display") != "source"
            or not isinstance(file_hashes, Mapping)
            or isinstance(file_count, bool)
            or not isinstance(file_count, int)
            or file_count != len(file_hashes)
            or not isinstance(excluded, list)
            or any(not isinstance(value, str) for value in excluded)
            or any(
                not isinstance(path, str)
                or not path
                or not isinstance(digest, str)
                or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
                for path, digest in file_hashes.items()
            )
        ):
            raise DocumentationIntegrityError(
                "Anchored source baseline structure is malformed."
            )
        computed_tree_hash = _tree_hash_from_file_hashes(file_hashes)
        if (
            source_payload.get("tree_hash") != computed_tree_hash
            or run.source.get("content_fingerprint") != computed_tree_hash
        ):
            raise DocumentationIntegrityError(
                "Anchored source baseline no longer matches the run source fingerprint."
            )

    generated_path = _workspace_path(
        workspace_root, run.evidence["generated_ownership"]
    )
    generated_payload = _read_json(generated_path)
    _require_exact_fields(
        generated_payload,
        allowed={"fingerprints"},
        required={"fingerprints"},
        label="anchored generated ownership",
    )
    fingerprints = generated_payload.get("fingerprints")
    if not isinstance(fingerprints, Mapping) or any(
        not isinstance(key, str)
        or not key
        or not isinstance(value, str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", value)
        for key, value in fingerprints.items()
    ):
        raise DocumentationIntegrityError(
            "Anchored generated-ownership fingerprints are malformed."
        )
    generated_difference = compare_generated_ownership(
        {str(key): str(value) for key, value in fingerprints.items()},
        workspace_root / run.paths["wiki"],
    )
    if any(generated_difference.values()):
        raise DocumentationIntegrityError(
            "generated ownership changed before supervisor dispatch or verification: "
            f"{generated_difference}"
        )


def _tree_hash_from_file_hashes(file_hashes: Mapping[str, Any]) -> str:
    digest = hashlib.sha256()
    for path, file_hash in sorted(file_hashes.items()):
        digest.update(str(path).replace("\\", "/").encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(file_hash).encode("ascii"))
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _adopted_input_wiki_tree_hash(input_root: str | Path) -> str:
    """Recompute an adopted input hash through the public importer contract."""

    from ..documentation_wiki_input import (
        DocumentationWikiInputError,
        fingerprint_documentation_wiki_input,
    )

    try:
        return fingerprint_documentation_wiki_input(input_root)
    except DocumentationWikiInputError as exc:
        raise DocumentationIntegrityError(
            f"Read-only adopted input wiki failed secure inventory: {exc}"
        ) from exc


def _verify_read_only_inputs(
    workspace_root: Path, run: DocumentationRun
) -> list[dict[str, Any]]:
    runtime_paths = _load_bound_runtime_policy(workspace_root, run)
    _verify_initial_integrity_anchors(workspace_root, run)
    checks: list[dict[str, Any]] = []
    source_evidence = run.evidence.get("source_baseline")
    source_root = runtime_paths.get("source_root")
    if run.source.get("available") and (not source_evidence or source_root is None):
        raise DocumentationIntegrityError(
            "Source-backed run lost its required source root or baseline evidence."
        )
    if source_evidence and source_root is not None:
        if not source_root.exists():
            checks.append(
                {
                    "check": "source_integrity",
                    "ok": True,
                    "limited": True,
                    "availability": "source_unavailable",
                }
            )
        else:
            if not source_root.is_dir():
                raise DocumentationIntegrityError(
                    "Bound read-only source root is no longer a directory."
                )
            baseline = TreeBaseline.from_dict(
                _read_json(_workspace_path(workspace_root, source_evidence))
            )
            difference = compare_tree_baseline(baseline, source_root)
            checks.append({"check": "source_integrity", **difference.to_dict()})
            if not difference.ok:
                raise DocumentationIntegrityError(
                    f"Read-only source integrity changed: {difference.to_dict()}"
                )
    input_root = runtime_paths.get("input_wiki_root")
    input_info = run.baseline.get("input_wiki")
    if isinstance(input_info, dict) and input_root is None:
        raise DocumentationIntegrityError(
            "Existing-wiki run lost its required read-only input-wiki root."
        )
    if input_root is not None and isinstance(input_info, dict):
        current_tree_hash = _adopted_input_wiki_tree_hash(input_root)
        expected = input_info.get("input_tree_hash")
        ok = current_tree_hash == expected
        checks.append(
            {
                "check": "input_wiki_integrity",
                "ok": ok,
                "expected_tree_hash": expected,
                "actual_tree_hash": current_tree_hash,
            }
        )
        if not ok:
            raise DocumentationIntegrityError(
                "Read-only adopted input wiki changed after prepare."
            )
    return checks


def _run_wiki_validation_pair(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    phase: str,
) -> bool:
    """Run lifecycle-owned lint and strict CI checks without loading plugins."""

    runtime_paths = _load_bound_runtime_policy(workspace_root, run)
    source_root = runtime_paths.get("source_root")
    helper_cache_root = runtime_paths.get("helper_cache_root")
    wiki_root = workspace_root / run.paths["wiki"]
    results: dict[str, dict[str, Any]] = {}

    source_is_current = run.baseline.get("freshness") == "verified_current"
    source_is_available = source_root is not None and source_root.is_dir()
    if source_root is not None and source_is_available and source_is_current:
        from ..lint_service import build_report, report_to_dict
        from ..inventory_cache import InventoryCacheOptions

        for name, strict in (("lint", False), ("ci-check", True)):
            try:
                report = build_report(
                    wiki_root,
                    str(source_root),
                    strict=strict,
                    cache_options=InventoryCacheOptions(enabled=False),
                    parallel_jobs=1,
                    helper_cache_dir=(
                        str(helper_cache_root) if helper_cache_root else None
                    ),
                    include_plugins=run.policy.get("source_plugins_trusted", False),
                )
                report_payload = report_to_dict(report, include_execution=True)
                report_payload["wiki_dir"] = "wiki"
                report_payload["src_dir"] = "source"
                results[name] = {
                    "schema_version": "llm-wiki-documentation-check/v1",
                    "run_id": run.run_id,
                    "checker": name,
                    "phase": phase,
                    "status": "passed" if report.passed else "failed",
                    "ok": report.passed,
                    "limited": False,
                    "report": report_payload,
                    "checked_at": _utc_now(),
                }
            except Exception as exc:
                results[name] = {
                    "schema_version": "llm-wiki-documentation-check/v1",
                    "run_id": run.run_id,
                    "checker": name,
                    "phase": phase,
                    "status": "error",
                    "ok": False,
                    "limited": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "checked_at": _utc_now(),
                }
    else:
        issues = _wiki_only_structural_issues(wiki_root)
        limitation = (
            "source_unavailable; source coverage was not checked"
            if not source_is_available
            else "source_not_verified_current; source coverage was not checked"
        )
        for name in ("lint", "ci-check"):
            results[name] = {
                "schema_version": "llm-wiki-documentation-check/v1",
                "run_id": run.run_id,
                "checker": name,
                "phase": phase,
                "status": "passed_limited" if not issues else "failed",
                "ok": not issues,
                "limited": True,
                "limitation": limitation,
                "report": {
                    "wiki_dir": "wiki",
                    "src_dir": (
                        "source_unavailable"
                        if not source_is_available
                        else "source_not_verified_current"
                    ),
                    "strict": name == "ci-check",
                    "knowledge_drift_gate": False,
                    "knowledge_drift_report": False,
                    "ok": not issues,
                    "issue_count": len(issues),
                    "issues": issues,
                    "diagnostics": [],
                },
                "checked_at": _utc_now(),
            }

    phase_slug = re.sub(r"[^a-z0-9-]+", "-", phase.lower()).strip("-")
    for name, result in results.items():
        canonical_name = "ci-check.json" if name == "ci-check" else "lint.json"
        phase_name = f"{phase_slug}-{canonical_name}"
        phase_path = workspace_root / RUN_CONTROL_DIR / "evidence" / phase_name
        canonical_path = workspace_root / RUN_CONTROL_DIR / "evidence" / canonical_name
        _write_json(phase_path, result)
        _write_json(canonical_path, result)
        evidence_key = "ci_check" if name == "ci-check" else "lint"
        run.evidence[evidence_key] = canonical_path.relative_to(
            workspace_root
        ).as_posix()
        run.evidence[f"{phase_slug}_{evidence_key}"] = phase_path.relative_to(
            workspace_root
        ).as_posix()
        run.validation_results.append(
            {
                "check": name,
                "ok": bool(result["ok"]),
                "status": result["status"],
                "phase": phase,
                "evidence": phase_path.relative_to(workspace_root).as_posix(),
            }
        )
    passed = all(bool(result.get("ok")) for result in results.values())
    if passed:
        blocking_messages = {
            "Deterministic baseline lint/CI validation did not pass.",
            "Post-enrichment lint/CI validation did not pass.",
        }
        run.unresolved_findings = [
            finding
            for finding in run.unresolved_findings
            if str(finding.get("message")) not in blocking_messages
        ]
    save_documentation_run(workspace_root, run)
    return passed


def _wiki_only_structural_issues(wiki_root: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    index = wiki_root / "index.md"
    if not index.is_file() or index.is_symlink():
        issues.append(
            {
                "category": "required_structure",
                "severity": "error",
                "path": "index.md",
                "target": None,
                "message": "Wiki-only validation requires a regular index.md.",
            }
        )
    for page in sorted(wiki_root.rglob("*.md")):
        if not page.is_file() or page.is_symlink():
            continue
        relative_page = page.relative_to(wiki_root).as_posix()
        content = page.read_text(encoding="utf-8")
        for link in iter_markdown_link_targets(strip_fenced_code_blocks(content)):
            local = local_link_path(link.raw_target)
            if local is None:
                continue
            candidate = (page.parent / local).resolve()
            try:
                candidate.relative_to(wiki_root.resolve())
            except ValueError:
                issues.append(
                    {
                        "category": "unsafe_link",
                        "severity": "error",
                        "path": relative_page,
                        "target": local,
                        "message": "Local Markdown link escapes the wiki root.",
                    }
                )
                continue
            if not candidate.exists():
                issues.append(
                    {
                        "category": "broken_link",
                        "severity": "error",
                        "path": relative_page,
                        "target": local,
                        "message": "Local Markdown link target does not exist.",
                    }
                )
    return issues


def _changed_paths(before: TreeBaseline, after: TreeBaseline) -> list[str]:
    before_paths = before.file_hashes
    after_paths = after.file_hashes
    return sorted(
        set(before_paths) ^ set(after_paths)
        | {
            path
            for path in set(before_paths) & set(after_paths)
            if before_paths[path] != after_paths[path]
        }
    )


def _validate_stage_changed_paths(
    stage: str,
    changed_paths: Iterable[str],
    *,
    current_tree: TreeBaseline,
    worklist: Mapping[str, Any],
    runtime_capture_paths: Iterable[str] = (),
) -> None:
    """Enforce the machine-readable wiki write boundary for one agent stage."""

    changed = set(changed_paths)
    capture_paths = set(runtime_capture_paths)
    removed = sorted(changed - set(current_tree.file_hashes))
    if removed:
        raise DocumentationIntegrityError(
            "Agent stages must not delete canonical wiki files: " + removed[0]
        )

    if stage == "review":
        forbidden = sorted(changed)
    elif stage == "user-docs":
        forbidden = sorted(
            path
            for path in changed
            if not (
                path in {"index.md", "deferred-docs.md"}
                or (path.startswith("guides/") and path.casefold().endswith(".md"))
                or (
                    path in capture_paths
                    and _is_supported_runtime_capture_asset(path)
                )
            )
        )
    elif stage == "wiki-enrichment":
        assigned_paths = {
            str(item.get("canonical_path"))
            for item in worklist.get("items", [])
            if isinstance(item, Mapping) and isinstance(item.get("canonical_path"), str)
        }
        assigned_paths.add("bootstrap-remainder.md")
        forbidden = sorted(
            path
            for path in changed
            if not path.casefold().endswith(".md") or path not in assigned_paths
        )
    else:  # defensive: result parsing already rejects unknown stages
        raise DocumentationIntegrityError(
            f"No wiki write contract exists for agent stage {stage!r}."
        )

    if forbidden:
        raise DocumentationIntegrityError(
            f"Stage {stage!r} changed a wiki path outside its write allowlist: "
            f"{forbidden[0]}"
        )


def _is_supported_runtime_capture_asset(path: str) -> bool:
    candidate = PurePosixPath(path)
    return (
        len(candidate.parts) >= 3
        and candidate.parts[0] == "assets"
        and candidate.suffix.casefold()
        in {
            ".gif",
            ".jpeg",
            ".jpg",
            ".json",
            ".log",
            ".md",
            ".mp4",
            ".png",
            ".svg",
            ".txt",
            ".webm",
            ".webp",
        }
    )


def _block_run_for_integrity(
    workspace_root: Path,
    run: DocumentationRun,
    message: str,
    *,
    integrity: bool = True,
) -> None:
    finding_id = "DOC-" + hashlib.sha256(message.encode("utf-8")).hexdigest()[:12]
    if not any(item.get("id") == finding_id for item in run.unresolved_findings):
        run.unresolved_findings.append(
            {
                "id": finding_id,
                "severity": "high" if integrity else "medium",
                "source": "integrity" if integrity else "agent_result",
                "status": "open",
                "message": message,
                "evidence": [],
            }
        )
    if run.state != "blocked":
        transition_documentation_run(run, "blocked", resume_state=run.state)
    save_documentation_run(workspace_root, run)


def _generated_sections(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines(keepends=True)
    sections: list[tuple[str, str]] = []
    starts = [index for index, line in enumerate(lines) if line.startswith("## ")]
    if not starts:
        if _GENERATED_MARKER in text and _DO_NOT_EDIT_MARKER in text:
            return [("document", text)]
        return []
    starts.append(len(lines))
    for position, start in enumerate(starts[:-1]):
        end = starts[position + 1]
        section = "".join(lines[start:end])
        if _GENERATED_MARKER not in section or _DO_NOT_EDIT_MARKER not in section:
            continue
        heading = lines[start][3:].strip().lower()
        section_id = re.sub(r"[^a-z0-9]+", "-", heading).strip("-") or str(position)
        sections.append((section_id, section))
    return sections

__all__ = (
    'capture_generated_ownership',
    'compare_generated_ownership',
    '_export_documentation_skills',
    '_initial_readiness_ledger',
    '_capture_control_integrity_snapshot',
    '_verify_stage_dispatch_integrity',
    '_hash_exported_skill',
    '_hash_skill_tree',
    '_assert_packet_stage',
    '_stage_contract',
    '_verify_initial_integrity_anchors',
    '_tree_hash_from_file_hashes',
    '_adopted_input_wiki_tree_hash',
    '_verify_read_only_inputs',
    '_run_wiki_validation_pair',
    '_wiki_only_structural_issues',
    '_changed_paths',
    '_validate_stage_changed_paths',
    '_is_supported_runtime_capture_asset',
    '_block_run_for_integrity',
    '_generated_sections',
)
