"""Deprecated alias for :mod:`llm_wiki_engine.maintenance_state`."""

import sys
import warnings

from llm_wiki_engine import maintenance_state

warnings.warn(
    "llm_wiki_cli.services.maintenance_state is deprecated; import llm_wiki_engine.maintenance_state instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = maintenance_state
