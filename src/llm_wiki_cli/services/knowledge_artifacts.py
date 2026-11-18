"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_artifacts`."""

import sys

from llm_wiki_engine import knowledge_artifacts

sys.modules[__name__] = knowledge_artifacts
