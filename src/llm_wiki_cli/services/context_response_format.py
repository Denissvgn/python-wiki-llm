"""Deprecated alias for :mod:`llm_wiki_engine.context_response_format`."""

import sys
import warnings

from llm_wiki_engine import context_response_format

warnings.warn(
    "llm_wiki_cli.services.context_response_format is deprecated; import llm_wiki_engine.context_response_format instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = context_response_format
