"""Deprecated alias for :mod:`llm_wiki_engine.maintenance_evidence`."""

import sys
import warnings

from llm_wiki_engine import maintenance_evidence

warnings.warn(
    "llm_wiki_cli.services.maintenance_evidence is deprecated; import llm_wiki_engine.maintenance_evidence instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = maintenance_evidence
