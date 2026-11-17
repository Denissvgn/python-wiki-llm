"""Compatibility alias for :mod:`llm_wiki_engine.path_policy`."""

import sys

from llm_wiki_engine import path_policy

sys.modules[__name__] = path_policy
