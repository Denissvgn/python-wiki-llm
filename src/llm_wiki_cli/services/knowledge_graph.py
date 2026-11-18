"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_graph`."""

import sys
import warnings

from llm_wiki_engine import knowledge_graph

warnings.warn(
    "llm_wiki_cli.services.knowledge_graph is deprecated; import llm_wiki_engine.knowledge_graph instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_graph
