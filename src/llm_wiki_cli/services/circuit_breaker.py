"""Deprecated alias for :mod:`llm_wiki_engine.circuit_breaker`."""

import sys
import warnings

from llm_wiki_engine import circuit_breaker

warnings.warn(
    "llm_wiki_cli.services.circuit_breaker is deprecated; import llm_wiki_engine.circuit_breaker instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = circuit_breaker
