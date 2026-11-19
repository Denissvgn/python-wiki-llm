"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_model`."""

import sys
import warnings

from llm_wiki_engine import knowledge_model

warnings.warn(
    "llm_wiki_cli.services.knowledge_model is deprecated; import llm_wiki_engine.knowledge_model instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_model
