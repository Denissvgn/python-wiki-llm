"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_storage_io`."""

import sys

from llm_wiki_engine import knowledge_storage_io

sys.modules[__name__] = knowledge_storage_io
