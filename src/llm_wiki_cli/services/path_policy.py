"""Deprecated alias for :mod:`llm_wiki_engine.path_policy`."""

import sys
import warnings

from llm_wiki_engine import path_policy

warnings.warn(
    "llm_wiki_cli.services.path_policy is deprecated; import llm_wiki_engine.path_policy instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = path_policy
