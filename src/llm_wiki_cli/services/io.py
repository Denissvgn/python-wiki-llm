"""Compatibility alias for :mod:`llm_wiki_engine.io`."""

import sys

from llm_wiki_engine import io

sys.modules[__name__] = io
