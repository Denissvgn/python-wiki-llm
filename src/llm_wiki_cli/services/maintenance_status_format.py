"""Deprecated alias for :mod:`llm_wiki_engine.maintenance_status_format`."""

import sys
import warnings

from llm_wiki_engine import maintenance_status_format

warnings.warn(
    "llm_wiki_cli.services.maintenance_status_format is deprecated; import llm_wiki_engine.maintenance_status_format instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = maintenance_status_format
