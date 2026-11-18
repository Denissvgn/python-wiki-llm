"""Deprecated alias for :mod:`llm_wiki_engine.io`."""

import sys
import warnings

from llm_wiki_engine import io

warnings.warn(
    "llm_wiki_cli.services.io is deprecated; import llm_wiki_engine.io instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = io
