"""Compatibility alias for :mod:`llm_wiki_engine.search_source`."""

import sys

from llm_wiki_engine import search_source

sys.modules[__name__] = search_source
