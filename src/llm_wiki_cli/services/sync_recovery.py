"""Deprecated alias for :mod:`llm_wiki_engine.sync_recovery`."""

import sys
import warnings

from llm_wiki_engine import sync_recovery

warnings.warn(
    "llm_wiki_cli.services.sync_recovery is deprecated; import llm_wiki_engine.sync_recovery instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = sync_recovery
