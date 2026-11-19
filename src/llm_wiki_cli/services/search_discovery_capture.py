"""Deprecated alias for :mod:`llm_wiki_engine.search_discovery_capture`."""

import sys
import warnings

from llm_wiki_engine import search_discovery_capture

warnings.warn(
    "llm_wiki_cli.services.search_discovery_capture is deprecated; import llm_wiki_engine.search_discovery_capture instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = search_discovery_capture
