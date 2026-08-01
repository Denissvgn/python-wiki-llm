"""Documentation-run record services."""

from __future__ import annotations

from .dependencies import *
from .contracts import *
from .schema import *
from .workspace import *
from .integrity import *
from .refresh import *

def _validate_result_work_ids(
    result: DocumentationAgentResult,
    worklist: Mapping[str, Any],
    *,
    stage: str,
    wiki_root: Path,
) -> None:
    known_items = {
        str(item.get("id")): item
        for item in worklist.get("items", [])
        if isinstance(item, dict) and item.get("id")
    }
    known = set(known_items)
    groups = {
        "reused": set(result.reused_work_ids),
        "completed": set(result.completed_work_ids),
        "deferred": set(result.deferred_work_ids),
    }
    unknown = set().union(*groups.values()) - known
    if unknown:
        raise DocumentationSchemaError(
            f"Agent result contains unknown work id: {sorted(unknown)[0]}"
        )
    if any(
        groups[left] & groups[right]
        for left, right in (
            ("reused", "completed"),
            ("reused", "deferred"),
            ("completed", "deferred"),
        )
    ):
        raise DocumentationSchemaError(
            "A work id cannot be reused, completed, and deferred in the same result."
        )
    if stage != "wiki-enrichment" and groups["reused"]:
        raise DocumentationSchemaError(
            "Only the wiki-enrichment result may classify imported work as reused."
        )
    rationale_ids = set(result.deferral_rationales)
    if rationale_ids != groups["deferred"]:
        missing_rationales = sorted(groups["deferred"] - rationale_ids)
        extra_rationales = sorted(rationale_ids - groups["deferred"])
        detail = f"missing={missing_rationales!r} extra={extra_rationales!r}"
        raise DocumentationSchemaError(
            "Every deferred work id requires exactly one evidence-backed rationale: "
            + detail
        )
    for path in result.claims_evidence_pages:
        if not path.casefold().endswith(".md"):
            raise DocumentationSchemaError(
                "Agent result claims_evidence_pages must identify canonical "
                f"Markdown wiki pages: {path}"
            )
        evidence_path = _workspace_path(wiki_root, path)
        if not evidence_path.is_file() or evidence_path.is_symlink():
            raise DocumentationSchemaError(
                f"Agent result evidence page does not exist as a regular wiki file: {path}"
            )
    if stage == "wiki-enrichment":
        evidence_pages = set(result.claims_evidence_pages)
        for work_id in sorted(groups["reused"] | groups["completed"]):
            item = known_items[work_id]
            canonical_path = item.get("canonical_path")
            if (
                not isinstance(canonical_path, str)
                or canonical_path not in evidence_pages
            ):
                raise DocumentationSchemaError(
                    "Completed/reused wiki work must cite its canonical page in "
                    f"claims_evidence_pages: {work_id}"
                )
        for work_id in sorted(groups["reused"]):
            item = known_items[work_id]
            if (
                item.get("imported_classification") != "candidate_reuse"
                or item.get("grounding_status") != "grounded"
                or item.get("reuse_eligible") is not True
            ):
                raise DocumentationSchemaError(
                    "Only grounded, reuse-eligible candidate_reuse items may be "
                    f"reported as reused: {work_id}"
                )


