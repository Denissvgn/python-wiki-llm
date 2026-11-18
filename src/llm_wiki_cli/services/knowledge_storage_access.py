"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_storage_access`."""

import sys

from llm_wiki_engine import knowledge_storage_access

sys.modules[__name__] = knowledge_storage_access
