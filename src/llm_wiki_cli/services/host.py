"""Compatibility alias for :mod:`llm_wiki_engine.host`."""

import sys

from llm_wiki_engine import host

sys.modules[__name__] = host
