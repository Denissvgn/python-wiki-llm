"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_storage_io`."""

import sys
import warnings

from llm_wiki_engine import knowledge_storage_io

warnings.warn(
    "llm_wiki_cli.services.knowledge_storage_io is deprecated; import llm_wiki_engine.knowledge_storage_io instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_storage_io
