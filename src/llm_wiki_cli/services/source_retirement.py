"""Deprecated alias for :mod:`llm_wiki_engine.source_retirement`."""

import sys
import warnings

from llm_wiki_engine import source_retirement

warnings.warn(
    "llm_wiki_cli.services.source_retirement is deprecated; import llm_wiki_engine.source_retirement instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = source_retirement
