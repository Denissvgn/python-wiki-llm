"""Compatibility alias for :mod:`llm_wiki_cli.services.calibration.broker`."""

from __future__ import annotations

import sys as _sys

from .calibration import broker as _implementation


_sys.modules[__name__] = _implementation
