"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_storage_lifecycle`."""

import sys

from llm_wiki_engine import knowledge_storage_lifecycle

sys.modules[__name__] = knowledge_storage_lifecycle
