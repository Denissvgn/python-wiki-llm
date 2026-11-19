"""Deprecated alias for :mod:`llm_wiki_engine.maintenance_status`."""

import sys
import warnings

from llm_wiki_engine import maintenance_status

warnings.warn(
    "llm_wiki_cli.services.maintenance_status is deprecated; import llm_wiki_engine.maintenance_status instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = maintenance_status
