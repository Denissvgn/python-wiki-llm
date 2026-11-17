"""Compatibility alias for :mod:`llm_wiki_engine.normalization_diagnostics`."""

import sys

from llm_wiki_engine import normalization_diagnostics

sys.modules[__name__] = normalization_diagnostics
