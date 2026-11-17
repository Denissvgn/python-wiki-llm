"""Compatibility alias for :mod:`llm_wiki_engine.progress`."""

import sys

from llm_wiki_engine import progress

sys.modules[__name__] = progress
