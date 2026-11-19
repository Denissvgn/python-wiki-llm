"""Deprecated alias for :mod:`llm_wiki_engine.contracts`."""

import sys
import warnings

from llm_wiki_engine import contracts

warnings.warn(
    "llm_wiki_cli.services.contracts is deprecated; import llm_wiki_engine.contracts instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = contracts
