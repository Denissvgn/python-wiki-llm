"""Documentation-run schema services."""

from __future__ import annotations

from .dependencies import *
from .contracts import *

def _require_exact_fields(
    payload: Mapping[str, Any],
    *,
    allowed: set[str],
    required: set[str],
    label: str,
) -> None:
    return require_shared_exact_fields(
        payload,
        allowed=allowed,
        required=required,
        mapping_error=DocumentationSchemaError(f"{label} must be an object."),
        missing_error=lambda fields: DocumentationSchemaError(
            f"{label} is missing required field: {fields[0]}"
        ),
        unknown_error=lambda fields: DocumentationSchemaError(
            f"{label} contains unsupported field: {fields[0]}"
        ),
        stringify_keys=True,
    )


def _assert_no_forbidden_packet_fields(
    value: Any, *, label: str, path: str = "$"
) -> None:
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
            forbidden_suffix = any(
                normalized == suffix or normalized.endswith(f"_{suffix}")
                for suffix in _PACKET_FORBIDDEN_KEY_SUFFIXES
            )
            if normalized in _PACKET_FORBIDDEN_FIELDS or forbidden_suffix:
                raise DocumentationSchemaError(
                    f"{label} contains forbidden provider, endpoint, or credential "
                    f"field at {path}.{key}."
                )
            _assert_no_forbidden_packet_fields(item, label=label, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_no_forbidden_packet_fields(
                item, label=label, path=f"{path}[{index}]"
            )


def _validated_worklist_counts(worklist: Mapping[str, Any]) -> dict[str, Any]:
    """Return a schema-checked count projection instead of copying raw JSON."""

    if worklist.get("schema_version") != DOCUMENTATION_WORKLIST_SCHEMA_VERSION:
        raise DocumentationSchemaError(
            "Semantic worklist schema_version is unsupported or was changed."
        )
    items = worklist.get("items")
    if not isinstance(items, list) or any(
        not isinstance(item, Mapping) for item in items
    ):
        raise DocumentationSchemaError("Semantic worklist items must be objects.")

    priorities = {"P0": 0, "P1": 0, "P2": 0}
    statuses = {"deferred": 0, "open": 0, "reused": 0}
    deferred = 0
    for item in items:
        priority = item.get("priority")
        status = item.get("status")
        is_deferred = item.get("deferred")
        if priority not in priorities or status not in statuses:
            raise DocumentationSchemaError(
                "Semantic worklist contains an unsupported priority or status."
            )
        if not isinstance(is_deferred, bool):
            raise DocumentationSchemaError(
                "Semantic worklist deferred flags must be booleans."
            )
        priorities[str(priority)] += 1
        statuses[str(status)] += 1
        deferred += int(is_deferred)

    projected = {
        "total": len(items),
        "by_priority": priorities,
        "by_status": statuses,
        "deferred": deferred,
    }
    if worklist.get("counts") != projected:
        raise DocumentationSchemaError(
            "Semantic worklist counts do not match its item inventory."
        )
    return projected


def _portable_packet_source(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: source[key]
        for key in (
            "available",
            "display_identifier",
            "revision",
            "revision_kind",
            "content_fingerprint",
        )
        if key in source
    }


def _portable_packet_baseline(baseline: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        key: baseline[key]
        for key in (
            "strategy",
            "freshness_policy",
            "freshness",
            "source_revision",
        )
        if key in baseline
    }
    imported = baseline.get("input_wiki")
    if isinstance(imported, Mapping):
        payload["input_wiki"] = {
            key: imported[key]
            for key in (
                "display_identifier",
                "input_tree_hash",
                "initial_snapshot_hash",
                "manifest_version",
                "surface_schema_version",
                "compatibility",
                "refresh_decision",
            )
            if key in imported
        }
    else:
        payload["input_wiki"] = None
    return payload


def _validate_run_payload(payload: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "run_id",
        "state",
        "integration_mode",
        "baseline_strategy",
        "created_at",
        "updated_at",
        "intake",
        "source",
        "baseline",
        "paths",
        "policy",
        "publication",
        "skills",
        "semantic_budget",
        "adjustment_loop_limit",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise DocumentationSchemaError(
            f"Documentation run is missing required field: {missing[0]}"
        )
    if payload.get("schema_version") != DOCUMENTATION_RUN_SCHEMA_VERSION:
        raise DocumentationSchemaError("Unsupported documentation run schema_version.")
    if payload.get("integration_mode") != "external_agent_docs":
        raise DocumentationSchemaError("Unsupported documentation integration_mode.")
    if payload.get("state") not in SUPPORTED_RUN_STATES:
        raise DocumentationSchemaError(
            f"Unsupported run state: {payload.get('state')!r}"
        )
    if payload.get("baseline_strategy") not in SUPPORTED_BASELINE_STRATEGIES:
        raise DocumentationSchemaError(
            f"Unsupported baseline strategy: {payload.get('baseline_strategy')!r}"
        )
    for field_name in (
        "intake",
        "source",
        "baseline",
        "paths",
        "policy",
        "publication",
    ):
        if not isinstance(payload.get(field_name), dict):
            raise DocumentationSchemaError(f"Run field {field_name} must be an object.")
    if not isinstance(payload.get("skills"), list):
        raise DocumentationSchemaError("Run skills must be a list.")
    semantic_budget = payload.get("semantic_budget")
    if isinstance(semantic_budget, bool) or not isinstance(semantic_budget, int):
        raise DocumentationSchemaError("semantic_budget must be an integer.")
    if semantic_budget < 0:
        raise DocumentationSchemaError("semantic_budget must not be negative.")
    loop_limit = payload.get("adjustment_loop_limit")
    if isinstance(loop_limit, bool) or not isinstance(loop_limit, int):
        raise DocumentationSchemaError("adjustment_loop_limit must be an integer.")
    if loop_limit < 1:
        raise DocumentationSchemaError("adjustment_loop_limit must be positive.")
    run_id = payload.get("run_id")
    try:
        parsed_run_id = uuid.UUID(run_id) if isinstance(run_id, str) else None
    except (ValueError, AttributeError) as exc:
        raise DocumentationSchemaError("run_id must be a UUID.") from exc
    if parsed_run_id is None or str(parsed_run_id) != run_id:
        raise DocumentationSchemaError("run_id must be a canonical UUID string.")
    created_at = _require_utc_timestamp(payload.get("created_at"), "Run created_at")
    updated_at = _require_utc_timestamp(payload.get("updated_at"), "Run updated_at")
    if updated_at < created_at:
        raise DocumentationSchemaError("Run updated_at must not precede created_at.")
    DocumentationIntakeBrief.from_dict(payload["intake"])
    _validate_source_contract(payload["source"])
    _validate_baseline_contract(
        payload["baseline"],
        strategy=str(payload["baseline_strategy"]),
        source=payload["source"],
    )
    _validate_integrity_anchor_contract(payload)
    paths = payload["paths"]
    expected_paths = workspace_paths()
    missing_paths = sorted(set(expected_paths) - set(paths))
    if missing_paths:
        raise DocumentationSchemaError(
            f"Run paths are missing required field: {missing_paths[0]}"
        )
    for name, value in paths.items():
        portable = _portable_path(str(value), field_name=f"paths.{name}")
        if name in expected_paths and portable != expected_paths[name]:
            raise DocumentationSchemaError(
                f"Run path {name} must remain {expected_paths[name]!r}."
            )
    _validate_policy_contract(
        payload["policy"],
        source=payload["source"],
        baseline=payload["baseline"],
        intake=payload["intake"],
    )
    _validate_publication_contract(payload["publication"])
    _validate_skill_contracts(payload["skills"])
    _validate_optional_run_collections(payload)
    _validate_run_state_contract(payload)


def _validate_source_contract(source: Mapping[str, Any]) -> None:
    _require_exact_fields(
        source,
        allowed={
            "available",
            "display_identifier",
            "revision",
            "revision_kind",
            "content_fingerprint",
        },
        required={"available", "display_identifier", "revision", "revision_kind"},
        label="run source",
    )
    available = source.get("available")
    if not isinstance(available, bool):
        raise DocumentationSchemaError("Run source available must be a boolean.")
    if source.get("revision_kind") not in {"git", "content", "unavailable"}:
        raise DocumentationSchemaError("Run source revision_kind is unsupported.")
    revision = source.get("revision")
    if not isinstance(revision, str) or not revision.strip():
        raise DocumentationSchemaError(
            "Run source revision must be a non-empty string."
        )
    if available:
        if source.get("display_identifier") != "source":
            raise DocumentationSchemaError(
                "Available run source must use display_identifier='source'."
            )
        if source.get("revision_kind") == "unavailable":
            raise DocumentationSchemaError(
                "Available run source cannot use unavailable revision_kind."
            )
        fingerprint = _require_sha256(
            source.get("content_fingerprint"), "source fingerprint"
        )
        if revision == "source_unavailable":
            raise DocumentationSchemaError(
                "Available run source requires a concrete revision."
            )
        if source.get("revision_kind") == "content" and revision != (
            f"content:{fingerprint}"
        ):
            raise DocumentationSchemaError(
                "Content-addressed source revision must match its fingerprint."
            )
        if source.get("revision_kind") == "git" and not re.fullmatch(
            r"[0-9a-f]{40}|[0-9a-f]{64}", revision
        ):
            raise DocumentationSchemaError(
                "Git source revision must be a full lowercase object id."
            )
    elif (
        source.get("display_identifier") != "source_unavailable"
        or source.get("revision") != "source_unavailable"
        or source.get("revision_kind") != "unavailable"
        or "content_fingerprint" in source
    ):
        raise DocumentationSchemaError(
            "Unavailable source fields must use the source_unavailable sentinel."
        )


def _validate_baseline_contract(
    baseline: Mapping[str, Any],
    *,
    strategy: str,
    source: Mapping[str, Any],
) -> None:
    _require_exact_fields(
        baseline,
        allowed={
            "strategy",
            "freshness_policy",
            "freshness",
            "source_revision",
            "input_wiki",
        },
        required={
            "strategy",
            "freshness_policy",
            "freshness",
            "source_revision",
            "input_wiki",
        },
        label="run baseline",
    )
    if baseline.get("strategy") != strategy:
        raise DocumentationSchemaError(
            "Run baseline strategy does not match baseline_strategy."
        )
    freshness_policy = baseline.get("freshness_policy")
    if freshness_policy not in SUPPORTED_FRESHNESS_POLICIES:
        raise DocumentationSchemaError("Run baseline freshness_policy is unsupported.")
    if baseline.get("freshness") not in {
        "verified_current",
        "verified_stale",
        "unverified",
    }:
        raise DocumentationSchemaError("Run baseline freshness is unsupported.")
    if baseline.get("source_revision") != source.get("revision"):
        raise DocumentationSchemaError(
            "Run baseline source_revision must match the source revision."
        )
    imported = baseline.get("input_wiki")
    if strategy == "bootstrap_source":
        if (
            imported is not None
            or not source.get("available")
            or freshness_policy != "require-current"
            or baseline.get("freshness") != "verified_current"
        ):
            raise DocumentationSchemaError(
                "bootstrap_source requires an available, verified-current source and "
                "no input_wiki."
            )
        return
    if not isinstance(imported, Mapping):
        raise DocumentationSchemaError(
            "adopt_existing_wiki requires input_wiki provenance."
        )
    _require_exact_fields(
        imported,
        allowed={
            "display_identifier",
            "input_tree_hash",
            "initial_snapshot_hash",
            "manifest_version",
            "surface_schema_version",
            "compatibility",
            "refresh_decision",
        },
        required={
            "display_identifier",
            "input_tree_hash",
            "initial_snapshot_hash",
            "manifest_version",
            "surface_schema_version",
            "compatibility",
            "refresh_decision",
        },
        label="run input_wiki",
    )
    if imported.get("display_identifier") != "input_wiki":
        raise DocumentationSchemaError(
            "Run input_wiki display_identifier must be input_wiki."
        )
    _require_sha256(imported.get("input_tree_hash"), "input wiki tree hash")
    _require_sha256(imported.get("initial_snapshot_hash"), "input wiki snapshot hash")
    if imported.get("compatibility") not in {"current", "legacy_index_only"}:
        raise DocumentationSchemaError("Run input_wiki compatibility is unsupported.")
    compatibility = imported.get("compatibility")
    manifest_version = imported.get("manifest_version")
    surface_schema_version = imported.get("surface_schema_version")
    if compatibility == "legacy_index_only":
        if manifest_version is not None or surface_schema_version is not None:
            raise DocumentationSchemaError(
                "Run legacy input_wiki schemas must remain null."
            )
    elif (
        isinstance(manifest_version, bool)
        or manifest_version not in SUPPORTED_MANIFEST_VERSIONS
        or surface_schema_version != WIKI_SURFACE_INDEX_SCHEMA_VERSION
    ):
        raise DocumentationSchemaError(
            "Run current input_wiki schemas must match the supported manifest and "
            "surface versions."
        )
    refresh_decision = imported.get("refresh_decision")
    if refresh_decision not in {
        "not_required",
        "allow_unverified",
        "workspace_only_required",
        "workspace_only_completed",
    }:
        raise DocumentationSchemaError(
            "Run input_wiki refresh_decision is unsupported."
        )
    if freshness_policy == "refresh-snapshot" and refresh_decision != (
        "workspace_only_completed"
    ):
        raise DocumentationSchemaError(
            "refresh-snapshot requires a completed workspace-only refresh."
        )
    if (
        freshness_policy == "allow-unverified"
        and not source.get("available")
        and baseline.get("freshness") != "unverified"
    ):
        raise DocumentationSchemaError(
            "Source-unavailable adoption must remain freshness=unverified."
        )
    if (
        freshness_policy == "require-current"
        and baseline.get("freshness") != "verified_current"
    ):
        raise DocumentationSchemaError(
            "require-current adoption must be verified_current."
        )


def _validate_policy_contract(
    policy: Mapping[str, Any],
    *,
    source: Mapping[str, Any],
    baseline: Mapping[str, Any],
    intake: Mapping[str, Any],
) -> None:
    _require_exact_fields(
        policy,
        allowed={
            "integration_mode",
            "allowed_write_roots",
            "forbidden_write_roots",
            "agent_integration_writes",
            "target_cache_writes",
            "source_plugins_trusted",
            "live_service",
        },
        required={
            "integration_mode",
            "allowed_write_roots",
            "forbidden_write_roots",
            "agent_integration_writes",
            "target_cache_writes",
            "source_plugins_trusted",
            "live_service",
        },
        label="run policy",
    )
    if policy.get("integration_mode") != "external_agent_docs":
        raise DocumentationSchemaError("Run policy integration_mode is unsupported.")
    if (
        policy.get("agent_integration_writes") is not False
        or policy.get("target_cache_writes") is not False
    ):
        raise DocumentationSchemaError(
            "External documentation policy must forbid integration/cache writes."
        )
    if not isinstance(policy.get("source_plugins_trusted"), bool):
        raise DocumentationSchemaError(
            "Run policy source_plugins_trusted must be a boolean."
        )
    allowed_roots = policy.get("allowed_write_roots")
    if (
        not isinstance(allowed_roots, list)
        or any(
            not isinstance(value, str)
            or value not in {"workspace", "helper_cache", "capture"}
            for value in allowed_roots
        )
        or len(allowed_roots) != len(set(allowed_roots))
        or not allowed_roots
        or allowed_roots[0] != "workspace"
    ):
        raise DocumentationSchemaError(
            "Run policy allowed_write_roots must start with workspace and contain "
            "unique supported root labels."
        )
    forbidden_roots = policy.get("forbidden_write_roots")
    expected_forbidden = []
    if source.get("available") is True:
        expected_forbidden.append("source")
    if isinstance(baseline.get("input_wiki"), Mapping):
        expected_forbidden.append("input_wiki")
    if forbidden_roots != expected_forbidden:
        raise DocumentationSchemaError(
            "Run policy forbidden_write_roots must match the tagged baseline roots."
        )
    live_service = policy.get("live_service")
    if not isinstance(live_service, Mapping):
        raise DocumentationSchemaError("Run policy live_service must be an object.")
    _require_exact_fields(
        live_service,
        allowed={
            "configured",
            "access_mode",
            "observation_allowed",
            "responses_are_untrusted_evidence",
            "secret_material_persisted",
        },
        required={
            "configured",
            "access_mode",
            "observation_allowed",
            "responses_are_untrusted_evidence",
            "secret_material_persisted",
        },
        label="run policy live_service",
    )
    configured = live_service.get("configured")
    observation_allowed = live_service.get("observation_allowed")
    access_mode = live_service.get("access_mode")
    if not isinstance(configured, bool):
        raise DocumentationSchemaError(
            "Run policy live_service configured must be a boolean."
        )
    if not isinstance(observation_allowed, bool):
        raise DocumentationSchemaError(
            "Run policy live_service observation_allowed must be a boolean."
        )
    if access_mode not in {"unspecified", "anonymous", "non-secret"}:
        raise DocumentationSchemaError(
            "Run policy live_service access_mode is unsupported."
        )
    if (
        live_service.get("responses_are_untrusted_evidence") is not True
        or live_service.get("secret_material_persisted") is not False
    ):
        raise DocumentationSchemaError(
            "Run policy must keep live responses untrusted and secrets unpersisted."
        )
    intake_live = intake.get("live_service")
    if not isinstance(intake_live, Mapping):
        raise DocumentationSchemaError(
            "Run policy cannot be reconciled without intake live_service."
        )
    expected_configured = intake_live.get("address") != "unspecified"
    if (
        configured != expected_configured
        or observation_allowed != intake_live.get("observation_allowed")
        or access_mode != intake_live.get("access_mode")
    ):
        raise DocumentationSchemaError(
            "Run policy live_service must match the trusted intake decision."
        )
    if observation_allowed and "capture" not in allowed_roots:
        raise DocumentationSchemaError(
            "Run policy live-service observation requires the capture write root."
        )


def _validate_documentation_projection_policy(
    knowledge_mode: Any,
    public_repository_identity: Any,
) -> tuple[str, str | None]:
    if not isinstance(knowledge_mode, str):
        raise DocumentationSchemaError(
            "knowledge_mode must be off, public-portable, or internal."
        )
    if knowledge_mode not in SUPPORTED_DOCUMENTATION_KNOWLEDGE_MODES:
        raise DocumentationSchemaError(
            "knowledge_mode must be off, public-portable, or internal."
        )
    if public_repository_identity is not None:
        if (
            not isinstance(public_repository_identity, str)
            or not public_repository_identity
            or public_repository_identity != public_repository_identity.strip()
            or len(public_repository_identity) > 512
            or any(
                ord(character) < 32 or ord(character) == 127
                for character in public_repository_identity
            )
        ):
            raise DocumentationSchemaError(
                "knowledge_public_repository_identity must be one exact, "
                "non-empty safe identity string."
            )
    if (
        public_repository_identity is not None
        and knowledge_mode != "public-portable"
    ):
        raise DocumentationSchemaError(
            "knowledge_public_repository_identity is valid only with "
            "knowledge_mode='public-portable'."
        )
    return knowledge_mode, public_repository_identity


def _validate_publication_contract(publication: Mapping[str, Any]) -> None:
    _require_exact_fields(
        publication,
        allowed={
            "site_name",
            "format",
            "link_mode",
            "deployment",
            "knowledge_mode",
            "knowledge_public_repository_identity",
        },
        required={"site_name", "format", "link_mode", "deployment"},
        label="run publication",
    )
    site_name = publication.get("site_name")
    if not isinstance(site_name, str) or not site_name.strip():
        raise DocumentationSchemaError("Run publication site_name is required.")
    if publication.get("format") not in {"mkdocs", "plain", "docusaurus"}:
        raise DocumentationSchemaError("Run publication format is unsupported.")
    if publication.get("link_mode") not in {"http", "file"}:
        raise DocumentationSchemaError("Run publication link_mode is unsupported.")
    if publication.get("deployment") != "handoff_only":
        raise DocumentationSchemaError(
            "Run publication deployment must remain handoff_only."
        )
    _validate_documentation_projection_policy(
        publication.get("knowledge_mode", "off"),
        publication.get("knowledge_public_repository_identity"),
    )


def _validate_skill_contracts(skills: list[Any]) -> None:
    seen: set[str] = set()
    for raw in skills:
        if not isinstance(raw, Mapping):
            raise DocumentationSchemaError("Run skills must contain objects.")
        _require_exact_fields(
            raw,
            allowed={"id", "package_version", "hash", "path"},
            required={"id", "package_version", "hash", "path"},
            label="run skill",
        )
        skill_id = raw.get("id")
        if not isinstance(skill_id, str):
            raise DocumentationSchemaError("Run skill id must be a string.")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,127}", skill_id):
            raise DocumentationSchemaError("Run skill id is not portable.")
        if skill_id in seen:
            raise DocumentationSchemaError("Run skill ids must be unique.")
        seen.add(skill_id)
        package_version = raw.get("package_version")
        if (
            not isinstance(package_version, str)
            or not package_version.strip()
            or package_version != package_version.strip()
        ):
            raise DocumentationSchemaError(
                f"Run skill {skill_id} package_version must be a non-empty string."
            )
        _require_sha256(raw.get("hash"), f"skill {skill_id} hash")
        raw_path = raw.get("path")
        if not isinstance(raw_path, str):
            raise DocumentationSchemaError(
                f"Run skill {skill_id} path must be a string."
            )
        path = _portable_path(raw_path, field_name="skill path")
        expected_path = f"{RUN_CONTROL_DIR}/skills/{skill_id}"
        if path != expected_path:
            raise DocumentationSchemaError(
                f"Run skill {skill_id} path must match its id at {expected_path!r}."
            )
    missing = [
        skill_id for skill_id in DEFAULT_DOCUMENTATION_SKILLS if skill_id not in seen
    ]
    if missing:
        raise DocumentationSchemaError(
            f"Run skills are missing required bundled skill: {missing[0]}"
        )


def _validate_integrity_anchor_contract(payload: Mapping[str, Any]) -> None:
    anchors = payload.get("integrity_anchors")
    if anchors is None:
        # Frozen v1 readers remain compatible with records written before the
        # additive anchors were introduced. Lifecycle operations fail closed
        # when those records are used as active workspaces.
        return
    if not isinstance(anchors, Mapping):
        raise DocumentationSchemaError("Run integrity_anchors must be an object.")
    expected = {"generated_ownership"}
    source = payload.get("source", {})
    if isinstance(source, Mapping) and source.get("available") is True:
        expected.add("source_baseline")
    if set(anchors) != expected:
        raise DocumentationSchemaError(
            "Run integrity_anchors do not match the baseline evidence contract."
        )
    for key, value in anchors.items():
        _require_sha256(value, f"integrity anchor {key}")


def _validate_optional_run_collections(payload: Mapping[str, Any]) -> None:
    evidence = payload.get("evidence", {})
    if not isinstance(evidence, Mapping):
        raise DocumentationSchemaError("Run evidence must be an object.")
    for key, value in evidence.items():
        if not isinstance(value, str):
            raise DocumentationSchemaError("Run evidence paths must be strings.")
        if value:
            path = _portable_path(value, field_name=f"evidence.{key}")
            if not path.startswith(f"{RUN_CONTROL_DIR}/"):
                raise DocumentationSchemaError(
                    "Run evidence must remain under the run control directory."
                )
    required_evidence = {
        "wiki_baseline": f"{RUN_CONTROL_DIR}/evidence/wiki-baseline.json",
        "generated_ownership": (f"{RUN_CONTROL_DIR}/evidence/generated-ownership.json"),
        "semantic_worklist": f"{RUN_CONTROL_DIR}/evidence/semantic-worklist.json",
        "semantic_readiness": (f"{RUN_CONTROL_DIR}/evidence/semantic-readiness.json"),
    }
    source = payload.get("source", {})
    required_evidence["source_baseline"] = (
        f"{RUN_CONTROL_DIR}/evidence/source-baseline.json"
        if source.get("available") is True
        else ""
    )
    strategy = payload.get("baseline_strategy")
    required_evidence["bootstrap"] = (
        f"{RUN_CONTROL_DIR}/evidence/bootstrap.json"
        if strategy == "bootstrap_source"
        else ""
    )
    baseline = payload.get("baseline", {})
    required_evidence["wiki_input"] = (
        f"{RUN_CONTROL_DIR}/evidence/wiki-input.json"
        if isinstance(baseline.get("input_wiki"), Mapping)
        else ""
    )
    for key, expected in required_evidence.items():
        value = evidence.get(key, "")
        if (expected and value != expected) or (not expected and value):
            raise DocumentationSchemaError(
                f"Run evidence.{key} must remain {expected!r}."
            )
    optional_exact = {
        "workspace_refresh": f"{RUN_CONTROL_DIR}/evidence/workspace-refresh.json",
        "continuation": f"{RUN_CONTROL_DIR}/evidence/continuation.json",
        "native_refresh": f"{RUN_CONTROL_DIR}/evidence/native-refresh.json",
        "lint": f"{RUN_CONTROL_DIR}/evidence/lint.json",
        "ci_check": f"{RUN_CONTROL_DIR}/evidence/ci-check.json",
        "verification": f"{RUN_CONTROL_DIR}/evidence/verification.json",
        "site_export": f"{RUN_CONTROL_DIR}/evidence/site-export.json",
        "builder": f"{RUN_CONTROL_DIR}/evidence/builder.json",
        "site_check": f"{RUN_CONTROL_DIR}/evidence/site-check.json",
        "final_report": f"{RUN_CONTROL_DIR}/evidence/final-report.json",
        "review_ledger": f"{RUN_CONTROL_DIR}/evidence/review-ledger.json",
        "p0_calibration_census": (
            f"{RUN_CONTROL_DIR}/evidence/p0-calibration-census.json"
        ),
        "p0_calibration_shadow": (
            f"{RUN_CONTROL_DIR}/evidence/p0-calibration-shadow.json"
        ),
    }
    for key, expected in optional_exact.items():
        value = evidence.get(key, "")
        if value and value != expected:
            raise DocumentationSchemaError(
                f"Run evidence.{key} must remain {expected!r}."
            )
    work = payload.get("work", {})
    if not isinstance(work, Mapping):
        raise DocumentationSchemaError("Run work must be an object.")
    for key in ("reused", "completed", "deferred", "blocked"):
        values = work.get(key, [])
        if not isinstance(values, list) or any(
            not isinstance(value, str) for value in values
        ):
            raise DocumentationSchemaError(f"Run work.{key} must be a string list.")
    for field_name in ("validation_results", "unresolved_findings"):
        values = payload.get(field_name, [])
        if not isinstance(values, list) or any(
            not isinstance(value, Mapping) for value in values
        ):
            raise DocumentationSchemaError(
                f"Run {field_name} must be a list of objects."
            )
    attempts = payload.get("stage_attempts", {})
    if not isinstance(attempts, Mapping):
        raise DocumentationSchemaError("Run stage_attempts must be an object.")
    for stage, attempt in attempts.items():
        if (
            stage not in SUPPORTED_AGENT_STAGES
            or isinstance(attempt, bool)
            or not isinstance(attempt, int)
            or attempt < 1
        ):
            raise DocumentationSchemaError("Run stage_attempts contains invalid data.")
        expected_stage_evidence = {
            f"{stage}_before": (
                f"{RUN_CONTROL_DIR}/evidence/{stage}-{attempt:02d}-before.json"
            ),
            f"{stage}_packet": (
                f"{RUN_CONTROL_DIR}/packets/{stage}-{attempt:02d}.json"
            ),
        }
        result_key = f"{stage}_result"
        for key, expected in expected_stage_evidence.items():
            if evidence.get(key) != expected:
                raise DocumentationSchemaError(
                    f"Run evidence.{key} must remain {expected!r}."
                )
        result_value = evidence.get(result_key, "")
        if result_value:
            match = re.fullmatch(
                rf"{re.escape(RUN_CONTROL_DIR)}/results/"
                rf"{re.escape(stage)}-(\d{{2}})\.json",
                str(result_value),
            )
            result_attempt = int(match.group(1)) if match else 0
            if not match or result_attempt < 1 or result_attempt > attempt:
                raise DocumentationSchemaError(
                    f"Run evidence.{result_key} has an invalid attempt path."
                )
    stage_evidence_prefixes = tuple(f"{stage}_" for stage in SUPPORTED_AGENT_STAGES)
    for key in evidence:
        if key.startswith(stage_evidence_prefixes):
            stage = key.rsplit("_", 1)[0]
            if stage not in attempts:
                raise DocumentationSchemaError(
                    f"Run evidence.{key} has no corresponding stage attempt."
                )
    limitations = payload.get("verdict_limitations", [])
    if not isinstance(limitations, list) or any(
        not isinstance(value, str) for value in limitations
    ):
        raise DocumentationSchemaError(
            "Run verdict_limitations must be a list of strings."
        )


def _validate_run_state_contract(payload: Mapping[str, Any]) -> None:
    state = str(payload["state"])
    current_stage = payload.get("current_stage")
    resume_state = payload.get("resume_state")
    if current_stage not in (None, "") and current_stage not in SUPPORTED_AGENT_STAGES:
        raise DocumentationSchemaError("Run current_stage is unsupported.")
    if state == "blocked":
        if current_stage not in (None, ""):
            raise DocumentationSchemaError(
                "Blocked runs must not expose an active current_stage."
            )
        if resume_state not in {
            "prepared",
            "baseline_ready",
            "wiki_enrichment",
            "user_docs",
            "review",
        }:
            raise DocumentationSchemaError(
                "Blocked runs require a valid non-terminal resume_state."
            )
        return
    if resume_state not in (None, ""):
        raise DocumentationSchemaError("Only blocked runs may contain resume_state.")
    expected_stage = _state_to_stage(state)
    if (current_stage or None) != expected_stage:
        raise DocumentationSchemaError(
            "Run current_stage does not match its lifecycle state."
        )


def _require_sha256(value: Any, label: str) -> str:
    return require_shared_sha256(
        value,
        digest_error=DocumentationSchemaError(
            f"{label} must be a lowercase sha256 digest."
        ),
    )


def _require_utc_timestamp(value: Any, label: str) -> datetime:
    """Preserve the documentation-run v1 ISO parser's timestamp acceptance."""

    return parse_utc_timestamp(
        value,
        string_error=DocumentationSchemaError(
            f"{label} must be a UTC timestamp string."
        ),
        timestamp_error=DocumentationSchemaError(
            f"{label} must be a UTC timestamp."
        ),
        reject_control_characters=False,
    )[1]


def _required_agent_result_text(value: Any, field_name: str) -> str:
    return require_nonempty_text(
        value,
        error=DocumentationSchemaError(
            f"Agent result {field_name} must be a non-empty string."
        ),
        trim_error=DocumentationSchemaError(
            f"Agent result {field_name} must not have surrounding whitespace."
        ),
        require_trimmed=True,
        reject_control_characters=False,
    )


def _validate_imported_page_edits(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise DocumentationSchemaError(
            "Agent result imported_page_edits must be a list of objects."
        )
    edits: list[dict[str, Any]] = []
    seen_work_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping):
            raise DocumentationSchemaError(
                f"Agent result imported_page_edits[{index}] must be an object."
            )
        label = f"agent result imported_page_edits[{index}]"
        _require_exact_fields(
            raw,
            allowed=set(_IMPORTED_PAGE_EDIT_FIELDS),
            required=set(_IMPORTED_PAGE_EDIT_FIELDS),
            label=label,
        )
        work_id = _required_agent_result_text(
            raw["work_id"], f"imported_page_edits[{index}].work_id"
        )
        canonical_path = _portable_path(
            _required_agent_result_text(
                raw["canonical_path"],
                f"imported_page_edits[{index}].canonical_path",
            ),
            field_name=f"imported_page_edits[{index}].canonical_path",
        )
        before_hash = _require_sha256(
            raw["before_hash"], f"imported_page_edits[{index}].before_hash"
        )
        after_hash = _require_sha256(
            raw["after_hash"], f"imported_page_edits[{index}].after_hash"
        )
        if before_hash == after_hash:
            raise DocumentationSchemaError(
                f"Agent result imported_page_edits[{index}] hashes must differ."
            )
        evidence = _portable_path_tuple(raw["evidence"])
        if not evidence:
            raise DocumentationSchemaError(
                f"Agent result imported_page_edits[{index}] requires non-empty evidence."
            )
        rationale = _required_agent_result_text(
            raw["rationale"], f"imported_page_edits[{index}].rationale"
        )
        path_key = portable_path_key(canonical_path)
        if work_id in seen_work_ids or path_key in seen_paths:
            raise DocumentationSchemaError(
                "Agent result imported_page_edits must contain unique work ids and "
                "canonical paths."
            )
        seen_work_ids.add(work_id)
        seen_paths.add(path_key)
        edits.append(
            {
                "work_id": work_id,
                "canonical_path": canonical_path,
                "before_hash": before_hash,
                "after_hash": after_hash,
                "evidence": list(evidence),
                "rationale": rationale,
            }
        )
    return tuple(edits)


def _validate_agent_result_findings(
    value: Any, *, stage: str
) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise DocumentationSchemaError(
            "Agent result findings must be a list of objects."
        )
    findings: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping):
            raise DocumentationSchemaError(
                f"Agent result findings[{index}] must be an object."
            )
        _require_exact_fields(
            raw,
            allowed=set(_AGENT_FINDING_FIELDS),
            required={"id", "category", "severity", "status"},
            label=f"agent result findings[{index}]",
        )
        _required_agent_result_text(raw["id"], f"findings[{index}].id")
        _required_agent_result_text(raw["category"], f"findings[{index}].category")
        severity = _required_agent_result_text(
            raw["severity"], f"findings[{index}].severity"
        )
        if severity not in _AGENT_FINDING_SEVERITIES:
            raise DocumentationSchemaError(
                f"Agent result findings[{index}] has unsupported severity {severity!r}."
            )
        status = _required_agent_result_text(raw["status"], f"findings[{index}].status")
        if status not in _AGENT_FINDING_STATUSES:
            raise DocumentationSchemaError(
                f"Agent result findings[{index}] has unsupported status {status!r}."
            )
        if "path" in raw and "paths" in raw:
            raise DocumentationSchemaError(
                f"Agent result findings[{index}] cannot contain both path and paths."
            )
        if "target" in raw and "targets" in raw:
            raise DocumentationSchemaError(
                f"Agent result findings[{index}] cannot contain both target and targets."
            )
        if "path" in raw:
            if not isinstance(raw["path"], str):
                raise DocumentationSchemaError(
                    f"Agent result findings[{index}].path must be a string."
                )
            _portable_path(raw["path"], field_name=f"findings[{index}].path")
        if "paths" in raw:
            _portable_path_tuple(raw["paths"])
        if "target" in raw and (
            not isinstance(raw["target"], str) or not raw["target"].strip()
        ):
            raise DocumentationSchemaError(
                f"Agent result findings[{index}].target must be a non-empty string."
            )
        if "targets" in raw:
            _strict_string_tuple(
                raw["targets"], label=f"Agent result findings[{index}].targets"
            )
        evidence = _strict_string_tuple(
            raw.get("evidence", []),
            label=f"Agent result findings[{index}].evidence",
        )
        message = raw.get("message", "")
        rationale = raw.get("rationale", "")
        if not isinstance(message, str) or not isinstance(rationale, str):
            raise DocumentationSchemaError(
                f"Agent result findings[{index}] message and rationale must be strings."
            )
        if status in _TERMINAL_AGENT_FINDING_STATUSES:
            if stage != "review":
                raise DocumentationSchemaError(
                    "Only a review-stage result may use a terminal finding status."
                )
            if not rationale.strip():
                raise DocumentationSchemaError(
                    f"Terminal agent finding {raw['id']!r} requires a rationale."
                )
            if not evidence:
                raise DocumentationSchemaError(
                    f"Terminal agent finding {raw['id']!r} requires explicit evidence."
                )
        elif not (message.strip() or rationale.strip() or evidence):
            raise DocumentationSchemaError(
                f"Open agent finding {raw['id']!r} requires a message or evidence."
            )
        findings.append(dict(raw))
    return tuple(findings)


