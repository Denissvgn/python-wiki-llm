"""Deprecated alias for :mod:`llm_wiki_engine.freshness_wording`."""

import sys
import warnings

from llm_wiki_engine import freshness_wording

warnings.warn(
    "llm_wiki_cli.services.freshness_wording is deprecated; import llm_wiki_engine.freshness_wording instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = freshness_wording
