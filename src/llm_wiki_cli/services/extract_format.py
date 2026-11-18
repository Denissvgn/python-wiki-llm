"""Deprecated alias for :mod:`llm_wiki_engine.extract_format`."""

import sys
import warnings

from llm_wiki_engine import extract_format

warnings.warn(
    "llm_wiki_cli.services.extract_format is deprecated; import llm_wiki_engine.extract_format instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = extract_format
