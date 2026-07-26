"""Ubuntu-only real-Docker qualification for the synthetic P0 OCI fixture."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from llm_wiki_cli.services.contracts import (
    P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION,
)
from llm_wiki_cli.services.documentation_calibration_broker import (
    REQUIRED_ISOLATION_PROBES,
    OciAdmissionProbeRequest,
    OciDispatchContext,
    OciRuntimeConfig,
    canonical_result_json_bytes,
    create_oci_admission_probe_environment,
    dispatch_oci_agent,
    execute_oci_admission_probe,
)


pytestmark = pytest.mark.oci_integration

_RUN_ENV = "LLM_WIKI_RUN_OCI_INTEGRATION"
_DOCKER_ENV = "LLM_WIKI_OCI_DOCKER"
_IMAGE_ENV = "LLM_WIKI_OCI_TEST_IMAGE"
_COHORT_ID = "00000000-0000-4000-8000-000000000101"
_PACKET_ID = "00000000-0000-4000-8000-000000000102"
_HASH_A = "sha256:" + "a" * 64
_HASH_B = "sha256:" + "b" * 64
_HASH_C = "sha256:" + "c" * 64
_HASH_D = "sha256:" + "d" * 64


def _sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            hasher.update(chunk)
    return "sha256:" + hasher.hexdigest()


def _required_oci_inputs() -> tuple[Path, str, int, int]:
    if os.environ.get(_RUN_ENV) != "1":
        pytest.skip(f"Set {_RUN_ENV}=1 only in the dedicated OCI lane.")
    assert os.name == "posix", "The qualifying OCI lane is Ubuntu-only."
    assert hasattr(os, "getuid") and hasattr(os, "getgid")
    uid, gid = os.getuid(), os.getgid()
    assert uid > 0 and gid > 0, "OCI fixture requires a non-root host account."
    executable_value = os.environ.get(_DOCKER_ENV)
    image = os.environ.get(_IMAGE_ENV)
    assert executable_value, f"{_DOCKER_ENV} is required."
    assert image and "@sha256:" in image, (
        f"{_IMAGE_ENV} must be a digest-pinned local image."
    )
    executable = Path(executable_value)
    assert executable.is_absolute() and executable.is_file()
    assert executable.resolve(strict=True) == executable
    return executable, image, uid, gid


def test_real_docker_probe_and_worker_are_isolated(tmp_path: Path):
    """Qualify only the public synthetic local-no-egress broker mechanics."""

    executable, image, uid, gid = _required_oci_inputs()
    config = OciRuntimeConfig.from_dict(
        {
            "runtime": "docker",
            "executable": str(executable),
            "executable_sha256": _sha256_file(executable),
            "worker": {
                "image": image,
                "entrypoint": ["/opt/llm-wiki/oci-fixture", "worker"],
            },
            "probe": {
                "image": image,
                "entrypoint": ["/opt/llm-wiki/oci-fixture", "probe"],
            },
            "user": f"{uid}:{gid}",
            "resources": {
                "pids_limit": 32,
                "memory_bytes": 268435456,
                "cpu_millis": 1000,
                "tmpfs_bytes": 16777216,
            },
            "timeout_seconds": 60,
            "termination_grace_seconds": 5,
            "max_packet_bytes": 1048576,
            "output_limits": {
                "stdout_bytes": 65536,
                "stderr_bytes": 65536,
                "result_bytes": 1048576,
            },
        }
    )

    with create_oci_admission_probe_environment(
        probe_id="synthetic-probe-001"
    ) as probe_environment:
        probe_request = OciAdmissionProbeRequest.create(
            cohort_id=_COHORT_ID,
            probe_id="synthetic-probe-001",
            authority_hash=_HASH_A,
            probe_environment=probe_environment,
            output_limit_bytes=config.output_limits.result_bytes,
        )
        probe_request_path = tmp_path / "probe-request.json"
        probe_request_path.write_bytes(
            canonical_result_json_bytes(probe_request.to_dict())
        )
        probe_output = tmp_path / "probe-output"
        probe_output.mkdir()
        probe = execute_oci_admission_probe(
            config,
            request_path=probe_request_path,
            output_dir=probe_output,
            probe_environment=probe_environment,
        )

        assert probe.passed is True
        assert probe.execution_status == "complete"
        assert probe.cleanup_status == "not_required"
        assert probe.process.returncode == 0
        assert probe.result is not None
        assert (
            tuple(event.probe for event in probe.result.access_events)
            == REQUIRED_ISOLATION_PROBES
        )
        assert all(
            event.attempted and event.outcome == "denied"
            for event in probe.result.access_events
        )
        output_bound = next(
            event
            for event in probe.result.access_events
            if event.probe == "output_write_bound"
        )
        assert output_bound.evidence == {
            "limit_bytes": config.output_limits.result_bytes,
            "attempted_bytes": config.output_limits.result_bytes + 1,
            "oversize_write_succeeded": False,
            "sibling_write_succeeded": False,
            "observed_size": 0,
        }
        assert [path.name for path in probe_output.iterdir()] == ["probe-result.json"]

    packet = {
        "schema_version": P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION,
        "cohort_id": _COHORT_ID,
        "packet_id": _PACKET_ID,
        "role": "intake-a",
        "attempt": 1,
        "idempotency_key": "synthetic-oci:intake-a:1",
        "evidence": {
            "citation_id": "synthetic-public-evidence",
            "statement": "Public synthetic fixture with no private source.",
        },
    }
    packet_bytes = canonical_result_json_bytes(packet)
    packet_path = tmp_path / "packet.json"
    packet_path.write_bytes(packet_bytes)
    packet_hash = _sha256_bytes(packet_bytes)
    worker_output = tmp_path / "worker-output"
    worker_output.mkdir()
    dispatch = dispatch_oci_agent(
        config,
        context=OciDispatchContext(
            cohort_id=_COHORT_ID,
            generation=3,
            head_transition_hash=_HASH_B,
            role="intake-a",
            attempt=1,
            packet_id=_PACKET_ID,
            packet_hash=packet_hash,
            authority_hash=_HASH_A,
            attestation_hash=_HASH_C,
            access_audit_hash=_HASH_D,
            idempotency_key="synthetic-oci:intake-a:1",
        ),
        packet_path=packet_path,
        output_dir=worker_output,
    )

    assert dispatch.receipt.status == "complete"
    assert dispatch.receipt.cleanup_status == "not_required"
    assert dispatch.receipt.packet_hash == packet_hash
    assert dispatch.receipt.image == image
    assert dispatch.receipt.response_hash is not None
    assert dispatch.result is not None
    assert dispatch.result["status"] == "complete"
    assert dispatch.result["proposal"]["purpose"]["citations"] == [
        "synthetic-public-evidence"
    ]
    assert [path.name for path in worker_output.iterdir()] == ["result.json"]
