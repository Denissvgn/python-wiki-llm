"""Compatibility alias for :mod:`llm_wiki_cli.services.calibration.controller`."""

from __future__ import annotations

import sys as _sys

from .calibration import controller as _implementation


_sys.modules[__name__] = _implementation
