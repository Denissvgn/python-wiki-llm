"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_observability`."""

import sys
import warnings

from llm_wiki_engine import knowledge_observability

warnings.warn(
    "llm_wiki_cli.services.knowledge_observability is deprecated; import llm_wiki_engine.knowledge_observability instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_observability
