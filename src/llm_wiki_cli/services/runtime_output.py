"""Deprecated alias for :mod:`llm_wiki_engine.runtime_output`."""

import sys
import warnings

from llm_wiki_engine import runtime_output

warnings.warn(
    "llm_wiki_cli.services.runtime_output is deprecated; import llm_wiki_engine.runtime_output instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = runtime_output
