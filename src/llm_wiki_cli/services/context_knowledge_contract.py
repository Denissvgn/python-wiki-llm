"""Deprecated alias for :mod:`llm_wiki_engine.context_knowledge_contract`."""

import sys
import warnings

from llm_wiki_engine import context_knowledge_contract

warnings.warn(
    "llm_wiki_cli.services.context_knowledge_contract is deprecated; import llm_wiki_engine.context_knowledge_contract instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = context_knowledge_contract
