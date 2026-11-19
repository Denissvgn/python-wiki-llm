"""Deprecated alias for :mod:`llm_wiki_engine.storage_sort`."""

import sys
import warnings

from llm_wiki_engine import storage_sort

warnings.warn(
    "llm_wiki_cli.services.storage_sort is deprecated; import llm_wiki_engine.storage_sort instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = storage_sort
