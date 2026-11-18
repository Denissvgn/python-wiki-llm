"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_loader`."""

import sys
import warnings

from llm_wiki_engine import knowledge_loader

warnings.warn(
    "llm_wiki_cli.services.knowledge_loader is deprecated; import llm_wiki_engine.knowledge_loader instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_loader
