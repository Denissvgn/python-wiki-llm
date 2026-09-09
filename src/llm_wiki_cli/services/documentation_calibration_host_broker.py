"""Compatibility alias for :mod:`llm_wiki_cli.services.calibration.host_broker`."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from .calibration import host_broker as _implementation


if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from .calibration.host_broker import (
        HostBrokerAuthenticationError as HostBrokerAuthenticationError,
        HostBrokerAuthenticationProof as HostBrokerAuthenticationProof,
        HostBrokerAuthenticationUnavailable as HostBrokerAuthenticationUnavailable,
        HostBrokerAuthenticator as HostBrokerAuthenticator,
        _HOST_BROKER_AUTHENTICATOR as _HOST_BROKER_AUTHENTICATOR,
        require_attestation_authentication as require_attestation_authentication,
        require_process_host_broker_authenticator as require_process_host_broker_authenticator,
        require_receipt_authentication as require_receipt_authentication,
        use_calibration_host_broker_authenticator as use_calibration_host_broker_authenticator,
        use_p0_calibration_host_broker_authenticator as use_p0_calibration_host_broker_authenticator,
    )

_sys.modules[__name__] = _implementation