def _reconcile_imported_page_edits(
    result: DocumentationAgentResult,
    worklist: Mapping[str, Any],
    *,
    actual_changed: Iterable[str],
    before_tree: TreeBaseline,
    after_tree: TreeBaseline,
    wiki_root: Path,
) -> list[dict[str, Any]]:
    imported_by_path: dict[str, dict[str, Any]] = {}
    imported_by_id: dict[str, dict[str, Any]] = {}
    for raw in worklist.get("items", []):
        if not isinstance(raw, dict) or raw.get("imported_classification") is None:
            continue
        work_id = str(raw.get("id", ""))
        canonical = raw.get("canonical_path")
        if not work_id or not isinstance(canonical, str):
            raise DocumentationIntegrityError(
                "Imported semantic worklist entries require a work id and canonical path."
            )
        canonical = _portable_path(
            canonical, field_name="imported semantic worklist canonical_path"
        )
        if canonical in imported_by_path or work_id in imported_by_id:
            raise DocumentationIntegrityError(
                "Imported semantic worklist entries must have unique ids and paths."
            )
        imported_by_path[canonical] = raw
        imported_by_id[work_id] = raw

    changed_imported_paths = set(actual_changed) & set(imported_by_path)
    reported_paths = {
        str(edit["canonical_path"]) for edit in result.imported_page_edits
    }
    if reported_paths != changed_imported_paths:
        raise DocumentationIntegrityError(
            "Imported-page edit evidence does not match independently derived "
            "imported semantic changes: "
            f"reported={sorted(reported_paths)} actual={sorted(changed_imported_paths)}"
        )

    reconciled: list[dict[str, Any]] = []
    for edit in result.imported_page_edits:
        work_id = str(edit["work_id"])
        canonical = str(edit["canonical_path"])
        item = imported_by_id.get(work_id)
        if item is None or str(item.get("canonical_path")) != canonical:
            raise DocumentationIntegrityError(
                "Imported-page edit work_id and canonical_path do not identify the "
                f"same imported worklist item: {work_id!r} / {canonical!r}"
            )
        expected_before = before_tree.file_hashes.get(canonical)
        expected_after = after_tree.file_hashes.get(canonical)
        if expected_before is None or expected_after is None:
            raise DocumentationIntegrityError(
                "Changed imported semantic pages must remain regular files in both "
                f"the pre-stage and post-stage tree: {canonical}"
            )
        if (
            edit["before_hash"] != expected_before
            or edit["after_hash"] != expected_after
        ):
            raise DocumentationIntegrityError(
                "Imported-page edit hashes do not match the supervisor baselines: "
                f"{canonical}"
            )
        for evidence in edit["evidence"]:
            evidence_path = _workspace_path(wiki_root, str(evidence))
            if not evidence_path.is_file() or evidence_path.is_symlink():
                raise DocumentationSchemaError(
                    "Imported-page edit evidence must identify a regular wiki page: "
                    f"{evidence}"
                )
        reconciled.append(
            {
                **dict(edit),
                "worklist_classification": item.get("imported_classification"),
                "verified": True,
            }
        )
    return sorted(reconciled, key=lambda item: str(item["canonical_path"]))


