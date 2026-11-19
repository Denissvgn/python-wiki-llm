"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_validators`."""

import sys
import warnings

from llm_wiki_engine import knowledge_validators

warnings.warn(
    "llm_wiki_cli.services.knowledge_validators is deprecated; import llm_wiki_engine.knowledge_validators instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_validators
