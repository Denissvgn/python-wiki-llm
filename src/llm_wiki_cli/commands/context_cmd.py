"""CLI compatibility adapter for the context service."""

from __future__ import annotations

import sys as _sys

from ..services import context_service as _service

_sys.modules[__name__] = _service
