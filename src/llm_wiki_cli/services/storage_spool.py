"""Deprecated alias for :mod:`llm_wiki_engine.storage_spool`."""

import sys
import warnings

from llm_wiki_engine import storage_spool

warnings.warn(
    "llm_wiki_cli.services.storage_spool is deprecated; import llm_wiki_engine.storage_spool instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = storage_spool
