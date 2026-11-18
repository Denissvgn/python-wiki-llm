"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_storage_access`."""

import sys
import warnings

from llm_wiki_engine import knowledge_storage_access

warnings.warn(
    "llm_wiki_cli.services.knowledge_storage_access is deprecated; import llm_wiki_engine.knowledge_storage_access instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_storage_access
