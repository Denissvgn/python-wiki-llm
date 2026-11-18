"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_index`."""

import sys

from llm_wiki_engine import knowledge_index

sys.modules[__name__] = knowledge_index
