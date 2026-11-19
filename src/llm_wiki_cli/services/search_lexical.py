"""Deprecated alias for :mod:`llm_wiki_engine.search_lexical`."""

import sys
import warnings

from llm_wiki_engine import search_lexical

warnings.warn(
    "llm_wiki_cli.services.search_lexical is deprecated; import llm_wiki_engine.search_lexical instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = search_lexical
