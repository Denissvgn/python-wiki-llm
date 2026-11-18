"""Deprecated alias for :mod:`llm_wiki_engine.wiki_surface`."""

import sys
import warnings

from llm_wiki_engine import wiki_surface

warnings.warn(
    "llm_wiki_cli.services.wiki_surface is deprecated; import llm_wiki_engine.wiki_surface instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = wiki_surface
