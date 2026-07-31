"""Provider-neutral OCI broker for qualifying documentation calibration agents.

The broker deliberately owns no model-provider SDK, endpoint, or credential.
For the qualifying ``local_no_egress`` profile it invokes a caller-resolved
Docker or Podman executable with fixed argument vectors, a minimal host
environment, a digest-pinned image, and exactly two bind mounts: one JSON packet
mounted read-only for the container and one pre-created result artifact.  The
surrounding container root is read-only, so the artifact is the only persistent
writable target; an exact ``RLIMIT_FSIZE`` bounds it while the process is
running.

This module is intentionally separate from the documentation-run v1 lifecycle.
The protected calibration controller owns authority, state transitions, and
artifact persistence; the broker only validates one frozen OCI runtime section,
executes a bounded process, and returns hash-bound evidence.

Frozen value objects and hash bindings provide application-level
content-integrity checks within the host trust domain.  They do not authenticate
evidence against the filesystem owner, root, or offline modification.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import socket
import stat
import subprocess
import tempfile
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping, Optional, Protocol, Sequence

from . import _restore_legacy_definition_modules
from ..contracts import (
    OCI_MAX_PACKET_BYTES,
    P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
    P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION,
    P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION,
    P0_CALIBRATION_ISOLATION_PROBE_REQUEST_SCHEMA_VERSION,
    P0_CALIBRATION_ISOLATION_PROBE_RESULT_SCHEMA_VERSION,
)
from ..filesystem_guard import atomic_write_private_bytes
from ..redaction import (
    LIKELY_SECRET_RE as _LIKELY_SECRET_RE,
    SENSITIVE_KEYS as _SENSITIVE_KEYS,
)
from ..validation import (
    is_canonical_uuid,
    path_is_within as shared_path_is_within,
    require_bounded_int,
    require_bounded_text,
    require_exact_fields,
    require_int,
    require_mapping,
    require_nonempty_text,
    require_sha256,
    require_string_tuple,
    require_uuid,
)


LOCAL_NO_EGRESS_PROFILE = "local_no_egress"
SUPPORTED_OCI_RUNTIMES = frozenset({"docker", "podman"})
CALIBRATION_AGENT_ROLES = ("intake-a", "intake-b", "intake-c", "verifier")
SUPPORTED_AGENT_ROLES = frozenset(CALIBRATION_AGENT_ROLES)
REQUIRED_ISOLATION_PROBES = (
    "controller_read",
    "source_read",
    "credential_read",
    "other_role_read",
    "holdout_read",
    "network_egress",
    "container_engine_socket",
    "output_write_bound",
)
FILESYSTEM_ISOLATION_PROBES = REQUIRED_ISOLATION_PROBES[:5]
_OUTPUT_WRITE_BOUND_PROBE = "output_write_bound"
_OUTPUT_BOUND_TARGET_ID = "single-result-output-bound"
_OUTPUT_BOUND_MECHANISM = "single_file_bind+rlimit_fsize/v1"
_CONTAINER_ENGINE_SOCKET_TARGETS = (
    "/var/run/docker.sock",
    "/run/podman/podman.sock",
)

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$")
_PUBLIC_RECIPIENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+~-]{0,255}$")
_CONTAINER_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,62}$")
_IMAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*@sha256:[0-9a-f]{64}$")
_NUMERIC_USER_RE = re.compile(r"^([0-9]{1,10}):([0-9]{1,10})$")
_HEX_32_RE = re.compile(r"^[0-9a-f]{64}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_HOST_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "PATH",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "WINDIR",
    "XDG_RUNTIME_DIR",
)
_CONTAINER_ENVIRONMENT = (
    "HOME=/tmp",
    "LANG=C.UTF-8",
    "LC_ALL=C.UTF-8",
    "TMPDIR=/tmp",
)
_PACKET_CONTAINER_PATH = "/llm-wiki/input/packet.json"
_RESULT_CONTAINER_PATH = "/llm-wiki/output/result.json"
_PROBE_REQUEST_CONTAINER_PATH = "/llm-wiki/input/probe-request.json"
_PROBE_RESULT_CONTAINER_PATH = "/llm-wiki/output/probe-result.json"
_RESULT_FILENAME = "result.json"
_PROBE_RESULT_FILENAME = "probe-result.json"
_MAX_RUNTIME_EXECUTABLE_BYTES = 512 * 1024 * 1024
_CLEANUP_TIMEOUT_SECONDS = 30
_CLEANUP_LOG_LIMIT_BYTES = 4096
_MIN_MEMORY_BYTES = 64 * 1024 * 1024
_MAX_MEMORY_BYTES = 64 * 1024 * 1024 * 1024
_MIN_TMPFS_BYTES = 1024 * 1024
_MAX_STREAM_BYTES = 16 * 1024 * 1024
_MAX_RESULT_BYTES = 64 * 1024 * 1024


class OciBrokerError(ValueError):
    """Raised when OCI configuration or dispatch evidence is unsafe."""


class OciProcessRunner(Protocol):
    """Dependency-injected bounded process runner."""

    def __call__(
        self,
        argv: Sequence[str],
        *,
        env: Mapping[str, str],
        timeout_seconds: int,
        termination_grace_seconds: int,
        stdout_limit: int,
        stderr_limit: int,
    ) -> "BoundedProcessResult":
        """Execute one fixed argument vector without a shell."""
        ...


@dataclass(frozen=True)
class OciImageCommand:
    """One digest-pinned OCI image and its fixed in-container entrypoint."""

    image: str
    entrypoint: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_digest_pinned_image(self.image)
        if not self.entrypoint or len(self.entrypoint) > 32:
            raise OciBrokerError("OCI entrypoint must contain 1-32 arguments.")
        executable = self.entrypoint[0]
        if not PurePosixPath(executable).is_absolute():
            raise OciBrokerError(
                "OCI entrypoint executable must be an absolute container path."
            )
        for index, value in enumerate(self.entrypoint):
            _validate_argv_value(value, f"OCI entrypoint argument {index}")
        reserved_flags = {
            "--packet",
            "--result",
            "--probe-request",
            "--probe-result",
            "--image-digest",
        }
        if any(
            value in reserved_flags
            or any(value.startswith(flag + "=") for flag in reserved_flags)
            for value in self.entrypoint[1:]
        ):
            raise OciBrokerError(
                "OCI entrypoint cannot override broker-owned packet/result flags."
            )

    @property
    def digest(self) -> str:
        """Return the digest-pinned image identifier."""

        return self.image.rsplit("@", 1)[1]

    def to_dict(self) -> dict[str, Any]:
        return {"image": self.image, "entrypoint": list(self.entrypoint)}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, label: str) -> "OciImageCommand":
        _validate_object(payload, {"image", "entrypoint"}, label)
        return cls(
            image=_required_text(payload.get("image"), f"{label}.image"),
            entrypoint=_text_tuple(
                payload.get("entrypoint"), f"{label}.entrypoint", maximum=32
            ),
        )


@dataclass(frozen=True)
class OciResourceLimits:
    """Portable Docker/Podman resource ceilings."""

    pids_limit: int
    memory_bytes: int
    cpu_millis: int
    tmpfs_bytes: int

    def __post_init__(self) -> None:
        _bounded_int(self.pids_limit, "pids_limit", minimum=1, maximum=1024)
        _bounded_int(
            self.memory_bytes,
            "memory_bytes",
            minimum=_MIN_MEMORY_BYTES,
            maximum=_MAX_MEMORY_BYTES,
        )
        _bounded_int(self.cpu_millis, "cpu_millis", minimum=100, maximum=8000)
        _bounded_int(
            self.tmpfs_bytes,
            "tmpfs_bytes",
            minimum=_MIN_TMPFS_BYTES,
            maximum=min(self.memory_bytes, _MAX_MEMORY_BYTES),
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "pids_limit": self.pids_limit,
            "memory_bytes": self.memory_bytes,
            "cpu_millis": self.cpu_millis,
            "tmpfs_bytes": self.tmpfs_bytes,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OciResourceLimits":
        _validate_object(
            payload,
            {"pids_limit", "memory_bytes", "cpu_millis", "tmpfs_bytes"},
            "oci.resources",
        )
        return cls(
            pids_limit=_required_int(payload.get("pids_limit"), "pids_limit"),
            memory_bytes=_required_int(payload.get("memory_bytes"), "memory_bytes"),
            cpu_millis=_required_int(payload.get("cpu_millis"), "cpu_millis"),
            tmpfs_bytes=_required_int(payload.get("tmpfs_bytes"), "tmpfs_bytes"),
        )


@dataclass(frozen=True)
class OciOutputLimits:
    """Bounded process and result capture sizes."""

    stdout_bytes: int
    stderr_bytes: int
    result_bytes: int

    def __post_init__(self) -> None:
        _bounded_int(
            self.stdout_bytes,
            "stdout_bytes",
            minimum=1,
            maximum=_MAX_STREAM_BYTES,
        )
        _bounded_int(
            self.stderr_bytes,
            "stderr_bytes",
            minimum=1,
            maximum=_MAX_STREAM_BYTES,
        )
        _bounded_int(
            self.result_bytes,
            "result_bytes",
            minimum=2,
            maximum=_MAX_RESULT_BYTES,
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "stdout_bytes": self.stdout_bytes,
            "stderr_bytes": self.stderr_bytes,
            "result_bytes": self.result_bytes,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OciOutputLimits":
        _validate_object(
            payload,
            {"stdout_bytes", "stderr_bytes", "result_bytes"},
            "oci.output_limits",
        )
        return cls(
            stdout_bytes=_required_int(payload.get("stdout_bytes"), "stdout_bytes"),
            stderr_bytes=_required_int(payload.get("stderr_bytes"), "stderr_bytes"),
            result_bytes=_required_int(payload.get("result_bytes"), "result_bytes"),
        )


@dataclass(frozen=True)
class OciRuntimeConfig:
    """Strict local-no-egress section of a frozen execution manifest."""

    runtime: str
    executable: str
    executable_sha256: str
    worker: OciImageCommand
    probe: OciImageCommand
    user: str
    resources: OciResourceLimits
    timeout_seconds: int
    termination_grace_seconds: int
    max_packet_bytes: int
    output_limits: OciOutputLimits

    def __post_init__(self) -> None:
        if self.runtime not in SUPPORTED_OCI_RUNTIMES:
            raise OciBrokerError("OCI runtime must be docker or podman.")
        _validate_runtime_executable_name(self.runtime, self.executable)
        _validate_hash(self.executable_sha256, "executable_sha256")
        match = _NUMERIC_USER_RE.fullmatch(self.user)
        if match is None:
            raise OciBrokerError("OCI user must use a numeric uid:gid form.")
        uid, gid = (int(value) for value in match.groups())
        if uid <= 0 or gid <= 0 or uid > 2**31 - 1 or gid > 2**31 - 1:
            raise OciBrokerError("OCI user uid and gid must both be non-root.")
        _bounded_int(
            self.timeout_seconds,
            "timeout_seconds",
            minimum=1,
            maximum=3600,
        )
        _bounded_int(
            self.termination_grace_seconds,
            "termination_grace_seconds",
            minimum=1,
            maximum=30,
        )
        _bounded_int(
            self.max_packet_bytes,
            "max_packet_bytes",
            minimum=2,
            maximum=OCI_MAX_PACKET_BYTES,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtime": self.runtime,
            "executable": self.executable,
            "executable_sha256": self.executable_sha256,
            "worker": self.worker.to_dict(),
            "probe": self.probe.to_dict(),
            "user": self.user,
            "resources": self.resources.to_dict(),
            "timeout_seconds": self.timeout_seconds,
            "termination_grace_seconds": self.termination_grace_seconds,
            "max_packet_bytes": self.max_packet_bytes,
            "output_limits": self.output_limits.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OciRuntimeConfig":
        """Parse an exact, credential-free OCI runtime object."""

        _reject_sensitive_material(payload, "oci")
        _validate_object(
            payload,
            {
                "runtime",
                "executable",
                "executable_sha256",
                "worker",
                "probe",
                "user",
                "resources",
                "timeout_seconds",
                "termination_grace_seconds",
                "max_packet_bytes",
                "output_limits",
            },
            "oci",
        )
        worker = _required_mapping(payload.get("worker"), "oci.worker")
        probe = _required_mapping(payload.get("probe"), "oci.probe")
        resources = _required_mapping(payload.get("resources"), "oci.resources")
        output_limits = _required_mapping(
            payload.get("output_limits"), "oci.output_limits"
        )
        return cls(
            runtime=_required_text(payload.get("runtime"), "oci.runtime"),
            executable=_required_text(payload.get("executable"), "oci.executable"),
            executable_sha256=_required_text(
                payload.get("executable_sha256"), "oci.executable_sha256"
            ),
            worker=OciImageCommand.from_dict(worker, label="oci.worker"),
            probe=OciImageCommand.from_dict(probe, label="oci.probe"),
            user=_required_text(payload.get("user"), "oci.user"),
            resources=OciResourceLimits.from_dict(resources),
            timeout_seconds=_required_int(
                payload.get("timeout_seconds"), "oci.timeout_seconds"
            ),
            termination_grace_seconds=_required_int(
                payload.get("termination_grace_seconds"),
                "oci.termination_grace_seconds",
            ),
            max_packet_bytes=_required_int(
                payload.get("max_packet_bytes"), "oci.max_packet_bytes"
            ),
            output_limits=OciOutputLimits.from_dict(output_limits),
        )

    @classmethod
    def from_execution_manifest(cls, payload: Mapping[str, Any]) -> "OciRuntimeConfig":
        """Extract the strict OCI object from a broader execution manifest."""

        validated = validate_execution_manifest(payload)
        if validated["profile"] != LOCAL_NO_EGRESS_PROFILE:
            raise OciBrokerError(
                "OCI broker only qualifies the local_no_egress profile."
            )
        return cls.from_dict(_required_mapping(validated.get("oci"), "oci"))


def validate_execution_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize either supported credential-free broker profile.

    The execution manifest is frozen before the controller allocates a cohort
    UUID, so cohort-specific authority and state never appear here.
    """

    _reject_sensitive_material(payload, "execution manifest")
    _validate_object(
        payload,
        {
            "schema_version",
            "profile",
            "roles",
            "budgets",
            "oci",
            "external_routes",
        },
        "execution manifest",
    )
    if (
        payload.get("schema_version")
        != P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION
    ):
        raise OciBrokerError("Unsupported execution-manifest schema_version.")
    profile = _required_text(payload.get("profile"), "profile")
    if profile not in {LOCAL_NO_EGRESS_PROFILE, "external_authorized"}:
        raise OciBrokerError("Execution manifest profile is unsupported.")
    raw_roles = payload.get("roles")
    if not isinstance(raw_roles, list) or tuple(raw_roles) != CALIBRATION_AGENT_ROLES:
        raise OciBrokerError(
            "Execution manifest roles must equal the canonical four-role lifecycle."
        )

    raw_budgets = _required_mapping(payload.get("budgets"), "budgets")
    _validate_object(
        raw_budgets,
        {
            "max_concurrent_workers",
            "max_attempts_per_role",
            "max_total_calls",
            "max_packet_bytes",
            "max_result_bytes",
        },
        "execution manifest budgets",
    )
    max_concurrent_workers = _required_int(
        raw_budgets.get("max_concurrent_workers"), "max_concurrent_workers"
    )
    max_attempts_per_role = _required_int(
        raw_budgets.get("max_attempts_per_role"), "max_attempts_per_role"
    )
    if max_concurrent_workers != 3:
        raise OciBrokerError("max_concurrent_workers must equal 3.")
    if max_attempts_per_role != 2:
        raise OciBrokerError("max_attempts_per_role must equal 2.")
    max_total_calls = _required_int(
        raw_budgets.get("max_total_calls"), "max_total_calls"
    )
    _bounded_int(max_total_calls, "max_total_calls", minimum=4, maximum=8)
    max_packet_bytes = _required_int(
        raw_budgets.get("max_packet_bytes"), "budgets.max_packet_bytes"
    )
    _bounded_int(
        max_packet_bytes,
        "budgets.max_packet_bytes",
        minimum=2,
        maximum=OCI_MAX_PACKET_BYTES,
    )
    max_result_bytes = _required_int(
        raw_budgets.get("max_result_bytes"), "budgets.max_result_bytes"
    )
    _bounded_int(
        max_result_bytes,
        "budgets.max_result_bytes",
        minimum=2,
        maximum=_MAX_RESULT_BYTES,
    )
    budgets = {
        "max_concurrent_workers": max_concurrent_workers,
        "max_attempts_per_role": max_attempts_per_role,
        "max_total_calls": max_total_calls,
        "max_packet_bytes": max_packet_bytes,
        "max_result_bytes": max_result_bytes,
    }

    raw_routes = payload.get("external_routes")
    if not isinstance(raw_routes, list):
        raise OciBrokerError("external_routes must be a list.")
    if profile == LOCAL_NO_EGRESS_PROFILE:
        if raw_routes:
            raise OciBrokerError(
                "local_no_egress cannot contain external broker routes."
            )
        config = OciRuntimeConfig.from_dict(
            _required_mapping(payload.get("oci"), "oci")
        )
        if config.max_packet_bytes != max_packet_bytes:
            raise OciBrokerError(
                "OCI max_packet_bytes must match the execution budget."
            )
        if config.output_limits.result_bytes > max_result_bytes:
            raise OciBrokerError("OCI result_bytes cannot exceed the execution budget.")
        oci: Optional[dict[str, Any]] = config.to_dict()
        routes: list[dict[str, Any]] = []
    else:
        if payload.get("oci") is not None:
            raise OciBrokerError("external_authorized requires oci=null.")
        if not raw_routes:
            raise OciBrokerError(
                "external_authorized requires at least one broker route."
            )
        oci = None
        routes = _validate_external_routes(
            raw_routes,
            max_total_calls=max_total_calls,
            max_packet_bytes=max_packet_bytes,
            max_result_bytes=max_result_bytes,
        )

    return {
        "schema_version": P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION,
        "profile": profile,
        "roles": list(CALIBRATION_AGENT_ROLES),
        "budgets": budgets,
        "oci": oci,
        "external_routes": routes,
    }


