"""Compatibility alias for :mod:`llm_wiki_engine.knowledge_stream_audit`."""

import sys

from llm_wiki_engine import knowledge_stream_audit

sys.modules[__name__] = knowledge_stream_audit
