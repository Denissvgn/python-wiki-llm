"""Deprecated alias for :mod:`llm_wiki_engine.normalization_diagnostics`."""

import sys
import warnings

from llm_wiki_engine import normalization_diagnostics

warnings.warn(
    "llm_wiki_cli.services.normalization_diagnostics is deprecated; import llm_wiki_engine.normalization_diagnostics instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = normalization_diagnostics
