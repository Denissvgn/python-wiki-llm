"""Deprecated alias for :mod:`llm_wiki_engine.progress`."""

import sys
import warnings

from llm_wiki_engine import progress

warnings.warn(
    "llm_wiki_cli.services.progress is deprecated; import llm_wiki_engine.progress instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = progress
