"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_verification`."""

import sys

from llm_wiki_engine import knowledge_verification

sys.modules[__name__] = knowledge_verification
