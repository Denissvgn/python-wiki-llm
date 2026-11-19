"""Deprecated alias for :mod:`llm_wiki_engine.filesystem_guard`."""

import sys
import warnings

from llm_wiki_engine import filesystem_guard

warnings.warn(
    "llm_wiki_cli.services.filesystem_guard is deprecated; import llm_wiki_engine.filesystem_guard instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = filesystem_guard