def _validate_external_routes(
    raw_routes: Sequence[Any],
    *,
    max_total_calls: int,
    max_packet_bytes: int,
    max_result_bytes: int,
) -> list[dict[str, Any]]:
    routes = []
    seen_route_ids: set[str] = set()
    seen_recipients: set[str] = set()
    for index, raw in enumerate(raw_routes):
        route = _required_mapping(raw, f"external_routes[{index}]")
        _validate_object(
            route,
            {
                "route_id",
                "recipient",
                "max_calls",
                "max_request_bytes",
                "max_response_bytes",
            },
            f"external_routes[{index}]",
        )
        route_id = _required_text(route.get("route_id"), "route_id")
        _validate_slug(route_id, "route_id")
        if route_id in seen_route_ids:
            raise OciBrokerError(f"Duplicate external route_id: {route_id}")
        seen_route_ids.add(route_id)
        recipient = _required_text(route.get("recipient"), "recipient")
        if (
            _PUBLIC_RECIPIENT_RE.fullmatch(recipient) is None
            or "://" in recipient
            or _LIKELY_SECRET_RE.search(recipient)
        ):
            raise OciBrokerError(
                "External route recipient must be a credential-free public identifier."
            )
        if recipient in seen_recipients:
            raise OciBrokerError(f"Duplicate external route recipient: {recipient}")
        seen_recipients.add(recipient)
        max_calls = _required_int(route.get("max_calls"), "route.max_calls")
        _bounded_int(
            max_calls,
            "route.max_calls",
            minimum=1,
            maximum=max_total_calls,
        )
        max_request = _required_int(
            route.get("max_request_bytes"), "route.max_request_bytes"
        )
        _bounded_int(
            max_request,
            "route.max_request_bytes",
            minimum=2,
            maximum=max_packet_bytes,
        )
        max_response = _required_int(
            route.get("max_response_bytes"), "route.max_response_bytes"
        )
        _bounded_int(
            max_response,
            "route.max_response_bytes",
            minimum=2,
            maximum=max_result_bytes,
        )
        routes.append(
            {
                "route_id": route_id,
                "recipient": recipient,
                "max_calls": max_calls,
                "max_request_bytes": max_request,
                "max_response_bytes": max_response,
            }
        )
    return routes


@dataclass(frozen=True)
class BoundedProcessResult:
    """Bounded in-memory output plus complete stream hashes and byte counts."""

    started: bool
    returncode: Optional[int]
    timed_out: bool
    error: Optional[str]
    stdout: bytes
    stderr: bytes
    stdout_bytes: int
    stderr_bytes: int
    stdout_sha256: str
    stderr_sha256: str
    stdout_truncated: bool
    stderr_truncated: bool

    def __post_init__(self) -> None:
        if not isinstance(self.stdout, bytes) or not isinstance(self.stderr, bytes):
            raise OciBrokerError("Bounded process output must be bytes.")
        if self.stdout_bytes < len(self.stdout) or self.stderr_bytes < len(self.stderr):
            raise OciBrokerError("Process byte counts cannot be below captured bytes.")
        _validate_hash(self.stdout_sha256, "stdout_sha256")
        _validate_hash(self.stderr_sha256, "stderr_sha256")
        if self.stdout_truncated != (self.stdout_bytes > len(self.stdout)):
            raise OciBrokerError("stdout_truncated is inconsistent.")
        if self.stderr_truncated != (self.stderr_bytes > len(self.stderr)):
            raise OciBrokerError("stderr_truncated is inconsistent.")
        if not self.stdout_truncated and self.stdout_sha256 != _bytes_sha256(
            self.stdout
        ):
            raise OciBrokerError("stdout_sha256 does not match captured output.")
        if not self.stderr_truncated and self.stderr_sha256 != _bytes_sha256(
            self.stderr
        ):
            raise OciBrokerError("stderr_sha256 does not match captured output.")
        if self.started:
            if self.error is not None and not self.timed_out:
                raise OciBrokerError(
                    "A started non-timeout process cannot carry a start error."
                )
        elif self.returncode is not None or self.timed_out or self.error is None:
            raise OciBrokerError("Unstarted process evidence is inconsistent.")

    @classmethod
    def completed(
        cls,
        *,
        returncode: int = 0,
        stdout: bytes = b"",
        stderr: bytes = b"",
    ) -> "BoundedProcessResult":
        """Build deterministic non-truncated evidence for injected tests/runners."""

        return cls(
            started=True,
            returncode=returncode,
            timed_out=False,
            error=None,
            stdout=stdout,
            stderr=stderr,
            stdout_bytes=len(stdout),
            stderr_bytes=len(stderr),
            stdout_sha256=_bytes_sha256(stdout),
            stderr_sha256=_bytes_sha256(stderr),
            stdout_truncated=False,
            stderr_truncated=False,
        )

    @classmethod
    def timeout(
        cls, *, stdout: bytes = b"", stderr: bytes = b""
    ) -> "BoundedProcessResult":
        """Build deterministic timeout evidence for an injected runner."""

        return cls(
            started=True,
            returncode=None,
            timed_out=True,
            error="process timed out",
            stdout=stdout,
            stderr=stderr,
            stdout_bytes=len(stdout),
            stderr_bytes=len(stderr),
            stdout_sha256=_bytes_sha256(stdout),
            stderr_sha256=_bytes_sha256(stderr),
            stdout_truncated=False,
            stderr_truncated=False,
        )


@dataclass(frozen=True)
class OciDispatchContext:
    """Controller-owned frozen value bindings for one agent attempt."""

    cohort_id: str
    generation: int
    head_transition_hash: str
    role: str
    attempt: int
    packet_id: str
    packet_hash: str
    authority_hash: str
    attestation_hash: str
    access_audit_hash: str
    idempotency_key: str

    def __post_init__(self) -> None:
        _validate_slug(self.cohort_id, "cohort_id")
        _bounded_int(self.generation, "generation", minimum=0, maximum=2**63 - 1)
        if self.role not in SUPPORTED_AGENT_ROLES:
            raise OciBrokerError(f"Unsupported calibration agent role: {self.role}")
        _bounded_int(self.attempt, "attempt", minimum=1, maximum=2)
        _validate_uuid(self.packet_id, "packet_id")
        for label, value in (
            ("head_transition_hash", self.head_transition_hash),
            ("packet_hash", self.packet_hash),
            ("authority_hash", self.authority_hash),
            ("attestation_hash", self.attestation_hash),
            ("access_audit_hash", self.access_audit_hash),
        ):
            _validate_hash(value, label)
        if _IDEMPOTENCY_RE.fullmatch(self.idempotency_key) is None:
            raise OciBrokerError("idempotency_key is malformed.")


@dataclass(frozen=True)
class OciStreamEvidence:
    """Complete hash/count evidence with only a bounded captured prefix."""

    sha256: str
    bytes: int
    captured_bytes: int
    truncated: bool

    def __post_init__(self) -> None:
        _validate_hash(self.sha256, "stream sha256")
        _bounded_int(self.bytes, "stream bytes", minimum=0, maximum=2**63 - 1)
        _bounded_int(
            self.captured_bytes,
            "stream captured_bytes",
            minimum=0,
            maximum=2**63 - 1,
        )
        if self.captured_bytes > self.bytes:
            raise OciBrokerError("Captured stream bytes exceed total bytes.")
        if self.truncated != (self.captured_bytes < self.bytes):
            raise OciBrokerError("Stream truncation flag is inconsistent.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "sha256": self.sha256,
            "bytes": self.bytes,
            "captured_bytes": self.captured_bytes,
            "truncated": self.truncated,
        }

    @classmethod
    def from_dict(
        cls, payload: Mapping[str, Any], *, label: str
    ) -> "OciStreamEvidence":
        _validate_object(
            payload, {"sha256", "bytes", "captured_bytes", "truncated"}, label
        )
        truncated = payload.get("truncated")
        if not isinstance(truncated, bool):
            raise OciBrokerError(f"{label}.truncated must be boolean.")
        return cls(
            sha256=_required_text(payload.get("sha256"), f"{label}.sha256"),
            bytes=_required_int(payload.get("bytes"), f"{label}.bytes"),
            captured_bytes=_required_int(
                payload.get("captured_bytes"), f"{label}.captured_bytes"
            ),
            truncated=truncated,
        )


