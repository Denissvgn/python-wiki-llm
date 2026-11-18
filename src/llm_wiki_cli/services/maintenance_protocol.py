"""Compatibility alias for :mod:`llm_wiki_engine.maintenance_protocol`."""

import sys

from llm_wiki_engine import maintenance_protocol

sys.modules[__name__] = maintenance_protocol
