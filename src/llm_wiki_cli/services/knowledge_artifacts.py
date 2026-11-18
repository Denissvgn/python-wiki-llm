"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_artifacts`."""

import sys
import warnings

from llm_wiki_engine import knowledge_artifacts

warnings.warn(
    "llm_wiki_cli.services.knowledge_artifacts is deprecated; import llm_wiki_engine.knowledge_artifacts instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_artifacts
