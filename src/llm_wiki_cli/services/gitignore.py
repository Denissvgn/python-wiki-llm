"""Deprecated alias for :mod:`llm_wiki_engine.gitignore`."""

import sys
import warnings

from llm_wiki_engine import gitignore

warnings.warn(
    "llm_wiki_cli.services.gitignore is deprecated; import llm_wiki_engine.gitignore instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = gitignore
