"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_audit`."""

import sys
import warnings

from llm_wiki_engine import knowledge_audit

warnings.warn(
    "llm_wiki_cli.services.knowledge_audit is deprecated; import llm_wiki_engine.knowledge_audit instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_audit
