"""Deprecated alias for :mod:`llm_wiki_engine.knowledge_links`."""

import sys
import warnings

from llm_wiki_engine import knowledge_links

warnings.warn(
    "llm_wiki_cli.services.knowledge_links is deprecated; import llm_wiki_engine.knowledge_links instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = knowledge_links
