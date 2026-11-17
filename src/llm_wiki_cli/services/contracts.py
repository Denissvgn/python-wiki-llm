"""Compatibility alias for :mod:`llm_wiki_engine.contracts`."""

import sys

from llm_wiki_engine import contracts

sys.modules[__name__] = contracts
