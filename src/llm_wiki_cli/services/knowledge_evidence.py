"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_evidence`."""

import sys
import warnings

from llm_wiki_engine import knowledge_evidence

warnings.warn(
    "llm_wiki_cli.services.knowledge_evidence is deprecated; import llm_wiki_engine.knowledge_evidence instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_evidence
