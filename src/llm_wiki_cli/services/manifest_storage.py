"""Compatibility alias for :mod:`llm_wiki_engine.manifest_storage`."""

import sys

from llm_wiki_engine import manifest_storage

sys.modules[__name__] = manifest_storage
