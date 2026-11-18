"""Deprecated alias for :mod:`llm_wiki_engine.maintenance_protocol`."""

import sys
import warnings

from llm_wiki_engine import maintenance_protocol

warnings.warn(
    "llm_wiki_cli.services.maintenance_protocol is deprecated; import llm_wiki_engine.maintenance_protocol instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = maintenance_protocol
