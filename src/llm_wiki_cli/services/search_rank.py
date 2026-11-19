"""Deprecated alias for :mod:`llm_wiki_engine.search_rank`."""

import sys
import warnings

from llm_wiki_engine import search_rank

warnings.warn(
    "llm_wiki_cli.services.search_rank is deprecated; import llm_wiki_engine.search_rank instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = search_rank
