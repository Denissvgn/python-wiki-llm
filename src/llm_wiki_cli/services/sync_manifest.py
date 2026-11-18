"""Compatibility alias for :mod:`llm_wiki_engine.sync_manifest`."""

import sys

from llm_wiki_engine import sync_manifest

sys.modules[__name__] = sync_manifest
