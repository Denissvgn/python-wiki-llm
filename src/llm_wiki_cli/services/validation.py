"""Compatibility alias for :mod:`llm_wiki_engine.validation`."""

import sys

from llm_wiki_engine import validation

sys.modules[__name__] = validation
