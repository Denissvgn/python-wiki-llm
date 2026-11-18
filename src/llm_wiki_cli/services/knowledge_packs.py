"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_packs`."""

import sys

from llm_wiki_engine import knowledge_packs

sys.modules[__name__] = knowledge_packs
