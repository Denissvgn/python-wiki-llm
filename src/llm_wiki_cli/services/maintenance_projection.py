"""Deprecated alias for :mod:`llm_wiki_engine.maintenance_projection`."""

import sys
import warnings

from llm_wiki_engine import maintenance_projection

warnings.warn(
    "llm_wiki_cli.services.maintenance_projection is deprecated; import llm_wiki_engine.maintenance_projection instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = maintenance_projection
