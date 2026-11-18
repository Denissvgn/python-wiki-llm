"""Deprecated alias for :mod:`llm_wiki_engine.maintenance_queue_format`."""

import sys
import warnings

from llm_wiki_engine import maintenance_queue_format

warnings.warn(
    "llm_wiki_cli.services.maintenance_queue_format is deprecated; import llm_wiki_engine.maintenance_queue_format instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = maintenance_queue_format
