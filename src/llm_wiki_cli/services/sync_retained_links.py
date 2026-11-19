"""Deprecated alias for :mod:`llm_wiki_engine.sync_retained_links`."""

import sys
import warnings

from llm_wiki_engine import sync_retained_links

warnings.warn(
    "llm_wiki_cli.services.sync_retained_links is deprecated; import llm_wiki_engine.sync_retained_links instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = sync_retained_links
