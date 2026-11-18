"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_links`."""

import sys

from llm_wiki_engine import knowledge_links

sys.modules[__name__] = knowledge_links
