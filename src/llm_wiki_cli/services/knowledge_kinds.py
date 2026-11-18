"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_kinds`."""

import sys

from llm_wiki_engine import knowledge_kinds

sys.modules[__name__] = knowledge_kinds
