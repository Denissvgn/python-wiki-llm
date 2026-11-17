"""Compatibility alias for :mod:`llm_wiki_engine.search_discovery`."""

import sys

from llm_wiki_engine import search_discovery

sys.modules[__name__] = search_discovery