_RECEIPT_STATUSES = frozenset(
    {
        "complete",
        "input_changed",
        "output_ambiguous",
        "process_failed",
        "result_invalid",
        "result_missing",
        "result_oversized",
        "start_failed",
        "timed_out",
    }
)
_CLEANUP_STATUSES = frozenset({"not_required", "complete", "failed", "inconclusive"})


@dataclass(frozen=True)
class OciDispatchReceipt:
    """Application-level hash-bound evidence for one broker attempt."""

    schema_version: str
    receipt_id: str
    receipt_hash: str
    cohort_id: str
    generation: int
    head_transition_hash: str
    role: str
    attempt: int
    idempotency_key: str
    packet_id: str
    packet_hash: str
    authority_hash: str
    attestation_hash: str
    access_audit_hash: str
    runtime: str
    runtime_executable_sha256: str
    image: str
    image_digest: str
    command_hash: str
    container_name: str
    started: bool
    status: str
    cleanup_status: str
    exit_code: Optional[int]
    response_hash: Optional[str]
    response_bytes: int
    stdout: OciStreamEvidence
    stderr: OciStreamEvidence

    def __post_init__(self) -> None:
        if self.schema_version != P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION:
            raise OciBrokerError("Unsupported dispatch-receipt schema_version.")
        context = OciDispatchContext(
            cohort_id=self.cohort_id,
            generation=self.generation,
            head_transition_hash=self.head_transition_hash,
            role=self.role,
            attempt=self.attempt,
            packet_id=self.packet_id,
            packet_hash=self.packet_hash,
            authority_hash=self.authority_hash,
            attestation_hash=self.attestation_hash,
            access_audit_hash=self.access_audit_hash,
            idempotency_key=self.idempotency_key,
        )
        del context
        if self.runtime not in SUPPORTED_OCI_RUNTIMES:
            raise OciBrokerError("Dispatch receipt runtime is unsupported.")
        for label, value in (
            ("runtime_executable_sha256", self.runtime_executable_sha256),
            ("image_digest", self.image_digest),
            ("command_hash", self.command_hash),
        ):
            _validate_hash(value, label)
        _validate_digest_pinned_image(self.image)
        if self.image.rsplit("@", 1)[1] != self.image_digest:
            raise OciBrokerError("Dispatch receipt image digest is inconsistent.")
        if _CONTAINER_NAME_RE.fullmatch(self.container_name) is None:
            raise OciBrokerError("Dispatch receipt container_name is malformed.")
        if self.status not in _RECEIPT_STATUSES:
            raise OciBrokerError("Dispatch receipt status is unsupported.")
        if self.cleanup_status not in _CLEANUP_STATUSES:
            raise OciBrokerError("Dispatch receipt cleanup_status is unsupported.")
        _bounded_int(
            self.response_bytes,
            "response_bytes",
            minimum=0,
            maximum=2**63 - 1,
        )
        if self.response_hash is not None:
            _validate_hash(self.response_hash, "response_hash")
        self._validate_status_consistency()
        expected_hash = _canonical_sha256(self._material_dict())
        if self.receipt_hash != expected_hash:
            raise OciBrokerError("Dispatch receipt hash does not match its fields.")
        if self.receipt_id != _receipt_id(expected_hash):
            raise OciBrokerError("Dispatch receipt id does not match its hash.")

    def _validate_status_consistency(self) -> None:
        if self.status == "start_failed":
            if self.started or self.exit_code is not None:
                raise OciBrokerError("start_failed receipt evidence is inconsistent.")
        elif not self.started:
            raise OciBrokerError("Only start_failed may report started=false.")
        if self.status == "complete":
            if (
                self.exit_code != 0
                or self.response_hash is None
                or self.response_bytes < 2
            ):
                raise OciBrokerError("Complete receipt lacks a valid response.")
        if self.status in {"process_failed", "timed_out", "start_failed"} and (
            self.response_hash is not None or self.response_bytes
        ):
            raise OciBrokerError(
                "Failed process receipt cannot claim a response artifact."
            )
        if self.status == "process_failed" and (
            self.exit_code is None or self.exit_code == 0
        ):
            raise OciBrokerError("process_failed receipt must have a non-zero exit.")
        if self.status == "timed_out" and self.cleanup_status == "not_required":
            raise OciBrokerError("Timed-out dispatch must record cleanup evidence.")
        cleanup_eligible = {
            "timed_out",
            "input_changed",
            "output_ambiguous",
        }
        if (
            self.status not in cleanup_eligible
            and self.cleanup_status != "not_required"
        ):
            raise OciBrokerError(
                "Receipt carries cleanup evidence for a non-timeout-compatible status."
            )

    def _material_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cohort_id": self.cohort_id,
            "generation": self.generation,
            "head_transition_hash": self.head_transition_hash,
            "role": self.role,
            "attempt": self.attempt,
            "idempotency_key": self.idempotency_key,
            "packet_id": self.packet_id,
            "packet_hash": self.packet_hash,
            "authority_hash": self.authority_hash,
            "attestation_hash": self.attestation_hash,
            "access_audit_hash": self.access_audit_hash,
            "runtime": self.runtime,
            "runtime_executable_sha256": self.runtime_executable_sha256,
            "image": self.image,
            "image_digest": self.image_digest,
            "command_hash": self.command_hash,
            "container_name": self.container_name,
            "started": self.started,
            "status": self.status,
            "cleanup_status": self.cleanup_status,
            "exit_code": self.exit_code,
            "response_hash": self.response_hash,
            "response_bytes": self.response_bytes,
            "stdout": self.stdout.to_dict(),
            "stderr": self.stderr.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._material_dict(),
            "receipt_id": self.receipt_id,
            "receipt_hash": self.receipt_hash,
        }

    @classmethod
    def create(
        cls,
        *,
        context: OciDispatchContext,
        config: OciRuntimeConfig,
        command: Sequence[str],
        container_name: str,
        process: BoundedProcessResult,
        status: str,
        cleanup_status: str,
        response_hash: Optional[str],
        response_bytes: int,
    ) -> "OciDispatchReceipt":
        material = {
            "schema_version": P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION,
            "cohort_id": context.cohort_id,
            "generation": context.generation,
            "head_transition_hash": context.head_transition_hash,
            "role": context.role,
            "attempt": context.attempt,
            "idempotency_key": context.idempotency_key,
            "packet_id": context.packet_id,
            "packet_hash": context.packet_hash,
            "authority_hash": context.authority_hash,
            "attestation_hash": context.attestation_hash,
            "access_audit_hash": context.access_audit_hash,
            "runtime": config.runtime,
            "runtime_executable_sha256": config.executable_sha256,
            "image": config.worker.image,
            "image_digest": config.worker.digest,
            "command_hash": _canonical_sha256(list(command)),
            "container_name": container_name,
            "started": process.started,
            "status": status,
            "cleanup_status": cleanup_status,
            "exit_code": process.returncode,
            "response_hash": response_hash,
            "response_bytes": response_bytes,
            "stdout": {
                "sha256": process.stdout_sha256,
                "bytes": process.stdout_bytes,
                "captured_bytes": len(process.stdout),
                "truncated": process.stdout_truncated,
            },
            "stderr": {
                "sha256": process.stderr_sha256,
                "bytes": process.stderr_bytes,
                "captured_bytes": len(process.stderr),
                "truncated": process.stderr_truncated,
            },
        }
        receipt_hash = _canonical_sha256(material)
        return cls.from_dict(
            {
                **material,
                "receipt_id": _receipt_id(receipt_hash),
                "receipt_hash": receipt_hash,
            }
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OciDispatchReceipt":
        _validate_object(
            payload,
            {
                "schema_version",
                "receipt_id",
                "receipt_hash",
                "cohort_id",
                "generation",
                "head_transition_hash",
                "role",
                "attempt",
                "idempotency_key",
                "packet_id",
                "packet_hash",
                "authority_hash",
                "attestation_hash",
                "access_audit_hash",
                "runtime",
                "runtime_executable_sha256",
                "image",
                "image_digest",
                "command_hash",
                "container_name",
                "started",
                "status",
                "cleanup_status",
                "exit_code",
                "response_hash",
                "response_bytes",
                "stdout",
                "stderr",
            },
            "dispatch receipt",
        )
        started = payload.get("started")
        if not isinstance(started, bool):
            raise OciBrokerError("Dispatch receipt started must be boolean.")
        exit_code = payload.get("exit_code")
        if exit_code is not None and (
            isinstance(exit_code, bool) or not isinstance(exit_code, int)
        ):
            raise OciBrokerError("Dispatch receipt exit_code must be integer or null.")
        response_hash = payload.get("response_hash")
        if response_hash is not None and not isinstance(response_hash, str):
            raise OciBrokerError("Dispatch receipt response_hash must be text or null.")
        return cls(
            schema_version=_required_text(
                payload.get("schema_version"), "schema_version"
            ),
            receipt_id=_required_text(payload.get("receipt_id"), "receipt_id"),
            receipt_hash=_required_text(payload.get("receipt_hash"), "receipt_hash"),
            cohort_id=_required_text(payload.get("cohort_id"), "cohort_id"),
            generation=_required_int(payload.get("generation"), "generation"),
            head_transition_hash=_required_text(
                payload.get("head_transition_hash"), "head_transition_hash"
            ),
            role=_required_text(payload.get("role"), "role"),
            attempt=_required_int(payload.get("attempt"), "attempt"),
            idempotency_key=_required_text(
                payload.get("idempotency_key"), "idempotency_key"
            ),
            packet_id=_required_text(payload.get("packet_id"), "packet_id"),
            packet_hash=_required_text(payload.get("packet_hash"), "packet_hash"),
            authority_hash=_required_text(
                payload.get("authority_hash"), "authority_hash"
            ),
            attestation_hash=_required_text(
                payload.get("attestation_hash"),
                "attestation_hash",
            ),
            access_audit_hash=_required_text(
                payload.get("access_audit_hash"), "access_audit_hash"
            ),
            runtime=_required_text(payload.get("runtime"), "runtime"),
            runtime_executable_sha256=_required_text(
                payload.get("runtime_executable_sha256"),
                "runtime_executable_sha256",
            ),
            image=_required_text(payload.get("image"), "image"),
            image_digest=_required_text(payload.get("image_digest"), "image_digest"),
            command_hash=_required_text(payload.get("command_hash"), "command_hash"),
            container_name=_required_text(
                payload.get("container_name"), "container_name"
            ),
            started=started,
            status=_required_text(payload.get("status"), "status"),
            cleanup_status=_required_text(
                payload.get("cleanup_status"), "cleanup_status"
            ),
            exit_code=exit_code,
            response_hash=response_hash,
            response_bytes=_required_int(
                payload.get("response_bytes"), "response_bytes"
            ),
            stdout=OciStreamEvidence.from_dict(
                _required_mapping(payload.get("stdout"), "stdout"),
                label="stdout",
            ),
            stderr=OciStreamEvidence.from_dict(
                _required_mapping(payload.get("stderr"), "stderr"),
                label="stderr",
            ),
        )


@dataclass(frozen=True)
class OciDispatchOutcome:
    """Bounded local evidence and a hash-bound receipt returned to the controller."""

    receipt: OciDispatchReceipt
    result: Optional[Mapping[str, Any]]
    stdout: str
    stderr: str


@dataclass(frozen=True)
class OciProbeSentinel:
    """One real host file that must remain inaccessible to the probe container."""

    probe: str
    sentinel_id: str
    host_path: str
    content_sha256: str
    content_bytes: int

    def __post_init__(self) -> None:
        if self.probe not in FILESYSTEM_ISOLATION_PROBES:
            raise OciBrokerError(f"Unsupported filesystem sentinel probe: {self.probe}")
        _validate_slug(self.sentinel_id, "sentinel_id")
        _validate_mount_text(self.host_path, "sentinel host_path")
        if not Path(self.host_path).is_absolute():
            raise OciBrokerError("Sentinel host_path must be absolute.")
        _validate_hash(self.content_sha256, "sentinel content_sha256")
        _bounded_int(
            self.content_bytes,
            "sentinel content_bytes",
            minimum=1,
            maximum=4096,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe": self.probe,
            "sentinel_id": self.sentinel_id,
            "host_path": self.host_path,
            "content_sha256": self.content_sha256,
            "content_bytes": self.content_bytes,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OciProbeSentinel":
        _validate_object(
            payload,
            {
                "probe",
                "sentinel_id",
                "host_path",
                "content_sha256",
                "content_bytes",
            },
            "probe sentinel",
        )
        return cls(
            probe=_required_text(payload.get("probe"), "sentinel probe"),
            sentinel_id=_required_text(
                payload.get("sentinel_id"), "sentinel sentinel_id"
            ),
            host_path=_required_text(payload.get("host_path"), "sentinel host_path"),
            content_sha256=_required_text(
                payload.get("content_sha256"), "sentinel content_sha256"
            ),
            content_bytes=_required_int(
                payload.get("content_bytes"), "sentinel content_bytes"
            ),
        )


@dataclass(frozen=True)
class OciNetworkCanaryBinding:
    """Host-controlled loopback canary with a successful pre-probe control."""

    canary_id: str
    host: str
    port: int
    challenge: str
    challenge_sha256: str
    response_sha256: str
    control_sha256: str

    def __post_init__(self) -> None:
        _validate_slug(self.canary_id, "network canary_id")
        if self.host != "127.0.0.1":
            raise OciBrokerError("Network canary must use host loopback.")
        _bounded_int(self.port, "network canary port", minimum=1, maximum=65535)
        if (
            not isinstance(self.challenge, str)
            or _HEX_32_RE.fullmatch(self.challenge) is None
        ):
            raise OciBrokerError("Network canary challenge must be 32-byte hex.")
        challenge_bytes = bytes.fromhex(self.challenge)
        if self.challenge_sha256 != _bytes_sha256(challenge_bytes):
            raise OciBrokerError("Network canary challenge hash is inconsistent.")
        response = _network_canary_response(self.challenge)
        if self.response_sha256 != _bytes_sha256(response):
            raise OciBrokerError("Network canary response hash is inconsistent.")
        transcript = b"host-control\x00" + challenge_bytes + response
        if self.control_sha256 != _bytes_sha256(transcript):
            raise OciBrokerError("Network canary control hash is inconsistent.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "canary_id": self.canary_id,
            "host": self.host,
            "port": self.port,
            "challenge": self.challenge,
            "challenge_sha256": self.challenge_sha256,
            "response_sha256": self.response_sha256,
            "control_sha256": self.control_sha256,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OciNetworkCanaryBinding":
        _validate_object(
            payload,
            {
                "canary_id",
                "host",
                "port",
                "challenge",
                "challenge_sha256",
                "response_sha256",
                "control_sha256",
            },
            "network canary",
        )
        return cls(
            canary_id=_required_text(payload.get("canary_id"), "network canary_id"),
            host=_required_text(payload.get("host"), "network canary host"),
            port=_required_int(payload.get("port"), "network canary port"),
            challenge=_required_text(
                payload.get("challenge"), "network canary challenge"
            ),
            challenge_sha256=_required_text(
                payload.get("challenge_sha256"),
                "network canary challenge_sha256",
            ),
            response_sha256=_required_text(
                payload.get("response_sha256"), "network canary response_sha256"
            ),
            control_sha256=_required_text(
                payload.get("control_sha256"), "network canary control_sha256"
            ),
        )


class _LocalEgressCanary:
    """Small host-loopback challenge server used only during one admission probe."""

    def __init__(self, *, probe_id: str) -> None:
        _validate_slug(probe_id, "probe_id")
        self._challenge = secrets.token_hex(32)
        self._response = _network_canary_response(self._challenge)
        listener: socket.socket | None = None
        try:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", 0))
            listener.listen(8)
            listener.settimeout(0.1)
        except OSError as exc:
            if listener is not None:
                try:
                    listener.close()
                except OSError:
                    pass
            raise OciBrokerError(
                "Local egress canary enforcement is unavailable."
            ) from exc
        self._listener = listener
        self._stop = threading.Event()
        self._guard = threading.Lock()
        self._control_complete = False
        self._pre_control_connections = 0
        self._pre_control_authenticated = 0
        self._post_control_connections = 0
        thread_started = False
        try:
            self._thread = threading.Thread(
                target=self._serve,
                name="llm-wiki-oci-egress-canary",
                daemon=True,
            )
            self._thread.start()
            thread_started = True
            self._run_host_control()
            with self._guard:
                invalid_control = (
                    self._pre_control_connections != 1
                    or self._pre_control_authenticated != 1
                )
                if not invalid_control:
                    self._control_complete = True
            if invalid_control:
                raise OciBrokerError(
                    "Local egress canary control was not uniquely reachable."
                )
            challenge_bytes = bytes.fromhex(self._challenge)
            transcript = b"host-control\x00" + challenge_bytes + self._response
            host, port = self._listener.getsockname()[:2]
            self.binding = OciNetworkCanaryBinding(
                canary_id=f"canary-{uuid.uuid4().hex}",
                host=str(host),
                port=int(port),
                challenge=self._challenge,
                challenge_sha256=_bytes_sha256(challenge_bytes),
                response_sha256=_bytes_sha256(self._response),
                control_sha256=_bytes_sha256(transcript),
            )
        except BaseException as exc:
            if thread_started:
                self.close()
            else:
                self._stop.set()
                try:
                    self._listener.close()
                except OSError:
                    pass
            if isinstance(exc, (OSError, RuntimeError)):
                raise OciBrokerError(
                    "Local egress canary enforcement is unavailable."
                ) from exc
            raise

    @property
    def post_control_connections(self) -> int:
        with self._guard:
            return self._post_control_connections

    def assert_ready(self) -> None:
        if self._stop.is_set() or not self._thread.is_alive():
            raise OciBrokerError("Local egress canary stopped before probe completion.")

    def close(self) -> None:
        if self._stop.is_set():
            return
        self._stop.set()
        try:
            with socket.create_connection(
                self._listener.getsockname()[:2], timeout=0.2
            ):
                pass
        except OSError:
            pass
        self._thread.join(timeout=2)
        try:
            self._listener.close()
        except OSError:
            pass

    def _run_host_control(self) -> None:
        try:
            with socket.create_connection(
                self._listener.getsockname()[:2], timeout=2
            ) as connection:
                connection.settimeout(2)
                connection.sendall(self._challenge.encode("ascii") + b"\n")
                response = _read_socket_line(connection, maximum=256)
        except OSError as exc:
            self.close()
            raise OciBrokerError(
                f"Local egress canary control was unreachable: {exc}"
            ) from exc
        if response != self._response:
            self.close()
            raise OciBrokerError(
                "Local egress canary control returned the wrong challenge response."
            )

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                connection, _address = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with connection:
                if self._stop.is_set():
                    break
                connection.settimeout(1)
                try:
                    request = _read_socket_line(connection, maximum=256)
                except (OSError, OciBrokerError):
                    request = b""
                authenticated = request == self._challenge.encode("ascii") + b"\n"
                with self._guard:
                    if self._control_complete:
                        self._post_control_connections += 1
                    else:
                        self._pre_control_connections += 1
                        if authenticated:
                            self._pre_control_authenticated += 1
                if authenticated:
                    try:
                        connection.sendall(self._response)
                    except OSError:
                        pass


class OciAdmissionProbeEnvironment:
    """Live host evidence required to execute one admission probe."""

    def __init__(
        self,
        *,
        sentinels: tuple[OciProbeSentinel, ...],
        sentinel_identities: Mapping[str, tuple[int, int, int, int]],
        canary: _LocalEgressCanary,
    ) -> None:
        self.sentinels = sentinels
        self.network_canary = canary.binding
        self._sentinel_identities = dict(sentinel_identities)
        self._canary = canary

    @property
    def post_control_network_connections(self) -> int:
        return self._canary.post_control_connections

    def assert_ready(self) -> None:
        self._canary.assert_ready()
        for sentinel in self.sentinels:
            path = Path(sentinel.host_path)
            identity = self._sentinel_identities.get(sentinel.sentinel_id)
            if identity is None or not _identity_matches(path, identity):
                raise OciBrokerError(
                    f"Host isolation sentinel changed: {sentinel.sentinel_id}"
                )
            digest, size = _bounded_file_sha256(
                path,
                maximum=sentinel.content_bytes,
                label=f"{sentinel.probe} sentinel",
            )
            if digest != sentinel.content_sha256 or size != sentinel.content_bytes:
                raise OciBrokerError(
                    f"Host isolation sentinel bytes changed: {sentinel.sentinel_id}"
                )

    def validate_request(self, request: "OciAdmissionProbeRequest") -> None:
        if (
            request.filesystem_sentinels != self.sentinels
            or request.network_canary != self.network_canary
        ):
            raise OciBrokerError(
                "Isolation probe request is not bound to the live host controls."
            )


@contextmanager
def create_oci_admission_probe_environment(
    *, probe_id: str
) -> Iterator[OciAdmissionProbeEnvironment]:
    """Create real host sentinels and a reachable loopback canary for one probe."""

    _validate_slug(probe_id, "probe_id")
    with tempfile.TemporaryDirectory(
        prefix=f"llm-wiki-{probe_id[:32]}-sentinels-"
    ) as raw_root:
        root = Path(raw_root).resolve(strict=True)
        sentinels: list[OciProbeSentinel] = []
        identities: dict[str, tuple[int, int, int, int]] = {}
        for probe in FILESYSTEM_ISOLATION_PROBES:
            sentinel_id = f"{probe}-{uuid.uuid4().hex}"
            path = root / f"{sentinel_id}.bin"
            content = secrets.token_bytes(32)
            _write_exclusive_sentinel(path, content)
            sentinel = OciProbeSentinel(
                probe=probe,
                sentinel_id=sentinel_id,
                host_path=os.fspath(path),
                content_sha256=_bytes_sha256(content),
                content_bytes=len(content),
            )
            sentinels.append(sentinel)
            identities[sentinel_id] = _file_identity(path)
        canary = _LocalEgressCanary(probe_id=probe_id)
        environment = OciAdmissionProbeEnvironment(
            sentinels=tuple(sentinels),
            sentinel_identities=identities,
            canary=canary,
        )
        try:
            environment.assert_ready()
            yield environment
            environment.assert_ready()
        finally:
            canary.close()


@dataclass(frozen=True)
class OciProbeCheck:
    """One mandatory, request-bound adversarial isolation attempt."""

    probe: str
    target_id: str
    target_sha256: str
    attempted: bool
    outcome: str
    evidence: Mapping[str, Any]
    detail: str

    def __post_init__(self) -> None:
        if self.probe not in REQUIRED_ISOLATION_PROBES:
            raise OciBrokerError(f"Unsupported isolation probe: {self.probe}")
        _validate_slug(self.target_id, "isolation probe target_id")
        _validate_hash(self.target_sha256, "isolation probe target_sha256")
        if not isinstance(self.attempted, bool):
            raise OciBrokerError("Isolation probe attempted must be boolean.")
        if self.outcome not in {"denied", "accessible", "inconclusive"}:
            raise OciBrokerError("Isolation probe outcome is unsupported.")
        if not self.attempted and self.outcome != "inconclusive":
            raise OciBrokerError("An unattempted isolation probe must be inconclusive.")
        _bounded_text(self.detail, "isolation probe detail", maximum=1024)
        self._validate_evidence()

    def _validate_evidence(self) -> None:
        evidence = _required_mapping(self.evidence, "isolation probe evidence")
        if self.probe in FILESYSTEM_ISOLATION_PROBES:
            _validate_object(
                evidence,
                {"read_succeeded", "observed_sha256"},
                "filesystem probe evidence",
            )
            succeeded = evidence.get("read_succeeded")
            observed = evidence.get("observed_sha256")
            if not isinstance(succeeded, bool):
                raise OciBrokerError("Filesystem probe read_succeeded must be boolean.")
            if observed is not None:
                _validate_hash(observed, "filesystem probe observed_sha256")
            if succeeded != (self.outcome == "accessible"):
                raise OciBrokerError(
                    "Filesystem probe evidence does not match its outcome."
                )
            if succeeded and observed is None:
                raise OciBrokerError(
                    "Accessible filesystem probe must hash the observed bytes."
                )
            if not succeeded and observed is not None:
                raise OciBrokerError(
                    "Denied filesystem probe cannot claim observed bytes."
                )
            return
        if self.probe == "network_egress":
            _validate_object(
                evidence,
                {
                    "canary_connected",
                    "non_loopback_interfaces",
                    "default_route",
                },
                "network probe evidence",
            )
            connected = evidence.get("canary_connected")
            default_route = evidence.get("default_route")
            interfaces = evidence.get("non_loopback_interfaces")
            if not isinstance(connected, bool) or not isinstance(default_route, bool):
                raise OciBrokerError("Network probe booleans are malformed.")
            if not isinstance(interfaces, list) or len(interfaces) > 16:
                raise OciBrokerError("Network probe interfaces must be a bounded list.")
            for interface in interfaces:
                _bounded_text(interface, "network interface", maximum=64)
            accessible = connected or default_route or bool(interfaces)
            if accessible != (self.outcome == "accessible"):
                raise OciBrokerError(
                    "Network probe evidence does not match its outcome."
                )
            return
        if self.probe == _OUTPUT_WRITE_BOUND_PROBE:
            _validate_object(
                evidence,
                {
                    "limit_bytes",
                    "attempted_bytes",
                    "oversize_write_succeeded",
                    "sibling_write_succeeded",
                    "observed_size",
                },
                "output-bound probe evidence",
            )
            limit_bytes = _required_int(
                evidence.get("limit_bytes"),
                "output-bound limit_bytes",
            )
            attempted_bytes = _required_int(
                evidence.get("attempted_bytes"),
                "output-bound attempted_bytes",
            )
            observed_size = _required_int(
                evidence.get("observed_size"),
                "output-bound observed_size",
            )
            _bounded_int(
                limit_bytes,
                "output-bound limit_bytes",
                minimum=1,
                maximum=_MAX_RESULT_BYTES,
            )
            if attempted_bytes != limit_bytes + 1:
                raise OciBrokerError(
                    "Output-bound probe must attempt exactly one byte above its limit."
                )
            _bounded_int(
                observed_size,
                "output-bound observed_size",
                minimum=0,
                maximum=_MAX_RESULT_BYTES + 1,
            )
            oversize_succeeded = evidence.get("oversize_write_succeeded")
            sibling_succeeded = evidence.get("sibling_write_succeeded")
            if not isinstance(oversize_succeeded, bool) or not isinstance(
                sibling_succeeded, bool
            ):
                raise OciBrokerError("Output-bound probe booleans are malformed.")
            accessible = (
                oversize_succeeded or sibling_succeeded or observed_size > limit_bytes
            )
            if self.outcome == "denied" and accessible:
                raise OciBrokerError(
                    "Denied output-bound probe reports accessible output capacity."
                )
            if self.outcome == "accessible" and not accessible:
                raise OciBrokerError(
                    "Accessible output-bound probe lacks successful write evidence."
                )
            return
        _validate_object(
            evidence,
            {"connected_targets"},
            "container-engine socket probe evidence",
        )
        connected_targets = evidence.get("connected_targets")
        if not isinstance(connected_targets, list) or any(
            target not in _CONTAINER_ENGINE_SOCKET_TARGETS
            for target in connected_targets
        ):
            raise OciBrokerError(
                "Container-engine socket evidence contains an unknown target."
            )
        if len(set(connected_targets)) != len(connected_targets):
            raise OciBrokerError("Container-engine socket evidence repeats a target.")
        if bool(connected_targets) != (self.outcome == "accessible"):
            raise OciBrokerError(
                "Container-engine socket evidence does not match its outcome."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe": self.probe,
            "target_id": self.target_id,
            "target_sha256": self.target_sha256,
            "attempted": self.attempted,
            "outcome": self.outcome,
            "evidence": dict(self.evidence),
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OciProbeCheck":
        _validate_object(
            payload,
            {
                "probe",
                "target_id",
                "target_sha256",
                "attempted",
                "outcome",
                "evidence",
                "detail",
            },
            "probe check",
        )
        attempted = payload.get("attempted")
        if not isinstance(attempted, bool):
            raise OciBrokerError("Probe check attempted must be boolean.")
        return cls(
            probe=_required_text(payload.get("probe"), "probe"),
            target_id=_required_text(payload.get("target_id"), "target_id"),
            target_sha256=_required_text(payload.get("target_sha256"), "target_sha256"),
            attempted=attempted,
            outcome=_required_text(payload.get("outcome"), "outcome"),
            evidence=dict(_required_mapping(payload.get("evidence"), "probe evidence")),
            detail=_required_text(payload.get("detail"), "detail"),
        )


@dataclass(frozen=True)
class OciAdmissionProbeRequest:
    """Evidence-bound request consumed by the pinned adversarial probe image."""

    schema_version: str
    cohort_id: str
    probe_id: str
    authority_hash: str
    required_checks: tuple[str, ...]
    filesystem_sentinels: tuple[OciProbeSentinel, ...]
    network_canary: OciNetworkCanaryBinding
    output_limit_bytes: int

    def __post_init__(self) -> None:
        if self.schema_version != P0_CALIBRATION_ISOLATION_PROBE_REQUEST_SCHEMA_VERSION:
            raise OciBrokerError("Unsupported isolation-probe request schema.")
        _validate_slug(self.cohort_id, "cohort_id")
        _validate_slug(self.probe_id, "probe_id")
        _validate_hash(self.authority_hash, "authority_hash")
        _bounded_int(
            self.output_limit_bytes,
            "output_limit_bytes",
            minimum=1,
            maximum=_MAX_RESULT_BYTES,
        )
        if self.required_checks != REQUIRED_ISOLATION_PROBES:
            raise OciBrokerError(
                "Isolation probe request must contain the fixed complete checklist."
            )
        if (
            tuple(sentinel.probe for sentinel in self.filesystem_sentinels)
            != FILESYSTEM_ISOLATION_PROBES
        ):
            raise OciBrokerError(
                "Isolation probe request must bind every host sentinel in order."
            )
        if len({item.sentinel_id for item in self.filesystem_sentinels}) != len(
            self.filesystem_sentinels
        ):
            raise OciBrokerError("Isolation probe sentinel ids must be unique.")

    @property
    def request_hash(self) -> str:
        return _bytes_sha256(canonical_result_json_bytes(self.to_dict()))

    def target_binding(self, probe: str) -> tuple[str, str]:
        if probe in FILESYSTEM_ISOLATION_PROBES:
            sentinel = next(
                item for item in self.filesystem_sentinels if item.probe == probe
            )
            return sentinel.sentinel_id, sentinel.content_sha256
        if probe == "network_egress":
            return (
                self.network_canary.canary_id,
                _canonical_sha256(self.network_canary.to_dict()),
            )
        if probe == "container_engine_socket":
            return (
                "container-engine-sockets",
                _canonical_sha256(list(_CONTAINER_ENGINE_SOCKET_TARGETS)),
            )
        if probe == _OUTPUT_WRITE_BOUND_PROBE:
            return (
                _OUTPUT_BOUND_TARGET_ID,
                _canonical_sha256(
                    {
                        "mechanism": _OUTPUT_BOUND_MECHANISM,
                        "result_bytes": self.output_limit_bytes,
                    }
                ),
            )
        raise OciBrokerError(f"Unsupported isolation probe: {probe}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cohort_id": self.cohort_id,
            "probe_id": self.probe_id,
            "authority_hash": self.authority_hash,
            "required_checks": list(self.required_checks),
            "filesystem_sentinels": [
                sentinel.to_dict() for sentinel in self.filesystem_sentinels
            ],
            "container_engine_sockets": list(_CONTAINER_ENGINE_SOCKET_TARGETS),
            "network_canary": self.network_canary.to_dict(),
            "output_limit_bytes": self.output_limit_bytes,
        }

    @classmethod
    def create(
        cls,
        *,
        cohort_id: str,
        probe_id: str,
        authority_hash: str,
        probe_environment: OciAdmissionProbeEnvironment,
        output_limit_bytes: int,
    ) -> "OciAdmissionProbeRequest":
        probe_environment.assert_ready()
        return cls(
            schema_version=P0_CALIBRATION_ISOLATION_PROBE_REQUEST_SCHEMA_VERSION,
            cohort_id=cohort_id,
            probe_id=probe_id,
            authority_hash=authority_hash,
            required_checks=REQUIRED_ISOLATION_PROBES,
            filesystem_sentinels=probe_environment.sentinels,
            network_canary=probe_environment.network_canary,
            output_limit_bytes=output_limit_bytes,
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OciAdmissionProbeRequest":
        _validate_object(
            payload,
            {
                "schema_version",
                "cohort_id",
                "probe_id",
                "authority_hash",
                "required_checks",
                "filesystem_sentinels",
                "container_engine_sockets",
                "network_canary",
                "output_limit_bytes",
            },
            "isolation probe request",
        )
        raw_checks = payload.get("required_checks")
        raw_sentinels = payload.get("filesystem_sentinels")
        raw_sockets = payload.get("container_engine_sockets")
        if not isinstance(raw_checks, list):
            raise OciBrokerError("Isolation probe required_checks must be a list.")
        if not isinstance(raw_sentinels, list):
            raise OciBrokerError("Isolation probe filesystem_sentinels must be a list.")
        if raw_sockets != list(_CONTAINER_ENGINE_SOCKET_TARGETS):
            raise OciBrokerError(
                "Isolation probe container-engine socket targets are not fixed."
            )
        return cls(
            schema_version=_required_text(
                payload.get("schema_version"), "schema_version"
            ),
            cohort_id=_required_text(payload.get("cohort_id"), "cohort_id"),
            probe_id=_required_text(payload.get("probe_id"), "probe_id"),
            authority_hash=_required_text(
                payload.get("authority_hash"), "authority_hash"
            ),
            required_checks=tuple(
                _required_text(value, "required check") for value in raw_checks
            ),
            filesystem_sentinels=tuple(
                OciProbeSentinel.from_dict(
                    _required_mapping(value, "filesystem sentinel")
                )
                for value in raw_sentinels
            ),
            network_canary=OciNetworkCanaryBinding.from_dict(
                _required_mapping(payload.get("network_canary"), "network canary")
            ),
            output_limit_bytes=_required_int(
                payload.get("output_limit_bytes"),
                "output_limit_bytes",
            ),
        )


@dataclass(frozen=True)
class OciAdmissionProbeResult:
    """Strict result emitted by the pinned adversarial probe image."""

    schema_version: str
    cohort_id: str
    probe_id: str
    request_hash: str
    image_digest: str
    access_events: tuple[OciProbeCheck, ...]
    status: str

    def __post_init__(self) -> None:
        if self.schema_version != P0_CALIBRATION_ISOLATION_PROBE_RESULT_SCHEMA_VERSION:
            raise OciBrokerError("Unsupported isolation-probe result schema.")
        _validate_slug(self.cohort_id, "cohort_id")
        _validate_slug(self.probe_id, "probe_id")
        _validate_hash(self.request_hash, "request_hash")
        _validate_hash(self.image_digest, "image_digest")
        if (
            tuple(event.probe for event in self.access_events)
            != REQUIRED_ISOLATION_PROBES
        ):
            raise OciBrokerError(
                "Isolation probe result must contain every access event exactly once "
                "in canonical order."
            )
        passed = all(
            event.attempted and event.outcome == "denied"
            for event in self.access_events
        )
        expected_status = "passed" if passed else "failed"
        if self.status != expected_status:
            raise OciBrokerError(
                "Isolation probe status does not match its mandatory checks."
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cohort_id": self.cohort_id,
            "probe_id": self.probe_id,
            "request_hash": self.request_hash,
            "image_digest": self.image_digest,
            "access_events": [event.to_dict() for event in self.access_events],
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OciAdmissionProbeResult":
        _validate_object(
            payload,
            {
                "schema_version",
                "cohort_id",
                "probe_id",
                "request_hash",
                "image_digest",
                "access_events",
                "status",
            },
            "isolation probe result",
        )
        raw_events = payload.get("access_events")
        if not isinstance(raw_events, list):
            raise OciBrokerError("Isolation probe result access_events must be a list.")
        events = []
        for raw in raw_events:
            events.append(
                OciProbeCheck.from_dict(
                    _required_mapping(raw, "isolation probe access event")
                )
            )
        return cls(
            schema_version=_required_text(
                payload.get("schema_version"), "schema_version"
            ),
            cohort_id=_required_text(payload.get("cohort_id"), "cohort_id"),
            probe_id=_required_text(payload.get("probe_id"), "probe_id"),
            request_hash=_required_text(payload.get("request_hash"), "request_hash"),
            image_digest=_required_text(payload.get("image_digest"), "image_digest"),
            access_events=tuple(events),
            status=_required_text(payload.get("status"), "status"),
        )


@dataclass(frozen=True)
class OciAdmissionProbeOutcome:
    """Execution and result evidence for admission; never an authority grant."""

    passed: bool
    execution_status: str
    request_hash: str
    result_hash: Optional[str]
    result: Optional[OciAdmissionProbeResult]
    process: BoundedProcessResult
    command_hash: str
    cleanup_status: str
    stdout: str
    stderr: str
    error: Optional[str]


def canonical_result_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Encode a broker JSON object using the supported artifact hash contract."""

    if not isinstance(payload, Mapping):
        raise OciBrokerError("Agent result must be a JSON object.")
    try:
        return (
            json.dumps(
                payload,
                allow_nan=False,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OciBrokerError("Agent result is not canonical JSON.") from exc


def sanitized_oci_environment(
    source: Optional[Mapping[str, str]] = None,
) -> dict[str, str]:
    """Return a minimal host environment with credential/proxy settings removed."""

    source_environment = os.environ if source is None else source
    result: dict[str, str] = {}
    for key in _HOST_ENV_ALLOWLIST:
        value = source_environment.get(key)
        if value is None or not isinstance(value, str):
            continue
        if _CONTROL_RE.search(value) or _LIKELY_SECRET_RE.search(value):
            continue
        result[key] = value
    result["LANG"] = "C.UTF-8"
    result["LC_ALL"] = "C.UTF-8"
    return result


def build_oci_dispatch_command(
    config: OciRuntimeConfig,
    *,
    packet_path: str | Path,
    output_dir: str | Path,
    context: OciDispatchContext,
) -> tuple[str, ...]:
    """Build the exact no-shell Docker/Podman argv for one agent attempt."""

    packet, output = _validate_mount_paths(
        packet_path,
        output_dir,
        packet_limit=config.max_packet_bytes,
        require_empty_output=False,
    )
    container_name = _dispatch_container_name(context)
    return _build_oci_run_command(
        config,
        image_command=config.worker,
        input_path=packet,
        input_container_path=_PACKET_CONTAINER_PATH,
        output_path=output / _RESULT_FILENAME,
        output_container_path=_RESULT_CONTAINER_PATH,
        workload_args=(
            "--packet",
            _PACKET_CONTAINER_PATH,
            "--result",
            _RESULT_CONTAINER_PATH,
        ),
        container_name=container_name,
    )


def build_oci_probe_command(
    config: OciRuntimeConfig,
    *,
    request_path: str | Path,
    output_dir: str | Path,
    probe_id: str,
) -> tuple[str, ...]:
    """Build the exact no-shell argv for the adversarial admission probe."""

    _validate_slug(probe_id, "probe_id")
    request, output = _validate_mount_paths(
        request_path,
        output_dir,
        packet_limit=config.max_packet_bytes,
        require_empty_output=False,
    )
    container_name = _probe_container_name(probe_id)
    return _build_oci_run_command(
        config,
        image_command=config.probe,
        input_path=request,
        input_container_path=_PROBE_REQUEST_CONTAINER_PATH,
        output_path=output / _PROBE_RESULT_FILENAME,
        output_container_path=_PROBE_RESULT_CONTAINER_PATH,
        workload_args=(
            "--probe-request",
            _PROBE_REQUEST_CONTAINER_PATH,
            "--probe-result",
            _PROBE_RESULT_CONTAINER_PATH,
            "--image-digest",
            config.probe.digest,
        ),
        container_name=container_name,
    )


def dispatch_oci_agent(
    config: OciRuntimeConfig,
    *,
    context: OciDispatchContext,
    packet_path: str | Path,
    output_dir: str | Path,
    runner: Optional[OciProcessRunner] = None,
    environment: Optional[Mapping[str, str]] = None,
) -> OciDispatchOutcome:
    """Execute one bounded local agent and return a hash-bound receipt.

    Configuration/path/packet failures occur before invoking the process runner.
    Once an invocation is attempted, all terminal process/result conditions are
    represented in the returned receipt so the controller can fail closed.
    """

    process_runner = run_bounded_process if runner is None else runner
    packet, output = _validate_mount_paths(
        packet_path,
        output_dir,
        packet_limit=config.max_packet_bytes,
        require_empty_output=True,
    )
    _validate_runtime_executable_identity(config)
    packet_hash, _ = _bounded_file_sha256(
        packet, maximum=config.max_packet_bytes, label="agent packet"
    )
    if packet_hash != context.packet_hash:
        raise OciBrokerError("Agent packet hash does not match dispatch context.")
    packet_identity = _file_identity(packet)
    output_identity = _file_identity(output)
    command = build_oci_dispatch_command(
        config,
        packet_path=packet,
        output_dir=output,
        context=context,
    )
    result_artifact, result_identity = _prepare_single_result_artifact(
        output,
        filename=_RESULT_FILENAME,
    )
    container_name = _dispatch_container_name(context)
    process = _execute_container_command(
        config,
        command=command,
        container_name=container_name,
        runner=process_runner,
        environment=environment,
    )
    _validate_process_result_bounds(process, config.output_limits)
    cleanup_status = "not_required"
    if process.timed_out:
        cleanup_status = _cleanup_timed_out_container(
            config,
            container_name=container_name,
            runner=process_runner,
            environment=environment,
        )

    status = _process_status(process)
    result_payload: Optional[Mapping[str, Any]] = None
    response_hash: Optional[str] = None
    response_bytes = 0
    if not _input_file_unchanged(
        packet,
        expected_identity=packet_identity,
        expected_hash=context.packet_hash,
        maximum=config.max_packet_bytes,
        label="agent packet",
    ):
        status = "input_changed"
    elif not _identity_matches(output, output_identity):
        status = "output_ambiguous"
    elif not _identity_matches(result_artifact, result_identity):
        status = "output_ambiguous"
    elif status == "complete":
        (
            status,
            result_payload,
            response_hash,
            response_bytes,
        ) = _load_agent_result(
            output,
            context=context,
            maximum=config.output_limits.result_bytes,
        )

    receipt = OciDispatchReceipt.create(
        context=context,
        config=config,
        command=command,
        container_name=container_name,
        process=process,
        status=status,
        cleanup_status=cleanup_status,
        response_hash=response_hash,
        response_bytes=response_bytes,
    )
    return OciDispatchOutcome(
        receipt=receipt,
        result=result_payload,
        stdout=process.stdout.decode("utf-8", errors="replace"),
        stderr=process.stderr.decode("utf-8", errors="replace"),
    )


def execute_oci_admission_probe(
    config: OciRuntimeConfig,
    *,
    request_path: str | Path,
    output_dir: str | Path,
    probe_environment: OciAdmissionProbeEnvironment,
    runner: Optional[OciProcessRunner] = None,
    environment: Optional[Mapping[str, str]] = None,
) -> OciAdmissionProbeOutcome:
    """Run the pinned adversarial image and validate every mandatory denial."""

    process_runner = run_bounded_process if runner is None else runner
    probe_environment.assert_ready()
    request_file, output = _validate_mount_paths(
        request_path,
        output_dir,
        packet_limit=config.max_packet_bytes,
        require_empty_output=True,
    )
    _validate_runtime_executable_identity(config)
    request_payload, request_file_hash, request_file_bytes = _load_bounded_json_object(
        request_file,
        maximum=config.max_packet_bytes,
        label="isolation probe request",
    )
    request = OciAdmissionProbeRequest.from_dict(request_payload)
    probe_environment.validate_request(request)
    if request.output_limit_bytes != config.output_limits.result_bytes:
        raise OciBrokerError(
            "Isolation probe request output limit does not match the frozen runtime."
        )
    request_hash = request.request_hash
    canonical_request = canonical_result_json_bytes(request_payload)
    if request_file_hash != request_hash or request_file_bytes != len(
        canonical_request
    ):
        raise OciBrokerError(
            "Isolation probe request must use canonical JSON encoding."
        )
    request_identity = _file_identity(request_file)
    output_identity = _file_identity(output)
    command = build_oci_probe_command(
        config,
        request_path=request_file,
        output_dir=output,
        probe_id=request.probe_id,
    )
    result_artifact, result_identity = _prepare_single_result_artifact(
        output,
        filename=_PROBE_RESULT_FILENAME,
    )
    container_name = _probe_container_name(request.probe_id)
    process = _execute_container_command(
        config,
        command=command,
        container_name=container_name,
        runner=process_runner,
        environment=environment,
    )
    _validate_process_result_bounds(process, config.output_limits)
    probe_environment.assert_ready()
    cleanup_status = "not_required"
    if process.timed_out:
        cleanup_status = _cleanup_timed_out_container(
            config,
            container_name=container_name,
            runner=process_runner,
            environment=environment,
        )

    execution_status = _process_status(process)
    result: Optional[OciAdmissionProbeResult] = None
    result_hash: Optional[str] = None
    error: Optional[str] = process.error
    if not _input_file_unchanged(
        request_file,
        expected_identity=request_identity,
        expected_hash=request_file_hash,
        maximum=config.max_packet_bytes,
        label="isolation probe request",
    ):
        execution_status = "input_changed"
        error = "Isolation probe request changed during execution."
    elif not _identity_matches(output, output_identity):
        execution_status = "output_ambiguous"
        error = "Isolation probe output directory changed during execution."
    elif not _identity_matches(result_artifact, result_identity):
        execution_status = "output_ambiguous"
        error = "Isolation probe result target changed during execution."
    elif execution_status == "complete":
        try:
            raw_result, raw_hash, raw_bytes = _load_single_json_result(
                output,
                filename=_PROBE_RESULT_FILENAME,
                maximum=config.output_limits.result_bytes,
                label="isolation probe result",
            )
            canonical_result = canonical_result_json_bytes(raw_result)
            result_hash = _bytes_sha256(canonical_result)
            if raw_hash != result_hash or raw_bytes != len(canonical_result):
                raise OciBrokerError(
                    "Isolation probe result must use canonical JSON encoding."
                )
            result = OciAdmissionProbeResult.from_dict(raw_result)
            if (
                result.cohort_id != request.cohort_id
                or result.probe_id != request.probe_id
                or result.request_hash != request_hash
                or result.image_digest != config.probe.digest
            ):
                raise OciBrokerError(
                    "Isolation probe result does not match its request/runtime."
                )
            _validate_probe_result_bindings(
                result,
                request=request,
                probe_environment=probe_environment,
            )
            execution_status = (
                "complete" if result.status == "passed" else "probe_failed"
            )
        except _ResultArtifactError as exc:
            execution_status = exc.status
            error = str(exc)
        except OciBrokerError as exc:
            execution_status = "result_invalid"
            error = str(exc)

    passed = execution_status == "complete" and result is not None
    return OciAdmissionProbeOutcome(
        passed=passed,
        execution_status=execution_status,
        request_hash=request_hash,
        result_hash=result_hash,
        result=result,
        process=process,
        command_hash=_canonical_sha256(list(command)),
        cleanup_status=cleanup_status,
        stdout=process.stdout.decode("utf-8", errors="replace"),
        stderr=process.stderr.decode("utf-8", errors="replace"),
        error=error,
    )


def _validate_probe_result_bindings(
    result: OciAdmissionProbeResult,
    *,
    request: OciAdmissionProbeRequest,
    probe_environment: OciAdmissionProbeEnvironment,
) -> None:
    for event in result.access_events:
        expected_id, expected_hash = request.target_binding(event.probe)
        if event.target_id != expected_id or event.target_sha256 != expected_hash:
            raise OciBrokerError(
                f"Isolation probe result is not bound to {event.probe} target evidence."
            )
    network_event = next(
        event for event in result.access_events if event.probe == "network_egress"
    )
    network_evidence = _required_mapping(
        network_event.evidence, "network probe evidence"
    )
    observed_connection = probe_environment.post_control_network_connections > 0
    if network_evidence.get("canary_connected") is not observed_connection:
        raise OciBrokerError(
            "Network probe canary claim does not match the host-side connection audit."
        )


def run_bounded_process(
    argv: Sequence[str],
    *,
    env: Mapping[str, str],
    timeout_seconds: int,
    termination_grace_seconds: int,
    stdout_limit: int,
    stderr_limit: int,
) -> BoundedProcessResult:
    """Execute fixed argv, draining complete streams while retaining bounded bytes."""

    command = tuple(argv)
    if not command:
        raise OciBrokerError("Process argv cannot be empty.")
    for index, value in enumerate(command):
        _validate_argv_value(value, f"process argument {index}")
    _bounded_int(timeout_seconds, "timeout_seconds", minimum=1, maximum=3600)
    _bounded_int(
        termination_grace_seconds,
        "termination_grace_seconds",
        minimum=1,
        maximum=30,
    )
    _bounded_int(stdout_limit, "stdout_limit", minimum=1, maximum=_MAX_STREAM_BYTES)
    _bounded_int(stderr_limit, "stderr_limit", minimum=1, maximum=_MAX_STREAM_BYTES)
    if dict(env) != sanitized_oci_environment(env):
        raise OciBrokerError(
            "Process environment must equal the broker's sanitized allowlist."
        )
    try:
        process = subprocess.Popen(  # noqa: S603 - validated fixed argv, no shell
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=dict(env),
            close_fds=True,
        )
    except OSError as exc:
        empty_hash = _bytes_sha256(b"")
        return BoundedProcessResult(
            started=False,
            returncode=None,
            timed_out=False,
            error=str(exc),
            stdout=b"",
            stderr=b"",
            stdout_bytes=0,
            stderr_bytes=0,
            stdout_sha256=empty_hash,
            stderr_sha256=empty_hash,
            stdout_truncated=False,
            stderr_truncated=False,
        )

    assert process.stdout is not None
    assert process.stderr is not None
    stdout_capture = _StreamCapture(stdout_limit)
    stderr_capture = _StreamCapture(stderr_limit)
    stdout_thread = threading.Thread(
        target=stdout_capture.drain,
        args=(process.stdout,),
        name="llm-wiki-oci-stdout",
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=stderr_capture.drain,
        args=(process.stderr,),
        name="llm-wiki-oci-stderr",
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()
    timed_out = False
    error: Optional[str] = None
    try:
        returncode = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        error = f"Process timed out after {timeout_seconds} seconds."
        process.terminate()
        try:
            returncode = process.wait(timeout=termination_grace_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            returncode = process.wait()
    except BaseException:
        # The runtime CLI may already have created the named container.  First
        # stop this local child and drain its pipes; the caller then removes
        # the independently named container before propagating the exception.
        try:
            process.terminate()
        except BaseException:
            pass
        try:
            process.wait(timeout=termination_grace_seconds)
        except BaseException:
            try:
                process.kill()
            except BaseException:
                pass
            try:
                process.wait(timeout=termination_grace_seconds)
            except BaseException:
                pass
        for capture_thread in (stdout_thread, stderr_thread):
            try:
                capture_thread.join(timeout=termination_grace_seconds)
            except BaseException:
                pass
        raise
    stdout_thread.join()
    stderr_thread.join()
    stdout = stdout_capture.finish()
    stderr = stderr_capture.finish()
    return BoundedProcessResult(
        started=True,
        returncode=returncode,
        timed_out=timed_out,
        error=error,
        stdout=stdout.data,
        stderr=stderr.data,
        stdout_bytes=stdout.total_bytes,
        stderr_bytes=stderr.total_bytes,
        stdout_sha256=stdout.sha256,
        stderr_sha256=stderr.sha256,
        stdout_truncated=stdout.truncated,
        stderr_truncated=stderr.truncated,
    )


@dataclass(frozen=True)
class _CapturedStream:
    data: bytes
    total_bytes: int
    sha256: str
    truncated: bool


class _StreamCapture:
    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._captured = bytearray()
        self._total = 0
        self._hasher = hashlib.sha256()
        self._error: Optional[BaseException] = None

    def drain(self, stream) -> None:
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                self._total += len(chunk)
                self._hasher.update(chunk)
                remaining = self._limit - len(self._captured)
                if remaining > 0:
                    self._captured.extend(chunk[:remaining])
        except BaseException as exc:  # pragma: no cover - OS pipe failure
            self._error = exc
        finally:
            stream.close()

    def finish(self) -> _CapturedStream:
        if self._error is not None:
            raise OciBrokerError(f"Cannot capture process output: {self._error}")
        data = bytes(self._captured)
        return _CapturedStream(
            data=data,
            total_bytes=self._total,
            sha256="sha256:" + self._hasher.hexdigest(),
            truncated=self._total > len(data),
        )


class _ResultArtifactError(OciBrokerError):
    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status


def _build_oci_run_command(
    config: OciRuntimeConfig,
    *,
    image_command: OciImageCommand,
    input_path: Path,
    input_container_path: str,
    output_path: Path,
    output_container_path: str,
    workload_args: tuple[str, ...],
    container_name: str,
) -> tuple[str, ...]:
    if _CONTAINER_NAME_RE.fullmatch(container_name) is None:
        raise OciBrokerError("OCI container name is malformed.")
    cpu_value = f"{config.resources.cpu_millis / 1000:.3f}"
    command = [
        config.executable,
        "run",
        "--rm",
        "--pull=never",
        f"--name={container_name}",
        "--log-driver=none",
        "--network=none",
        "--read-only",
        f"--user={config.user}",
    ]
    if config.runtime == "podman":
        user_match = _NUMERIC_USER_RE.fullmatch(config.user)
        if user_match is None:  # pragma: no cover - config invariant
            raise OciBrokerError("Podman output mapping requires a numeric user.")
        command.append(
            "--userns=keep-id:"
            f"uid={int(user_match.group(1))},gid={int(user_match.group(2))}"
        )
    command.extend(
        (
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            f"--pids-limit={config.resources.pids_limit}",
            f"--memory={config.resources.memory_bytes}",
            f"--memory-swap={config.resources.memory_bytes}",
            f"--cpus={cpu_value}",
            (
                "--ulimit=fsize="
                f"{config.output_limits.result_bytes}:"
                f"{config.output_limits.result_bytes}"
            ),
            "--workdir=/tmp",
            "--tmpfs",
            (
                # This target is inside the isolated container, not on the host.
                f"/tmp:rw,noexec,nosuid,nodev,size={config.resources.tmpfs_bytes}"  # nosec B108
            ),
        )
    )
    for value in _CONTAINER_ENVIRONMENT:
        command.extend(("--env", value))
    command.extend(
        (
            "--mount",
            _mount_argument(input_path, input_container_path, readonly=True),
            "--mount",
            _mount_argument(output_path, output_container_path, readonly=False),
            f"--entrypoint={image_command.entrypoint[0]}",
            image_command.image,
            *image_command.entrypoint[1:],
            *workload_args,
        )
    )
    return tuple(command)


def _mount_argument(path: Path, target: str, *, readonly: bool) -> str:
    source = os.fspath(path)
    _validate_mount_text(source, "OCI mount source")
    _validate_mount_text(target, "OCI mount target")
    parts = ["type=bind", f"source={source}", f"target={target}"]
    if readonly:
        parts.append("readonly")
    return ",".join(parts)


def _validate_mount_paths(
    packet_path: str | Path,
    output_dir: str | Path,
    *,
    packet_limit: int,
    require_empty_output: bool,
) -> tuple[Path, Path]:
    packet = _absolute_regular_file(
        packet_path, label="OCI input packet", maximum=packet_limit
    )
    output = _absolute_regular_directory(output_dir, label="OCI output directory")
    if _is_relative_to(packet, output):
        raise OciBrokerError(
            "OCI output directory cannot contain the read-only input packet."
        )
    if require_empty_output:
        try:
            with os.scandir(output) as entries:
                has_entry = next(entries, None) is not None
        except OSError as exc:
            raise OciBrokerError(f"Cannot inspect OCI output directory: {exc}") from exc
        if has_entry:
            raise OciBrokerError(
                "OCI role output directory must be empty before execution."
            )
    return packet, output


def _validate_runtime_executable_identity(config: OciRuntimeConfig) -> None:
    executable = _absolute_regular_file(
        config.executable,
        label="OCI runtime executable",
        maximum=_MAX_RUNTIME_EXECUTABLE_BYTES,
    )
    actual, _ = _bounded_file_sha256(
        executable,
        maximum=_MAX_RUNTIME_EXECUTABLE_BYTES,
        label="OCI runtime executable",
    )
    if actual != config.executable_sha256:
        raise OciBrokerError(
            "OCI runtime executable hash does not match the frozen manifest."
        )
    try:
        executable_mode = executable.stat().st_mode
    except OSError as exc:
        raise OciBrokerError(f"Cannot stat OCI runtime executable: {exc}") from exc
    if os.name != "nt" and not executable_mode & 0o111:
        raise OciBrokerError("OCI runtime executable is not executable.")


def _prepare_single_result_artifact(
    output_dir: Path,
    *,
    filename: str,
) -> tuple[Path, tuple[int, int, int, int]]:
    """Create the sole persistent writable container target as a private file."""

    artifact = output_dir / filename
    try:
        atomic_write_private_bytes(artifact, b"")
    except (OSError, TypeError) as exc:
        raise OciBrokerError(
            f"Cannot create the bounded OCI result artifact {artifact}: {exc}"
        ) from exc
    try:
        metadata = artifact.stat(follow_symlinks=False)
    except OSError as exc:
        raise OciBrokerError(
            f"Cannot inspect the bounded OCI result artifact: {exc}"
        ) from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_size != 0
        or int(getattr(metadata, "st_nlink", 1)) != 1
    ):
        raise OciBrokerError(
            "Bounded OCI result artifact is not one empty single-link file."
        )
    if os.name != "nt" and stat.S_IMODE(metadata.st_mode) != 0o600:
        raise OciBrokerError("Bounded OCI result artifact is not private.")
    return artifact, _file_identity(artifact)


def _load_agent_result(
    output_dir: Path,
    *,
    context: OciDispatchContext,
    maximum: int,
) -> tuple[str, Optional[Mapping[str, Any]], Optional[str], int]:
    try:
        payload, raw_hash, raw_bytes = _load_single_json_result(
            output_dir,
            filename=_RESULT_FILENAME,
            maximum=maximum,
            label="agent result",
        )
    except _ResultArtifactError as exc:
        return exc.status, None, None, 0
    try:
        canonical = canonical_result_json_bytes(payload)
    except OciBrokerError:
        return "result_invalid", payload, None, 0
    response_hash = _bytes_sha256(canonical)
    response_bytes = len(canonical)
    if response_bytes > maximum:
        return "result_oversized", payload, None, 0
    canonical_artifact = raw_hash == response_hash and raw_bytes == response_bytes
    expected = {
        "schema_version": P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
        "cohort_id": context.cohort_id,
        "packet_id": context.packet_id,
        "role": context.role,
        "attempt": context.attempt,
        "packet_hash": context.packet_hash,
        "idempotency_key": context.idempotency_key,
        "status": "complete",
    }
    result_id = payload.get("result_id")
    if (
        not canonical_artifact
        or not _is_canonical_uuid(result_id)
        or any(payload.get(key) != value for key, value in expected.items())
    ):
        return "result_invalid", payload, response_hash, response_bytes
    return "complete", payload, response_hash, response_bytes


def _load_single_json_result(
    output_dir: Path,
    *,
    filename: str,
    maximum: int,
    label: str,
) -> tuple[Mapping[str, Any], str, int]:
    artifact: Optional[Path] = None
    aggregate_bytes = 0
    try:
        # A bind-mounted host directory has no portable hard byte quota across
        # Docker and Podman.  Inspect at most the two entries needed to prove
        # the one-artifact contract, and account their stat sizes before any
        # result bytes are read.
        with os.scandir(output_dir) as entries:
            for entry_count, entry in enumerate(entries, start=1):
                try:
                    metadata = entry.stat(follow_symlinks=False)
                except OSError as exc:
                    raise _ResultArtifactError(
                        "output_ambiguous",
                        f"Cannot inspect {label} output artifact: {exc}",
                    ) from exc
                aggregate_bytes += metadata.st_size
                if aggregate_bytes > maximum:
                    raise _ResultArtifactError(
                        "result_oversized",
                        f"{label} output exceeds the {maximum}-byte aggregate limit.",
                    )
                if entry_count == 1:
                    artifact = Path(entry.path)
                    continue
                raise _ResultArtifactError(
                    "output_ambiguous",
                    f"{label} output must contain only {filename}.",
                )
    except OSError as exc:
        raise _ResultArtifactError(
            "output_ambiguous", f"Cannot inspect {label} output directory: {exc}"
        ) from exc
    if artifact is None:
        raise _ResultArtifactError("result_missing", f"{label} is missing.")
    if artifact.name != filename:
        raise _ResultArtifactError(
            "output_ambiguous",
            f"{label} output must contain only {filename}.",
        )
    if aggregate_bytes == 0:
        raise _ResultArtifactError("result_missing", f"{label} is missing.")
    try:
        return _load_bounded_json_object(artifact, maximum=maximum, label=label)
    except _ResultArtifactError:
        raise
    except OciBrokerError as exc:
        raise _ResultArtifactError("result_invalid", str(exc)) from exc


def _load_bounded_json_object(
    path: Path,
    *,
    maximum: int,
    label: str,
) -> tuple[Mapping[str, Any], str, int]:
    try:
        target = _absolute_regular_file(path, label=label, maximum=maximum)
        digest, size, raw = _read_bounded_file(target, maximum=maximum, label=label)
    except OciBrokerError as exc:
        if "exceeds" in str(exc):
            raise _ResultArtifactError("result_oversized", str(exc)) from exc
        raise
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OciBrokerError(f"{label} must be one UTF-8 JSON object.") from exc
    if not isinstance(payload, Mapping):
        raise OciBrokerError(f"{label} must be a JSON object.")
    return payload, digest, size


def _cleanup_timed_out_container(
    config: OciRuntimeConfig,
    *,
    container_name: str,
    runner: OciProcessRunner,
    environment: Optional[Mapping[str, str]],
) -> str:
    cleanup_command = (config.executable, "rm", "--force", container_name)
    try:
        cleanup = runner(
            cleanup_command,
            env=sanitized_oci_environment(environment),
            timeout_seconds=_CLEANUP_TIMEOUT_SECONDS,
            termination_grace_seconds=config.termination_grace_seconds,
            stdout_limit=_CLEANUP_LOG_LIMIT_BYTES,
            stderr_limit=_CLEANUP_LOG_LIMIT_BYTES,
        )
    except Exception:
        return "inconclusive"
    if cleanup.timed_out or not cleanup.started:
        return "inconclusive"
    return "complete" if cleanup.returncode == 0 else "failed"


def _execute_container_command(
    config: OciRuntimeConfig,
    *,
    command: tuple[str, ...],
    container_name: str,
    runner: OciProcessRunner,
    environment: Optional[Mapping[str, str]],
) -> BoundedProcessResult:
    """Run one named container and fail closed when exception cleanup is unknown."""

    try:
        return runner(
            command,
            env=sanitized_oci_environment(environment),
            timeout_seconds=config.timeout_seconds,
            termination_grace_seconds=config.termination_grace_seconds,
            stdout_limit=config.output_limits.stdout_bytes,
            stderr_limit=config.output_limits.stderr_bytes,
        )
    except BaseException as execution_error:
        cleanup_error: Optional[BaseException] = None
        try:
            cleanup_status = _cleanup_timed_out_container(
                config,
                container_name=container_name,
                runner=runner,
                environment=environment,
            )
        except BaseException as exc:
            cleanup_status = "inconclusive"
            cleanup_error = exc
        if cleanup_status == "complete":
            raise
        detail = (
            f"OCI container cleanup could not be proven "
            f"(container={container_name}, cleanup_status={cleanup_status})."
        )
        if cleanup_error is not None:
            detail += f" Cleanup runner error: {cleanup_error}"
        failure = OciBrokerError(detail)
        if isinstance(execution_error, (KeyboardInterrupt, SystemExit)):
            raise execution_error from failure
        raise failure from execution_error


def _process_status(process: BoundedProcessResult) -> str:
    if not process.started:
        return "start_failed"
    if process.timed_out:
        return "timed_out"
    if process.returncode != 0:
        return "process_failed"
    return "complete"


def _validate_process_result_bounds(
    process: BoundedProcessResult, limits: OciOutputLimits
) -> None:
    if len(process.stdout) > limits.stdout_bytes:
        raise OciBrokerError("Process runner exceeded the stdout capture bound.")
    if len(process.stderr) > limits.stderr_bytes:
        raise OciBrokerError("Process runner exceeded the stderr capture bound.")


def _dispatch_container_name(context: OciDispatchContext) -> str:
    suffix = hashlib.sha256(context.idempotency_key.encode("utf-8")).hexdigest()[:12]
    name = f"p0-{context.role}-{context.attempt}-{suffix}"
    if _CONTAINER_NAME_RE.fullmatch(name) is None:  # pragma: no cover - invariant
        raise OciBrokerError("Derived dispatch container name is unsafe.")
    return name


def _probe_container_name(probe_id: str) -> str:
    _validate_slug(probe_id, "probe_id")
    suffix = hashlib.sha256(probe_id.encode("utf-8")).hexdigest()[:16]
    return f"p0-admission-probe-{suffix}"


def _validate_digest_pinned_image(image: str) -> None:
    if not isinstance(image, str) or _IMAGE_RE.fullmatch(image) is None:
        raise OciBrokerError("OCI image must be a named sha256 digest reference.")
    name = image.rsplit("@", 1)[0]
    if ":" in name.rsplit("/", 1)[-1]:
        raise OciBrokerError(
            "OCI image reference cannot include a mutable tag beside its digest."
        )


def _validate_runtime_executable_name(runtime: str, executable: str) -> None:
    _bounded_text(executable, "OCI executable", maximum=4096)
    candidate = Path(executable)
    if not candidate.is_absolute():
        raise OciBrokerError("OCI executable must be an absolute caller-resolved path.")
    basename = candidate.name.casefold()
    allowed = {runtime, f"{runtime}.exe"}
    if basename not in allowed:
        raise OciBrokerError(
            "OCI executable basename must match the selected docker/podman runtime."
        )
    _validate_mount_text(executable, "OCI executable")


def _absolute_regular_file(path: str | Path, *, label: str, maximum: int) -> Path:
    target = _strict_absolute_path(path, label=label)
    try:
        metadata = target.lstat()
    except OSError as exc:
        raise OciBrokerError(f"Cannot stat {label}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or _is_windows_reparse(metadata):
        raise OciBrokerError(f"{label} cannot be a link or reparse point.")
    if not stat.S_ISREG(metadata.st_mode):
        raise OciBrokerError(f"{label} must be a regular file.")
    if metadata.st_size > maximum:
        raise OciBrokerError(f"{label} exceeds its {maximum}-byte bound.")
    return target


def _absolute_regular_directory(path: str | Path, *, label: str) -> Path:
    target = _strict_absolute_path(path, label=label)
    try:
        metadata = target.lstat()
    except OSError as exc:
        raise OciBrokerError(f"Cannot stat {label}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode) or _is_windows_reparse(metadata):
        raise OciBrokerError(f"{label} cannot be a link or reparse point.")
    if not stat.S_ISDIR(metadata.st_mode):
        raise OciBrokerError(f"{label} must be a regular directory.")
    return target


def _strict_absolute_path(path: str | Path, *, label: str) -> Path:
    target = Path(path)
    if not target.is_absolute():
        raise OciBrokerError(f"{label} must be an absolute path.")
    _validate_mount_text(os.fspath(target), label)
    normalized = Path(os.path.abspath(os.fspath(target)))
    try:
        resolved = normalized.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise OciBrokerError(f"Cannot resolve {label}: {exc}") from exc
    if resolved != normalized:
        raise OciBrokerError(
            f"{label} path cannot traverse a link or non-canonical component."
        )
    return normalized


def _bounded_file_sha256(path: Path, *, maximum: int, label: str) -> tuple[str, int]:
    digest, size, _ = _read_bounded_file(
        path, maximum=maximum, label=label, retain=False
    )
    return digest, size


def _read_bounded_file(
    path: Path,
    *,
    maximum: int,
    label: str,
    retain: bool = True,
) -> tuple[str, int, bytes]:
    hasher = hashlib.sha256()
    captured = bytearray()
    total = 0
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise OciBrokerError(f"Cannot open {label}: {exc}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OciBrokerError(f"{label} must remain a regular file.")
        if metadata.st_size > maximum:
            raise OciBrokerError(f"{label} exceeds its {maximum}-byte bound.")
        while True:
            chunk = os.read(descriptor, min(65536, maximum + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise OciBrokerError(f"{label} exceeds its {maximum}-byte bound.")
            hasher.update(chunk)
            if retain:
                captured.extend(chunk)
    finally:
        os.close(descriptor)
    return "sha256:" + hasher.hexdigest(), total, bytes(captured)


def _file_identity(path: Path) -> tuple[int, int, int, int]:
    try:
        metadata = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise OciBrokerError(
            f"Cannot establish file identity for {path}: {exc}"
        ) from exc
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        int(metadata.st_mode),
        int(getattr(metadata, "st_file_attributes", 0)),
    )


def _identity_matches(path: Path, expected: tuple[int, int, int, int]) -> bool:
    try:
        return _file_identity(path) == expected
    except OciBrokerError:
        return False


def _input_file_unchanged(
    path: Path,
    *,
    expected_identity: tuple[int, int, int, int],
    expected_hash: str,
    maximum: int,
    label: str,
) -> bool:
    if not _identity_matches(path, expected_identity):
        return False
    try:
        actual_hash, _ = _bounded_file_sha256(path, maximum=maximum, label=label)
    except OciBrokerError:
        return False
    return actual_hash == expected_hash


def _is_windows_reparse(metadata: os.stat_result) -> bool:
    attributes = int(getattr(metadata, "st_file_attributes", 0))
    return bool(attributes & 0x00000400)


def _is_relative_to(path: Path, parent: Path) -> bool:
    return shared_path_is_within(path, parent)


def _validate_object(
    payload: Mapping[str, Any], expected: set[str], label: str
) -> None:
    return require_exact_fields(
        payload,
        allowed=expected,
        required=expected,
        mapping_error=OciBrokerError(f"{label} must be an object."),
        missing_error=lambda values: AssertionError(values),
        unknown_error=lambda values: AssertionError(values),
        invalid_error=lambda missing, unknown: _object_fields_error(
            label, missing, unknown
        ),
    )


def _object_fields_error(
    label: str,
    missing: tuple[str, ...],
    unexpected: tuple[str, ...],
) -> OciBrokerError:
    details = []
    if missing:
        details.append(f"missing={list(missing)}")
    if unexpected:
        details.append(f"unexpected={list(unexpected)}")
    return OciBrokerError(f"{label} fields are invalid ({'; '.join(details)}).")


def _required_mapping(value: Any, label: str) -> Mapping[str, Any]:
    return require_mapping(
        value,
        error=OciBrokerError(f"{label} must be an object."),
    )


def _required_text(value: Any, label: str) -> str:
    """Retain the broker protocol's historical non-normalizing text policy."""

    return require_nonempty_text(
        value,
        error=OciBrokerError(f"{label} must be non-empty text."),
        reject_control_characters=False,
    )


def _bounded_text(value: str, label: str, *, maximum: int) -> None:
    require_bounded_text(
        value,
        maximum=maximum,
        error=OciBrokerError(
            f"{label} must contain 1-{maximum} characters."
        ),
        control_error=OciBrokerError(
            f"{label} cannot contain control characters."
        ),
    )


def _required_int(value: Any, label: str) -> int:
    return require_int(
        value,
        error=OciBrokerError(f"{label} must be an integer."),
    )


def _bounded_int(value: int, label: str, *, minimum: int, maximum: int) -> None:
    require_bounded_int(
        value,
        minimum=minimum,
        maximum=maximum,
        invalid_error=OciBrokerError(f"{label} must be an integer."),
        bounds_error=OciBrokerError(
            f"{label} must be between {minimum} and {maximum}."
        ),
    )


def _text_tuple(value: Any, label: str, *, maximum: int) -> tuple[str, ...]:
    return require_string_tuple(
        value,
        error=OciBrokerError(f"{label} must contain 1-{maximum} strings."),
        item_error=OciBrokerError(f"{label} must contain only strings."),
        minimum=1,
        maximum=maximum,
    )


def _validate_slug(value: str, label: str) -> None:
    if not isinstance(value, str) or _SLUG_RE.fullmatch(value) is None:
        raise OciBrokerError(f"{label} must be a portable lowercase identifier.")


def _is_canonical_uuid(value: Any) -> bool:
    return is_canonical_uuid(value)


def _validate_uuid(value: str, label: str) -> None:
    error = OciBrokerError(f"{label} must be a canonical UUID.")
    require_uuid(
        value,
        text_error=error,
        uuid_error=error,
        canonical_error=error,
    )


def _validate_hash(value: str, label: str) -> None:
    require_sha256(
        value,
        digest_error=OciBrokerError(f"{label} must be a sha256 digest."),
    )


def _validate_argv_value(value: str, label: str) -> None:
    _bounded_text(value, label, maximum=4096)
    if "\x00" in value:
        raise OciBrokerError(f"{label} cannot contain NUL.")


def _validate_mount_text(value: str, label: str) -> None:
    _bounded_text(value, label, maximum=8192)
    if "," in value:
        raise OciBrokerError(f"{label} cannot contain commas used by OCI mount syntax.")


def _reject_sensitive_material(value: Any, label: str) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            if not isinstance(raw_key, str):
                raise OciBrokerError(f"{label} object keys must be strings.")
            normalized = raw_key.casefold().replace("-", "_")
            if normalized in _SENSITIVE_KEYS:
                raise OciBrokerError(
                    f"{label} cannot contain credential-bearing field {raw_key!r}."
                )
            _reject_sensitive_material(child, f"{label}.{raw_key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _reject_sensitive_material(child, f"{label}[{index}]")
    elif isinstance(value, str) and _LIKELY_SECRET_RE.search(value):
        raise OciBrokerError(f"{label} appears to contain credential material.")


def _network_canary_response(challenge: str) -> bytes:
    if not isinstance(challenge, str) or _HEX_32_RE.fullmatch(challenge) is None:
        raise OciBrokerError("Network canary challenge must be 32-byte hex.")
    return b"llm-wiki-canary-ack:" + challenge.encode("ascii") + b"\n"


def _read_socket_line(connection: socket.socket, *, maximum: int) -> bytes:
    _bounded_int(maximum, "socket line bound", minimum=1, maximum=4096)
    captured = bytearray()
    while len(captured) <= maximum:
        chunk = connection.recv(min(256, maximum + 1 - len(captured)))
        if not chunk:
            break
        captured.extend(chunk)
        if captured.endswith(b"\n"):
            break
    if len(captured) > maximum:
        raise OciBrokerError("Network canary message exceeded its bound.")
    return bytes(captured)


def _write_exclusive_sentinel(path: Path, content: bytes) -> None:
    if not isinstance(content, bytes) or not content:
        raise OciBrokerError("Host isolation sentinel content must be non-empty bytes.")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        offset = 0
        while offset < len(content):
            written = os.write(descriptor, content[offset:])
            if written <= 0:
                raise OciBrokerError("Cannot write host isolation sentinel.")
            offset += written
        os.fsync(descriptor)
        if os.name != "nt":
            os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)


def _canonical_sha256(value: Any) -> str:
    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OciBrokerError("Value is not canonical JSON.") from exc
    return _bytes_sha256(encoded)


def _bytes_sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _receipt_id(receipt_hash: str) -> str:
    _validate_hash(receipt_hash, "receipt_hash")
    return "receipt-" + receipt_hash.removeprefix("sha256:")[:24]


_restore_legacy_definition_modules(
    globals(),
    legacy_module="llm_wiki_cli.services.documentation_calibration_broker",
)
del _restore_legacy_definition_modules
