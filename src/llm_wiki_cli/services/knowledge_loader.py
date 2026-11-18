"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_loader`."""

import sys

from llm_wiki_engine import knowledge_loader

sys.modules[__name__] = knowledge_loader
