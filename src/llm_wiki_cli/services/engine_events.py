"""Deprecated alias for :mod:`llm_wiki_engine.engine_events`."""

import sys
import warnings

from llm_wiki_engine import engine_events

warnings.warn(
    "llm_wiki_cli.services.engine_events is deprecated; import llm_wiki_engine.engine_events instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = engine_events
