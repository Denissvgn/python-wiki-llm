"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_model`."""

import sys

from llm_wiki_engine import knowledge_model

sys.modules[__name__] = knowledge_model
