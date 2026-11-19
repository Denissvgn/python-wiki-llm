"""Deprecated alias for :mod:`llm_wiki_engine.query_result_format`."""

import sys
import warnings

from llm_wiki_engine import query_result_format

warnings.warn(
    "llm_wiki_cli.services.query_result_format is deprecated; import llm_wiki_engine.query_result_format instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = query_result_format