def _portable_path_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise DocumentationSchemaError("Expected a list of portable paths.")
    if any(not isinstance(item, str) for item in value):
        raise DocumentationSchemaError("Portable paths must be strings.")
    paths = tuple(
        _portable_path(item, defer_non_nfc_error=True) for item in value
    )
    seen: dict[str, str] = {}
    for path in paths:
        key = portable_path_key(path)
        previous = seen.get(key)
        if previous is not None:
            raise DocumentationSchemaError(
                "Portable paths must not collide on case-insensitive or "
                f"Unicode-normalizing filesystems: {previous!r} and {path!r}."
            )
        seen[key] = path
    return tuple(_portable_path(path) for path in paths)


def _portable_path(
    value: str,
    *,
    field_name: str = "path",
    defer_non_nfc_error: bool = False,
) -> str:
    """Validate a path, with NFC deferral only for tuple collision preflights."""

    return require_portable_relative_path(
        value,
        defer_non_nfc_error=defer_non_nfc_error,
        text_error=DocumentationSchemaError(
            f"{field_name} must be a non-empty workspace-relative portable path: {value!r}"
        ),
        relative_error=DocumentationSchemaError(
            f"{field_name} must be a non-empty workspace-relative portable path: {value!r}"
        ),
        separator_error=DocumentationSchemaError(
            f"{field_name} must be a non-empty workspace-relative portable path: {value!r}"
        ),
        non_nfc_error=DocumentationSchemaError(
            f"{field_name} is not portable across supported systems: {value!r}"
        ),
        nonportable_error=DocumentationSchemaError(
            f"{field_name} is not portable across supported systems: {value!r}"
        ),
        reserved_error=DocumentationSchemaError(
            f"{field_name} uses a reserved Windows name: {value!r}"
        ),
    )


