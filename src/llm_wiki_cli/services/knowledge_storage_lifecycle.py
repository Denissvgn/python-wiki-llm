"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_storage_lifecycle`."""

import sys
import warnings

from llm_wiki_engine import knowledge_storage_lifecycle

warnings.warn(
    "llm_wiki_cli.services.knowledge_storage_lifecycle is deprecated; import llm_wiki_engine.knowledge_storage_lifecycle instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_storage_lifecycle
