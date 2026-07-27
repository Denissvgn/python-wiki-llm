"""Focused lifecycle tests for evidence-backed P0 calibration."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli.services import (
    documentation_calibration_controller as controller_module,
    documentation_calibration_host_broker as host_broker,
)
from llm_wiki_cli.services.contracts import (
    P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
    P0_CALIBRATION_AUTHORITY_GRANT_SCHEMA_VERSION,
    P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION,
    P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION,
    P0_CALIBRATION_ISOLATION_ATTESTATION_SCHEMA_VERSION,
)
from llm_wiki_cli.services.documentation_calibration_controller import (
    CALIBRATION_ROLES,
    P0CalibrationAgentResult,
    P0CalibrationDispatchReceipt,
    P0CalibrationIntegrityError,
    P0CalibrationSchemaError,
    P0CalibrationTransitionError,
    admit_p0_calibration_run,
    build_p0_calibration_agent_packet,
    dispatch_p0_calibration_agent,
    get_p0_calibration_run_status,
    prepare_p0_calibration_run,
    record_p0_calibration_agent_result,
    validate_p0_calibration_packet_output,
    verify_p0_calibration_run,
)
from llm_wiki_cli.services.documentation_run import prepare_documentation_run
from llm_wiki_cli.services.protected_artifacts import (
    ProtectedArtifactStore,
    canonical_json_bytes,
)


_HASH_A = "sha256:" + "a" * 64


class _HostBrokerAuthenticator:
    authenticator_id = "controller-test-host-authenticator-v1"

    def authenticate_attestation(
        self,
        *,
        cohort_id: str,
        authority_grant,
        execution_manifest,
        attestation,
        attestation_hash: str,
    ):
        del authority_grant, execution_manifest
        return host_broker.HostBrokerAuthenticationProof(
            proof_kind="attestation",
            authenticator_id=self.authenticator_id,
            broker_id=attestation["runtime"]["broker_id"],
            broker_session=attestation["authentication"]["reference"],
            principal="test-host-broker",
            reference="test-host-ipc-attestation",
            cohort_id=cohort_id,
            expires_at=attestation["expires_at"],
            authority_hash=attestation["authority_hash"],
            execution_manifest_hash=attestation["execution_manifest_hash"],
            evidence_bundle_hash=attestation["evidence_bundle_hash"],
            attestation_hash=attestation_hash,
        )

    def authenticate_receipt(
        self,
        *,
        cohort_id: str,
        execution_manifest,
        attestation,
        receipt,
        receipt_hash: str,
        result,
        result_hash: str,
    ):
        del execution_manifest, result
        return host_broker.HostBrokerAuthenticationProof(
            proof_kind="receipt",
            authenticator_id=self.authenticator_id,
            broker_id=attestation["runtime"]["broker_id"],
            broker_session=attestation["authentication"]["reference"],
            principal="test-host-broker",
            reference="test-host-ipc-receipt",
            cohort_id=cohort_id,
            expires_at=attestation["expires_at"],
            authority_hash=attestation["authority_hash"],
            execution_manifest_hash=attestation["execution_manifest_hash"],
            evidence_bundle_hash=attestation["evidence_bundle_hash"],
            attestation_hash=_sha256_json(attestation),
            receipt_hash=receipt_hash,
            result_hash=result_hash,
            packet_hash=receipt["packet_hash"],
            idempotency_key=receipt["idempotency_key"],
            route_id=receipt["route_id"],
            role=receipt["role"],
            attempt=receipt["attempt"],
        )


@pytest.fixture(autouse=True)
def _install_test_host_broker_authenticator():
    with host_broker.use_p0_calibration_host_broker_authenticator(
        _HostBrokerAuthenticator()
    ):
        yield


def _timestamp(delta: timedelta) -> str:
    return (
        (datetime.now(timezone.utc) + delta)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _sha256_json(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _external_manifest() -> dict:
    return {
        "schema_version": P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION,
        "profile": "external_authorized",
        "roles": list(CALIBRATION_ROLES),
        "budgets": {
            "max_concurrent_workers": 3,
            "max_attempts_per_role": 2,
            "max_total_calls": 8,
            "max_packet_bytes": 1048576,
            "max_result_bytes": 1048576,
        },
        "oci": None,
        "external_routes": [
            {
                "route_id": "host-broker-1",
                "recipient": "credential-free-model-route",
                "max_calls": 8,
                "max_request_bytes": 1048576,
                "max_response_bytes": 1048576,
            }
        ],
    }


def _local_manifest(tmp_path: Path) -> dict:
    runtime = tmp_path / ("docker.exe" if os.name == "nt" else "docker")
    runtime.write_bytes(b"synthetic OCI executable")
    if os.name != "nt":
        runtime.chmod(0o700)
    return {
        "schema_version": P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION,
        "profile": "local_no_egress",
        "roles": list(CALIBRATION_ROLES),
        "budgets": {
            "max_concurrent_workers": 3,
            "max_attempts_per_role": 2,
            "max_total_calls": 8,
            "max_packet_bytes": 1048576,
            "max_result_bytes": 1048576,
        },
        "oci": {
            "runtime": "docker",
            "executable": str(runtime),
            "executable_sha256": "sha256:"
            + hashlib.sha256(runtime.read_bytes()).hexdigest(),
            "worker": {
                "image": "example/worker@sha256:" + "1" * 64,
                "entrypoint": ["/opt/worker"],
            },
            "probe": {
                "image": "example/probe@sha256:" + "2" * 64,
                "entrypoint": ["/opt/probe"],
            },
            "user": "1000:1000",
            "resources": {
                "pids_limit": 32,
                "memory_bytes": 536870912,
                "cpu_millis": 750,
                "tmpfs_bytes": 16777216,
            },
            "timeout_seconds": 120,
            "termination_grace_seconds": 5,
            "max_packet_bytes": 1048576,
            "output_limits": {
                "stdout_bytes": 8192,
                "stderr_bytes": 4096,
                "result_bytes": 1048576,
            },
        },
        "external_routes": [],
    }


def _install_passing_local_probe(monkeypatch, tmp_path: Path):
    from llm_wiki_cli.services import documentation_calibration_broker as broker

    sentinels = tuple(
        broker.OciProbeSentinel(
            probe=probe,
            sentinel_id=f"{probe}-sentinel",
            host_path=str((tmp_path / f"{probe}.sentinel").resolve()),
            content_sha256=(
                "sha256:" + hashlib.sha256(probe.encode("utf-8")).hexdigest()
            ),
            content_bytes=len(probe.encode("utf-8")),
        )
        for probe in broker.FILESYSTEM_ISOLATION_PROBES
    )
    challenge = "ab" * 32
    challenge_bytes = bytes.fromhex(challenge)
    response = broker._network_canary_response(challenge)
    canary = broker.OciNetworkCanaryBinding(
        canary_id="canary-synthetic",
        host="127.0.0.1",
        port=65535,
        challenge=challenge,
        challenge_sha256=("sha256:" + hashlib.sha256(challenge_bytes).hexdigest()),
        response_sha256="sha256:" + hashlib.sha256(response).hexdigest(),
        control_sha256=(
            "sha256:"
            + hashlib.sha256(
                b"host-control\x00" + challenge_bytes + response
            ).hexdigest()
        ),
    )

    @contextmanager
    def synthetic_environment(*, probe_id):
        del probe_id
        yield SimpleNamespace(
            sentinels=sentinels,
            network_canary=canary,
            post_control_network_connections=0,
            assert_ready=lambda: None,
        )

    def passing_probe(config, *, request_path, output_dir, **_kwargs):
        del output_dir
        request = broker.OciAdmissionProbeRequest.from_dict(
            json.loads(Path(request_path).read_text(encoding="utf-8"))
        )

        def denied_event(probe):
            target_id, target_sha256 = request.target_binding(probe)
            if probe in broker.FILESYSTEM_ISOLATION_PROBES:
                evidence = {
                    "read_succeeded": False,
                    "observed_sha256": None,
                }
            elif probe == "network_egress":
                evidence = {
                    "canary_connected": False,
                    "non_loopback_interfaces": [],
                    "default_route": False,
                }
            elif probe == "output_write_bound":
                evidence = {
                    "limit_bytes": request.output_limit_bytes,
                    "attempted_bytes": request.output_limit_bytes + 1,
                    "oversize_write_succeeded": False,
                    "sibling_write_succeeded": False,
                    "observed_size": 0,
                }
            else:
                evidence = {"connected_targets": []}
            return {
                "probe": probe,
                "target_id": target_id,
                "target_sha256": target_sha256,
                "attempted": True,
                "outcome": "denied",
                "evidence": evidence,
                "detail": "denied by synthetic qualification runner",
            }

        result = broker.OciAdmissionProbeResult.from_dict(
            {
                "schema_version": ("llm-wiki-p0-calibration-isolation-probe-result/v1"),
                "cohort_id": request.cohort_id,
                "probe_id": request.probe_id,
                "request_hash": request.request_hash,
                "image_digest": config.probe.digest,
                "access_events": [
                    denied_event(probe) for probe in broker.REQUIRED_ISOLATION_PROBES
                ],
                "status": "passed",
            }
        )
        return SimpleNamespace(
            passed=True,
            execution_status="complete",
            request_hash=request.request_hash,
            result_hash=_sha256_json(result.to_dict()),
            result=result,
            process=broker.BoundedProcessResult.completed(),
            command_hash=_HASH_A,
            cleanup_status="not_required",
            error=None,
        )

    monkeypatch.setattr(
        broker,
        "create_oci_admission_probe_environment",
        synthetic_environment,
    )
    monkeypatch.setattr(broker, "execute_oci_admission_probe", passing_probe)
    return broker


def _prepare_controls(
    tmp_path: Path,
    *,
    readme_text: str | None = None,
    app_text: str | None = None,
) -> tuple[Path, Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "README.md").write_text(
        readme_text
        if readme_text is not None
        else "# Example\n\nA bounded command-line application for operators.\n",
        encoding="utf-8",
    )
    (source / "app.py").write_text(
        app_text
        if app_text is not None
        else (
            '"""Example application."""\n\n'
            "def run() -> str:\n"
            '    """Run the supported operation."""\n'
            '    return "ok"\n\n'
            "def main() -> None:\n"
            "    print(run())\n\n"
            'if __name__ == "__main__":\n'
            "    main()\n"
        ),
        encoding="utf-8",
    )
    workspaces = []
    for name in ("control-a", "control-b"):
        workspace = tmp_path / name
        run = prepare_documentation_run(
            workspace,
            source_root=source,
            site_name="Example",
            project_purpose="Help operators run Example.",
            audiences=["operator"],
            audience_intent={"operator": "run the supported operation"},
        )
        assert run.state == "baseline_ready"
        workspaces.append(workspace)
    return source, workspaces[0], workspaces[1]


def _add_matching_canonical_wiki_inputs(*workspaces: Path) -> tuple[Path, ...]:
    paths = []
    for workspace in workspaces:
        wiki = workspace / "wiki"
        wiki.mkdir(exist_ok=True)
        path = wiki / "Architecture.md"
        path.write_text(
            "# Architecture\n\nThe bounded command is the primary operator entrypoint.\n",
            encoding="utf-8",
        )
        paths.append(path)
    return tuple(paths)


def _prepare_external_cohort(tmp_path: Path):
    _source, control_a, control_b = _prepare_controls(tmp_path)
    root = tmp_path / "calibration"
    run = prepare_p0_calibration_run(
        root,
        control_workspaces=[control_a, control_b],
        execution_manifest=_external_manifest(),
    )
    assert run.state == "BASELINE_FROZEN"
    return root, run


def _authority(run, manifest: dict | None = None) -> dict:
    manifest = _external_manifest() if manifest is None else manifest
    return {
        "schema_version": P0_CALIBRATION_AUTHORITY_GRANT_SCHEMA_VERSION,
        "grant_id": "grant-001",
        "cohort_id": run.cohort_id,
        "decision_scope": "p0_policy_default",
        "profile": manifest["profile"],
        "evidence_bundle_hash": run.payload["evidence_bundle_hash"],
        "execution_manifest_hash": run.payload["execution_manifest_hash"],
        "allowed_roles": list(CALIBRATION_ROLES),
        "budgets": manifest["budgets"],
        "external_routes": manifest["external_routes"],
        "issued_at": _timestamp(timedelta(minutes=-1)),
        "expires_at": _timestamp(timedelta(hours=2)),
        "revocation": {"reference": "operator-revocations/001", "revoked": False},
        "authentication": {
            "method": "host-protected-operator",
            "principal": "release-operator",
            "reference": "approval-001",
            "verified_by_host": True,
        },
    }


def _attestation(
    run,
    authority: dict,
    manifest: dict | None = None,
) -> dict:
    manifest = _external_manifest() if manifest is None else manifest
    return {
        "schema_version": P0_CALIBRATION_ISOLATION_ATTESTATION_SCHEMA_VERSION,
        "attestation_id": "attestation-001",
        "cohort_id": run.cohort_id,
        "profile": "external_authorized",
        "authority_hash": _sha256_json(authority),
        "execution_manifest_hash": run.payload["execution_manifest_hash"],
        "evidence_bundle_hash": run.payload["evidence_bundle_hash"],
        "issued_at": _timestamp(timedelta(minutes=-1)),
        "expires_at": _timestamp(timedelta(hours=1)),
        "runtime": {
            "kind": "external_broker",
            "broker_id": "broker-001",
            "runtime_identity": "broker-runtime-v1",
            "image_identity": "model-runtime@sha256:" + "1" * 64,
        },
        "access_audit_hash": _HASH_A,
        "routes": manifest["external_routes"],
        "authentication": {
            "method": "host-protected-external-broker",
            "principal": "broker-001",
            "reference": "broker-authentication-001",
            "verified_by_host": True,
        },
    }


def _admit_external_cohort(tmp_path: Path):
    root, run = _prepare_external_cohort(tmp_path)
    authority = _authority(run)
    admitted = admit_p0_calibration_run(
        root,
        authority_grant=authority,
        broker_attestation=_attestation(run, authority),
    )
    assert admitted.state == "ADMISSION_AUTHORIZED"
    return root, admitted


def _claim(claim_id: str, citation_id: str, statement: str) -> dict:
    return {
        "claim_id": claim_id,
        "statement": statement,
        "citations": [citation_id],
    }


def _semantic_payload(prefix: str, citation_id: str, *, verifier: bool) -> dict:
    payload = {
        "purpose": _claim(
            f"{prefix}-purpose",
            citation_id,
            "The project exposes a bounded supported operation.",
        ),
        "audiences": [_claim(f"{prefix}-audience", citation_id, "Operators")],
        "capabilities": [
            _claim(f"{prefix}-capability", citation_id, "Run the operation")
        ],
        "tasks": [_claim(f"{prefix}-task", citation_id, "Invoke run")],
        "journeys": [
            _claim(
                f"{prefix}-journey",
                citation_id,
                "An operator invokes and observes the operation.",
            )
        ],
        "contradictions": [],
        "unknowns": [],
        "limitations": [
            _claim(
                f"{prefix}-limitation",
                citation_id,
                "Runtime behavior beyond the cited source is unknown.",
            )
        ],
    }
    if verifier:
        payload["primary_journey_claim_id"] = f"{prefix}-journey"
        payload["accepted_claims"] = [
            _claim(
                f"{prefix}-accepted",
                citation_id,
                "The supported operation is source-backed.",
            )
        ]
        payload["rejected_claims"] = []
    return payload


def _external_result_and_receipt(root: Path, packet, *, verifier: bool):
    run_payload = json.loads((root / "run.json").read_text(encoding="utf-8"))
    citation_id = packet.payload["evidence_bundle"]["source_excerpts"][0]["citation_id"]
    semantic = _semantic_payload(packet.payload["role"], citation_id, verifier=verifier)
    if verifier:
        proposal_claim_ids = []
        for record in packet.payload["intake_proposals"]:
            proposal = record["proposal"]
            proposal_claim_ids.append(
                f"{record['role']}/{proposal['purpose']['claim_id']}"
            )
            for field_name in (
                "audiences",
                "capabilities",
                "tasks",
                "journeys",
                "contradictions",
                "unknowns",
                "limitations",
            ):
                proposal_claim_ids.extend(
                    f"{record['role']}/{claim['claim_id']}"
                    for claim in proposal[field_name]
                )
        semantic["accepted_claims"][0]["proposal_claim_ids"] = proposal_claim_ids
    result = {
        "schema_version": P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
        "result_id": str(uuid.uuid4()),
        "cohort_id": packet.payload["cohort_id"],
        "packet_id": packet.payload["packet_id"],
        "role": packet.payload["role"],
        "attempt": packet.payload["attempt"],
        "packet_hash": _sha256_json(packet.payload),
        "idempotency_key": packet.payload["idempotency_key"],
        "status": "complete",
        ("verification" if verifier else "proposal"): semantic,
    }
    response_hash = _sha256_json(result)
    generation = run_payload["roles"][packet.payload["role"]]["packet_generation"]
    transition = json.loads(
        (root / "transitions" / f"{generation:08d}.json").read_text(encoding="utf-8")
    )
    material = {
        "schema_version": P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION,
        "cohort_id": packet.payload["cohort_id"],
        "generation": generation,
        "head_transition_hash": transition["transition_hash"],
        "role": packet.payload["role"],
        "attempt": packet.payload["attempt"],
        "idempotency_key": packet.payload["idempotency_key"],
        "packet_id": packet.payload["packet_id"],
        "packet_hash": _sha256_json(packet.payload),
        "authority_hash": packet.payload["authority_hash"],
        "attestation_hash": packet.payload["attestation_hash"],
        "access_audit_hash": _HASH_A,
        "broker_id": "broker-001",
        "route_id": "host-broker-1",
        "runtime_identity": "broker-runtime-v1",
        "image_identity": "model-runtime@sha256:" + "1" * 64,
        "started": True,
        "status": "complete",
        "response_hash": response_hash,
        "response_bytes": len(canonical_json_bytes(result)),
    }
    receipt_hash = _sha256_json(material)
    receipt = {
        **material,
        "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
        "receipt_hash": receipt_hash,
    }
    return (
        P0CalibrationAgentResult.from_dict(result),
        P0CalibrationDispatchReceipt.from_dict(receipt),
    )


def _external_failure_result_and_receipt(
    root: Path,
    packet,
    *,
    reason_code: str = "transport_inconclusive",
    dispatch_started: bool = True,
    message: str = "The authenticated broker could not reconcile the dispatch.",
):
    run_payload = json.loads((root / "run.json").read_text(encoding="utf-8"))
    result = {
        "schema_version": P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
        "result_id": str(uuid.uuid4()),
        "cohort_id": packet.payload["cohort_id"],
        "packet_id": packet.payload["packet_id"],
        "role": packet.payload["role"],
        "attempt": packet.payload["attempt"],
        "packet_hash": _sha256_json(packet.payload),
        "idempotency_key": packet.payload["idempotency_key"],
        "status": "dispatch_failed",
        "failure": {
            "reason_code": reason_code,
            "message": message,
            "dispatch_started": dispatch_started,
            "retry_allowed": False,
        },
    }
    generation = run_payload["roles"][packet.payload["role"]]["packet_generation"]
    transition = json.loads(
        (root / "transitions" / f"{generation:08d}.json").read_text(encoding="utf-8")
    )
    material = {
        "schema_version": P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION,
        "cohort_id": packet.payload["cohort_id"],
        "generation": generation,
        "head_transition_hash": transition["transition_hash"],
        "role": packet.payload["role"],
        "attempt": packet.payload["attempt"],
        "idempotency_key": packet.payload["idempotency_key"],
        "packet_id": packet.payload["packet_id"],
        "packet_hash": _sha256_json(packet.payload),
        "authority_hash": packet.payload["authority_hash"],
        "attestation_hash": packet.payload["attestation_hash"],
        "access_audit_hash": _HASH_A,
        "broker_id": "broker-001",
        "route_id": "host-broker-1",
        "runtime_identity": "broker-runtime-v1",
        "image_identity": "model-runtime@sha256:" + "1" * 64,
        "started": dispatch_started,
        "status": reason_code,
        "response_hash": _sha256_json(result),
        "response_bytes": len(canonical_json_bytes(result)),
    }
    receipt_hash = _sha256_json(material)
    receipt = {
        **material,
        "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
        "receipt_hash": receipt_hash,
    }
    return (
        P0CalibrationAgentResult.from_dict(result),
        P0CalibrationDispatchReceipt.from_dict(receipt),
    )


def test_prepare_requires_reproduced_complete_priority_blind_controls(
    tmp_path: Path,
):
    root, run = _prepare_external_cohort(tmp_path)

    assert run.state == "BASELINE_FROZEN"
    assert run.payload["population"]["total"] == 1
    bundle = json.loads((root / "evidence" / "bundle.json").read_text(encoding="utf-8"))
    encoded = json.dumps(bundle, sort_keys=True)
    assert bundle["priority_blind"] is True
    assert bundle["population"]["total"] == 1
    assert len(bundle["source_excerpts"]) == 1
    assert str(tmp_path) not in encoded
    assert '"current_priority"' not in encoded
    assert '"candidate_score"' not in encoded
    controls = [
        json.loads(
            (root / "baseline" / f"control-{index:02d}.json").read_text(
                encoding="utf-8"
            )
        )
        for index in (1, 2)
    ]
    assert controls[0]["documentation_run_id"]
    assert controls[0]["documentation_run_id"] != controls[1]["documentation_run_id"]


def test_prepare_rejects_copied_documentation_run_identity(tmp_path: Path):
    _source, control_a, control_b = _prepare_controls(tmp_path)
    first_run = json.loads(
        (control_a / ".llm-wiki-docs" / "run.json").read_text(encoding="utf-8")
    )
    second_run_path = control_b / ".llm-wiki-docs" / "run.json"
    second_run = json.loads(second_run_path.read_text(encoding="utf-8"))
    second_run["run_id"] = first_run["run_id"]
    second_run_path.write_bytes(canonical_json_bytes(second_run))

    with pytest.raises(
        P0CalibrationIntegrityError,
        match="independently prepared documentation run identities",
    ):
        prepare_p0_calibration_run(
            tmp_path / "calibration",
            control_workspaces=[control_a, control_b],
            execution_manifest=_external_manifest(),
        )


def test_packet_output_rejects_every_frozen_or_linked_root(tmp_path: Path):
    root, _run = _prepare_external_cohort(tmp_path)
    outside = tmp_path / "packet-output"
    outside.mkdir()

    assert (
        validate_p0_calibration_packet_output(root, outside / "intake-a.json")
        == (outside / "intake-a.json").resolve()
    )

    for forbidden in (
        root / "packet.json",
        tmp_path / "source" / "packet.json",
        tmp_path / "control-a" / "packet.json",
        Path(__file__).resolve().parent / "packet.json",
    ):
        with pytest.raises(P0CalibrationIntegrityError, match="must remain outside"):
            validate_p0_calibration_packet_output(root, forbidden)

    target = outside / "target.json"
    target.write_text("{}\n", encoding="utf-8")
    linked = outside / "linked.json"
    try:
        linked.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"file symlinks are unavailable: {exc}")
    with pytest.raises(P0CalibrationIntegrityError, match="symlink|reparse"):
        validate_p0_calibration_packet_output(root, linked)


def test_expired_authority_blocks_without_admission_or_packet(tmp_path: Path):
    root, run = _prepare_external_cohort(tmp_path)
    authority = _authority(run)
    authority["expires_at"] = _timestamp(timedelta(seconds=-1))

    blocked = admit_p0_calibration_run(root, authority_grant=authority)

    assert blocked.state == "BLOCKED_NO_SHIP"
    assert blocked.payload["decision_scope"] == "p0_policy_default"
    assert not (root / "packets").exists()
    assert get_p0_calibration_run_status(root).terminal is True


def test_status_rejects_source_mutation_before_admission(tmp_path: Path):
    root, _run = _prepare_external_cohort(tmp_path)
    (tmp_path / "source" / "app.py").write_text(
        "def changed_before_status() -> None:\n    pass\n",
        encoding="utf-8",
    )

    status = get_p0_calibration_run_status(root)

    assert status.state == "REJECT"
    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert snapshot["terminal_reason_codes"] == ["source_or_control_mutation"]


def test_admission_rejects_source_mutation_before_authority_or_probe(
    tmp_path: Path,
):
    root, run = _prepare_external_cohort(tmp_path)
    authority = _authority(run)
    attestation = _attestation(run, authority)
    (tmp_path / "source" / "app.py").write_text(
        "def changed_before_admission() -> None:\n    pass\n",
        encoding="utf-8",
    )

    rejected = admit_p0_calibration_run(
        root,
        authority_grant=authority,
        broker_attestation=attestation,
    )

    assert rejected.state == "REJECT"
    assert rejected.payload["authority_hash"] is None
    assert "authority_grant" not in rejected.payload["artifacts"]


def test_self_asserted_external_attestation_cannot_authenticate_itself(
    tmp_path: Path,
):
    root, run = _prepare_external_cohort(tmp_path)
    authority = _authority(run)
    token = host_broker._HOST_BROKER_AUTHENTICATOR.set(None)
    try:
        blocked = admit_p0_calibration_run(
            root,
            authority_grant=authority,
            broker_attestation=_attestation(run, authority),
        )
    finally:
        host_broker._HOST_BROKER_AUTHENTICATOR.reset(token)

    assert blocked.state == "BLOCKED_NO_SHIP"
    assert blocked.payload["terminal_reason_codes"] == [
        "external_broker_attestation_invalid"
    ]
    assert not (root / "packets").exists()


def test_external_attestation_proof_binding_mismatch_blocks(
    tmp_path: Path,
):
    class _WrongCohortAuthenticator(_HostBrokerAuthenticator):
        def authenticate_attestation(self, **kwargs):
            return replace(
                super().authenticate_attestation(**kwargs),
                cohort_id="another-cohort",
            )

    root, run = _prepare_external_cohort(tmp_path)
    authority = _authority(run)
    with host_broker.use_p0_calibration_host_broker_authenticator(
        _WrongCohortAuthenticator()
    ):
        blocked = admit_p0_calibration_run(
            root,
            authority_grant=authority,
            broker_attestation=_attestation(run, authority),
        )

    assert blocked.state == "BLOCKED_NO_SHIP"
    assert (
        "external_broker_attestation_invalid"
        in blocked.payload["terminal_reason_codes"]
    )


def test_status_blocks_when_admitted_authority_is_no_longer_fresh(
    tmp_path: Path,
    monkeypatch,
):
    root, _run = _admit_external_cohort(tmp_path)
    monkeypatch.setattr(
        controller_module,
        "_authority_freshness_failure",
        lambda _store, _run: "Authority expired during status verification.",
    )

    status = get_p0_calibration_run_status(root)

    assert status.state == "BLOCKED_NO_SHIP"
    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert snapshot["terminal_reason_codes"] == ["authority_no_longer_valid"]


def test_status_rejects_source_mutation_after_admission(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    source = tmp_path / "source" / "app.py"
    source.write_text(
        "def changed_after_admission() -> None:\n    pass\n",
        encoding="utf-8",
    )

    status = get_p0_calibration_run_status(root)

    assert status.state == "REJECT"
    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert snapshot["terminal_reason_codes"] == ["source_or_control_mutation"]


def test_admission_replay_rejects_source_mutation_after_admission(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    authority = json.loads(
        (root / "authority" / "grant-grant-001.json").read_text(encoding="utf-8")
    )
    (tmp_path / "source" / "app.py").write_text(
        "def changed_before_admission_replay() -> None:\n    pass\n",
        encoding="utf-8",
    )

    replay = admit_p0_calibration_run(root, authority_grant=authority)

    assert replay.state == "REJECT"
    assert replay.payload["terminal_reason_codes"] == ["source_or_control_mutation"]


@pytest.mark.parametrize("checkpoint", ["status", "admit", "dispatch"])
def test_canonical_wiki_input_mutation_rejects_at_every_action_gate(
    tmp_path: Path,
    monkeypatch,
    checkpoint: str,
):
    _source, control_a, control_b = _prepare_controls(tmp_path)
    wiki_a, _wiki_b = _add_matching_canonical_wiki_inputs(control_a, control_b)
    manifest = (
        _local_manifest(tmp_path) if checkpoint == "dispatch" else _external_manifest()
    )
    root = tmp_path / "calibration"
    run = prepare_p0_calibration_run(
        root,
        control_workspaces=[control_a, control_b],
        execution_manifest=manifest,
    )
    control_record = json.loads(
        (root / "baseline" / "control-01.json").read_text(encoding="utf-8")
    )
    assert any(
        item["path"] == "wiki/Architecture.md"
        for item in control_record["documentation_inputs"]["selected"]
    )
    assert str(tmp_path) not in json.dumps(control_record)

    if checkpoint == "dispatch":
        _install_passing_local_probe(monkeypatch, tmp_path)
        admitted = admit_p0_calibration_run(
            root,
            authority_grant=_authority(run, manifest),
        )
        assert admitted.state == "ADMISSION_AUTHORIZED"
        build_p0_calibration_agent_packet(root, role="intake-a")

    wiki_a.write_text(
        "# Architecture\n\nThis control changed after the calibration freeze.\n",
        encoding="utf-8",
    )

    if checkpoint == "status":
        assert get_p0_calibration_run_status(root).state == "REJECT"
    elif checkpoint == "admit":
        authority = _authority(run)
        rejected = admit_p0_calibration_run(
            root,
            authority_grant=authority,
            broker_attestation=_attestation(run, authority),
        )
        assert rejected.state == "REJECT"
    else:
        with pytest.raises(P0CalibrationIntegrityError, match="documentation_inputs"):
            dispatch_p0_calibration_agent(root, role="intake-a")

    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert snapshot["state"] == "REJECT"
    assert snapshot["terminal_reason_codes"] == ["source_or_control_mutation"]


def test_external_admission_rechecks_controls_after_host_authentication(
    tmp_path: Path,
):
    source, control_a, control_b = _prepare_controls(tmp_path)
    root = tmp_path / "calibration"
    run = prepare_p0_calibration_run(
        root,
        control_workspaces=[control_a, control_b],
        execution_manifest=_external_manifest(),
    )
    authority = _authority(run)

    class _MutatingAuthenticator(_HostBrokerAuthenticator):
        def authenticate_attestation(self, **kwargs):
            proof = super().authenticate_attestation(**kwargs)
            (source / "app.py").write_text(
                "def changed_during_broker_authentication() -> None:\n    pass\n",
                encoding="utf-8",
            )
            return proof

    with host_broker.use_p0_calibration_host_broker_authenticator(
        _MutatingAuthenticator()
    ):
        rejected = admit_p0_calibration_run(
            root,
            authority_grant=authority,
            broker_attestation=_attestation(run, authority),
        )

    assert rejected.state == "REJECT"
    assert rejected.payload["terminal_reason_codes"] == ["source_or_control_mutation"]
    assert not (root / "authority" / "admission.json").exists()


def test_external_admission_rechecks_authority_after_host_authentication(
    tmp_path: Path,
    monkeypatch,
):
    root, run = _prepare_external_cohort(tmp_path)
    authority = _authority(run)
    monkeypatch.setattr(
        controller_module,
        "_pre_admission_authority_freshness_failure",
        lambda _store, _run: "Authority expired during broker authentication.",
    )

    blocked = admit_p0_calibration_run(
        root,
        authority_grant=authority,
        broker_attestation=_attestation(run, authority),
    )

    assert blocked.state == "BLOCKED_NO_SHIP"
    assert blocked.payload["terminal_reason_codes"] == ["authority_no_longer_valid"]
    assert not (root / "authority" / "admission.json").exists()


@pytest.mark.parametrize(
    ("change_replayed_grant", "expected_state"),
    [(False, "ADMISSION_AUTHORIZED"), (True, "REJECT")],
)
def test_admission_resumes_from_one_frozen_authority_without_rewriting_it(
    tmp_path: Path,
    monkeypatch,
    change_replayed_grant: bool,
    expected_state: str,
):
    root, run = _prepare_external_cohort(tmp_path)
    authority = _authority(run)
    attestation = _attestation(run, authority)
    real_admit_external = controller_module._admit_external_broker

    def interrupt_after_authority(*_args, **_kwargs):
        raise KeyboardInterrupt("process stopped after authority freeze")

    monkeypatch.setattr(
        controller_module,
        "_admit_external_broker",
        interrupt_after_authority,
    )
    with pytest.raises(KeyboardInterrupt, match="after authority freeze"):
        admit_p0_calibration_run(
            root,
            authority_grant=authority,
            broker_attestation=attestation,
        )

    grant_path = root / "authority" / "grant-grant-001.json"
    original_grant_bytes = grant_path.read_bytes()
    frozen = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert frozen["state"] == "BASELINE_FROZEN"
    assert frozen["authority_hash"] == _sha256_json(authority)
    assert "admission_probe_request" not in frozen["artifacts"]

    monkeypatch.setattr(
        controller_module,
        "_admit_external_broker",
        real_admit_external,
    )
    replayed_authority = json.loads(json.dumps(authority))
    if change_replayed_grant:
        replayed_authority["authentication"]["reference"] = "different-approval"
    resumed = admit_p0_calibration_run(
        root,
        authority_grant=replayed_authority,
        broker_attestation=attestation,
    )

    assert resumed.state == expected_state
    assert grant_path.read_bytes() == original_grant_bytes
    events = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((root / "transitions").glob("*.json"))
    ]
    assert sum(event["event_type"] == "authority_validated" for event in events) == 1
    if change_replayed_grant:
        assert resumed.payload["terminal_reason_codes"] == [
            "authority_replay_bytes_changed"
        ]


def test_external_intake_freezes_without_labels_or_default_change(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)

    for role in CALIBRATION_ROLES[:3]:
        packet = build_p0_calibration_agent_packet(root, role=role)
        result, receipt = _external_result_and_receipt(root, packet, verifier=False)
        record_p0_calibration_agent_result(
            root, dispatch_receipt=receipt, result=result
        )

    verifier_packet = build_p0_calibration_agent_packet(root, role="verifier")
    verifier_result, verifier_receipt = _external_result_and_receipt(
        root, verifier_packet, verifier=True
    )
    record_p0_calibration_agent_result(
        root,
        dispatch_receipt=verifier_receipt,
        result=verifier_result,
    )

    preview = verify_p0_calibration_run(root, advance=False)
    assert preview.ok is True
    assert preview.payload["advanced"] is False
    report = verify_p0_calibration_run(root)

    assert report.ok is True
    assert report.payload["advanced"] is True
    assert get_p0_calibration_run_status(root).state == "INTAKE_FROZEN"
    frozen = json.loads(
        (root / "intake" / "frozen-intake.json").read_text(encoding="utf-8")
    )
    oracle = json.loads(
        (root / "intake" / "task-oracle.json").read_text(encoding="utf-8")
    )
    optimizer = json.loads(
        (root / "intake" / "optimizer-search-contract.json").read_text(encoding="utf-8")
    )
    assert frozen["contains_labels"] is False
    assert frozen["contains_candidate_policy"] is False
    assert len(oracle["cases"]) == 1
    assert all("label" not in case for case in oracle["cases"])
    assert oracle["primary_journey_claim_id"] == oracle["primary_journey"]["claim_id"]
    assert oracle["primary_journey"] in oracle["journeys"]
    assert "weights" not in optimizer
    assert "scores" not in optimizer
    assert "candidate_policy" not in optimizer


def test_early_verify_with_pending_roles_is_read_only_and_ineligible(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    build_p0_calibration_agent_packet(root, role="intake-a")
    before_snapshot = (root / "run.json").read_bytes()
    before_transitions = sorted((root / "transitions").glob("*.json"))

    report = verify_p0_calibration_run(root)

    assert report.ok is False
    assert report.payload["eligible"] is False
    assert report.payload["advanced"] is False
    assert report.payload["next_state"] is None
    assert (root / "run.json").read_bytes() == before_snapshot
    assert sorted((root / "transitions").glob("*.json")) == before_transitions
    assert get_p0_calibration_run_status(root).state == "INTAKE_OPEN"


def test_semantic_result_gets_only_one_fresh_context_attempt(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    result, receipt = _external_result_and_receipt(root, packet, verifier=False)
    result.payload["proposal"]["purpose"]["citations"] = ["citation-forged"]
    material = dict(receipt.payload)
    material["response_hash"] = _sha256_json(result.payload)
    material["response_bytes"] = len(canonical_json_bytes(result.payload))
    material.pop("receipt_id")
    material.pop("receipt_hash")
    receipt_hash = _sha256_json(material)
    replacement = P0CalibrationDispatchReceipt.from_dict(
        {
            **material,
            "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
            "receipt_hash": receipt_hash,
        }
    )

    with pytest.raises(P0CalibrationSchemaError, match="Semantic result"):
        record_p0_calibration_agent_result(
            root, dispatch_receipt=replacement, result=result
        )

    status = get_p0_calibration_run_status(root)
    assert status.state == "INTAKE_OPEN"
    result_id_path = root / "intake" / "result-ids" / f"{result.result_id}.json"
    invalid_result_paths = list(
        (root / "intake" / "intake-a").glob("*-invalid-result.json")
    )
    assert result_id_path.read_bytes() == canonical_json_bytes(result.payload)
    assert len(invalid_result_paths) == 1
    assert invalid_result_paths[0].read_bytes() == canonical_json_bytes(result.payload)
    retry = build_p0_calibration_agent_packet(root, role="intake-a")
    assert retry.payload["attempt"] == 2
    assert retry.payload["packet_id"] != packet.payload["packet_id"]
    retry_snapshot = (root / "run.json").read_bytes()
    retry_transitions = sorted((root / "transitions").glob("*.json"))

    pending_retry = verify_p0_calibration_run(root)

    assert pending_retry.payload["eligible"] is False
    assert pending_retry.payload["advanced"] is False
    assert (root / "run.json").read_bytes() == retry_snapshot
    assert sorted((root / "transitions").glob("*.json")) == retry_transitions

    valid_result, valid_receipt = _external_result_and_receipt(
        root,
        retry,
        verifier=False,
    )
    valid_result.payload["result_id"] = result.result_id
    material = dict(valid_receipt.payload)
    material.pop("receipt_id")
    material.pop("receipt_hash")
    material["response_hash"] = _sha256_json(valid_result.payload)
    material["response_bytes"] = len(canonical_json_bytes(valid_result.payload))
    receipt_hash = _sha256_json(material)
    reused_receipt = P0CalibrationDispatchReceipt.from_dict(
        {
            **material,
            "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
            "receipt_hash": receipt_hash,
        }
    )

    with pytest.raises(P0CalibrationIntegrityError, match="Result id was reused"):
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=reused_receipt,
            result=valid_result,
        )
    assert get_p0_calibration_run_status(root).state == "REJECT"


def test_local_admission_requires_complete_denial_probe_results(
    tmp_path: Path, monkeypatch
):
    source, control_a, control_b = _prepare_controls(tmp_path)
    manifest = _local_manifest(tmp_path)
    root = tmp_path / "local-calibration"
    run = prepare_p0_calibration_run(
        root,
        control_workspaces=[control_a, control_b],
        execution_manifest=manifest,
    )
    broker = _install_passing_local_probe(monkeypatch, tmp_path)
    admitted = admit_p0_calibration_run(
        root,
        authority_grant=_authority(run, manifest),
    )

    assert admitted.state == "ADMISSION_AUTHORIZED"
    audit = json.loads(
        (root / "authority" / "access-audit.json").read_text(encoding="utf-8")
    )
    assert len(audit["events"]) == len(broker.REQUIRED_ISOLATION_PROBES)
    assert {event["outcome"] for event in audit["events"]} == {"denied"}
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    assert str(tmp_path) not in packet.to_json()
    result, receipt = _external_result_and_receipt(root, packet, verifier=False)
    with pytest.raises(
        P0CalibrationTransitionError,
        match="only be recorded by dispatch",
    ):
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=receipt,
            result=result,
        )
    (source / "app.py").write_text(
        "def changed_after_packet() -> None:\n    pass\n",
        encoding="utf-8",
    )
    with pytest.raises(P0CalibrationIntegrityError, match="source changed"):
        dispatch_p0_calibration_agent(root, role="intake-a")
    assert get_p0_calibration_run_status(root).state == "REJECT"


def test_interrupted_local_admission_probe_is_ledgered_and_blocks(
    tmp_path: Path,
    monkeypatch,
):
    source, control_a, control_b = _prepare_controls(tmp_path)
    del source
    manifest = _local_manifest(tmp_path)
    root = tmp_path / "interrupted-admission"
    run = prepare_p0_calibration_run(
        root,
        control_workspaces=[control_a, control_b],
        execution_manifest=manifest,
    )
    broker = _install_passing_local_probe(monkeypatch, tmp_path)

    def interrupt_probe(*_args, **_kwargs):
        raise KeyboardInterrupt("operator interrupted admission probe")

    monkeypatch.setattr(broker, "execute_oci_admission_probe", interrupt_probe)

    with pytest.raises(KeyboardInterrupt, match="interrupted admission"):
        admit_p0_calibration_run(
            root,
            authority_grant=_authority(run, manifest),
        )

    request_paths = list((root / "authority").glob("probe-request-*.json"))
    assert len(request_paths) == 1
    status = get_p0_calibration_run_status(root)
    assert status.state == "BLOCKED_NO_SHIP"
    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert snapshot["terminal_reason_codes"] == [
        "indeterminate_started_admission_probe"
    ]


def test_interrupted_local_dispatch_blocks_and_reraises(
    tmp_path: Path,
    monkeypatch,
):
    _source, control_a, control_b = _prepare_controls(tmp_path)
    manifest = _local_manifest(tmp_path)
    root = tmp_path / "interrupted-dispatch"
    run = prepare_p0_calibration_run(
        root,
        control_workspaces=[control_a, control_b],
        execution_manifest=manifest,
    )
    broker = _install_passing_local_probe(monkeypatch, tmp_path)
    admitted = admit_p0_calibration_run(
        root,
        authority_grant=_authority(run, manifest),
    )
    assert admitted.state == "ADMISSION_AUTHORIZED"
    build_p0_calibration_agent_packet(root, role="intake-a")

    def interrupt_dispatch(*_args, **_kwargs):
        raise KeyboardInterrupt("operator interrupted dispatch")

    monkeypatch.setattr(broker, "dispatch_oci_agent", interrupt_dispatch)

    with pytest.raises(KeyboardInterrupt, match="interrupted dispatch"):
        dispatch_p0_calibration_agent(root, role="intake-a")

    status = get_p0_calibration_run_status(root)
    assert status.state == "BLOCKED_NO_SHIP"
    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert snapshot["terminal_reason_codes"] == ["dispatch_inconclusive"]


def test_verifier_cannot_be_issued_before_three_intake_results(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)

    with pytest.raises(P0CalibrationTransitionError, match="all three"):
        build_p0_calibration_agent_packet(root, role="verifier")


def test_external_result_import_rejects_control_mutation_before_freeze(
    tmp_path: Path,
):
    root, _run = _admit_external_cohort(tmp_path)
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    result, receipt = _external_result_and_receipt(root, packet, verifier=False)
    (tmp_path / "source" / "app.py").write_text(
        "def changed_before_import() -> None:\n    pass\n",
        encoding="utf-8",
    )

    with pytest.raises(P0CalibrationIntegrityError, match="source changed"):
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=receipt,
            result=result,
        )

    assert get_p0_calibration_run_status(root).state == "REJECT"


def test_verifier_must_bind_exactly_one_synthesized_primary_journey(
    tmp_path: Path,
):
    root, _run = _admit_external_cohort(tmp_path)
    for role in CALIBRATION_ROLES[:3]:
        packet = build_p0_calibration_agent_packet(root, role=role)
        result, receipt = _external_result_and_receipt(root, packet, verifier=False)
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=receipt,
            result=result,
        )
    verifier = build_p0_calibration_agent_packet(root, role="verifier")
    assert verifier.payload["result_contract"]["primary_journey_contract"] == {
        "field": "primary_journey_claim_id",
        "references": "verification.journeys[].claim_id",
        "cardinality": "exactly_one",
    }
    result, receipt = _external_result_and_receipt(root, verifier, verifier=True)
    result.payload["verification"]["primary_journey_claim_id"] = "not-a-journey"
    material = dict(receipt.payload)
    material.pop("receipt_id")
    material.pop("receipt_hash")
    material["response_hash"] = _sha256_json(result.payload)
    material["response_bytes"] = len(canonical_json_bytes(result.payload))
    receipt_hash = _sha256_json(material)
    replacement = P0CalibrationDispatchReceipt.from_dict(
        {
            **material,
            "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
            "receipt_hash": receipt_hash,
        }
    )

    with pytest.raises(P0CalibrationSchemaError, match="primary_journey_claim_id"):
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=replacement,
            result=result,
        )


def test_verifier_synthesis_must_come_from_accepted_proposal_claims(
    tmp_path: Path,
):
    root, _run = _admit_external_cohort(tmp_path)
    for role in CALIBRATION_ROLES[:3]:
        packet = build_p0_calibration_agent_packet(root, role=role)
        result, receipt = _external_result_and_receipt(root, packet, verifier=False)
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=receipt,
            result=result,
        )
    verifier_packet = build_p0_calibration_agent_packet(root, role="verifier")
    result, receipt = _external_result_and_receipt(root, verifier_packet, verifier=True)
    result.payload["verification"]["purpose"]["statement"] = (
        "A new source-cited statement absent from every accepted proposal."
    )
    material = dict(receipt.payload)
    material.pop("receipt_id")
    material.pop("receipt_hash")
    material["response_hash"] = _sha256_json(result.payload)
    material["response_bytes"] = len(canonical_json_bytes(result.payload))
    receipt_hash = _sha256_json(material)
    replacement = P0CalibrationDispatchReceipt.from_dict(
        {
            **material,
            "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
            "receipt_hash": receipt_hash,
        }
    )

    with pytest.raises(P0CalibrationSchemaError, match="not retained from an accepted"):
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=replacement,
            result=result,
        )

    status = get_p0_calibration_run_status(root)
    assert status.role_statuses["verifier"] == "not_issued"


def test_identical_result_delivery_is_a_noop(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    result, receipt = _external_result_and_receipt(root, packet, verifier=False)
    first = record_p0_calibration_agent_result(
        root, dispatch_receipt=receipt, result=result
    )

    replay = record_p0_calibration_agent_result(
        root, dispatch_receipt=receipt, result=result
    )

    assert replay.generation == first.generation
    assert replay.head_transition_hash == first.head_transition_hash


def test_external_dispatch_failure_is_authenticated_preserved_and_terminal(
    tmp_path: Path,
):
    root, _run = _admit_external_cohort(tmp_path)
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    result, receipt = _external_failure_result_and_receipt(
        root,
        packet,
        reason_code="resource_exhausted",
        dispatch_started=True,
    )

    blocked = record_p0_calibration_agent_result(
        root,
        dispatch_receipt=receipt,
        result=result,
    )

    assert blocked.state == "BLOCKED_NO_SHIP"
    assert blocked.payload["terminal_reason_codes"] == [
        "external_dispatch_failed_or_inconclusive"
    ]
    binding = blocked.payload["recorded_receipts"][receipt.receipt_id]
    assert binding["idempotency_key"] == packet.payload["idempotency_key"]
    assert binding["route_id"] == "host-broker-1"
    assert binding["attempt"] == 1
    assert blocked.payload["roles"]["intake-a"]["attempts"] == 1
    assert blocked.payload["roles"]["intake-a"]["result_id"] == result.result_id
    receipt_path = root / blocked.payload["artifacts"]["receipts"]["intake-a"]
    result_path = root / blocked.payload["artifacts"]["results"]["intake-a"]
    authentication_path = (
        root
        / blocked.payload["artifacts"]["receipt_authentications"][receipt.receipt_id]
    )
    assert json.loads(receipt_path.read_text(encoding="utf-8")) == receipt.payload
    assert json.loads(result_path.read_text(encoding="utf-8")) == result.payload
    proof = json.loads(authentication_path.read_text(encoding="utf-8"))["proof"]
    assert proof["receipt_hash"] == _sha256_json(receipt.payload)
    assert proof["result_hash"] == _sha256_json(result.payload)
    (tmp_path / "source" / "app.py").write_text(
        "def changed_after_terminal_failure() -> None:\n    pass\n",
        encoding="utf-8",
    )
    replay = record_p0_calibration_agent_result(
        root,
        dispatch_receipt=receipt,
        result=result,
    )
    assert replay.generation == blocked.generation
    assert replay.head_transition_hash == blocked.head_transition_hash
    with pytest.raises(P0CalibrationTransitionError, match="terminal"):
        build_p0_calibration_agent_packet(root, role="intake-a")


def test_external_dispatch_failure_receipt_mismatch_rejects_cohort(
    tmp_path: Path,
):
    root, _run = _admit_external_cohort(tmp_path)
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    result, receipt = _external_failure_result_and_receipt(root, packet)
    material = dict(receipt.payload)
    material.pop("receipt_id")
    material.pop("receipt_hash")
    material["status"] = "resource_exhausted"
    receipt_hash = _sha256_json(material)
    forged = P0CalibrationDispatchReceipt.from_dict(
        {
            **material,
            "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
            "receipt_hash": receipt_hash,
        }
    )

    with pytest.raises(P0CalibrationIntegrityError, match="reason_code"):
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=forged,
            result=result,
        )

    assert get_p0_calibration_run_status(root).state == "REJECT"


def test_external_dispatch_failure_result_contract_is_strict(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    result, _receipt = _external_failure_result_and_receipt(root, packet)
    invalid_results = []
    retryable = result.to_dict()
    retryable["failure"]["retry_allowed"] = True
    invalid_results.append(retryable)
    unknown_field = result.to_dict()
    unknown_field["failure"]["provider_error"] = "private-provider-error"
    invalid_results.append(unknown_field)
    control_character = result.to_dict()
    control_character["failure"]["message"] = "line one\nline two"
    invalid_results.append(control_character)
    oversized = result.to_dict()
    oversized["failure"]["message"] = "x" * 2049
    invalid_results.append(oversized)
    unsupported_reason = result.to_dict()
    unsupported_reason["failure"]["reason_code"] = "retryable"
    invalid_results.append(unsupported_reason)

    for payload in invalid_results:
        with pytest.raises(P0CalibrationSchemaError):
            P0CalibrationAgentResult.from_dict(payload)


def test_mismatched_receipt_rejects_cohort(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    result, receipt = _external_result_and_receipt(root, packet, verifier=False)
    material = dict(receipt.payload)
    material.pop("receipt_id")
    material.pop("receipt_hash")
    material["packet_hash"] = "sha256:" + "f" * 64
    receipt_hash = _sha256_json(material)
    forged = P0CalibrationDispatchReceipt.from_dict(
        {
            **material,
            "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
            "receipt_hash": receipt_hash,
        }
    )

    with pytest.raises(P0CalibrationIntegrityError, match="packet_hash"):
        record_p0_calibration_agent_result(root, dispatch_receipt=forged, result=result)

    assert get_p0_calibration_run_status(root).state == "REJECT"


def test_receipt_response_byte_mismatch_rejects_cohort(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    result, receipt = _external_result_and_receipt(root, packet, verifier=False)
    material = dict(receipt.payload)
    material.pop("receipt_id")
    material.pop("receipt_hash")
    material["response_bytes"] += 1
    receipt_hash = _sha256_json(material)
    forged = P0CalibrationDispatchReceipt.from_dict(
        {
            **material,
            "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
            "receipt_hash": receipt_hash,
        }
    )

    with pytest.raises(P0CalibrationIntegrityError, match="byte count"):
        record_p0_calibration_agent_result(root, dispatch_receipt=forged, result=result)

    assert get_p0_calibration_run_status(root).state == "REJECT"


def test_external_receipt_requires_matching_host_authentication(
    tmp_path: Path,
):
    class _WrongReceiptAuthenticator(_HostBrokerAuthenticator):
        def authenticate_receipt(self, **kwargs):
            return replace(
                super().authenticate_receipt(**kwargs),
                packet_hash=_HASH_A,
            )

    root, _run = _admit_external_cohort(tmp_path)
    packet = build_p0_calibration_agent_packet(root, role="intake-a")
    result, receipt = _external_result_and_receipt(root, packet, verifier=False)
    with host_broker.use_p0_calibration_host_broker_authenticator(
        _WrongReceiptAuthenticator()
    ):
        with pytest.raises(
            P0CalibrationIntegrityError,
            match="receipt proof packet_hash",
        ):
            record_p0_calibration_agent_result(
                root,
                dispatch_receipt=receipt,
                result=result,
            )

    assert get_p0_calibration_run_status(root).state == "REJECT"


def test_external_authentication_proof_tampering_rejects(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    proof_path = root / "authority" / "external-broker-authentication.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    proof["proof"]["principal"] = "tampered-principal"
    proof_path.write_bytes(canonical_json_bytes(proof))

    status = get_p0_calibration_run_status(root)

    assert status.state == "REJECT"
    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert "ledger_tampering" in snapshot["terminal_reason_codes"]


def test_external_route_call_limit_is_enforced_across_semantic_results(
    tmp_path: Path,
):
    _source, control_a, control_b = _prepare_controls(tmp_path)
    manifest = _external_manifest()
    manifest["external_routes"][0]["max_calls"] = 1
    root = tmp_path / "calibration"
    run = prepare_p0_calibration_run(
        root,
        control_workspaces=[control_a, control_b],
        execution_manifest=manifest,
    )
    authority = _authority(run, manifest)
    admitted = admit_p0_calibration_run(
        root,
        authority_grant=authority,
        broker_attestation=_attestation(run, authority, manifest),
    )
    assert admitted.state == "ADMISSION_AUTHORIZED"

    first = build_p0_calibration_agent_packet(root, role="intake-a")
    first_result, first_receipt = _external_result_and_receipt(
        root, first, verifier=False
    )
    record_p0_calibration_agent_result(
        root,
        dispatch_receipt=first_receipt,
        result=first_result,
    )
    second = build_p0_calibration_agent_packet(root, role="intake-b")
    second_result, second_receipt = _external_result_and_receipt(
        root, second, verifier=False
    )

    with pytest.raises(P0CalibrationIntegrityError, match="call limit"):
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=second_receipt,
            result=second_result,
        )

    assert get_p0_calibration_run_status(root).state == "REJECT"


def test_frozen_total_call_budget_blocks_a_fifth_role_attempt(tmp_path: Path):
    _source, control_a, control_b = _prepare_controls(tmp_path)
    manifest = _external_manifest()
    manifest["budgets"]["max_total_calls"] = 4
    manifest["external_routes"][0]["max_calls"] = 4
    root = tmp_path / "calibration"
    run = prepare_p0_calibration_run(
        root,
        control_workspaces=[control_a, control_b],
        execution_manifest=manifest,
    )
    authority = _authority(run, manifest)
    admitted = admit_p0_calibration_run(
        root,
        authority_grant=authority,
        broker_attestation=_attestation(run, authority, manifest),
    )
    assert admitted.state == "ADMISSION_AUTHORIZED"
    for role in CALIBRATION_ROLES[:3]:
        packet = build_p0_calibration_agent_packet(root, role=role)
        result, receipt = _external_result_and_receipt(root, packet, verifier=False)
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=receipt,
            result=result,
        )
    verifier = build_p0_calibration_agent_packet(root, role="verifier")
    result, receipt = _external_result_and_receipt(root, verifier, verifier=True)
    result.payload["verification"]["purpose"]["citations"] = ["citation-forged"]
    material = dict(receipt.payload)
    material.pop("receipt_id")
    material.pop("receipt_hash")
    material["response_hash"] = _sha256_json(result.payload)
    material["response_bytes"] = len(canonical_json_bytes(result.payload))
    receipt_hash = _sha256_json(material)
    replacement = P0CalibrationDispatchReceipt.from_dict(
        {
            **material,
            "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
            "receipt_hash": receipt_hash,
        }
    )
    with pytest.raises(P0CalibrationSchemaError, match="Semantic result"):
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=replacement,
            result=result,
        )

    with pytest.raises(P0CalibrationTransitionError, match="budget is exhausted"):
        build_p0_calibration_agent_packet(root, role="verifier")

    assert get_p0_calibration_run_status(root).state == "BLOCKED_NO_SHIP"


def test_snapshot_is_rebuilt_but_ledger_tampering_rejects(tmp_path: Path):
    root, run = _prepare_external_cohort(tmp_path)
    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    snapshot["state"] = "PREFLIGHT"
    (root / "run.json").write_bytes(canonical_json_bytes(snapshot))

    assert get_p0_calibration_run_status(root).state == "BASELINE_FROZEN"
    repaired = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert repaired["state"] == "BASELINE_FROZEN"

    control = json.loads(
        (root / "baseline" / "control-01.json").read_text(encoding="utf-8")
    )
    control["source"]["revision"] = "tampered"
    (root / "baseline" / "control-01.json").write_bytes(canonical_json_bytes(control))

    rejected = get_p0_calibration_run_status(root)
    assert rejected.state == "REJECT"
    assert rejected.decision_scope == "p0_policy_default"
    assert (root / "terminal-rejection.json").is_file()
    assert rejected.cohort_id == run.cohort_id


def test_unknown_controller_file_blocks_without_deleting_evidence(tmp_path: Path):
    root, _run = _prepare_external_cohort(tmp_path)
    unknown = root / "unexpected.json"
    ProtectedArtifactStore(root)._write_bytes(
        "unexpected.json",
        b"{}\n",
        immutable=True,
    )

    status = get_p0_calibration_run_status(root)

    assert status.state == "BLOCKED_NO_SHIP"
    assert unknown.is_file()


def test_nested_unknown_controller_file_blocks_without_deleting_evidence(
    tmp_path: Path,
):
    root, _run = _prepare_external_cohort(tmp_path)
    unknown = root / "baseline" / "unexpected.json"
    ProtectedArtifactStore(root)._write_bytes(
        "baseline/unexpected.json",
        b"{}\n",
        immutable=True,
    )

    status = get_p0_calibration_run_status(root)

    assert status.state == "BLOCKED_NO_SHIP"
    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert snapshot["terminal_reason_codes"] == ["unknown_controller_artifact"]
    assert unknown.is_file()


def test_fully_written_pending_transaction_is_recovered_idempotently(
    tmp_path: Path,
):
    root, run = _prepare_external_cohort(tmp_path)
    pending_path = root / "pending-transaction.json"
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    pending["status"] = "pending"
    pending_path.write_bytes(canonical_json_bytes(pending))

    status = get_p0_calibration_run_status(root)

    assert status.state == "BASELINE_FROZEN"
    assert status.generation == run.generation
    recovered = json.loads(pending_path.read_text(encoding="utf-8"))
    assert recovered["status"] == "committed"


def test_ambiguous_pending_transaction_blocks_and_preserves_marker(
    tmp_path: Path,
):
    root, _run = _prepare_external_cohort(tmp_path)
    pending_path = root / "pending-transaction.json"
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    pending["status"] = "unknown-after-crash"
    pending_path.write_bytes(canonical_json_bytes(pending))

    status = get_p0_calibration_run_status(root)

    assert status.state == "BLOCKED_NO_SHIP"
    preserved = list((root / "verification").glob("ambiguous-recovery-*.json"))
    assert len(preserved) == 1
    evidence = json.loads(preserved[0].read_text(encoding="utf-8"))
    assert evidence["pending_transaction"]["status"] == "unknown-after-crash"


@pytest.mark.parametrize(
    "corruption",
    ["cas", "snapshot", "artifact-index", "transition-hash"],
)
def test_incoherent_pending_transaction_blocks_before_replay(
    tmp_path: Path,
    corruption: str,
):
    root, _run = _prepare_external_cohort(tmp_path)
    pending_path = root / "pending-transaction.json"
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    pending["status"] = "pending"
    if corruption == "cas":
        pending["expected_generation"] += 1
    elif corruption == "snapshot":
        pending["snapshot"]["limitations"].append(
            "Snapshot payload not present in the transition."
        )
    elif corruption == "artifact-index":
        pending["artifacts"][0]["payload"]["unexpected"] = True
    else:
        pending["transition"]["details"]["tampered"] = True
    pending_path.write_bytes(canonical_json_bytes(pending))

    status = get_p0_calibration_run_status(root)

    assert status.state == "BLOCKED_NO_SHIP"
    snapshot = json.loads((root / "run.json").read_text(encoding="utf-8"))
    assert snapshot["terminal_reason_codes"] == ["ambiguous_crash_recovery"]
    preserved = list((root / "verification").glob("ambiguous-recovery-*.json"))
    assert len(preserved) == 1
    evidence = json.loads(preserved[0].read_text(encoding="utf-8"))
    assert evidence["pending_transaction"] == pending


def test_prepare_rejects_nonreproducible_control_worklists(tmp_path: Path):
    _source, control_a, control_b = _prepare_controls(tmp_path)
    worklist_path = control_b / ".llm-wiki-docs" / "evidence" / "semantic-worklist.json"
    worklist = json.loads(worklist_path.read_text(encoding="utf-8"))
    worklist["policy"]["p1_budget"] += 1
    worklist_path.write_text(
        json.dumps(worklist, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(P0CalibrationIntegrityError, match="worklist_hash"):
        prepare_p0_calibration_run(
            tmp_path / "calibration",
            control_workspaces=[control_a, control_b],
            execution_manifest=_external_manifest(),
        )


def test_outbound_evidence_redacts_credentials_keys_and_host_paths(
    tmp_path: Path,
):
    github_token = "ghp_" + ("A" * 36)
    aws_access_key = "AKIA" + ("B" * 16)
    private_key_payload = "c3VwZXItc2VjcmV0LWtleQ=="
    private_path = tmp_path / "operator-home" / "secrets.toml"
    readme = (
        "# Example\n\n"
        f'api_key = "{github_token}"\n'
        f"AWS_ACCESS_KEY_ID={aws_access_key}\n"
        f"configuration = {private_path}\n"
        "backup = /data/private/secrets.json\n"
        "application = /Applications/Private/config.json\n"
        "password is hunter2\n"
        "Password is required for production access.\n"
        "-----BEGIN PRIVATE KEY-----\n"
        f"{private_key_payload}\n"
        "-----END PRIVATE KEY-----\n"
    )
    _source, control_a, control_b = _prepare_controls(
        tmp_path,
        readme_text=readme,
    )
    root = tmp_path / "calibration"
    run = prepare_p0_calibration_run(
        root,
        control_workspaces=[control_a, control_b],
        execution_manifest=_external_manifest(),
    )

    bundle = json.loads((root / "evidence" / "bundle.json").read_text(encoding="utf-8"))
    encoded_bundle = json.dumps(bundle, sort_keys=True)
    assert github_token not in encoded_bundle
    assert aws_access_key not in encoded_bundle
    assert private_key_payload not in encoded_bundle
    assert str(tmp_path) not in encoded_bundle
    assert "/data/private/secrets.json" not in encoded_bundle
    assert "/Applications/Private/config.json" not in encoded_bundle
    assert "hunter2" not in encoded_bundle
    assert "Password is required for production access." in encoded_bundle
    readme_record = next(
        item for item in bundle["documents"] if item["path"] == "source/README.md"
    )
    assert readme_record["content_status"] == "redacted"
    assert readme_record["redactions"]
    assert bundle["outbound_safety"]["status"] == "redacted"
    assert {item["reason"] for item in bundle["unknowns"]} >= {
        "sensitive_content_redacted"
    }

    authority = _authority(run)
    admitted = admit_p0_calibration_run(
        root,
        authority_grant=authority,
        broker_attestation=_attestation(run, authority),
    )
    assert admitted.state == "ADMISSION_AUTHORIZED"
    packet = build_p0_calibration_agent_packet(root, role="intake-a").to_json()
    assert github_token not in packet
    assert aws_access_key not in packet
    assert private_key_payload not in packet
    assert str(tmp_path) not in packet
    assert "/data/private/secrets.json" not in packet
    assert "/Applications/Private/config.json" not in packet
    assert "hunter2" not in packet


def test_prepare_rejects_source_document_changed_after_tree_check(
    tmp_path: Path,
    monkeypatch,
):
    source, control_a, control_b = _prepare_controls(tmp_path)
    real_compile = controller_module._compile_evidence_bundle
    mutated = False

    def compile_after_mutation(control, *, bound_roots):
        nonlocal mutated
        if not mutated:
            mutated = True
            (source / "README.md").write_text(
                "# Mutated after the frozen tree check\n",
                encoding="utf-8",
            )
        return real_compile(control, bound_roots=bound_roots)

    monkeypatch.setattr(
        controller_module,
        "_compile_evidence_bundle",
        compile_after_mutation,
    )

    with pytest.raises(
        P0CalibrationIntegrityError,
        match="Source documentation changed from the frozen tree baseline",
    ):
        prepare_p0_calibration_run(
            tmp_path / "calibration",
            control_workspaces=[control_a, control_b],
            execution_manifest=_external_manifest(),
        )


def test_cited_source_with_sensitive_content_fails_closed(tmp_path: Path):
    github_token = "ghp_" + ("C" * 36)
    app_text = (
        '"""Example application."""\n\n'
        "def run() -> str:\n"
        '    """Run the supported operation."""\n'
        '    return "ok"\n\n'
        "def main() -> None:\n"
        f'    api_token = "{github_token}"\n'
        "    print(run())\n\n"
        'if __name__ == "__main__":\n'
        "    main()\n"
    )
    _source, control_a, control_b = _prepare_controls(
        tmp_path,
        app_text=app_text,
    )

    with pytest.raises(P0CalibrationIntegrityError, match="outbound-sensitive"):
        prepare_p0_calibration_run(
            tmp_path / "calibration",
            control_workspaces=[control_a, control_b],
            execution_manifest=_external_manifest(),
        )


def test_verifier_packet_redacts_sensitive_intake_statements(tmp_path: Path):
    root, _run = _admit_external_cohort(tmp_path)
    proposal_token = "ghp_" + ("D" * 36)
    for role in CALIBRATION_ROLES[:3]:
        packet = build_p0_calibration_agent_packet(root, role=role)
        result, receipt = _external_result_and_receipt(root, packet, verifier=False)
        if role == "intake-a":
            result.payload["proposal"]["purpose"]["statement"] = (
                f"Use api_key={proposal_token} from {tmp_path / 'private.txt'}."
            )
            material = dict(receipt.payload)
            material.pop("receipt_id")
            material.pop("receipt_hash")
            material["response_hash"] = _sha256_json(result.payload)
            material["response_bytes"] = len(canonical_json_bytes(result.payload))
            receipt_hash = _sha256_json(material)
            receipt = P0CalibrationDispatchReceipt.from_dict(
                {
                    **material,
                    "receipt_id": "receipt-" + receipt_hash.split(":", 1)[1][:24],
                    "receipt_hash": receipt_hash,
                }
            )
        record_p0_calibration_agent_result(
            root,
            dispatch_receipt=receipt,
            result=result,
        )

    verifier = build_p0_calibration_agent_packet(root, role="verifier")
    encoded = verifier.to_json()
    assert proposal_token not in encoded
    assert str(tmp_path) not in encoded
    proposal = next(
        record
        for record in verifier.payload["intake_proposals"]
        if record["role"] == "intake-a"
    )
    assert proposal["outbound_safety"]["status"] == "redacted"
    assert proposal["outbound_safety"]["redactions"]


@pytest.mark.skipif(
    os.name == "nt" or not getattr(os, "O_NOFOLLOW", 0),
    reason="POSIX descriptor-relative traversal is unavailable",
)
def test_posix_control_json_read_does_not_reopen_by_path(
    tmp_path: Path,
    monkeypatch,
):
    _source, control_a, _control_b = _prepare_controls(tmp_path)

    def reject_path_open(*_args, **_kwargs):
        raise AssertionError("control JSON path was reopened")

    monkeypatch.setattr(Path, "open", reject_path_open)

    payload = controller_module._read_workspace_json(
        control_a,
        ".llm-wiki-docs/run.json",
    )

    assert payload["state"] == "baseline_ready"


@pytest.mark.skipif(
    os.name == "nt" or not getattr(os, "O_NOFOLLOW", 0),
    reason="POSIX descriptor-relative traversal is unavailable",
)
def test_posix_evidence_read_uses_one_no_follow_leaf_handle(
    tmp_path: Path,
    monkeypatch,
):
    evidence_root = tmp_path / "evidence-root"
    nested = evidence_root / "nested"
    nested.mkdir(parents=True)
    payload = (b"bounded evidence\n" * 32) + b"tail"
    (nested / "evidence.md").write_bytes(payload)
    real_open = controller_module.os.open
    leaf_opens: list[int] = []

    def tracking_open(path, flags, mode=0o777, *, dir_fd=None):
        if path == "evidence.md":
            leaf_opens.append(flags)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    def reject_path_open(*_args, **_kwargs):
        raise AssertionError("evidence path was reopened")

    monkeypatch.setattr(controller_module.os, "open", tracking_open)
    monkeypatch.setattr(Path, "open", reject_path_open)

    snapshot = controller_module._read_bound_evidence_file(
        evidence_root,
        "nested/evidence.md",
        included_maximum=64,
        maximum=4096,
    )

    assert len(leaf_opens) == 1
    assert leaf_opens[0] & os.O_NOFOLLOW
    assert snapshot.original_bytes == len(payload)
    assert snapshot.included == payload[:64]
    assert snapshot.sha256 == "sha256:" + hashlib.sha256(payload).hexdigest()
    assert snapshot.included_sha256 == (
        "sha256:" + hashlib.sha256(payload[:64]).hexdigest()
    )
    assert snapshot.truncated is True


@pytest.mark.skipif(
    os.name == "nt" or not hasattr(os, "symlink"),
    reason="POSIX symlink traversal test",
)
def test_posix_evidence_read_rejects_linked_directory(tmp_path: Path):
    evidence_root = tmp_path / "evidence-root"
    outside = tmp_path / "outside"
    evidence_root.mkdir()
    outside.mkdir()
    (outside / "evidence.md").write_text("outside secret", encoding="utf-8")
    (evidence_root / "linked").symlink_to(outside, target_is_directory=True)

    with pytest.raises(P0CalibrationIntegrityError, match="safely read"):
        controller_module._read_bound_evidence_file(
            evidence_root,
            "linked/evidence.md",
            included_maximum=64,
            maximum=4096,
        )
