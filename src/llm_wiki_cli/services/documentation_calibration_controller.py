"""Compatibility alias for :mod:`llm_wiki_cli.services.calibration.controller`."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from .calibration import controller as _implementation


if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from .calibration.controller import (
        ADMISSION_PROFILES as ADMISSION_PROFILES,
        CALIBRATION_ROLES as CALIBRATION_ROLES,
        CALIBRATION_STATES as CALIBRATION_STATES,
        CALIBRATION_TERMINAL_STATES as CALIBRATION_TERMINAL_STATES,
        INTAKE_ROLES as INTAKE_ROLES,
        P0CalibrationAgentPacket as P0CalibrationAgentPacket,
        P0CalibrationAgentResult as P0CalibrationAgentResult,
        P0CalibrationDispatchReceipt as P0CalibrationDispatchReceipt,
        P0CalibrationError as P0CalibrationError,
        P0CalibrationIntegrityError as P0CalibrationIntegrityError,
        P0CalibrationRecoveryError as P0CalibrationRecoveryError,
        P0CalibrationRun as P0CalibrationRun,
        P0CalibrationSchemaError as P0CalibrationSchemaError,
        P0CalibrationStatus as P0CalibrationStatus,
        P0CalibrationTransitionError as P0CalibrationTransitionError,
        P0CalibrationVerificationReport as P0CalibrationVerificationReport,
        _admit_external_broker as _admit_external_broker,
        _compile_evidence_bundle as _compile_evidence_bundle,
        _portable_relative_path as _portable_relative_path,
        _read_bound_evidence_file as _read_bound_evidence_file,
        _read_workspace_json as _read_workspace_json,
        _require_choice as _require_choice,
        _require_sha256 as _require_sha256,
        _require_timestamp as _require_timestamp,
        _require_uuid as _require_uuid,
        admit_calibration_run as admit_calibration_run,
        admit_p0_calibration_run as admit_p0_calibration_run,
        build_calibration_agent_packet as build_calibration_agent_packet,
        build_p0_calibration_agent_packet as build_p0_calibration_agent_packet,
        dispatch_calibration_agent as dispatch_calibration_agent,
        dispatch_p0_calibration_agent as dispatch_p0_calibration_agent,
        get_calibration_run_status as get_calibration_run_status,
        get_p0_calibration_run_status as get_p0_calibration_run_status,
        os as os,
        prepare_calibration_run as prepare_calibration_run,
        prepare_p0_calibration_run as prepare_p0_calibration_run,
        record_calibration_agent_result as record_calibration_agent_result,
        record_p0_calibration_agent_result as record_p0_calibration_agent_result,
        validate_p0_calibration_packet_output as validate_p0_calibration_packet_output,
        verify_calibration_run as verify_calibration_run,
        verify_p0_calibration_run as verify_p0_calibration_run,
    )

_sys.modules[__name__] = _implementation
