"""Compatibility alias for :mod:`llm_wiki_engine.query_result_format`."""

import sys

from llm_wiki_engine import query_result_format

sys.modules[__name__] = query_result_format
