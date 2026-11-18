"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_governance`."""

import sys
import warnings

from llm_wiki_engine import knowledge_governance

warnings.warn(
    "llm_wiki_cli.services.knowledge_governance is deprecated; import llm_wiki_engine.knowledge_governance instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_governance
