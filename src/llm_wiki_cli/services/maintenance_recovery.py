"""Compatibility alias for :mod:`llm_wiki_engine.maintenance_recovery`."""

import sys

from llm_wiki_engine import maintenance_recovery

sys.modules[__name__] = maintenance_recovery
