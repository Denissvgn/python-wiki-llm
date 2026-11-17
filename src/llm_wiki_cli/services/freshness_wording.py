"""Compatibility alias for :mod:`llm_wiki_engine.freshness_wording`."""

import sys

from llm_wiki_engine import freshness_wording

sys.modules[__name__] = freshness_wording
