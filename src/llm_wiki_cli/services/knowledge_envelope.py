"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_envelope`."""

import sys

from llm_wiki_engine import knowledge_envelope

sys.modules[__name__] = knowledge_envelope
