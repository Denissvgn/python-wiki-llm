"""Deprecated alias for :mod:`llm_wiki_engine.context_budget_format`."""

import sys
import warnings

from llm_wiki_engine import context_budget_format

warnings.warn(
    "llm_wiki_cli.services.context_budget_format is deprecated; import llm_wiki_engine.context_budget_format instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = context_budget_format
