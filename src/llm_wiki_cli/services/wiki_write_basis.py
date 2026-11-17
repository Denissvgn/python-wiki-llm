"""Compatibility alias for :mod:`llm_wiki_engine.wiki_write_basis`."""

import sys

from llm_wiki_engine import wiki_write_basis

sys.modules[__name__] = wiki_write_basis
