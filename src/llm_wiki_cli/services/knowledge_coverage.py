"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_coverage`."""

import sys

from llm_wiki_engine import knowledge_coverage

sys.modules[__name__] = knowledge_coverage
