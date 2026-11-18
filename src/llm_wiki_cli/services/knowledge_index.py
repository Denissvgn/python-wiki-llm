"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_index`."""

import sys
import warnings

from llm_wiki_engine import knowledge_index

warnings.warn(
    "llm_wiki_cli.services.knowledge_index is deprecated; import llm_wiki_engine.knowledge_index instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_index
