#!/usr/local/bin/python3
"""Synthetic worker and adversarial probe used only by the public OCI CI lane."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import signal
import socket
import uuid
from pathlib import Path
from typing import Any, Mapping


_AGENT_RESULT_SCHEMA = "llm-wiki-p0-calibration-agent-result/v1"
_PROBE_RESULT_SCHEMA = "llm-wiki-p0-calibration-isolation-probe-result/v1"
_PROBES = (
    "controller_read",
    "source_read",
    "credential_read",
    "other_role_read",
    "holdout_read",
    "network_egress",
    "container_engine_socket",
    "output_write_bound",
)
_IMAGE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_MAX_INPUT_BYTES = 1024 * 1024


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
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


def _canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _read_json(path: str) -> tuple[dict[str, Any], bytes]:
    raw = Path(path).read_bytes()
    if len(raw) > _MAX_INPUT_BYTES:
        raise ValueError("Synthetic fixture input exceeds its public test bound.")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Synthetic fixture input must be a JSON object.")
    return payload, raw


def _write_json(path: str, payload: Mapping[str, Any]) -> None:
    with Path(path).open("r+b") as stream:
        stream.seek(0)
        stream.truncate(0)
        stream.write(_canonical_json_bytes(payload))
        stream.flush()
        os.fsync(stream.fileno())


def _claim(claim_id: str, statement: str) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "statement": statement,
        "citations": ["synthetic-public-evidence"],
    }


def _run_worker(packet_path: str, result_path: str) -> None:
    packet, packet_bytes = _read_json(packet_path)
    packet_id = str(packet["packet_id"])
    result = {
        "schema_version": _AGENT_RESULT_SCHEMA,
        "result_id": str(uuid.uuid5(uuid.UUID(packet_id), "synthetic-oci-result")),
        "cohort_id": packet["cohort_id"],
        "packet_id": packet_id,
        "role": packet["role"],
        "attempt": packet["attempt"],
        "packet_hash": ("sha256:" + hashlib.sha256(packet_bytes).hexdigest()),
        "idempotency_key": packet["idempotency_key"],
        "status": "complete",
        "proposal": {
            "purpose": _claim(
                "purpose",
                "Exercise a public synthetic OCI isolation fixture.",
            ),
            "audiences": [_claim("audience", "Maintainers qualifying the OCI broker.")],
            "capabilities": [
                _claim("capability", "Run a bounded credential-free worker.")
            ],
            "tasks": [_claim("task", "Verify one isolated synthetic dispatch.")],
            "journeys": [
                _claim("journey", "Build, probe, dispatch, and verify locally.")
            ],
            "contradictions": [],
            "unknowns": [],
            "limitations": [
                _claim(
                    "limitation",
                    "This fixture does not qualify private evidence or providers.",
                )
            ],
        },
    }
    _write_json(result_path, result)


def _filesystem_probe(sentinel: Mapping[str, Any]) -> dict[str, Any]:
    probe = str(sentinel["probe"])
    target = str(sentinel["host_path"])
    observed_sha256: str | None = None
    try:
        with open(target, "rb") as stream:
            observed = stream.read(int(sentinel["content_bytes"]) + 1)
        observed_sha256 = "sha256:" + hashlib.sha256(observed).hexdigest()
    except (FileNotFoundError, PermissionError):
        outcome = "denied"
        detail = "host sentinel read was denied"
    except OSError:
        outcome = "inconclusive"
        detail = "host sentinel read was inconclusive"
    else:
        outcome = "accessible"
        detail = "host sentinel bytes were accessible"
    return {
        "probe": probe,
        "target_id": str(sentinel["sentinel_id"]),
        "target_sha256": str(sentinel["content_sha256"]),
        "attempted": True,
        "outcome": outcome,
        "evidence": {
            "read_succeeded": outcome == "accessible",
            "observed_sha256": observed_sha256,
        },
        "detail": detail,
    }


def _network_probe(canary: Mapping[str, Any]) -> dict[str, Any]:
    connected = False
    try:
        connection = socket.create_connection(
            (str(canary["host"]), int(canary["port"])),
            timeout=0.5,
        )
    except OSError:
        pass
    else:
        with connection:
            connected = True
            connection.settimeout(0.5)
            connection.sendall(str(canary["challenge"]).encode("ascii") + b"\n")
            response = connection.recv(256)
            if (
                "sha256:" + hashlib.sha256(response).hexdigest()
                != canary["response_sha256"]
            ):
                connected = True
    non_loopback_interfaces = sorted(
        name
        for _index, name in socket.if_nameindex()
        if name.casefold() not in {"lo", "lo0"}
    )
    default_route = False
    try:
        route_lines = Path("/proc/net/route").read_text(encoding="ascii").splitlines()
    except OSError:
        route_lines = []
    for line in route_lines[1:]:
        fields = line.split()
        if len(fields) >= 4 and fields[1] == "00000000":
            try:
                route_is_up = bool(int(fields[3], 16) & 0x1)
            except ValueError:
                route_is_up = False
            default_route = default_route or route_is_up
    accessible = connected or bool(non_loopback_interfaces) or default_route
    outcome = "accessible" if accessible else "denied"
    return {
        "probe": "network_egress",
        "target_id": str(canary["canary_id"]),
        "target_sha256": _canonical_sha256(canary),
        "attempted": True,
        "outcome": outcome,
        "evidence": {
            "canary_connected": connected,
            "non_loopback_interfaces": non_loopback_interfaces,
            "default_route": default_route,
        },
        "detail": (
            "local canary or non-loopback network capability was accessible"
            if accessible
            else "known-reachable host canary was denied and namespace had only loopback"
        ),
    }


def _engine_socket_probe(targets: list[str]) -> dict[str, Any]:
    connected_targets: list[str] = []
    for target in targets:
        candidate = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        candidate.settimeout(0.5)
        try:
            candidate.connect(target)
        except OSError:
            pass
        else:
            connected_targets.append(target)
        finally:
            candidate.close()
    return {
        "probe": "container_engine_socket",
        "target_id": "container-engine-sockets",
        "target_sha256": _canonical_sha256(targets),
        "attempted": True,
        "outcome": "accessible" if connected_targets else "denied",
        "evidence": {"connected_targets": connected_targets},
        "detail": (
            "container-engine socket unexpectedly accepted a connection"
            if connected_targets
            else "container-engine sockets were inaccessible"
        ),
    }


def _output_write_bound_probe(result_path: str, limit_bytes: int) -> dict[str, Any]:
    attempted_bytes = limit_bytes + 1
    result = Path(result_path)
    oversize_succeeded = False
    oversize_denied = False
    previous_handler = signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    try:
        try:
            with result.open("r+b", buffering=0) as stream:
                os.ftruncate(stream.fileno(), attempted_bytes)
        except OSError as exc:
            oversize_denied = exc.errno == errno.EFBIG
        else:
            oversize_succeeded = True
    finally:
        signal.signal(signal.SIGXFSZ, previous_handler)

    try:
        observed_size = result.stat().st_size
    except OSError:
        observed_size = attempted_bytes

    sibling = result.with_name("unexpected-output-probe")
    sibling_succeeded = False
    sibling_denied = False
    try:
        with sibling.open("xb"):
            sibling_succeeded = True
    except OSError as exc:
        sibling_denied = exc.errno in {errno.EACCES, errno.EPERM, errno.EROFS}
    finally:
        if sibling_succeeded:
            try:
                sibling.unlink()
            except OSError:
                pass

    accessible = oversize_succeeded or sibling_succeeded or observed_size > limit_bytes
    if accessible:
        outcome = "accessible"
        detail = "persistent output exceeded its single-file byte boundary"
    elif oversize_denied and sibling_denied:
        outcome = "denied"
        detail = "oversize and sibling persistent writes were denied"
    else:
        outcome = "inconclusive"
        detail = "persistent output enforcement could not be proven"

    # Restore the pre-created slot for the canonical result.  A missing or
    # non-writable slot fails the probe process instead of manufacturing proof.
    with result.open("r+b", buffering=0) as stream:
        stream.truncate(0)
        os.fsync(stream.fileno())

    binding = {
        "mechanism": "single_file_bind+rlimit_fsize/v1",
        "result_bytes": limit_bytes,
    }
    return {
        "probe": "output_write_bound",
        "target_id": "single-result-output-bound",
        "target_sha256": _canonical_sha256(binding),
        "attempted": True,
        "outcome": outcome,
        "evidence": {
            "limit_bytes": limit_bytes,
            "attempted_bytes": attempted_bytes,
            "oversize_write_succeeded": oversize_succeeded,
            "sibling_write_succeeded": sibling_succeeded,
            "observed_size": observed_size,
        },
        "detail": detail,
    }


def _run_probe(
    request_path: str,
    result_path: str,
    image_digest: str,
) -> None:
    request, _ = _read_json(request_path)
    if tuple(request.get("required_checks", ())) != _PROBES:
        raise ValueError("Synthetic probe request omitted a mandatory check.")
    if _IMAGE_DIGEST_RE.fullmatch(image_digest) is None:
        raise ValueError("Synthetic probe image digest is malformed.")
    access_events = [
        _filesystem_probe(sentinel) for sentinel in request["filesystem_sentinels"]
    ]
    access_events.append(_network_probe(request["network_canary"]))
    access_events.append(
        _engine_socket_probe(
            [str(value) for value in request["container_engine_sockets"]]
        )
    )
    access_events.append(
        _output_write_bound_probe(
            result_path,
            int(request["output_limit_bytes"]),
        )
    )
    status = (
        "passed"
        if all(
            event["attempted"] and event["outcome"] == "denied"
            for event in access_events
        )
        else "failed"
    )
    result = {
        "schema_version": _PROBE_RESULT_SCHEMA,
        "cohort_id": request["cohort_id"],
        "probe_id": request["probe_id"],
        "request_hash": (
            "sha256:" + hashlib.sha256(_canonical_json_bytes(request)).hexdigest()
        ),
        "image_digest": image_digest,
        "access_events": access_events,
        "status": status,
    }
    _write_json(result_path, result)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    worker = subparsers.add_parser("worker")
    worker.add_argument("--packet", required=True)
    worker.add_argument("--result", required=True)
    probe = subparsers.add_parser("probe")
    probe.add_argument("--probe-request", required=True)
    probe.add_argument("--probe-result", required=True)
    probe.add_argument("--image-digest", required=True)
    args = parser.parse_args()
    if args.mode == "worker":
        _run_worker(args.packet, args.result)
    else:
        _run_probe(args.probe_request, args.probe_result, args.image_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
