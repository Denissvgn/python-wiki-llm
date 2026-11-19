"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_storage`."""

import sys
import warnings

from llm_wiki_engine import knowledge_storage

warnings.warn(
    "llm_wiki_cli.services.knowledge_storage is deprecated; import llm_wiki_engine.knowledge_storage instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_storage
