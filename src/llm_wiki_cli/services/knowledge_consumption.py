"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_consumption`."""

import sys

from llm_wiki_engine import knowledge_consumption

sys.modules[__name__] = knowledge_consumption
