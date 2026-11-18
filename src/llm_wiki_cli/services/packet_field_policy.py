"""Deprecated alias for :mod:`llm_wiki_engine.packet_field_policy`."""

import sys
import warnings

from llm_wiki_engine import packet_field_policy

warnings.warn(
    "llm_wiki_cli.services.packet_field_policy is deprecated; import llm_wiki_engine.packet_field_policy instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = packet_field_policy
