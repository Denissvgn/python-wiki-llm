"""Deprecated alias for :mod:`llm_wiki_engine.manifest_storage`."""

import sys
import warnings

from llm_wiki_engine import manifest_storage

warnings.warn(
    "llm_wiki_cli.services.manifest_storage is deprecated; import llm_wiki_engine.manifest_storage instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = manifest_storage
