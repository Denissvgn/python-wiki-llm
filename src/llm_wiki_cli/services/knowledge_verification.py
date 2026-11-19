"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_verification`."""

import sys
import warnings

from llm_wiki_engine import knowledge_verification

warnings.warn(
    "llm_wiki_cli.services.knowledge_verification is deprecated; import llm_wiki_engine.knowledge_verification instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_verification
