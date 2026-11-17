"""Compatibility alias for :mod:`llm_wiki_engine.filesystem_guard`."""

import sys

from llm_wiki_engine import filesystem_guard

sys.modules[__name__] = filesystem_guard
