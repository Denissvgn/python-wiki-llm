"""Deprecated alias for :mod:`llm_wiki_engine.request_json`."""

import sys
import warnings

from llm_wiki_engine import request_json

warnings.warn(
    "llm_wiki_cli.services.request_json is deprecated; import llm_wiki_engine.request_json instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = request_json