def _strict_string_tuple(value: Any, *, label: str) -> tuple[str, ...]:
    """Preserve v1 result strings without trimming or control filtering."""

    return tuple(
        require_trimmed_text_list(
            value,
            error=DocumentationSchemaError(
                f"{label} must be a list of non-empty strings."
            ),
            require_trimmed_items=False,
            reject_control_characters=False,
        )
    )


def _text_tuple(value: Any) -> tuple[str, ...]:
    return _strict_string_tuple(value, label="Agent result field")

__all__ = (
    '_require_exact_fields',
    '_assert_no_forbidden_packet_fields',
    '_validated_worklist_counts',
    '_portable_packet_source',
    '_portable_packet_baseline',
    '_validate_run_payload',
    '_validate_source_contract',
    '_validate_baseline_contract',
    '_validate_policy_contract',
    '_validate_documentation_projection_policy',
    '_validate_publication_contract',
    '_validate_skill_contracts',
    '_validate_integrity_anchor_contract',
    '_validate_optional_run_collections',
    '_validate_run_state_contract',
    '_require_sha256',
    '_require_utc_timestamp',
    '_required_agent_result_text',
    '_validate_imported_page_edits',
    '_validate_agent_result_findings',
    '_portable_path_tuple',
    '_portable_path',
    '_strict_string_tuple',
    '_text_tuple',
)
