"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_validators`."""

import sys

from llm_wiki_engine import knowledge_validators

sys.modules[__name__] = knowledge_validators
