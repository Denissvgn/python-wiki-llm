"""CLI compatibility adapter for the lint service."""

from __future__ import annotations

import sys as _sys

from ..services import lint_service as _service

_sys.modules[__name__] = _service
