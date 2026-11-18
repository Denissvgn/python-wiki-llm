"""Compatibility alias for :mod:`llm_wiki_engine.storage_spool`."""

import sys

from llm_wiki_engine import storage_spool

sys.modules[__name__] = storage_spool
