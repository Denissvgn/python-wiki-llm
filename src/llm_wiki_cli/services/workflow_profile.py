"""Deprecated alias for :mod:`llm_wiki_engine.workflow_profile`."""

import sys
import warnings

from llm_wiki_engine import workflow_profile

warnings.warn(
    "llm_wiki_cli.services.workflow_profile is deprecated; import llm_wiki_engine.workflow_profile instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = workflow_profile
