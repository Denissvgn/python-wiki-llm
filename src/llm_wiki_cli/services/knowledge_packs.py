"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_packs`."""

import sys
import warnings

from llm_wiki_engine import knowledge_packs

warnings.warn(
    "llm_wiki_cli.services.knowledge_packs is deprecated; import llm_wiki_engine.knowledge_packs instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_packs
