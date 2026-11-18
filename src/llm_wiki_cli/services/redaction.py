"""Deprecated alias for :mod:`llm_wiki_engine.redaction`."""

import sys
import warnings

from llm_wiki_engine import redaction

warnings.warn(
    "llm_wiki_cli.services.redaction is deprecated; import llm_wiki_engine.redaction instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = redaction
