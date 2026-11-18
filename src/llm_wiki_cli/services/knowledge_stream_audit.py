"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_stream_audit`."""

import sys
import warnings

from llm_wiki_engine import knowledge_stream_audit

warnings.warn(
    "llm_wiki_cli.services.knowledge_stream_audit is deprecated; import llm_wiki_engine.knowledge_stream_audit instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_stream_audit
