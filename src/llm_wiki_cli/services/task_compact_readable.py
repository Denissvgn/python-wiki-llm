"""Deprecated alias for :mod:`llm_wiki_engine.task_compact_readable`."""

import sys
import warnings

from llm_wiki_engine import task_compact_readable

warnings.warn(
    "llm_wiki_cli.services.task_compact_readable is deprecated; import llm_wiki_engine.task_compact_readable instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = task_compact_readable
