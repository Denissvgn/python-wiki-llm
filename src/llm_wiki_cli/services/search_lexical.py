"""Compatibility alias for :mod:`llm_wiki_engine.search_lexical`."""

import sys

from llm_wiki_engine import search_lexical

sys.modules[__name__] = search_lexical
