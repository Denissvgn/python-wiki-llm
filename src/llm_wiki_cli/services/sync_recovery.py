"""Compatibility alias for :mod:`llm_wiki_engine.sync_recovery`."""

import sys

from llm_wiki_engine import sync_recovery

sys.modules[__name__] = sync_recovery
