"""Deprecated alias for :mod:`llm_wiki_engine.context_packet`."""

import sys
import warnings

from llm_wiki_engine import context_packet

warnings.warn(
    "llm_wiki_cli.services.context_packet is deprecated; import llm_wiki_engine.context_packet instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = context_packet
