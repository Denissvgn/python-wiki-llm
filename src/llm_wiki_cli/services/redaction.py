"""Compatibility alias for :mod:`llm_wiki_engine.redaction`."""

import sys

from llm_wiki_engine import redaction

sys.modules[__name__] = redaction
