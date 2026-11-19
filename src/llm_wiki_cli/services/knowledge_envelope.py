"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_envelope`."""

import sys
import warnings

from llm_wiki_engine import knowledge_envelope

warnings.warn(
    "llm_wiki_cli.services.knowledge_envelope is deprecated; import llm_wiki_engine.knowledge_envelope instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_envelope