def _reconcile_semantic_readiness(
    workspace_root: Path,
    run: DocumentationRun,
    result: DocumentationAgentResult,
    worklist: Mapping[str, Any],
) -> dict[str, Any]:
    items = [item for item in worklist.get("items", []) if isinstance(item, dict)]
    reused = set(result.reused_work_ids)
    completed = set(result.completed_work_ids)
    deferred = set(result.deferred_work_ids)
    accounted = reused | completed | deferred
    p0 = {str(item["id"]) for item in items if item.get("priority") == "P0"}
    p1 = {
        str(item["id"])
        for item in items
        if item.get("priority") == "P1" and not item.get("deferred")
    }
    imported = {
        str(item["id"])
        for item in items
        if item.get("imported_classification") is not None
    }
    missing = sorted((p0 | p1 | imported) - accounted)
    deferred_p0 = sorted(p0 & deferred)
    deferred_p1 = sorted(p1 & deferred)
    passed = result.status == "complete" and not missing and not deferred_p1
    items_by_work = {str(item["id"]): item for item in items}
    imported_edits_by_work = {
        str(edit["work_id"]): {
            **dict(edit),
            "worklist_classification": items_by_work[str(edit["work_id"])].get(
                "imported_classification"
            ),
            "verified": True,
        }
        for edit in result.imported_page_edits
    }
    evidence_by_work = {
        work_id: list(imported_edits_by_work[work_id]["evidence"])
        if work_id in imported_edits_by_work
        else [str(item.get("canonical_path"))]
        for work_id, item in sorted(
            (
                (str(item["id"]), item)
                for item in items
                if str(item.get("id")) in reused | completed
            ),
            key=lambda pair: pair[0],
        )
    }
    ledger = {
        "schema_version": DOCUMENTATION_SEMANTIC_READINESS_SCHEMA_VERSION,
        "run_id": run.run_id,
        "status": "ready" if passed else "incomplete",
        "passed": passed,
        "p0": {
            "required": sorted(p0),
            "reused": sorted(p0 & reused),
            "completed": sorted(p0 & completed),
            "deferred": deferred_p0,
            "deferral_rationales": {
                work_id: result.deferral_rationales[work_id] for work_id in deferred_p0
            },
        },
        "p1": {
            "budget": run.semantic_budget,
            "selected": sorted(p1),
            "reused": sorted(p1 & reused),
            "completed": sorted(p1 & completed),
            "deferred": deferred_p1,
        },
        "imported_page_accounting": {
            work_id: (
                "changed"
                if work_id in imported_edits_by_work
                else "reused"
                if work_id in reused
                else "completed"
                if work_id in completed
                else "deferred"
                if work_id in deferred
                else "missing"
            )
            for work_id in sorted(imported)
        },
        "imported_page_edits": [
            dict(imported_edits_by_work[work_id])
            for work_id in sorted(imported_edits_by_work)
        ],
        "missing_work_ids": missing,
        "claims_evidence_pages": list(result.claims_evidence_pages),
        "claim_evidence": [dict(item) for item in result.claim_evidence],
        "runtime_captures": [dict(item) for item in result.runtime_captures],
        "evidence_by_work": evidence_by_work,
        "deferral_rationales": dict(sorted(result.deferral_rationales.items())),
        "unresolved_unknowns": list(result.unresolved_unknowns),
        "unsupported_coverage": list(result.unsupported_source_notices),
        "generator_defects": list(result.requested_follow_up_checks),
        "updated_at": _utc_now(),
    }
    path = workspace_root / RUN_CONTROL_DIR / "evidence" / "semantic-readiness.json"
    _write_json(path, ledger)
    return ledger


