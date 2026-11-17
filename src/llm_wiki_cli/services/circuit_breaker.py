"""Compatibility alias for :mod:`llm_wiki_engine.circuit_breaker`."""

import sys

from llm_wiki_engine import circuit_breaker

sys.modules[__name__] = circuit_breaker
