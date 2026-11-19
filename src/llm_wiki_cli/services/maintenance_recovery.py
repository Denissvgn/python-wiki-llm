"""Deprecated alias for :mod:`llm_wiki_engine.maintenance_recovery`."""

import sys
import warnings

from llm_wiki_engine import maintenance_recovery

warnings.warn(
    "llm_wiki_cli.services.maintenance_recovery is deprecated; import llm_wiki_engine.maintenance_recovery instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = maintenance_recovery
