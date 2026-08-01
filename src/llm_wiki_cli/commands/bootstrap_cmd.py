"""CLI compatibility adapter for the bootstrap runtime service."""

from __future__ import annotations

import sys as _sys

from ..services import bootstrap_runtime as _service

_sys.modules[__name__] = _service
