"""Compatibility alias for :mod:`llm_wiki_engine.storage_receipts`."""

import sys

from llm_wiki_engine import storage_receipts

sys.modules[__name__] = storage_receipts
