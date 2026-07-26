"""Focused tests for the private external-broker authentication seam."""

from __future__ import annotations

from typing import Any, Mapping

import pytest

from llm_wiki_cli.services import documentation_calibration_host_broker as host_broker


_HASH_A = "sha256:" + "a" * 64
_HASH_B = "sha256:" + "b" * 64
_HASH_C = "sha256:" + "c" * 64
_HASH_D = "sha256:" + "d" * 64


class _Authenticator:
    authenticator_id = "host-authenticator-v1"

    def authenticate_attestation(
        self,
        *,
        cohort_id: str,
        authority_grant: Mapping[str, Any],
        execution_manifest: Mapping[str, Any],
        attestation: Mapping[str, Any],
        attestation_hash: str,
    ) -> host_broker.HostBrokerAuthenticationProof:
        del authority_grant, execution_manifest
        return host_broker.HostBrokerAuthenticationProof(
            proof_kind="attestation",
            authenticator_id=self.authenticator_id,
            broker_id=str(attestation["runtime"]["broker_id"]),
            broker_session=str(attestation["authentication"]["reference"]),
            principal="authenticated-broker-principal",
            reference="host-ipc-attestation-001",
            cohort_id=cohort_id,
            expires_at=str(attestation["expires_at"]),
            authority_hash=str(attestation["authority_hash"]),
            execution_manifest_hash=str(attestation["execution_manifest_hash"]),
            evidence_bundle_hash=str(attestation["evidence_bundle_hash"]),
            attestation_hash=attestation_hash,
        )

    def authenticate_receipt(
        self,
        *,
        cohort_id: str,
        execution_manifest: Mapping[str, Any],
        attestation: Mapping[str, Any],
        receipt: Mapping[str, Any],
        receipt_hash: str,
        result: Mapping[str, Any],
        result_hash: str,
    ) -> host_broker.HostBrokerAuthenticationProof:
        del execution_manifest, result
        return host_broker.HostBrokerAuthenticationProof(
            proof_kind="receipt",
            authenticator_id=self.authenticator_id,
            broker_id=str(attestation["runtime"]["broker_id"]),
            broker_session=str(attestation["authentication"]["reference"]),
            principal="authenticated-broker-principal",
            reference="host-ipc-receipt-001",
            cohort_id=cohort_id,
            expires_at=str(attestation["expires_at"]),
            authority_hash=str(attestation["authority_hash"]),
            execution_manifest_hash=str(attestation["execution_manifest_hash"]),
            evidence_bundle_hash=str(attestation["evidence_bundle_hash"]),
            attestation_hash=_HASH_D,
            receipt_hash=receipt_hash,
            result_hash=result_hash,
            packet_hash=str(receipt["packet_hash"]),
            idempotency_key=str(receipt["idempotency_key"]),
            route_id=str(receipt["route_id"]),
            role=str(receipt["role"]),
            attempt=int(receipt["attempt"]),
        )


def test_external_broker_authentication_is_unavailable_by_default():
    with pytest.raises(
        host_broker.HostBrokerAuthenticationError,
        match="no host authenticator",
    ):
        host_broker.require_process_host_broker_authenticator()


def test_host_authenticator_returns_structured_bound_proofs():
    authenticator = _Authenticator()
    attestation = {
        "authority_hash": _HASH_A,
        "execution_manifest_hash": _HASH_B,
        "evidence_bundle_hash": _HASH_C,
        "expires_at": "2099-01-01T00:00:00Z",
        "runtime": {"broker_id": "broker-001"},
        "authentication": {"reference": "broker-session-001"},
    }
    with host_broker.use_p0_calibration_host_broker_authenticator(authenticator):
        proof = host_broker.require_attestation_authentication(
            cohort_id="cohort-001",
            authority_grant={},
            execution_manifest={},
            attestation=attestation,
            attestation_hash=_HASH_D,
        )

    assert proof.proof_kind == "attestation"
    assert proof.authenticator_id == authenticator.authenticator_id
    assert proof.broker_session == "broker-session-001"
    assert proof.attestation_hash == _HASH_D
    assert proof.receipt_hash is None


def test_host_authenticator_binds_dispatch_failure_result_bytes():
    class _CapturingAuthenticator(_Authenticator):
        seen_result: dict[str, Any] | None = None

        def authenticate_receipt(self, **kwargs):  # type: ignore[no-untyped-def]
            self.seen_result = dict(kwargs["result"])
            return super().authenticate_receipt(**kwargs)

    authenticator = _CapturingAuthenticator()
    attestation = {
        "authority_hash": _HASH_A,
        "execution_manifest_hash": _HASH_B,
        "evidence_bundle_hash": _HASH_C,
        "expires_at": "2099-01-01T00:00:00Z",
        "runtime": {"broker_id": "broker-001"},
        "authentication": {"reference": "broker-session-001"},
    }
    receipt = {
        "packet_hash": _HASH_C,
        "idempotency_key": "idempotency-001",
        "route_id": "route-001",
        "role": "intake-a",
        "attempt": 1,
        "status": "resource_exhausted",
        "started": True,
    }
    failure_result = {
        "status": "dispatch_failed",
        "failure": {
            "reason_code": "resource_exhausted",
            "message": "The authenticated broker exhausted its resource limit.",
            "dispatch_started": True,
            "retry_allowed": False,
        },
    }

    with host_broker.use_p0_calibration_host_broker_authenticator(authenticator):
        proof = host_broker.require_receipt_authentication(
            cohort_id="cohort-001",
            execution_manifest={},
            attestation=attestation,
            receipt=receipt,
            receipt_hash=_HASH_A,
            result=failure_result,
            result_hash=_HASH_B,
        )

    assert authenticator.seen_result == failure_result
    assert proof.receipt_hash == _HASH_A
    assert proof.result_hash == _HASH_B
    assert proof.idempotency_key == "idempotency-001"


def test_boolean_authentication_result_is_rejected():
    class _BooleanAuthenticator(_Authenticator):
        def authenticate_attestation(self, **_kwargs):  # type: ignore[no-untyped-def]
            return True

    with host_broker.use_p0_calibration_host_broker_authenticator(
        _BooleanAuthenticator()  # type: ignore[arg-type]
    ):
        with pytest.raises(
            host_broker.HostBrokerAuthenticationError,
            match="invalid proof",
        ):
            host_broker.require_attestation_authentication(
                cohort_id="cohort-001",
                authority_grant={},
                execution_manifest={},
                attestation={},
                attestation_hash=_HASH_A,
            )


def test_receipt_proof_requires_every_dispatch_binding():
    with pytest.raises(
        host_broker.HostBrokerAuthenticationError,
        match="every dispatch binding",
    ):
        host_broker.HostBrokerAuthenticationProof(
            proof_kind="receipt",
            authenticator_id="host-authenticator-v1",
            broker_id="broker-001",
            broker_session="broker-session-001",
            principal="authenticated-broker-principal",
            reference="host-ipc-receipt-001",
            cohort_id="cohort-001",
            expires_at="2099-01-01T00:00:00Z",
            authority_hash=_HASH_A,
            execution_manifest_hash=_HASH_B,
            evidence_bundle_hash=_HASH_C,
            attestation_hash=_HASH_D,
        )
