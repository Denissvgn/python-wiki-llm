"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_governance`."""

import sys

from llm_wiki_engine import knowledge_governance

sys.modules[__name__] = knowledge_governance
