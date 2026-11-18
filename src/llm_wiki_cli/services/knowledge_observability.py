"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_observability`."""

import sys

from llm_wiki_engine import knowledge_observability

sys.modules[__name__] = knowledge_observability
