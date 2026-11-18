"""Deprecated alias for :mod:`llm_wiki_engine.validation`."""

import sys
import warnings

from llm_wiki_engine import validation

warnings.warn(
    "llm_wiki_cli.services.validation is deprecated; import llm_wiki_engine.validation instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = validation
