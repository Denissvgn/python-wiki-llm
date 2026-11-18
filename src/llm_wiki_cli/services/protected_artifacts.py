"""Deprecated alias for :mod:`llm_wiki_engine.protected_artifacts`."""

import sys
import warnings

from llm_wiki_engine import protected_artifacts

warnings.warn(
    "llm_wiki_cli.services.protected_artifacts is deprecated; import llm_wiki_engine.protected_artifacts instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = protected_artifacts
