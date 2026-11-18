"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_freshness`."""

import sys
import warnings

from llm_wiki_engine import knowledge_freshness

warnings.warn(
    "llm_wiki_cli.services.knowledge_freshness is deprecated; import llm_wiki_engine.knowledge_freshness instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_freshness
