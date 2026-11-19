"""Deprecated alias for :mod:`llm_wiki_engine.source_selection`."""

import sys
import warnings

from llm_wiki_engine import source_selection

warnings.warn(
    "llm_wiki_cli.services.source_selection is deprecated; import llm_wiki_engine.source_selection instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = source_selection
