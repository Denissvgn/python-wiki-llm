"""Compatibility alias for :mod:`llm_wiki_engine.canonical_json`."""

import sys

from llm_wiki_engine import canonical_json

sys.modules[__name__] = canonical_json
