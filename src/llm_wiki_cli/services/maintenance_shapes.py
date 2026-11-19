"""Deprecated alias for :mod:`llm_wiki_engine.maintenance_shapes`."""

import sys
import warnings

from llm_wiki_engine import maintenance_shapes

warnings.warn(
    "llm_wiki_cli.services.maintenance_shapes is deprecated; import llm_wiki_engine.maintenance_shapes instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = maintenance_shapes
