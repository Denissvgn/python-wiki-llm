"""Compatibility alias for :mod:`llm_wiki_engine.wiki_surface`."""

import sys

from llm_wiki_engine import wiki_surface

sys.modules[__name__] = wiki_surface
