"""Compatibility alias for :mod:`llm_wiki_cli.services.calibration.host_broker`."""

from __future__ import annotations

import sys as _sys

from .calibration import host_broker as _implementation


_sys.modules[__name__] = _implementation
