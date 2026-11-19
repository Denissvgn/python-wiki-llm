"""Deprecated alias for :mod:`llm_wiki_engine.search_source`."""

import sys
import warnings

from llm_wiki_engine import search_source

warnings.warn(
    "llm_wiki_cli.services.search_source is deprecated; import llm_wiki_engine.search_source instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = search_source
