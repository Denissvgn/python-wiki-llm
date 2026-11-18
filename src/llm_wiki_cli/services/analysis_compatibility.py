"""Deprecated alias for :mod:`llm_wiki_engine.analysis_compatibility`."""

import sys
import warnings

from llm_wiki_engine import analysis_compatibility

warnings.warn(
    "llm_wiki_cli.services.analysis_compatibility is deprecated; import llm_wiki_engine.analysis_compatibility instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = analysis_compatibility
