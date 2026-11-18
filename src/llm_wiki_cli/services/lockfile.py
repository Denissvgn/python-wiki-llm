"""Deprecated alias for :mod:`llm_wiki_engine.lockfile`."""

import sys
import warnings

from llm_wiki_engine import lockfile

warnings.warn(
    "llm_wiki_cli.services.lockfile is deprecated; import llm_wiki_engine.lockfile instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = lockfile
