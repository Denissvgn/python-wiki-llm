"""Deprecated alias for :mod:`llm_wiki_engine.sync_manifest`."""

import sys
import warnings

from llm_wiki_engine import sync_manifest

warnings.warn(
    "llm_wiki_cli.services.sync_manifest is deprecated; import llm_wiki_engine.sync_manifest instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = sync_manifest
