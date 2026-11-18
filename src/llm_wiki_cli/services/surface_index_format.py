"""Deprecated alias for :mod:`llm_wiki_engine.surface_index_format`."""

import sys
import warnings

from llm_wiki_engine import surface_index_format

warnings.warn(
    "llm_wiki_cli.services.surface_index_format is deprecated; import llm_wiki_engine.surface_index_format instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = surface_index_format
