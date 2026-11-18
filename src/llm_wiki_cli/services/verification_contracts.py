"""Compatibility alias for :mod:`llm_wiki_engine.verification_contracts`."""

import sys

from llm_wiki_engine import verification_contracts

sys.modules[__name__] = verification_contracts
