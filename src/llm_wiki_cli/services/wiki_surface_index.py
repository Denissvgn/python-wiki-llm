"""Deprecated alias for :mod:`llm_wiki_engine.wiki_surface_index`."""

import sys
import warnings

from llm_wiki_engine import wiki_surface_index

warnings.warn(
    "llm_wiki_cli.services.wiki_surface_index is deprecated; import llm_wiki_engine.wiki_surface_index instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = wiki_surface_index
