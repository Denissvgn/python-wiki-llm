"""Deprecated alias for :mod:`llm_wiki_engine.task_contract`."""

import sys
import warnings

from llm_wiki_engine import task_contract

warnings.warn(
    "llm_wiki_cli.services.task_contract is deprecated; import llm_wiki_engine.task_contract instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = task_contract
