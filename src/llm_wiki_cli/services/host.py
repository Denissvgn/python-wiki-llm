"""Deprecated alias for :mod:`llm_wiki_engine.host`."""

import sys
import warnings

from llm_wiki_engine import host

warnings.warn(
    "llm_wiki_cli.services.host is deprecated; import llm_wiki_engine.host instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = host
