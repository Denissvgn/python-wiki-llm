"""Compatibility alias for :mod:`llm_wiki_engine.request_json`."""

import sys

from llm_wiki_engine import request_json

sys.modules[__name__] = request_json
