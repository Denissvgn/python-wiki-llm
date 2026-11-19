"""Deprecated alias for :mod:`llm_wiki_engine.search_discovery`."""

import sys
import warnings

from llm_wiki_engine import search_discovery

warnings.warn(
    "llm_wiki_cli.services.search_discovery is deprecated; import llm_wiki_engine.search_discovery instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = search_discovery
