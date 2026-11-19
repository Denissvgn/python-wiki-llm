"""Deprecated alias for :mod:`llm_wiki_engine.wiki_write_basis`."""

import sys
import warnings

from llm_wiki_engine import wiki_write_basis

warnings.warn(
    "llm_wiki_cli.services.wiki_write_basis is deprecated; import llm_wiki_engine.wiki_write_basis instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = wiki_write_basis
