"""Compatibility alias for :mod:`llm_wiki_engine.search_rank`."""

import sys

from llm_wiki_engine import search_rank

sys.modules[__name__] = search_rank
