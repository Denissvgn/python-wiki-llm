"""Deprecated alias for :mod:`llm_wiki_engine.section_ownership`."""

import sys
import warnings

from llm_wiki_engine import section_ownership

warnings.warn(
    "llm_wiki_cli.services.section_ownership is deprecated; import llm_wiki_engine.section_ownership instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = section_ownership
