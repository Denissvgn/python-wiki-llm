"""Deprecated alias for :mod:`llm_wiki_engine.immutable`."""

import sys
import warnings

from llm_wiki_engine import immutable

warnings.warn(
    "llm_wiki_cli.services.immutable is deprecated; import llm_wiki_engine.immutable instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = immutable
