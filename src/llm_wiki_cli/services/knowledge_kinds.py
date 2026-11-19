"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_kinds`."""

import sys
import warnings

from llm_wiki_engine import knowledge_kinds

warnings.warn(
    "llm_wiki_cli.services.knowledge_kinds is deprecated; import llm_wiki_engine.knowledge_kinds instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_kinds
