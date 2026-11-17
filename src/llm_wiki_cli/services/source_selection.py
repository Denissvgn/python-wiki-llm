"""Compatibility alias for :mod:`llm_wiki_engine.source_selection`."""

import sys

from llm_wiki_engine import source_selection

sys.modules[__name__] = source_selection
