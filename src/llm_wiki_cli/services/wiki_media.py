"""Compatibility alias for :mod:`llm_wiki_engine.wiki_media`."""

import sys

from llm_wiki_engine import wiki_media

sys.modules[__name__] = wiki_media
