"""Compatibility alias for :mod:`llm_wiki_engine.sync_retained_links`."""

import sys

from llm_wiki_engine import sync_retained_links

sys.modules[__name__] = sync_retained_links
