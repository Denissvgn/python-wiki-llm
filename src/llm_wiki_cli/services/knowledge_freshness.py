"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_freshness`."""

import sys

from llm_wiki_engine import knowledge_freshness

sys.modules[__name__] = knowledge_freshness
