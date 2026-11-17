"""Compatibility alias for :mod:`llm_wiki_engine.engine_events`."""

import sys

from llm_wiki_engine import engine_events

sys.modules[__name__] = engine_events
