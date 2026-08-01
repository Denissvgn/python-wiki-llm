"""Supported host-authentication context for external calibration brokers.

The package deliberately ships no authenticator, credential, provider adapter,
or dynamic plugin loader. An embedding host may scope an authenticator to
lifecycle API calls only after it has established broker identity with an
OS-protected mechanism. Submitted JSON can never select or satisfy the
authenticator, and the stock CLI remains fail-closed outside that context.
"""

from __future__ import annotations

import warnings
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from functools import wraps
from typing import Any, Iterator, Literal, Mapping, Protocol, runtime_checkable

from . import _restore_legacy_definition_modules
from ..validation import require_bounded_text, require_sha256


class HostBrokerAuthenticationError(ValueError):
    """Raised when external broker authentication is unavailable or invalid."""


class HostBrokerAuthenticationUnavailable(HostBrokerAuthenticationError):
    """Raised when no supported host-authenticator context is active."""


@dataclass(frozen=True)
class HostBrokerAuthenticationProof:
    """Secret-free proof returned by a separately authenticated host broker."""

    proof_kind: Literal["attestation", "receipt"]
    authenticator_id: str
    broker_id: str
    broker_session: str
    principal: str
    reference: str
    cohort_id: str
    expires_at: str
    authority_hash: str
    execution_manifest_hash: str
    evidence_bundle_hash: str
    attestation_hash: str
    receipt_hash: str | None = None
    result_hash: str | None = None
    packet_hash: str | None = None
    idempotency_key: str | None = None
    route_id: str | None = None
    role: str | None = None
    attempt: int | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("authenticator_id", self.authenticator_id),
            ("broker_id", self.broker_id),
            ("broker_session", self.broker_session),
            ("principal", self.principal),
            ("reference", self.reference),
            ("cohort_id", self.cohort_id),
            ("expires_at", self.expires_at),
        ):
            _require_bounded_text(value, label)
        for label, value in (
            ("authority_hash", self.authority_hash),
            ("execution_manifest_hash", self.execution_manifest_hash),
            ("evidence_bundle_hash", self.evidence_bundle_hash),
            ("attestation_hash", self.attestation_hash),
        ):
            _require_hash(value, label)
        optional_text = (
            ("idempotency_key", self.idempotency_key),
            ("route_id", self.route_id),
            ("role", self.role),
        )
        for label, value in optional_text:
            if value is not None:
                _require_bounded_text(value, label)
        optional_hashes = (
            ("receipt_hash", self.receipt_hash),
            ("result_hash", self.result_hash),
            ("packet_hash", self.packet_hash),
        )
        for label, value in optional_hashes:
            if value is not None:
                _require_hash(value, label)
        if self.proof_kind == "attestation":
            if any(
                value is not None
                for value in (
                    self.receipt_hash,
                    self.result_hash,
                    self.packet_hash,
                    self.idempotency_key,
                    self.route_id,
                    self.role,
                    self.attempt,
                )
            ):
                raise HostBrokerAuthenticationError(
                    "Attestation proof cannot carry receipt-only bindings."
                )
        elif self.proof_kind == "receipt":
            if any(
                value is None
                for value in (
                    self.receipt_hash,
                    self.result_hash,
                    self.packet_hash,
                    self.idempotency_key,
                    self.route_id,
                    self.role,
                    self.attempt,
                )
            ):
                raise HostBrokerAuthenticationError(
                    "Receipt proof must carry every dispatch binding."
                )
            if (
                not isinstance(self.attempt, int)
                or isinstance(self.attempt, bool)
                or not 1 <= self.attempt <= 2
            ):
                raise HostBrokerAuthenticationError(
                    "Receipt proof attempt must be one or two."
                )
        else:
            raise HostBrokerAuthenticationError(
                "Host broker proof kind is unsupported."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return bounded, secret-free proof evidence for protected storage."""

        return asdict(self)


@runtime_checkable
class HostBrokerAuthenticator(Protocol):
    """Supported protocol implemented after protected host authentication."""

    @property
    def authenticator_id(self) -> str:
        """Return a stable identity for the host authentication implementation."""
        ...

    def authenticate_attestation(
        self,
        *,
        cohort_id: str,
        authority_grant: Mapping[str, Any],
        execution_manifest: Mapping[str, Any],
        attestation: Mapping[str, Any],
        attestation_hash: str,
    ) -> HostBrokerAuthenticationProof:
        """Authenticate and bind one broker attestation."""
        ...

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
    ) -> HostBrokerAuthenticationProof:
        """Authenticate and bind one external dispatch receipt."""
        ...


# The stock CLI never accepts a selector, module name, environment variable, or
# JSON field that can populate this host-owned context.
_HOST_BROKER_AUTHENTICATOR: ContextVar[HostBrokerAuthenticator | None] = ContextVar(
    "llm_wiki_p0_host_broker_authenticator",
    default=None,
)


@contextmanager
def use_calibration_host_broker_authenticator(
    authenticator: HostBrokerAuthenticator,
) -> Iterator[None]:
    """Scope one already-authenticated host broker to lifecycle API calls.

    The caller is part of the trusted computing base and must establish broker
    identity outside submitted JSON before entering this context.  The context
    installs no provider adapter and carries no credential into artifacts.
    """

    if not isinstance(authenticator, HostBrokerAuthenticator):
        raise HostBrokerAuthenticationUnavailable(
            "The host broker authenticator is malformed."
        )
    _require_bounded_text(authenticator.authenticator_id, "authenticator_id")
    token = _HOST_BROKER_AUTHENTICATOR.set(authenticator)
    try:
        yield
    finally:
        _HOST_BROKER_AUTHENTICATOR.reset(token)


@wraps(use_calibration_host_broker_authenticator)
def use_p0_calibration_host_broker_authenticator(
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Compatibility wrapper for the former public API name."""

    warnings.warn(
        "use_p0_calibration_host_broker_authenticator is deprecated; "
        "use use_calibration_host_broker_authenticator instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return use_calibration_host_broker_authenticator(*args, **kwargs)


use_p0_calibration_host_broker_authenticator.__name__ = (
    "use_p0_calibration_host_broker_authenticator"
)
use_p0_calibration_host_broker_authenticator.__qualname__ = (
    "use_p0_calibration_host_broker_authenticator"
)


def require_process_host_broker_authenticator() -> HostBrokerAuthenticator:
    """Return the context-scoped host authenticator or fail closed."""

    authenticator = _HOST_BROKER_AUTHENTICATOR.get()
    if authenticator is None:
        raise HostBrokerAuthenticationUnavailable(
            "External admission requires a separately authenticated host broker; "
            "this process has no host authenticator."
        )
    if not isinstance(authenticator, HostBrokerAuthenticator):
        raise HostBrokerAuthenticationUnavailable(
            "The process host broker authenticator is malformed."
        )
    _require_bounded_text(authenticator.authenticator_id, "authenticator_id")
    return authenticator


def require_attestation_authentication(
    *,
    cohort_id: str,
    authority_grant: Mapping[str, Any],
    execution_manifest: Mapping[str, Any],
    attestation: Mapping[str, Any],
    attestation_hash: str,
) -> HostBrokerAuthenticationProof:
    """Obtain a structured host proof for an external attestation."""

    authenticator = require_process_host_broker_authenticator()
    try:
        proof = authenticator.authenticate_attestation(
            cohort_id=cohort_id,
            authority_grant=authority_grant,
            execution_manifest=execution_manifest,
            attestation=attestation,
            attestation_hash=attestation_hash,
        )
    except Exception as exc:
        raise HostBrokerAuthenticationError(
            f"Host broker rejected the isolation attestation: {exc}"
        ) from exc
    if not isinstance(proof, HostBrokerAuthenticationProof):
        raise HostBrokerAuthenticationError(
            "Host broker attestation authentication returned an invalid proof."
        )
    if proof.authenticator_id != authenticator.authenticator_id:
        raise HostBrokerAuthenticationError(
            "Host broker proof authenticator identity does not match the process."
        )
    return proof


def require_receipt_authentication(
    *,
    cohort_id: str,
    execution_manifest: Mapping[str, Any],
    attestation: Mapping[str, Any],
    receipt: Mapping[str, Any],
    receipt_hash: str,
    result: Mapping[str, Any],
    result_hash: str,
) -> HostBrokerAuthenticationProof:
    """Obtain a structured host proof for an external dispatch receipt."""

    authenticator = require_process_host_broker_authenticator()
    try:
        proof = authenticator.authenticate_receipt(
            cohort_id=cohort_id,
            execution_manifest=execution_manifest,
            attestation=attestation,
            receipt=receipt,
            receipt_hash=receipt_hash,
            result=result,
            result_hash=result_hash,
        )
    except Exception as exc:
        raise HostBrokerAuthenticationError(
            f"Host broker rejected the dispatch receipt: {exc}"
        ) from exc
    if not isinstance(proof, HostBrokerAuthenticationProof):
        raise HostBrokerAuthenticationError(
            "Host broker receipt authentication returned an invalid proof."
        )
    if proof.authenticator_id != authenticator.authenticator_id:
        raise HostBrokerAuthenticationError(
            "Host broker proof authenticator identity does not match the process."
        )
    return proof


def _require_bounded_text(value: Any, label: str) -> str:
    return require_bounded_text(
        value,
        maximum=512,
        error=HostBrokerAuthenticationError(
            f"Host broker {label} must be bounded printable text."
        ),
    )


def _require_hash(value: Any, label: str) -> str:
    return require_sha256(
        value,
        digest_error=HostBrokerAuthenticationError(
            f"Host broker {label} must be a canonical sha256 hash."
        ),
    )


__all__ = [
    "HostBrokerAuthenticationError",
    "HostBrokerAuthenticationProof",
    "HostBrokerAuthenticationUnavailable",
    "HostBrokerAuthenticator",
    "require_attestation_authentication",
    "require_process_host_broker_authenticator",
    "require_receipt_authentication",
    "use_calibration_host_broker_authenticator",
    "use_p0_calibration_host_broker_authenticator",
]


_restore_legacy_definition_modules(
    globals(),
    legacy_module="llm_wiki_cli.services.documentation_calibration_host_broker",
)
del _restore_legacy_definition_modules
