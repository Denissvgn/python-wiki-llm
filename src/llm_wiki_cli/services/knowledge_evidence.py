"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_evidence`."""

import sys

from llm_wiki_engine import knowledge_evidence

sys.modules[__name__] = knowledge_evidence
