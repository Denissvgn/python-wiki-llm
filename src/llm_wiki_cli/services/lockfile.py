"""Compatibility alias for :mod:`llm_wiki_engine.lockfile`."""

import sys

from llm_wiki_engine import lockfile

sys.modules[__name__] = lockfile
