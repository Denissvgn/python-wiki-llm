"""Deprecated alias for :mod:`llm_wiki_engine.storage_receipts`."""

import sys
import warnings

from llm_wiki_engine import storage_receipts

warnings.warn(
    "llm_wiki_cli.services.storage_receipts is deprecated; import llm_wiki_engine.storage_receipts instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = storage_receipts
