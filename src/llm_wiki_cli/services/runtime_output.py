"""Compatibility alias for :mod:`llm_wiki_engine.runtime_output`."""

import sys

from llm_wiki_engine import runtime_output

sys.modules[__name__] = runtime_output
