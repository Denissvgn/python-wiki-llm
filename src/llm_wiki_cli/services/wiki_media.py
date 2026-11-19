"""Deprecated alias for :mod:`llm_wiki_engine.wiki_media`."""

import sys
import warnings

from llm_wiki_engine import wiki_media

warnings.warn(
    "llm_wiki_cli.services.wiki_media is deprecated; import llm_wiki_engine.wiki_media instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = wiki_media
