"""Deprecated alias for :mod:`llm_wiki_engine.sync_transition_execution`."""

import sys
import warnings

from llm_wiki_engine import sync_transition_execution

warnings.warn(
    "llm_wiki_cli.services.sync_transition_execution is deprecated; import llm_wiki_engine.sync_transition_execution instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = sync_transition_execution
