"""Compatibility alias for :mod:`llm_wiki_engine.protected_artifacts`."""

import sys

from llm_wiki_engine import protected_artifacts

sys.modules[__name__] = protected_artifacts
