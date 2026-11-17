"""Compatibility alias for :mod:`llm_wiki_engine.immutable`."""

import sys

from llm_wiki_engine import immutable

sys.modules[__name__] = immutable
