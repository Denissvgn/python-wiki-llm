"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_coverage`."""

import sys
import warnings

from llm_wiki_engine import knowledge_coverage

warnings.warn(
    "llm_wiki_cli.services.knowledge_coverage is deprecated; import llm_wiki_engine.knowledge_coverage instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_coverage
