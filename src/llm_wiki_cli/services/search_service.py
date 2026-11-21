"""Deprecated alias for :mod:`llm_wiki_engine.search_service`."""

import sys
import warnings

from llm_wiki_engine import search_service

warnings.warn(
    "llm_wiki_cli.services.search_service is deprecated; import llm_wiki_engine.search_service instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = search_service
