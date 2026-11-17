"""Compatibility alias for :mod:`llm_wiki_engine.extract_format`."""

import sys

from llm_wiki_engine import extract_format

sys.modules[__name__] = extract_format