def _verify_user_docs_gate(
    wiki_root: Path,
    run: DocumentationRun,
    result: DocumentationAgentResult | None = None,
) -> None:
    workspace_root = wiki_root.parent
    worklist = _read_json(
        _workspace_path(workspace_root, run.evidence["semantic_worklist"])
    )
    deferred_ids = set(run.work.get("deferred", []))
    deferred_paths = {
        str(item.get("canonical_path"))
        for item in worklist.get("items", [])
        if isinstance(item, Mapping)
        and str(item.get("id")) in deferred_ids
        and isinstance(item.get("canonical_path"), str)
    }
    unverified_imported_paths = (
        {
            str(item.get("canonical_path"))
            for item in worklist.get("items", [])
            if isinstance(item, Mapping)
            and item.get("imported_classification") is not None
            and isinstance(item.get("canonical_path"), str)
        }
        if run.baseline.get("freshness") != "verified_current"
        else set()
    )
    reported_claims_evidence = set(result.claims_evidence_pages) if result else set()
    if result is None:
        result_path = run.evidence.get("user-docs_result")
        if result_path:
            result_payload = _read_json(_workspace_path(workspace_root, result_path))
            reported_claims_evidence = set(
                _portable_path_tuple(result_payload.get("claims_evidence_pages", []))
            )
    reported_unverified_imported_evidence = sorted(
        reported_claims_evidence & unverified_imported_paths
    )
    if reported_unverified_imported_evidence:
        raise DocumentationTransitionError(
            "User-docs result cites imported semantic evidence without a "
            "verified-current source baseline: "
            f"{reported_unverified_imported_evidence[0]}"
        )
    deferred_landing = [
        str(item.get("id"))
        for item in worklist.get("items", [])
        if isinstance(item, Mapping)
        and str(item.get("id")) in deferred_ids
        and item.get("category") == "landing_context"
    ]
    if deferred_landing:
        raise DocumentationTransitionError(
            "The primary overview cannot advance while landing-context work is "
            f"deferred: {deferred_landing[0]}"
        )
    overview = wiki_root / "index.md"
    if not overview.is_file() or overview.is_symlink():
        raise DocumentationTransitionError(
            "User-docs result requires a regular canonical index.md overview."
        )
    overview_text = overview.read_text(encoding="utf-8")
    generic_phrases = (
        "Replace this placeholder",
        "Describe what",
        "Use this landing page to choose the right wiki surface.",
    )
    if any(phrase in overview_text for phrase in generic_phrases):
        raise DocumentationTransitionError(
            "Canonical index.md still contains generic bootstrap landing prose."
        )
    guides = sorted((wiki_root / "guides").glob("*.md"))
    if not guides:
        raise DocumentationTransitionError(
            "User-docs result cannot advance without at least one guides/*.md page."
        )
    for guide in guides:
        text = guide.read_text(encoding="utf-8")
        if any(
            phrase in text for phrase in ("Replace this placeholder", "Describe what")
        ):
            raise DocumentationTransitionError(
                f"Primary user guide still contains a bootstrap placeholder: {guide.name}"
            )
        evidence_targets = _canonical_evidence_targets(guide, text, wiki_root)
        if not evidence_targets:
            raise DocumentationTransitionError(
                f"Primary user guide must link to canonical wiki evidence: {guide.name}"
            )
        deferred_targets = sorted(set(evidence_targets) & deferred_paths)
        if deferred_targets:
            raise DocumentationTransitionError(
                "Primary user guide links to deferred semantic evidence: "
                f"{guide.name} -> {deferred_targets[0]}"
            )
        unverified_imported_targets = sorted(
            set(evidence_targets) & unverified_imported_paths
        )
        if unverified_imported_targets:
            raise DocumentationTransitionError(
                "Primary user guide links to imported semantic evidence without a "
                "verified-current source baseline: "
                f"{guide.name} -> {unverified_imported_targets[0]}"
            )
    if run.intake.audiences == ("unspecified",):
        if "audience_unspecified" not in run.verdict_limitations:
            run.verdict_limitations.append("audience_unspecified")


def _canonical_evidence_targets(
    guide: Path, text: str, wiki_root: Path
) -> tuple[str, ...]:
    targets: list[str] = []
    for link in iter_markdown_link_targets(strip_fenced_code_blocks(text)):
        local = local_link_path(link.raw_target)
        if local is None:
            continue
        candidate = (guide.parent / local).resolve()
        try:
            relative = candidate.relative_to(wiki_root.resolve()).as_posix()
        except ValueError:
            continue
        if (
            relative == guide.relative_to(wiki_root).as_posix()
            or candidate.suffix.casefold() != ".md"
            or not candidate.is_file()
            or candidate.is_symlink()
        ):
            continue
        targets.append(relative)
    return tuple(dict.fromkeys(targets))


