"""Deprecated alias for :mod:`llm_wiki_engine.verification_contracts`."""

import sys
import warnings

from llm_wiki_engine import verification_contracts

warnings.warn(
    "llm_wiki_cli.services.verification_contracts is deprecated; import llm_wiki_engine.verification_contracts instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = verification_contracts
