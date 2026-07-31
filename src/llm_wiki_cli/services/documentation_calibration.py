"""Compatibility alias for :mod:`llm_wiki_cli.services.calibration.contracts`."""

from __future__ import annotations

import sys as _sys

from .calibration import contracts as _implementation


# A module alias, rather than copied exports, keeps legacy monkeypatch targets
# connected to the globals used by the relocated implementation.
_sys.modules[__name__] = _implementation