def _merge_unique(target: list[str], values: Iterable[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _merge_agent_findings(
    run: DocumentationRun, findings: Iterable[Mapping[str, Any]]
) -> None:
    existing = {str(item.get("id")): item for item in run.unresolved_findings}
    for raw in findings:
        severity = str(raw["severity"])
        status = str(raw["status"])
        if status != "open":
            raise DocumentationSchemaError(
                "Only the review ledger may apply a terminal finding status."
            )
        evidence = _finding_text_values(raw.get("evidence", []))
        paths = _finding_text_values(raw.get("paths", raw.get("path", [])))
        targets = _finding_text_values(raw.get("targets", raw.get("target", [])))
        finding_id = str(raw["id"])
        category = str(raw["category"])
        previous = existing.get(finding_id)
        if previous is not None and (
            str(previous.get("category", "unspecified")) != category
            or _finding_text_values(previous.get("paths", previous.get("path", [])))
            != paths
            or _finding_text_values(previous.get("targets", previous.get("target", [])))
            != targets
        ):
            raise DocumentationSchemaError(
                f"Agent finding {finding_id!r} changed its stable identity."
            )
        normalized = {
            "id": finding_id,
            "severity": severity,
            "source": "agent_review",
            "status": status,
            "category": category,
            "message": str(raw.get("message", "")),
            "evidence": evidence,
            "paths": paths,
            "targets": targets,
            "rationale": str(raw.get("rationale", "")),
        }
        existing[finding_id] = normalized
    run.unresolved_findings = [existing[key] for key in sorted(existing)]


def _finding_text_values(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, (str, Path)):
        return [str(value)]
    if isinstance(value, Iterable):
        return sorted({str(item) for item in value if item not in (None, "")})
    return [str(value)]


def _record_review_ledger_iteration(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    review_result: DocumentationAgentResult,
    review_result_path: Path,
) -> dict[str, Any]:
    ledger_path = workspace_root / RUN_CONTROL_DIR / "evidence" / "review-ledger.json"
    ledger_exists = ledger_path.is_file()
    if ledger_exists:
        ledger = DocumentationReviewLedger.from_dict(_read_json(ledger_path))
    else:
        ledger = create_review_ledger(
            run.run_id,
            max_loops=run.adjustment_loop_limit,
        )
    if ledger.run_id != run.run_id:
        raise DocumentationSchemaError(
            "Review ledger run_id does not match the documentation run."
        )

    iteration = ledger.loop_count + 1
    user_packet_relative = run.evidence.get("user-docs_packet")
    user_result_relative = run.evidence.get("user-docs_result")
    review_packet_relative = run.evidence.get("review_packet")
    if (
        not user_packet_relative
        or not user_result_relative
        or not review_packet_relative
    ):
        raise DocumentationSchemaError(
            "Review reconciliation requires recorded user-docs and review packets/results."
        )
    user_packet_path = _workspace_path(workspace_root, user_packet_relative)
    user_result_path = _workspace_path(workspace_root, user_result_relative)
    review_packet_path = _workspace_path(workspace_root, review_packet_relative)
    required_artifacts = (
        user_packet_path,
        user_result_path,
        review_packet_path,
        review_result_path,
    )
    missing = [path for path in required_artifacts if not path.is_file()]
    if missing:
        raise DocumentationSchemaError(
            "Review reconciliation is missing required packet/result evidence: "
            f"{missing[0].name}"
        )

    recorded_at = _utc_now()
    if not ledger_exists and run.unresolved_findings:
        try:
            prior_findings = normalize_review_findings(
                {"agent-review": [dict(item) for item in run.unresolved_findings]},
                observed_at=recorded_at,
            )
        except DocumentationReviewError as exc:
            raise DocumentationSchemaError(
                f"Invalid prior review finding state: {exc}"
            ) from exc
        ledger = DocumentationReviewLedger(
            run_id=ledger.run_id,
            max_loops=ledger.max_loops,
            findings=prior_findings,
        )
    worker_packet = DocumentationReviewPacket(
        packet_id=f"{run.run_id}:worker:{iteration}",
        role="worker",
        actor_id="documentation-worker",
        iteration=iteration,
        packet_hash=hash_bytes(user_packet_path.read_bytes()),
        result_hash=hash_bytes(user_result_path.read_bytes()),
        recorded_at=recorded_at,
        evidence=(
            user_packet_path.relative_to(workspace_root).as_posix(),
            user_result_path.relative_to(workspace_root).as_posix(),
        ),
    )
    reviewer_packet = DocumentationReviewPacket(
        packet_id=f"{run.run_id}:reviewer:{iteration}",
        role="reviewer",
        actor_id="documentation-reviewer",
        iteration=iteration,
        packet_hash=hash_bytes(review_packet_path.read_bytes()),
        result_hash=hash_bytes(review_result_path.read_bytes()),
        recorded_at=recorded_at,
        evidence=(
            review_packet_path.relative_to(workspace_root).as_posix(),
            review_result_path.relative_to(workspace_root).as_posix(),
        ),
    )
    records = [dict(item) for item in review_result.findings]
    try:
        loop = apply_review_loop(
            ledger,
            {"agent-review": records},
            observed_at=recorded_at,
            worker_packet=worker_packet,
            reviewer_packet=reviewer_packet,
        )
    except DocumentationReviewError as exc:
        raise DocumentationSchemaError(f"Invalid review result: {exc}") from exc
    _write_json(ledger_path, loop.ledger.to_dict())
    run.evidence["review_ledger"] = ledger_path.relative_to(workspace_root).as_posix()
    run.unresolved_findings = [
        finding.to_dict() for finding in loop.ledger.unresolved_findings
    ]
    return loop.to_dict()


def _record_site_review_findings(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    export_path: Path,
    check_path: Path,
    check_payload: Mapping[str, Any],
) -> dict[str, Any]:
    ledger_path = workspace_root / RUN_CONTROL_DIR / "evidence" / "review-ledger.json"
    if ledger_path.is_file():
        ledger = DocumentationReviewLedger.from_dict(_read_json(ledger_path))
    else:
        ledger = create_review_ledger(
            run.run_id,
            max_loops=run.adjustment_loop_limit,
        )
    iteration = ledger.loop_count + 1
    recorded_at = _utc_now()
    worker_packet = DocumentationReviewPacket(
        packet_id=f"{run.run_id}:site-export:{iteration}",
        role="worker",
        actor_id="deterministic-site-exporter",
        iteration=iteration,
        packet_hash=hash_bytes(export_path.read_bytes()),
        result_hash=hash_bytes(export_path.read_bytes()),
        recorded_at=recorded_at,
        evidence=(export_path.relative_to(workspace_root).as_posix(),),
    )
    reviewer_packet = DocumentationReviewPacket(
        packet_id=f"{run.run_id}:site-check:{iteration}",
        role="reviewer",
        actor_id="deterministic-site-checker",
        iteration=iteration,
        packet_hash=hash_bytes(check_path.read_bytes()),
        result_hash=hash_bytes(check_path.read_bytes()),
        recorded_at=recorded_at,
        evidence=(check_path.relative_to(workspace_root).as_posix(),),
    )
    records_by_source: dict[str, list[dict[str, Any]]] = {
        "site": [],
        "built-site": [],
        "media": [],
    }
    for raw in check_payload.get("issues", []):
        if not isinstance(raw, Mapping):
            continue
        issue = dict(raw)
        category = str(issue.get("category", "")).casefold()
        if "media" in category or "asset" in category:
            source = "media"
        elif "built" in category or str(check_payload.get("built_site_dir", "")):
            source = "built-site"
        else:
            source = "site"
        issue.setdefault("severity", "high")
        issue.setdefault("status", "open")
        records_by_source[source].append(issue)
    records_by_source = {
        source: records for source, records in records_by_source.items() if records
    }
    try:
        loop = apply_review_loop(
            ledger,
            records_by_source,
            observed_at=recorded_at,
            worker_packet=worker_packet,
            reviewer_packet=reviewer_packet,
        )
    except DocumentationReviewError as exc:
        raise DocumentationSchemaError(
            f"Invalid deterministic site finding: {exc}"
        ) from exc
    _write_json(ledger_path, loop.ledger.to_dict())
    run.evidence["review_ledger"] = ledger_path.relative_to(workspace_root).as_posix()
    run.unresolved_findings = [
        finding.to_dict() for finding in loop.ledger.unresolved_findings
    ]
    return loop.to_dict()


def _approve_review_ledger(
    workspace_root: Path,
    run: DocumentationRun,
    *,
    checks: Iterable[Mapping[str, Any]],
) -> None:
    relative = run.evidence.get("review_ledger")
    if not relative:
        raise DocumentationTransitionError(
            "Publish-ready transition requires a review ledger."
        )
    ledger_path = _workspace_path(workspace_root, relative)
    try:
        ledger = DocumentationReviewLedger.from_dict(_read_json(ledger_path))
        checks_payload = {"checks": [dict(check) for check in checks]}
        supervisor_packet = DocumentationReviewPacket(
            packet_id=f"{run.run_id}:supervisor:{ledger.loop_count}",
            role="supervisor",
            actor_id="host-supervisor",
            iteration=ledger.loop_count,
            packet_hash=hash_bytes(ledger_path.read_bytes()),
            result_hash=_sha256_json(checks_payload),
            recorded_at=_utc_now(),
            evidence=tuple(
                sorted(
                    value
                    for key, value in run.evidence.items()
                    if key
                    in {
                        "review_result",
                        "site_check",
                        "semantic_readiness",
                        "generated_ownership",
                    }
                    and value
                )
            ),
        )
        approved = reconcile_review_ledger(
            ledger,
            supervisor_packet=supervisor_packet,
            approved=True,
            rationale=(
                "The host supervisor independently reconciled the clean review ledger "
                "with deterministic source, ownership, semantic, user-doc, and site checks."
            ),
            evidence=supervisor_packet.evidence,
            reconciled_at=_utc_now(),
        )
    except DocumentationReviewError as exc:
        raise DocumentationTransitionError(
            f"Review ledger cannot advance to publish-ready: {exc}"
        ) from exc
    _write_json(ledger_path, approved.to_dict())


def _has_unresolved_high_findings(findings: Iterable[Mapping[str, Any]]) -> bool:
    return any(
        str(item.get("severity", "")).lower() in {"high", "critical"}
        and str(item.get("status", "open")).lower() not in {"resolved", "fixed"}
        for item in findings
    )


def _review_adjustment_state(findings: Iterable[Mapping[str, Any]]) -> str:
    wiki_prefixes = (
        "modules/",
        "entities/",
        "workflows/",
        "flows/",
        "infrastructure/",
    )
    wiki_root_pages = {
        "api-contracts.md",
        "dependencies.md",
        "load-order.md",
        "bootstrap-remainder.md",
    }
    for finding in findings:
        paths = finding.get("paths", finding.get("path", ()))
        if isinstance(paths, str):
            candidates = (paths,)
        elif isinstance(paths, Iterable):
            candidates = tuple(str(value) for value in paths)
        else:
            candidates = ()
        for raw in candidates:
            path = raw.replace("\\", "/").lstrip("./")
            if path.startswith("wiki/"):
                path = path[5:]
            if path in wiki_root_pages or path.startswith(wiki_prefixes):
                return "wiki_enrichment"
        category = str(finding.get("category", "")).casefold()
        if any(
            token in category
            for token in (
                "architecture",
                "dependency",
                "generated",
                "semantic",
                "source-claim",
            )
        ):
            return "wiki_enrichment"
    return "user_docs"


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
    '_validate_result_work_ids',
    '_reconcile_imported_page_edits',
    '_reconcile_semantic_readiness',
    '_verify_user_docs_gate',
    '_canonical_evidence_targets',
    '_merge_unique',
    '_merge_agent_findings',
    '_finding_text_values',
    '_record_review_ledger_iteration',
    '_record_site_review_findings',
    '_approve_review_ledger',
    '_has_unresolved_high_findings',
    '_review_adjustment_state',
    'record_documentation_agent_result',
    '_preflight_documentation_native_evidence',
    '_capture_native_evidence_transaction',
    '_rollback_native_evidence_transaction',
    '_reconcile_documentation_native_evidence',
)
