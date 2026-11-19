"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_consumption`."""

import sys
import warnings

from llm_wiki_engine import knowledge_consumption

warnings.warn(
    "llm_wiki_cli.services.knowledge_consumption is deprecated; import llm_wiki_engine.knowledge_consumption instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_consumption
