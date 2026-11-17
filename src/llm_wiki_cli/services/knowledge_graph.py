"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_graph`."""

import sys

from llm_wiki_engine import knowledge_graph

sys.modules[__name__] = knowledge_graph
