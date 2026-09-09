"""Compatibility alias for :mod:`llm_wiki_cli.services.calibration.contracts`."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from .calibration import contracts as _implementation


# A module alias, rather than copied exports, keeps legacy monkeypatch targets
# connected to the globals used by the relocated implementation.
if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from .calibration.contracts import (
        CALIBRATION_TERMINAL_OUTCOMES as CALIBRATION_TERMINAL_OUTCOMES,
        DocumentationCalibrationError as DocumentationCalibrationError,
        _portable_relative_path as _portable_relative_path,
        build_flow_evidence_census as build_flow_evidence_census,
        build_p0_calibration_shadow as build_p0_calibration_shadow,
        canonical_json_sha256 as canonical_json_sha256,
        evaluate_calibration_preflight as evaluate_calibration_preflight,
        mechanical_calibration_verdict as mechanical_calibration_verdict,
        validate_flow_evidence_census as validate_flow_evidence_census,
        validate_source_citation as validate_source_citation,
    )

_sys.modules[__name__] = _implementation
