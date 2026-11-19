"""Deprecated alias for :mod:`llm_wiki_engine.concept_identity`."""

import sys
import warnings

from llm_wiki_engine import concept_identity

warnings.warn(
    "llm_wiki_cli.services.concept_identity is deprecated; import llm_wiki_engine.concept_identity instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = concept_identity
