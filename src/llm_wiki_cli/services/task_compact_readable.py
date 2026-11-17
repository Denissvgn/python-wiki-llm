"""Compatibility alias for :mod:`llm_wiki_engine.task_compact_readable`."""

import sys

from llm_wiki_engine import task_compact_readable

sys.modules[__name__] = task_compact_readable
