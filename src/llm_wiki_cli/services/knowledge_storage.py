"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_storage`."""

import sys

from llm_wiki_engine import knowledge_storage

sys.modules[__name__] = knowledge_storage
