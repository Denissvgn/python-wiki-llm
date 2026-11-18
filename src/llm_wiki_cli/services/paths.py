"""Deprecated alias for :mod:`llm_wiki_engine.paths`."""

import sys
import warnings

from llm_wiki_engine import paths

warnings.warn(
    "llm_wiki_cli.services.paths is deprecated; import llm_wiki_engine.paths instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = paths
