"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_storage_diagnostics`."""

import sys
import warnings

from llm_wiki_engine import knowledge_storage_diagnostics

warnings.warn(
    "llm_wiki_cli.services.knowledge_storage_diagnostics is deprecated; import llm_wiki_engine.knowledge_storage_diagnostics instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_storage_diagnostics
