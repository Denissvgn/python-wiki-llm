"""Focused, runtime-free tests for the P0 OCI capability broker."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import stat
import sys
from pathlib import Path

import pytest

from llm_wiki_cli.services import documentation_calibration_broker as broker
from llm_wiki_cli.services.contracts import (
    P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
    P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION,
    P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION,
    P0_CALIBRATION_ISOLATION_PROBE_RESULT_SCHEMA_VERSION,
)
from llm_wiki_cli.services.documentation_calibration_broker import (
    REQUIRED_ISOLATION_PROBES,
    BoundedProcessResult,
    OciAdmissionProbeRequest,
    OciAdmissionProbeResult,
    OciBrokerError,
    OciDispatchContext,
    OciDispatchReceipt,
    OciRuntimeConfig,
    build_oci_dispatch_command,
    build_oci_probe_command,
    canonical_result_json_bytes,
    create_oci_admission_probe_environment,
    dispatch_oci_agent,
    execute_oci_admission_probe,
    run_bounded_process,
    sanitized_oci_environment,
    validate_execution_manifest,
)


_HASH_A = "sha256:" + "a" * 64
_HASH_B = "sha256:" + "b" * 64
_HASH_C = "sha256:" + "c" * 64
_HASH_D = "sha256:" + "d" * 64
_HASH_E = "sha256:" + "e" * 64
_WORKER_IMAGE = "registry.example/llm-wiki/worker@sha256:" + "1" * 64
_PROBE_IMAGE = "registry.example/llm-wiki/probe@sha256:" + "2" * 64
_PACKET_ID = "00000000-0000-4000-8000-000000000001"
_RESULT_ID = "00000000-0000-4000-8000-000000000002"


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _runtime_path(tmp_path: Path) -> Path:
    name = "docker.exe" if os.name == "nt" else "docker"
    runtime = tmp_path / name
    runtime.write_bytes(b"synthetic docker executable")
    if os.name != "nt":
        runtime.chmod(0o700)
    return runtime


def _oci_payload(runtime: Path) -> dict:
    return {
        "runtime": "docker",
        "executable": str(runtime),
        "executable_sha256": _sha256(runtime.read_bytes()),
        "worker": {
            "image": _WORKER_IMAGE,
            "entrypoint": ["/opt/llm-wiki/worker", "--mode", "intake"],
        },
        "probe": {
            "image": _PROBE_IMAGE,
            "entrypoint": ["/opt/llm-wiki/probe"],
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
            "result_bytes": 65536,
        },
    }


def _config(tmp_path: Path) -> OciRuntimeConfig:
    return OciRuntimeConfig.from_dict(_oci_payload(_runtime_path(tmp_path)))


def _manifest(runtime: Path) -> dict:
    return {
        "schema_version": P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION,
        "profile": "local_no_egress",
        "roles": ["intake-a", "intake-b", "intake-c", "verifier"],
        "budgets": {
            "max_concurrent_workers": 3,
            "max_attempts_per_role": 2,
            "max_total_calls": 8,
            "max_packet_bytes": 1048576,
            "max_result_bytes": 65536,
        },
        "oci": _oci_payload(runtime),
        "external_routes": [],
    }


def _write_packet(path: Path) -> str:
    raw = b'{"packet":"bounded"}\n'
    path.write_bytes(raw)
    return _sha256(raw)


def _context(packet_hash: str) -> OciDispatchContext:
    return OciDispatchContext(
        cohort_id="cohort-001",
        generation=7,
        head_transition_hash=_HASH_A,
        role="intake-a",
        attempt=1,
        packet_id=_PACKET_ID,
        packet_hash=packet_hash,
        authority_hash=_HASH_B,
        attestation_hash=_HASH_C,
        access_audit_hash=_HASH_D,
        idempotency_key="cohort-001:intake-a:1",
    )


def _agent_result(context: OciDispatchContext) -> dict:
    return {
        "schema_version": P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
        "result_id": _RESULT_ID,
        "cohort_id": context.cohort_id,
        "packet_id": context.packet_id,
        "role": context.role,
        "attempt": context.attempt,
        "packet_hash": context.packet_hash,
        "idempotency_key": context.idempotency_key,
        "status": "complete",
        "proposal": {"purpose": "Source-cited bounded proposal."},
    }


def _passing_probe_result(
    request: OciAdmissionProbeRequest,
    *,
    failed_probe: str | None = None,
) -> dict:
    access_events = []
    for probe in REQUIRED_ISOLATION_PROBES:
        failed = probe == failed_probe
        target_id, target_sha256 = request.target_binding(probe)
        if probe in REQUIRED_ISOLATION_PROBES[:5]:
            evidence = {
                "read_succeeded": failed,
                "observed_sha256": target_sha256 if failed else None,
            }
        elif probe == "network_egress":
            evidence = {
                "canary_connected": False,
                "non_loopback_interfaces": ["eth0"] if failed else [],
                "default_route": failed,
            }
        elif probe == "output_write_bound":
            evidence = {
                "limit_bytes": request.output_limit_bytes,
                "attempted_bytes": request.output_limit_bytes + 1,
                "oversize_write_succeeded": failed,
                "sibling_write_succeeded": False,
                "observed_size": (request.output_limit_bytes + 1 if failed else 0),
            }
        else:
            evidence = {"connected_targets": ["/var/run/docker.sock"] if failed else []}
        access_events.append(
            {
                "probe": probe,
                "target_id": target_id,
                "target_sha256": target_sha256,
                "attempted": True,
                "outcome": "accessible" if failed else "denied",
                "evidence": evidence,
                "detail": "access unexpectedly succeeded"
                if failed
                else "access denied",
            }
        )
    return {
        "schema_version": P0_CALIBRATION_ISOLATION_PROBE_RESULT_SCHEMA_VERSION,
        "cohort_id": request.cohort_id,
        "probe_id": request.probe_id,
        "request_hash": request.request_hash,
        "image_digest": _PROBE_IMAGE.rsplit("@", 1)[1],
        "access_events": access_events,
        "status": "failed" if failed_probe else "passed",
    }


def test_runtime_config_strictly_parses_local_no_egress_manifest(tmp_path: Path):
    runtime = _runtime_path(tmp_path)
    payload = _oci_payload(runtime)
    manifest = _manifest(runtime)

    config = OciRuntimeConfig.from_execution_manifest(manifest)

    assert config.to_dict() == payload
    assert validate_execution_manifest(manifest) == manifest
    assert config.runtime == "docker"
    assert config.worker.digest == "sha256:" + "1" * 64
    assert config.probe.digest == "sha256:" + "2" * 64


def test_podman_must_also_be_explicitly_resolved_and_uses_fixed_argv(
    tmp_path: Path,
):
    runtime = tmp_path / ("podman.exe" if os.name == "nt" else "podman")
    runtime.write_bytes(b"synthetic podman executable")
    if os.name != "nt":
        runtime.chmod(0o700)
    payload = _oci_payload(runtime)
    payload["runtime"] = "podman"
    payload["executable_sha256"] = _sha256(runtime.read_bytes())
    config = OciRuntimeConfig.from_dict(payload)
    packet = tmp_path / "packet.json"
    context = _context(_write_packet(packet))
    output = tmp_path / "output"
    output.mkdir()

    command = build_oci_dispatch_command(
        config,
        packet_path=packet,
        output_dir=output,
        context=context,
    )

    assert command[0] == str(runtime)
    assert command[1] == "run"
    assert "--network=none" in command
    assert "--pull=never" in command
    assert "--userns=keep-id:uid=1000,gid=1000" in command
    assert (
        f"type=bind,source={output / 'result.json'},target=/llm-wiki/output/result.json"
    ) in command


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda payload: payload.update({"unexpected": True}),
            "fields are invalid",
        ),
        (
            lambda payload: payload.update({"environment": {"API_KEY": "secret"}}),
            "credential-bearing field",
        ),
        (
            lambda payload: payload["worker"].update(
                {"image": "registry.example/worker:latest"}
            ),
            "digest",
        ),
        (
            lambda payload: payload["worker"].update(
                {"image": ("registry.example/worker:latest@sha256:" + "1" * 64)}
            ),
            "mutable tag",
        ),
        (
            lambda payload: payload.update({"user": "0:1000"}),
            "non-root",
        ),
        (
            lambda payload: payload["resources"].update({"pids_limit": 0}),
            "pids_limit",
        ),
        (
            lambda payload: payload["worker"].update({"entrypoint": ["worker"]}),
            "absolute container path",
        ),
    ],
)
def test_runtime_config_rejects_unsafe_or_ambiguous_fields(
    tmp_path: Path, mutate, message: str
):
    payload = _oci_payload(_runtime_path(tmp_path))
    mutate(payload)

    with pytest.raises(OciBrokerError, match=message):
        OciRuntimeConfig.from_dict(payload)


def test_runtime_manifest_rejects_external_profile_and_likely_secret(
    tmp_path: Path,
):
    payload = _manifest(_runtime_path(tmp_path))
    payload["profile"] = "external_authorized"
    payload["oci"] = None
    payload["external_routes"] = [
        {
            "route_id": "broker-route-a",
            "recipient": "provider-account-a",
            "max_calls": 8,
            "max_request_bytes": 1048576,
            "max_response_bytes": 65536,
        }
    ]
    with pytest.raises(OciBrokerError, match="local_no_egress"):
        OciRuntimeConfig.from_execution_manifest(payload)

    payload = _manifest(_runtime_path(tmp_path))
    payload["note"] = "Bearer this-is-definitely-a-secret-token"
    with pytest.raises(OciBrokerError, match="credential material"):
        OciRuntimeConfig.from_execution_manifest(payload)


def test_external_manifest_is_oci_neutral_strict_and_credential_free(
    tmp_path: Path,
):
    payload = _manifest(_runtime_path(tmp_path))
    payload["profile"] = "external_authorized"
    payload["oci"] = None
    payload["external_routes"] = [
        {
            "route_id": "provider-route-a",
            "recipient": "provider-account-a",
            "max_calls": 4,
            "max_request_bytes": 524288,
            "max_response_bytes": 32768,
        },
        {
            "route_id": "provider-route-b",
            "recipient": "provider-account-b",
            "max_calls": 4,
            "max_request_bytes": 1048576,
            "max_response_bytes": 65536,
        },
    ]

    assert validate_execution_manifest(payload) == payload

    payload["external_routes"][0]["recipient"] = "https://provider.example/api"
    with pytest.raises(OciBrokerError, match="public identifier"):
        validate_execution_manifest(payload)


def test_manifest_budget_and_backend_limits_must_match(tmp_path: Path):
    payload = _manifest(_runtime_path(tmp_path))
    payload["budgets"]["max_packet_bytes"] += 1
    with pytest.raises(OciBrokerError, match="max_packet_bytes must match"):
        validate_execution_manifest(payload)

    payload = _manifest(_runtime_path(tmp_path))
    payload["budgets"]["max_result_bytes"] = 1024
    with pytest.raises(OciBrokerError, match="result_bytes cannot exceed"):
        validate_execution_manifest(payload)

    payload = _manifest(_runtime_path(tmp_path))
    payload["roles"] = list(reversed(payload["roles"]))
    with pytest.raises(OciBrokerError, match="canonical four-role"):
        validate_execution_manifest(payload)


def test_dispatch_command_is_exact_hardened_argv_with_only_two_mounts(
    tmp_path: Path,
):
    config = _config(tmp_path)
    packet = tmp_path / "packet with spaces Ω.json"
    packet_hash = _write_packet(packet)
    output = tmp_path / "role output Ω"
    output.mkdir()
    context = _context(packet_hash)

    command = build_oci_dispatch_command(
        config,
        packet_path=packet,
        output_dir=output,
        context=context,
    )

    suffix = hashlib.sha256(context.idempotency_key.encode()).hexdigest()[:12]
    expected_name = f"p0-intake-a-1-{suffix}"
    assert command == (
        str(tmp_path / ("docker.exe" if os.name == "nt" else "docker")),
        "run",
        "--rm",
        "--pull=never",
        f"--name={expected_name}",
        "--log-driver=none",
        "--network=none",
        "--read-only",
        "--user=1000:1000",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=32",
        "--memory=536870912",
        "--memory-swap=536870912",
        "--cpus=0.750",
        "--ulimit=fsize=65536:65536",
        "--workdir=/tmp",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=16777216",
        "--env",
        "HOME=/tmp",
        "--env",
        "LANG=C.UTF-8",
        "--env",
        "LC_ALL=C.UTF-8",
        "--env",
        "TMPDIR=/tmp",
        "--mount",
        (f"type=bind,source={packet},target=/llm-wiki/input/packet.json,readonly"),
        "--mount",
        (
            f"type=bind,source={output / 'result.json'},"
            "target=/llm-wiki/output/result.json"
        ),
        "--entrypoint=/opt/llm-wiki/worker",
        _WORKER_IMAGE,
        "--mode",
        "intake",
        "--packet",
        "/llm-wiki/input/packet.json",
        "--result",
        "/llm-wiki/output/result.json",
    )
    assert command.count("--mount") == 2
    assert all(
        f"source={output}," not in value for value in command if isinstance(value, str)
    )
    assert all("docker.sock" not in value for value in command)
    assert all("podman.sock" not in value for value in command)
    assert "--network=none" in command
    assert "--read-only" in command
    assert isinstance(command, tuple)


def test_probe_command_uses_separate_pinned_image_and_same_hardening(
    tmp_path: Path,
):
    config = _config(tmp_path)
    request_file = tmp_path / "probe-request.json"
    request_file.write_text("{}\n", encoding="utf-8")
    output = tmp_path / "probe-output"
    output.mkdir()

    command = build_oci_probe_command(
        config,
        request_path=request_file,
        output_dir=output,
        probe_id="probe-001",
    )

    assert _PROBE_IMAGE in command
    assert _WORKER_IMAGE not in command
    assert "--entrypoint=/opt/llm-wiki/probe" in command
    assert command[-6:] == (
        "--probe-request",
        "/llm-wiki/input/probe-request.json",
        "--probe-result",
        "/llm-wiki/output/probe-result.json",
        "--image-digest",
        "sha256:" + "2" * 64,
    )
    assert command.count("--mount") == 2
    assert (
        f"type=bind,source={output / 'probe-result.json'},"
        "target=/llm-wiki/output/probe-result.json"
    ) in command
    assert "--network=none" in command


def test_mount_validation_rejects_relative_comma_symlink_and_overlap(
    tmp_path: Path,
):
    config = _config(tmp_path)
    packet = tmp_path / "packet.json"
    packet_hash = _write_packet(packet)
    context = _context(packet_hash)
    output = tmp_path / "output"
    output.mkdir()

    with pytest.raises(OciBrokerError, match="absolute path"):
        build_oci_dispatch_command(
            config,
            packet_path=Path("packet.json"),
            output_dir=output,
            context=context,
        )

    comma_packet = tmp_path / "packet,unsafe.json"
    _write_packet(comma_packet)
    with pytest.raises(OciBrokerError, match="commas"):
        build_oci_dispatch_command(
            config,
            packet_path=comma_packet,
            output_dir=output,
            context=context,
        )

    nested_packet = output / "packet.json"
    _write_packet(nested_packet)
    with pytest.raises(OciBrokerError, match="cannot contain"):
        build_oci_dispatch_command(
            config,
            packet_path=nested_packet,
            output_dir=output,
            context=context,
        )

    link = tmp_path / "packet-link.json"
    try:
        link.symlink_to(packet)
    except OSError:
        pytest.skip("Symlinks are unavailable to this test account.")
    with pytest.raises(OciBrokerError, match="link|non-canonical"):
        build_oci_dispatch_command(
            config,
            packet_path=link,
            output_dir=output,
            context=context,
        )


def test_sanitized_environment_excludes_credentials_proxies_and_runtime_config():
    result = sanitized_oci_environment(
        {
            "PATH": "/usr/bin",
            "HOME": "/secret/home",
            "DOCKER_HOST": "tcp://runtime.example",
            "DOCKER_CONFIG": "/secret/docker",
            "HTTP_PROXY": "http://proxy.example",
            "HTTPS_PROXY": "http://proxy.example",
            "API_KEY": "secret",
            "XDG_RUNTIME_DIR": "/run/user/1000",
            "SYSTEMROOT": "C:\\Windows",
        }
    )

    assert result == {
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin",
        "SYSTEMROOT": "C:\\Windows",
        "XDG_RUNTIME_DIR": "/run/user/1000",
    }


def test_dispatch_uses_injected_runner_and_returns_hash_bound_receipt(
    tmp_path: Path,
):
    config = _config(tmp_path)
    packet = tmp_path / "packet.json"
    context = _context(_write_packet(packet))
    output = tmp_path / "output"
    output.mkdir()
    calls = []

    def runner(argv, **kwargs):
        calls.append((tuple(argv), kwargs))
        result_path = output / "result.json"
        assert result_path.read_bytes() == b""
        if os.name != "nt":
            assert stat.S_IMODE(result_path.stat().st_mode) == 0o600
        assert (
            f"type=bind,source={result_path},target=/llm-wiki/output/result.json"
        ) in argv
        result_path.write_bytes(canonical_result_json_bytes(_agent_result(context)))
        return BoundedProcessResult.completed(stdout=b"bounded", stderr=b"")

    outcome = dispatch_oci_agent(
        config,
        context=context,
        packet_path=packet,
        output_dir=output,
        runner=runner,
        environment={"PATH": "/usr/bin", "API_KEY": "secret"},
    )

    assert len(calls) == 1
    assert calls[0][1]["env"] == {
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin",
    }
    assert outcome.result == _agent_result(context)
    assert outcome.stdout == "bounded"
    assert outcome.receipt.status == "complete"
    assert outcome.receipt.schema_version == (
        P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION
    )
    assert outcome.receipt.packet_hash == context.packet_hash
    assert outcome.receipt.authority_hash == context.authority_hash
    assert outcome.receipt.attestation_hash == context.attestation_hash
    assert outcome.receipt.access_audit_hash == context.access_audit_hash
    assert outcome.receipt.runtime_executable_sha256 == config.executable_sha256
    assert outcome.receipt.image == _WORKER_IMAGE
    assert outcome.receipt.response_hash == _sha256(
        canonical_result_json_bytes(_agent_result(context))
    )
    assert OciDispatchReceipt.from_dict(outcome.receipt.to_dict()) == outcome.receipt

    tampered = outcome.receipt.to_dict()
    tampered["response_bytes"] += 1
    with pytest.raises(OciBrokerError, match="hash"):
        OciDispatchReceipt.from_dict(tampered)


def test_packet_or_runtime_identity_mismatch_prevents_dispatch(tmp_path: Path):
    config = _config(tmp_path)
    packet = tmp_path / "packet.json"
    _write_packet(packet)
    output = tmp_path / "output"
    output.mkdir()
    called = False

    def runner(argv, **kwargs):
        nonlocal called
        called = True
        return BoundedProcessResult.completed()

    with pytest.raises(OciBrokerError, match="packet hash"):
        dispatch_oci_agent(
            config,
            context=_context(_HASH_E),
            packet_path=packet,
            output_dir=output,
            runner=runner,
        )
    assert called is False

    bad_payload = config.to_dict()
    bad_payload["executable_sha256"] = _HASH_E
    bad_config = OciRuntimeConfig.from_dict(bad_payload)
    with pytest.raises(OciBrokerError, match="executable hash"):
        dispatch_oci_agent(
            bad_config,
            context=_context(_sha256(packet.read_bytes())),
            packet_path=packet,
            output_dir=output,
            runner=runner,
        )
    assert called is False


def test_noncanonical_agent_result_is_rejected_with_recomputable_hash(
    tmp_path: Path,
):
    config = _config(tmp_path)
    packet = tmp_path / "packet.json"
    context = _context(_write_packet(packet))
    output = tmp_path / "output"
    output.mkdir()
    payload = _agent_result(context)

    def runner(argv, **kwargs):
        (output / "result.json").write_text(
            json.dumps(payload, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return BoundedProcessResult.completed()

    outcome = dispatch_oci_agent(
        config,
        context=context,
        packet_path=packet,
        output_dir=output,
        runner=runner,
    )

    canonical = canonical_result_json_bytes(payload)
    assert outcome.receipt.status == "result_invalid"
    assert outcome.receipt.response_hash == _sha256(canonical)
    assert outcome.receipt.response_bytes == len(canonical)


def test_in_place_packet_mutation_is_recorded_as_input_changed(tmp_path: Path):
    config = _config(tmp_path)
    packet = tmp_path / "packet.json"
    context = _context(_write_packet(packet))
    output = tmp_path / "output"
    output.mkdir()

    def runner(argv, **kwargs):
        packet.write_bytes(b'{"packet":"mutated"}\n')
        return BoundedProcessResult.completed()

    outcome = dispatch_oci_agent(
        config,
        context=context,
        packet_path=packet,
        output_dir=output,
        runner=runner,
    )

    assert outcome.receipt.status == "input_changed"
    assert outcome.result is None


@pytest.mark.parametrize(
    ("kind", "expected_status"),
    [
        ("process_failed", "process_failed"),
        ("missing", "result_missing"),
        ("invalid_binding", "result_invalid"),
        ("invalid_result_id", "result_invalid"),
        ("ambiguous", "output_ambiguous"),
        ("replaced_result", "output_ambiguous"),
        ("oversized", "result_oversized"),
    ],
)
def test_dispatch_failures_are_fail_closed_receipts(
    tmp_path: Path, kind: str, expected_status: str
):
    config_payload = _oci_payload(_runtime_path(tmp_path))
    config_payload["output_limits"]["result_bytes"] = 1024
    config = OciRuntimeConfig.from_dict(config_payload)
    packet = tmp_path / "packet.json"
    context = _context(_write_packet(packet))
    output = tmp_path / "output"
    output.mkdir()

    def runner(argv, **kwargs):
        if kind == "process_failed":
            return BoundedProcessResult.completed(
                returncode=137, stderr=b"resource limit"
            )
        if kind == "invalid_binding":
            payload = _agent_result(context)
            payload["role"] = "intake-b"
            (output / "result.json").write_bytes(canonical_result_json_bytes(payload))
        elif kind == "invalid_result_id":
            payload = _agent_result(context)
            payload["result_id"] = "result-not-a-uuid"
            (output / "result.json").write_bytes(canonical_result_json_bytes(payload))
        elif kind == "ambiguous":
            (output / "result.json").write_bytes(
                canonical_result_json_bytes(_agent_result(context))
            )
            (output / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        elif kind == "replaced_result":
            (output / "result.json").unlink()
            (output / "result.json").write_bytes(
                canonical_result_json_bytes(_agent_result(context))
            )
        elif kind == "oversized":
            (output / "result.json").write_bytes(b"{" + b"x" * 1200 + b"}")
        return BoundedProcessResult.completed()

    outcome = dispatch_oci_agent(
        config,
        context=context,
        packet_path=packet,
        output_dir=output,
        runner=runner,
    )

    assert outcome.receipt.status == expected_status
    assert outcome.receipt.receipt_hash.startswith("sha256:")
    if kind in {"invalid_binding", "invalid_result_id"}:
        assert outcome.receipt.response_hash is not None
        assert outcome.result is not None
    else:
        assert outcome.result is None


def test_timeout_uses_fixed_force_cleanup_command_and_records_result(
    tmp_path: Path,
):
    config = _config(tmp_path)
    packet = tmp_path / "packet.json"
    context = _context(_write_packet(packet))
    output = tmp_path / "output"
    output.mkdir()
    calls = []

    def runner(argv, **kwargs):
        calls.append((tuple(argv), kwargs))
        if len(calls) == 1:
            return BoundedProcessResult.timeout(stderr=b"deadline")
        return BoundedProcessResult.completed()

    outcome = dispatch_oci_agent(
        config,
        context=context,
        packet_path=packet,
        output_dir=output,
        runner=runner,
    )

    assert outcome.receipt.status == "timed_out"
    assert outcome.receipt.cleanup_status == "complete"
    assert calls[1][0][1:3] == ("rm", "--force")
    assert calls[1][0][3] == outcome.receipt.container_name
    assert all(isinstance(command, tuple) for command, _ in calls)


@pytest.mark.parametrize(
    ("interruption", "expected_code"),
    [
        (KeyboardInterrupt(), None),
        (SystemExit(23), 23),
    ],
)
def test_started_dispatch_interrupt_forces_cleanup_and_preserves_semantics(
    tmp_path: Path,
    interruption: BaseException,
    expected_code: int | None,
):
    config = _config(tmp_path)
    packet = tmp_path / "packet.json"
    context = _context(_write_packet(packet))
    output = tmp_path / "output"
    output.mkdir()
    calls = []

    def runner(argv, **kwargs):
        calls.append((tuple(argv), kwargs))
        if len(calls) == 1:
            raise interruption
        return BoundedProcessResult.completed()

    with pytest.raises(type(interruption)) as exc_info:
        dispatch_oci_agent(
            config,
            context=context,
            packet_path=packet,
            output_dir=output,
            runner=runner,
        )

    assert calls[1][0][1:3] == ("rm", "--force")
    assert calls[1][0][3].startswith("p0-intake-a-1-")
    if isinstance(interruption, SystemExit):
        raised = exc_info.value
        assert isinstance(raised, SystemExit)
        assert raised.code == expected_code
    assert exc_info.value.__cause__ is None


def test_started_dispatch_interrupt_reports_unproven_cleanup_as_cause(
    tmp_path: Path,
):
    config = _config(tmp_path)
    packet = tmp_path / "packet.json"
    context = _context(_write_packet(packet))
    output = tmp_path / "output"
    output.mkdir()
    calls = []

    def runner(argv, **kwargs):
        calls.append((tuple(argv), kwargs))
        if len(calls) == 1:
            raise KeyboardInterrupt
        return BoundedProcessResult.completed(returncode=1, stderr=b"not found")

    with pytest.raises(KeyboardInterrupt) as exc_info:
        dispatch_oci_agent(
            config,
            context=context,
            packet_path=packet,
            output_dir=output,
            runner=runner,
        )

    assert len(calls) == 2
    assert isinstance(exc_info.value.__cause__, OciBrokerError)
    assert "cleanup_status=failed" in str(exc_info.value.__cause__)


def test_result_directory_scan_stops_after_proving_ambiguity(
    tmp_path: Path,
    monkeypatch,
):
    output = tmp_path / "output"
    output.mkdir()
    for name in ("result.json", "unexpected-a", "unexpected-b"):
        (output / name).write_text("{}", encoding="utf-8")
    real_scandir = os.scandir
    next_calls = 0

    class _CountingScandir:
        def __init__(self, path):
            self._entries = real_scandir(path)

        def __enter__(self):
            self._entries.__enter__()
            return self

        def __exit__(self, *args):
            return self._entries.__exit__(*args)

        def __iter__(self):
            return self

        def __next__(self):
            nonlocal next_calls
            next_calls += 1
            if next_calls > 2:
                raise AssertionError("result scan exceeded its two-entry proof bound")
            return next(self._entries)

    monkeypatch.setattr(broker.os, "scandir", _CountingScandir)

    with pytest.raises(broker._ResultArtifactError) as exc_info:
        broker._load_single_json_result(
            output,
            filename="result.json",
            maximum=1024,
            label="agent result",
        )

    assert exc_info.value.status == "output_ambiguous"
    assert next_calls == 2


def test_result_directory_accounts_aggregate_stat_size_before_read(
    tmp_path: Path,
):
    output = tmp_path / "output"
    output.mkdir()
    (output / "result.json").write_bytes(b"x" * 600)
    (output / "unexpected").write_bytes(b"x" * 500)

    with pytest.raises(broker._ResultArtifactError) as exc_info:
        broker._load_single_json_result(
            output,
            filename="result.json",
            maximum=1024,
            label="agent result",
        )

    assert exc_info.value.status == "result_oversized"


def test_probe_request_binds_real_host_controls_and_is_strict():
    with create_oci_admission_probe_environment(
        probe_id="probe-001"
    ) as probe_environment:
        request = OciAdmissionProbeRequest.create(
            cohort_id="cohort-001",
            probe_id="probe-001",
            authority_hash=_HASH_A,
            probe_environment=probe_environment,
            output_limit_bytes=65536,
        )

        assert request.required_checks == REQUIRED_ISOLATION_PROBES
        assert request.to_dict()["container_engine_sockets"] == [
            "/var/run/docker.sock",
            "/run/podman/podman.sock",
        ]
        assert request.output_limit_bytes == 65536
        output_target_id, output_target_hash = request.target_binding(
            "output_write_bound"
        )
        assert output_target_id == "single-result-output-bound"
        assert output_target_hash.startswith("sha256:")
        assert all(
            Path(sentinel.host_path).is_file()
            for sentinel in request.filesystem_sentinels
        )
        assert (
            request.network_canary.control_sha256
            == probe_environment.network_canary.control_sha256
        )
        assert OciAdmissionProbeRequest.from_dict(request.to_dict()) == request

        tampered = request.to_dict()
        tampered["required_checks"].remove("holdout_read")
        with pytest.raises(OciBrokerError, match="complete checklist"):
            OciAdmissionProbeRequest.from_dict(tampered)


def test_admission_probe_requires_all_denied_access_events(tmp_path: Path):
    config = _config(tmp_path)
    with create_oci_admission_probe_environment(
        probe_id="probe-001"
    ) as probe_environment:
        request = OciAdmissionProbeRequest.create(
            cohort_id="cohort-001",
            probe_id="probe-001",
            authority_hash=_HASH_A,
            probe_environment=probe_environment,
            output_limit_bytes=config.output_limits.result_bytes,
        )
        request_file = tmp_path / "probe-request.json"
        request_file.write_bytes(canonical_result_json_bytes(request.to_dict()))
        output = tmp_path / "probe-output"
        output.mkdir()

        def runner(argv, **kwargs):
            result_path = output / "probe-result.json"
            assert result_path.read_bytes() == b""
            assert (
                f"type=bind,source={result_path},"
                "target=/llm-wiki/output/probe-result.json"
            ) in argv
            result_path.write_bytes(
                canonical_result_json_bytes(_passing_probe_result(request))
            )
            return BoundedProcessResult.completed(stdout=b"probe complete")

        outcome = execute_oci_admission_probe(
            config,
            request_path=request_file,
            output_dir=output,
            probe_environment=probe_environment,
            runner=runner,
        )

        assert outcome.passed is True
        assert outcome.execution_status == "complete"
        assert outcome.result is not None
        assert len(outcome.result.access_events) == len(REQUIRED_ISOLATION_PROBES)
        assert all(
            event.attempted and event.outcome == "denied"
            for event in outcome.result.access_events
        )
        assert outcome.result_hash == _sha256(
            (output / "probe-result.json").read_bytes()
        )
        assert outcome.command_hash.startswith("sha256:")


def test_probe_rejects_a_denial_claim_after_the_host_canary_was_reached(
    tmp_path: Path,
):
    config = _config(tmp_path)
    with create_oci_admission_probe_environment(
        probe_id="probe-canary-audit"
    ) as probe_environment:
        request = OciAdmissionProbeRequest.create(
            cohort_id="cohort-001",
            probe_id="probe-canary-audit",
            authority_hash=_HASH_A,
            probe_environment=probe_environment,
            output_limit_bytes=config.output_limits.result_bytes,
        )
        request_file = tmp_path / "probe-request.json"
        request_file.write_bytes(canonical_result_json_bytes(request.to_dict()))
        output = tmp_path / "probe-output"
        output.mkdir()

        def runner(argv, **kwargs):
            del argv, kwargs
            canary = request.network_canary
            with socket.create_connection(
                (canary.host, canary.port), timeout=2
            ) as conn:
                conn.sendall(canary.challenge.encode("ascii") + b"\n")
                assert conn.recv(256)
            (output / "probe-result.json").write_bytes(
                canonical_result_json_bytes(_passing_probe_result(request))
            )
            return BoundedProcessResult.completed()

        outcome = execute_oci_admission_probe(
            config,
            request_path=request_file,
            output_dir=output,
            probe_environment=probe_environment,
            runner=runner,
        )

        assert outcome.passed is False
        assert outcome.execution_status == "result_invalid"
        assert "host-side connection audit" in (outcome.error or "")
        assert probe_environment.post_control_network_connections == 1


def test_probe_rejects_changed_host_sentinel_before_process_start(tmp_path: Path):
    config = _config(tmp_path)
    with create_oci_admission_probe_environment(
        probe_id="probe-sentinel-audit"
    ) as probe_environment:
        request = OciAdmissionProbeRequest.create(
            cohort_id="cohort-001",
            probe_id="probe-sentinel-audit",
            authority_hash=_HASH_A,
            probe_environment=probe_environment,
            output_limit_bytes=config.output_limits.result_bytes,
        )
        request_file = tmp_path / "probe-request.json"
        request_file.write_bytes(canonical_result_json_bytes(request.to_dict()))
        output = tmp_path / "probe-output"
        output.mkdir()
        sentinel_path = Path(request.filesystem_sentinels[0].host_path)
        original = sentinel_path.read_bytes()
        sentinel_path.write_bytes(b"x" * len(original))
        called = False

        def runner(argv, **kwargs):
            del argv, kwargs
            nonlocal called
            called = True
            return BoundedProcessResult.completed()

        try:
            with pytest.raises(OciBrokerError, match="sentinel bytes changed"):
                execute_oci_admission_probe(
                    config,
                    request_path=request_file,
                    output_dir=output,
                    probe_environment=probe_environment,
                    runner=runner,
                )
        finally:
            sentinel_path.write_bytes(original)
        assert called is False


def test_probe_result_must_bind_every_host_target(tmp_path: Path):
    config = _config(tmp_path)
    with create_oci_admission_probe_environment(
        probe_id="probe-target-binding"
    ) as probe_environment:
        request = OciAdmissionProbeRequest.create(
            cohort_id="cohort-001",
            probe_id="probe-target-binding",
            authority_hash=_HASH_A,
            probe_environment=probe_environment,
            output_limit_bytes=config.output_limits.result_bytes,
        )
        request_file = tmp_path / "probe-request.json"
        request_file.write_bytes(canonical_result_json_bytes(request.to_dict()))
        output = tmp_path / "probe-output"
        output.mkdir()

        def runner(argv, **kwargs):
            del argv, kwargs
            payload = _passing_probe_result(request)
            payload["access_events"][0]["target_id"] = "forged-sentinel"
            (output / "probe-result.json").write_bytes(
                canonical_result_json_bytes(payload)
            )
            return BoundedProcessResult.completed()

        outcome = execute_oci_admission_probe(
            config,
            request_path=request_file,
            output_dir=output,
            probe_environment=probe_environment,
            runner=runner,
        )

        assert outcome.passed is False
        assert outcome.execution_status == "result_invalid"
        assert "target evidence" in (outcome.error or "")


def test_admission_probe_access_or_missing_event_cannot_pass(tmp_path: Path):
    config = _config(tmp_path)
    with create_oci_admission_probe_environment(
        probe_id="probe-001"
    ) as probe_environment:
        request = OciAdmissionProbeRequest.create(
            cohort_id="cohort-001",
            probe_id="probe-001",
            authority_hash=_HASH_A,
            probe_environment=probe_environment,
            output_limit_bytes=config.output_limits.result_bytes,
        )
        request_file = tmp_path / "probe-request.json"
        request_file.write_bytes(canonical_result_json_bytes(request.to_dict()))

        failed_output = tmp_path / "failed-output"
        failed_output.mkdir()

        def failed_runner(argv, **kwargs):
            (failed_output / "probe-result.json").write_bytes(
                canonical_result_json_bytes(
                    _passing_probe_result(request, failed_probe="holdout_read")
                )
            )
            return BoundedProcessResult.completed()

        failed = execute_oci_admission_probe(
            config,
            request_path=request_file,
            output_dir=failed_output,
            probe_environment=probe_environment,
            runner=failed_runner,
        )
        assert failed.passed is False
        assert failed.execution_status == "probe_failed"
        assert failed.result is not None
        assert failed.result.status == "failed"

        missing_output = tmp_path / "missing-output"
        missing_output.mkdir()

        def missing_runner(argv, **kwargs):
            payload = _passing_probe_result(request)
            payload["access_events"].pop()
            (missing_output / "probe-result.json").write_bytes(
                canonical_result_json_bytes(payload)
            )
            return BoundedProcessResult.completed()

        missing = execute_oci_admission_probe(
            config,
            request_path=request_file,
            output_dir=missing_output,
            probe_environment=probe_environment,
            runner=missing_runner,
        )
        assert missing.passed is False
        assert missing.execution_status == "result_invalid"
        assert "every access event" in (missing.error or "")


def test_admission_probe_result_contract_rejects_false_pass_status():
    with create_oci_admission_probe_environment(
        probe_id="probe-001"
    ) as probe_environment:
        request = OciAdmissionProbeRequest.create(
            cohort_id="cohort-001",
            probe_id="probe-001",
            authority_hash=_HASH_A,
            probe_environment=probe_environment,
            output_limit_bytes=65536,
        )
        payload = _passing_probe_result(request, failed_probe="network_egress")
        payload["status"] = "passed"

        with pytest.raises(OciBrokerError, match="status"):
            OciAdmissionProbeResult.from_dict(payload)


def test_output_bound_probe_rejects_forged_denial_evidence():
    with create_oci_admission_probe_environment(
        probe_id="probe-output-bound"
    ) as probe_environment:
        request = OciAdmissionProbeRequest.create(
            cohort_id="cohort-001",
            probe_id="probe-output-bound",
            authority_hash=_HASH_A,
            probe_environment=probe_environment,
            output_limit_bytes=65536,
        )
        payload = _passing_probe_result(request)
        output_event = next(
            event
            for event in payload["access_events"]
            if event["probe"] == "output_write_bound"
        )
        output_event["evidence"]["oversize_write_succeeded"] = True

        with pytest.raises(OciBrokerError, match="accessible output capacity"):
            OciAdmissionProbeResult.from_dict(payload)


def test_bounded_process_runner_hashes_full_output_but_retains_only_limit():
    command = (
        sys.executable,
        "-c",
        (
            "import sys;"
            "sys.stdout.buffer.write(b'abcdefghij');"
            "sys.stderr.buffer.write(b'uvwxyz')"
        ),
    )

    result = run_bounded_process(
        command,
        env=sanitized_oci_environment({}),
        timeout_seconds=10,
        termination_grace_seconds=1,
        stdout_limit=4,
        stderr_limit=3,
    )

    assert result.returncode == 0
    assert result.stdout == b"abcd"
    assert result.stderr == b"uvw"
    assert result.stdout_bytes == 10
    assert result.stderr_bytes == 6
    assert result.stdout_sha256 == _sha256(b"abcdefghij")
    assert result.stderr_sha256 == _sha256(b"uvwxyz")
    assert result.stdout_truncated is True
    assert result.stderr_truncated is True

    with pytest.raises(OciBrokerError, match="sanitized allowlist"):
        run_bounded_process(
            command,
            env={"API_KEY": "must-not-reach-child"},
            timeout_seconds=10,
            termination_grace_seconds=1,
            stdout_limit=4,
            stderr_limit=3,
        )
