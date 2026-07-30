"""Commands for deterministic standalone documentation workspaces."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

from ..config import PathValidationError, validate_source_root
from ..services.documentation_run import (
    DocumentationAgentResult,
    DocumentationRunError,
    SUPPORTED_DOCUMENTATION_KNOWLEDGE_MODES,
    build_documentation_agent_packet,
    export_documentation_run,
    get_documentation_run_status,
    load_documentation_run,
    prepare_documentation_run,
    record_documentation_agent_result,
    verify_documentation_run,
)
from ..services.filesystem_guard import atomic_write_private_bytes


_MAX_INTAKE_BYTES = 1_000_000
_MAX_CALIBRATION_JSON_BYTES = 4 * 1024 * 1024
_MAX_CALIBRATION_PACKET_BYTES = 16 * 1024 * 1024
_BASELINE_STRATEGIES = {
    "bootstrap-source": "bootstrap_source",
    "existing-wiki": "adopt_existing_wiki",
}
KNOWLEDGE_MODE_CHOICES = tuple(
    sorted(SUPPORTED_DOCUMENTATION_KNOWLEDGE_MODES)
)
_INTAKE_KEYS = {
    "project_purpose",
    "audiences",
    "audience_intent",
    "live_service",
}


def _read_bounded_text(path: str, *, label: str) -> str:
    source = Path(path).expanduser()
    try:
        with source.open("rb") as stream:
            data = stream.read(_MAX_INTAKE_BYTES + 1)
    except OSError as exc:
        raise DocumentationRunError(f"Cannot read {label} {source}: {exc}") from exc
    if len(data) > _MAX_INTAKE_BYTES:
        raise DocumentationRunError(
            f"{label} exceeds the {_MAX_INTAKE_BYTES}-byte input limit."
        )
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentationRunError(f"{label} must be UTF-8 text: {source}") from exc


def _read_json_object(path: str, *, label: str) -> dict[str, Any]:
    if path == "-":
        text = sys.stdin.read(_MAX_INTAKE_BYTES + 1)
        if len(text.encode("utf-8")) > _MAX_INTAKE_BYTES:
            raise DocumentationRunError(
                f"{label} exceeds the {_MAX_INTAKE_BYTES}-byte input limit."
            )
    else:
        text = _read_bounded_text(path, label=label)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DocumentationRunError(f"Invalid {label} JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise DocumentationRunError(f"{label} must contain one JSON object.")
    return payload


def _read_calibration_json_object(path: str, *, label: str) -> dict[str, Any]:
    if path == "-":
        text = sys.stdin.read(_MAX_CALIBRATION_JSON_BYTES + 1)
        if len(text.encode("utf-8")) > _MAX_CALIBRATION_JSON_BYTES:
            raise DocumentationRunError(
                f"{label} exceeds the {_MAX_CALIBRATION_JSON_BYTES}-byte input limit."
            )
    else:
        source = Path(path).expanduser()
        try:
            with source.open("rb") as stream:
                data = stream.read(_MAX_CALIBRATION_JSON_BYTES + 1)
        except OSError as exc:
            raise DocumentationRunError(f"Cannot read {label} {source}: {exc}") from exc
        if len(data) > _MAX_CALIBRATION_JSON_BYTES:
            raise DocumentationRunError(
                f"{label} exceeds the {_MAX_CALIBRATION_JSON_BYTES}-byte input limit."
            )
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentationRunError(
                f"{label} must be UTF-8 text: {source}"
            ) from exc
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise DocumentationRunError(f"Invalid {label} JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise DocumentationRunError(f"{label} must contain one JSON object.")
    return payload


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise DocumentationRunError(f"Duplicate JSON object key: {key!r}.")
        payload[key] = value
    return payload


def _reject_json_constant(value: str) -> None:
    raise DocumentationRunError(f"Non-finite JSON number is forbidden: {value}.")


def _parse_audiences(values: list[str] | None) -> list[str] | None:
    audiences = [
        item.strip()
        for value in values or []
        for item in value.split(",")
        if item.strip()
    ]
    return list(dict.fromkeys(audiences)) or None


def _parse_audience_intent(values: list[str] | None) -> dict[str, str] | None:
    parsed: dict[str, str] = {}
    for value in values or []:
        audience, separator, intent = value.partition("=")
        if not separator or not audience.strip() or not intent.strip():
            raise DocumentationRunError(
                "--audience-intent must use the form AUDIENCE=INTENT."
            )
        parsed[audience.strip().lower()] = intent.strip()
    return parsed or None


def _intake_from_args(args) -> dict[str, Any]:
    intake_path = getattr(args, "intake_file", None)
    direct_values_present = any(
        (
            getattr(args, "project_brief", None),
            getattr(args, "audience", None),
            getattr(args, "audience_intent", None),
            getattr(args, "live_service_url", None),
            getattr(args, "live_service_access_mode", "unspecified") != "unspecified",
            bool(getattr(args, "observe_live_service", False)),
        )
    )
    if intake_path and direct_values_present:
        raise DocumentationRunError(
            "--intake-file cannot be combined with direct intake flags."
        )

    if not intake_path:
        project_brief = getattr(args, "project_brief", None)
        return {
            "project_purpose": (
                _read_bounded_text(project_brief, label="project brief").strip()
                if project_brief
                else None
            ),
            "audiences": _parse_audiences(getattr(args, "audience", None)),
            "audience_intent": _parse_audience_intent(
                getattr(args, "audience_intent", None)
            ),
            "live_service_url": getattr(args, "live_service_url", None),
            "live_service_access_mode": getattr(
                args, "live_service_access_mode", "unspecified"
            ),
            "live_service_observation_allowed": bool(
                getattr(args, "observe_live_service", False)
            ),
        }

    payload = _read_json_object(intake_path, label="intake file")
    unknown = sorted(set(payload) - _INTAKE_KEYS)
    if unknown:
        raise DocumentationRunError(
            f"Unknown intake-file field(s): {', '.join(unknown)}."
        )
    audiences = payload.get("audiences")
    if audiences is not None and not (
        isinstance(audiences, list)
        and all(isinstance(value, str) for value in audiences)
    ):
        raise DocumentationRunError("intake audiences must be a list of strings.")
    audience_intent = payload.get("audience_intent")
    if audience_intent is not None and not (
        isinstance(audience_intent, dict)
        and all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in audience_intent.items()
        )
    ):
        raise DocumentationRunError(
            "intake audience_intent must map audience names to strings."
        )
    live_service = payload.get("live_service", {})
    if not isinstance(live_service, dict):
        raise DocumentationRunError("intake live_service must be an object.")
    live_unknown = sorted(
        set(live_service) - {"address", "url", "access_mode", "observation_allowed"}
    )
    if live_unknown:
        raise DocumentationRunError(
            f"Unknown intake live_service field(s): {', '.join(live_unknown)}."
        )
    access_mode = live_service.get("access_mode", "unspecified")
    if not isinstance(access_mode, str):
        raise DocumentationRunError("intake live_service access_mode must be a string.")
    observation_allowed = live_service.get("observation_allowed", False)
    if not isinstance(observation_allowed, bool):
        raise DocumentationRunError(
            "intake live_service observation_allowed must be a boolean."
        )
    return {
        "project_purpose": _optional_string(payload.get("project_purpose")),
        "audiences": list(audiences) if audiences is not None else None,
        "audience_intent": dict(audience_intent)
        if audience_intent is not None
        else None,
        "live_service_url": _optional_string(
            live_service.get("address", live_service.get("url"))
        ),
        "live_service_access_mode": access_mode,
        "live_service_observation_allowed": observation_allowed,
    }


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DocumentationRunError("intake text fields must be strings.")
    return value


def _validate_evidence_root(
    value: str | None,
    *,
    label: str,
    allow_external: bool,
) -> str | None:
    if value is None:
        return None
    return str(validate_source_root(value, label, allow_external=allow_external))


def _print_status(payload: Mapping[str, Any], *, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print(f"Documentation run: {payload['run_id']}")
    print(f"State: {payload['state']}")
    print(f"Baseline: {payload['baseline_strategy']}")
    print(f"Source freshness: {payload['freshness']}")
    print(f"Healthy: {'yes' if payload['healthy'] else 'no'}")
    for action in payload.get("next_actions", []):
        print(f"Next: {action}")
    for limitation in payload.get("limitations", []):
        print(f"Limitation: {limitation}")


def _print_run_status(workspace: str, *, output_format: str) -> None:
    _print_status(
        get_documentation_run_status(workspace).to_dict(),
        output_format=output_format,
    )


def _prepare(args) -> None:
    allow_external = bool(getattr(args, "allow_external_src", False))
    source_root = _validate_evidence_root(
        getattr(args, "src_dir", None),
        label="--src-dir",
        allow_external=allow_external,
    )
    input_wiki_root = _validate_evidence_root(
        getattr(args, "input_wiki_dir", None),
        label="--input-wiki-dir",
        allow_external=allow_external,
    )
    intake = _intake_from_args(args)
    link_mode = "file" if getattr(args, "file_friendly", False) else args.link_mode
    prepare_documentation_run(
        args.workspace,
        baseline_strategy=_BASELINE_STRATEGIES[args.baseline],
        source_root=source_root,
        input_wiki_root=input_wiki_root,
        freshness_policy=args.wiki_freshness,
        site_name=args.site_name,
        helper_cache_root=args.helper_cache_dir,
        capture_root=args.capture_dir,
        trust_source_plugins=bool(args.trust_source_plugins),
        semantic_budget=args.semantic_budget,
        adjustment_loop_limit=args.adjustment_loop_limit,
        distribution_format=args.site_format,
        link_mode=link_mode,
        knowledge_mode=getattr(args, "knowledge_mode", "off"),
        knowledge_public_repository_identity=(
            getattr(args, "knowledge_public_repository_identity", None)
        ),
        refresh=bool(args.refresh),
        **intake,
    )
    _print_run_status(args.workspace, output_format=args.output_format)


def _status(args) -> None:
    _print_run_status(args.workspace, output_format=args.format)


def _packet(args) -> None:
    packet = build_documentation_agent_packet(args.workspace, stage=args.stage)
    if args.format == "json":
        print(packet.to_json(), end="")
    else:
        print(packet.to_markdown(), end="")


def _record_result(args) -> None:
    payload = _read_json_object(args.result, label="agent result")
    result = DocumentationAgentResult.from_dict(payload)
    record_documentation_agent_result(args.workspace, result)
    _print_run_status(args.workspace, output_format=args.format)


def _verify(args) -> None:
    report = verify_documentation_run(
        args.workspace,
        advance=not bool(args.no_advance),
    )
    payload = report.to_dict()
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Documentation verification: {'passed' if report.ok else 'failed'}")
        print(f"Run: {report.run_id}")
        print(f"State: {report.state}")
        if report.next_state:
            print(f"Advanced to: {report.next_state}")
        for check in report.checks:
            print(
                f"Check {check.get('check', 'unknown')}: "
                f"{'passed' if check.get('ok') else 'failed'}"
            )
        for limitation in report.limitations:
            print(f"Limitation: {limitation}")
    if not report.ok:
        raise SystemExit(1)


def _calibration_controller():
    # Keep the controller dependency scoped to the nested lifecycle handlers.
    from ..services import documentation_calibration_controller

    return documentation_calibration_controller


def _calibration_error_type() -> type[RuntimeError]:
    from ..services.documentation_calibration_controller import P0CalibrationError

    return P0CalibrationError


def _calibration_json_payload(value: object, *, label: str) -> dict[str, Any]:
    if isinstance(value, Mapping):
        payload = dict(value)
    else:
        to_dict = getattr(value, "to_dict", None)
        if not callable(to_dict):
            raise DocumentationRunError(f"{label} did not produce a JSON object.")
        payload = to_dict()
    if not isinstance(payload, dict):
        raise DocumentationRunError(f"{label} did not produce a JSON object.")
    return payload


def _bounded_calibration_json(
    value: object,
    *,
    label: str,
    max_bytes: int | None = None,
    canonical: bool = False,
) -> str:
    payload = _calibration_json_payload(value, label=label)
    try:
        rendered = (
            json.dumps(
                payload,
                allow_nan=False,
                ensure_ascii=False,
                indent=None if canonical else 2,
                separators=(",", ":") if canonical else None,
                sort_keys=True,
            )
            + "\n"
        )
    except (TypeError, ValueError) as exc:
        raise DocumentationRunError(f"{label} is not valid JSON: {exc}") from exc
    limit = _MAX_CALIBRATION_JSON_BYTES if max_bytes is None else max_bytes
    if len(rendered.encode("utf-8")) > limit:
        raise DocumentationRunError(f"{label} exceeds the {limit}-byte output limit.")
    return rendered


def _print_calibration_json(value: object, *, label: str) -> None:
    print(_bounded_calibration_json(value, label=label), end="")


def _require_distinct_stdin_inputs(*paths: str | None) -> None:
    if sum(path == "-" for path in paths) > 1:
        raise DocumentationRunError(
            "Only one calibration JSON input may read from stdin."
        )


def _calibration_prepare(args) -> None:
    controls = tuple(getattr(args, "control_workspace", ()) or ())
    if len(controls) != 2:
        raise DocumentationRunError(
            "--control-workspace must be specified exactly twice."
        )
    manifest = _read_calibration_json_object(
        args.execution_manifest,
        label="execution manifest",
    )
    controller = _calibration_controller()
    run = controller.prepare_calibration_run(
        args.root,
        control_workspaces=controls,
        execution_manifest=manifest,
    )
    _print_calibration_json(run, label="calibration run")


def _calibration_admit(args) -> None:
    _require_distinct_stdin_inputs(args.authority_grant, args.broker_attestation)
    authority = _read_calibration_json_object(
        args.authority_grant,
        label="authority grant",
    )
    attestation = (
        _read_calibration_json_object(
            args.broker_attestation,
            label="broker attestation",
        )
        if args.broker_attestation is not None
        else None
    )
    controller = _calibration_controller()
    run = controller.admit_calibration_run(
        args.root,
        authority_grant=authority,
        broker_attestation=attestation,
    )
    payload = _calibration_json_payload(run, label="calibration run")
    _print_calibration_json(payload, label="calibration run")
    if payload.get("state") in {"BLOCKED_NO_SHIP", "REJECT"}:
        raise SystemExit(1)


def _calibration_status(args) -> None:
    status = _calibration_controller().get_calibration_run_status(args.root)
    _print_calibration_json(status, label="calibration status")


def _calibration_packet(args) -> None:
    if args.output == "-":
        raise DocumentationRunError(
            "Calibration packets require an explicit file path, not stdout."
        )
    controller = _calibration_controller()
    output = controller.validate_p0_calibration_packet_output(
        args.root,
        args.output,
    )
    packet = controller.build_calibration_agent_packet(
        args.root,
        role=args.role,
    )
    rendered = _bounded_calibration_json(
        packet,
        label="calibration agent packet",
        max_bytes=_MAX_CALIBRATION_PACKET_BYTES,
        canonical=True,
    )
    output = controller.validate_p0_calibration_packet_output(args.root, output)
    try:
        atomic_write_private_bytes(output, rendered.encode("utf-8"))
    except OSError as exc:
        raise DocumentationRunError(
            f"Cannot write calibration agent packet {output}: {exc}"
        ) from exc


def _calibration_dispatch(args) -> None:
    receipt = _calibration_controller().dispatch_calibration_agent(
        args.root,
        role=args.role,
    )
    payload = _calibration_json_payload(receipt, label="calibration dispatch receipt")
    _print_calibration_json(payload, label="calibration dispatch receipt")
    if payload.get("status") != "complete":
        raise SystemExit(1)


def _calibration_record_result(args) -> None:
    _require_distinct_stdin_inputs(args.dispatch_receipt, args.result)
    receipt_payload = _read_calibration_json_object(
        args.dispatch_receipt,
        label="calibration dispatch receipt",
    )
    result_payload = _read_calibration_json_object(
        args.result,
        label="calibration agent result",
    )
    controller = _calibration_controller()
    receipt = controller.P0CalibrationDispatchReceipt.from_dict(receipt_payload)
    result = controller.P0CalibrationAgentResult.from_dict(result_payload)
    run = controller.record_calibration_agent_result(
        args.root,
        dispatch_receipt=receipt,
        result=result,
    )
    _print_calibration_json(run, label="calibration run")


def _calibration_verify(args) -> None:
    report = _calibration_controller().verify_calibration_run(
        args.root,
        advance=not bool(args.no_advance),
    )
    payload = _calibration_json_payload(report, label="calibration verification")
    print(
        _bounded_calibration_json(payload, label="calibration verification"),
        end="",
    )
    if not bool(payload.get("ok", False)):
        raise SystemExit(1)


def _calibration(args) -> None:
    handlers = {
        "prepare": _calibration_prepare,
        "admit": _calibration_admit,
        "status": _calibration_status,
        "packet": _calibration_packet,
        "dispatch": _calibration_dispatch,
        "record-result": _calibration_record_result,
        "verify": _calibration_verify,
    }
    action = getattr(args, "calibration_action", None)
    handler = handlers.get(action) if isinstance(action, str) else None
    if handler is None:
        raise DocumentationRunError("Missing calibration action.")
    try:
        handler(args)
    except _calibration_error_type() as exc:
        raise DocumentationRunError(str(exc)) from exc


def _assert_export_options(args) -> None:
    if args.builder_command is not None and not args.builder_command:
        raise DocumentationRunError("--builder-command requires at least one argument.")
    if args.builder_command is not None and not args.build:
        raise DocumentationRunError("--builder-command requires --build.")
    run = load_documentation_run(args.workspace)
    requested_format = getattr(args, "format", None)
    if requested_format and requested_format != run.publication.get("format"):
        raise DocumentationRunError(
            "Export format differs from the prepared run contract; rerun docs "
            "prepare with --refresh and the intended --site-format."
        )
    if args.file_friendly and run.publication.get("link_mode") != "file":
        raise DocumentationRunError(
            "--file-friendly was not selected when the run was prepared; rerun docs "
            "prepare with --refresh --file-friendly."
        )
    requested_knowledge_mode = getattr(args, "knowledge_mode", None)
    recorded_knowledge_mode = run.publication.get("knowledge_mode", "off")
    if (
        requested_knowledge_mode is not None
        and requested_knowledge_mode != recorded_knowledge_mode
    ):
        raise DocumentationRunError(
            "Export knowledge mode differs from the prepared run contract; rerun "
            "docs prepare with --refresh and the intended --knowledge-mode."
        )
    requested_public_identity = getattr(
        args,
        "knowledge_public_repository_identity",
        None,
    )
    if (
        requested_public_identity is not None
        and requested_public_identity
        != run.publication.get("knowledge_public_repository_identity")
    ):
        raise DocumentationRunError(
            "Export public repository identity differs from the prepared run "
            "contract; rerun docs prepare with --refresh and the intended "
            "--knowledge-public-repository-identity."
        )


def _export(args) -> None:
    _assert_export_options(args)
    report = export_documentation_run(
        args.workspace,
        build=bool(args.build),
        builder_command=args.builder_command,
        knowledge_mode=getattr(args, "knowledge_mode", None),
        knowledge_public_repository_identity=getattr(
            args,
            "knowledge_public_repository_identity",
            None,
        ),
    )
    if args.output_format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Documentation export verdict: {report.get('verdict', 'unknown')}")
        print(f"Run: {report.get('run_id', '')}")
        print(f"State: {report.get('state', '')}")
        for limitation in report.get("limitations", []):
            print(f"Limitation: {limitation}")
        handoff = report.get("deployment_handoff", {})
        if isinstance(handoff, dict) and handoff.get("instructions"):
            print(f"Handoff: {handoff['instructions']}")
    if report.get("verdict") == "blocked":
        raise SystemExit(1)


def run(args) -> None:
    """Dispatch one standalone documentation action."""

    action = getattr(args, "docs_action", None)
    handlers = {
        "prepare": _prepare,
        "status": _status,
        "packet": _packet,
        "record-result": _record_result,
        "verify": _verify,
        "export": _export,
        "calibration": _calibration,
    }
    handler = handlers.get(action) if isinstance(action, str) else None
    if handler is None:
        raise DocumentationRunError("Missing documentation action.")
    try:
        handler(args)
    except PathValidationError:
        raise
    except DocumentationRunError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
