"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_audit`."""

import sys

from llm_wiki_engine import knowledge_audit

sys.modules[__name__] = knowledge_audit
