"""Compatibility alias for :mod:`llm_wiki_cli.services.calibration.broker`."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from .calibration import broker as _implementation


if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from .calibration.broker import (
        BoundedProcessResult as BoundedProcessResult,
        CALIBRATION_AGENT_ROLES as CALIBRATION_AGENT_ROLES,
        FILESYSTEM_ISOLATION_PROBES as FILESYSTEM_ISOLATION_PROBES,
        LOCAL_NO_EGRESS_PROFILE as LOCAL_NO_EGRESS_PROFILE,
        OciAdmissionProbeEnvironment as OciAdmissionProbeEnvironment,
        OciAdmissionProbeOutcome as OciAdmissionProbeOutcome,
        OciAdmissionProbeRequest as OciAdmissionProbeRequest,
        OciAdmissionProbeResult as OciAdmissionProbeResult,
        OciBrokerError as OciBrokerError,
        OciDispatchContext as OciDispatchContext,
        OciDispatchOutcome as OciDispatchOutcome,
        OciDispatchReceipt as OciDispatchReceipt,
        OciImageCommand as OciImageCommand,
        OciNetworkCanaryBinding as OciNetworkCanaryBinding,
        OciOutputLimits as OciOutputLimits,
        OciProbeCheck as OciProbeCheck,
        OciProbeSentinel as OciProbeSentinel,
        OciProcessRunner as OciProcessRunner,
        OciResourceLimits as OciResourceLimits,
        OciRuntimeConfig as OciRuntimeConfig,
        OciStreamEvidence as OciStreamEvidence,
        REQUIRED_ISOLATION_PROBES as REQUIRED_ISOLATION_PROBES,
        SUPPORTED_AGENT_ROLES as SUPPORTED_AGENT_ROLES,
        SUPPORTED_OCI_RUNTIMES as SUPPORTED_OCI_RUNTIMES,
        _LocalEgressCanary as _LocalEgressCanary,
        _ResultArtifactError as _ResultArtifactError,
        _load_single_json_result as _load_single_json_result,
        _network_canary_response as _network_canary_response,
        _read_socket_line as _read_socket_line,
        build_oci_dispatch_command as build_oci_dispatch_command,
        build_oci_probe_command as build_oci_probe_command,
        canonical_result_json_bytes as canonical_result_json_bytes,
        create_oci_admission_probe_environment as create_oci_admission_probe_environment,
        dispatch_oci_agent as dispatch_oci_agent,
        execute_oci_admission_probe as execute_oci_admission_probe,
        os as os,
        run_bounded_process as run_bounded_process,
        sanitized_oci_environment as sanitized_oci_environment,
        socket as socket,
        threading as threading,
        validate_execution_manifest as validate_execution_manifest,
    )

_sys.modules[__name__] = _implementation
