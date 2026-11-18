"""Deprecated alias for :mod:`llm_wiki_engine.canonical_json`."""

import sys
import warnings

from llm_wiki_engine import canonical_json

warnings.warn(
    "llm_wiki_cli.services.canonical_json is deprecated; import llm_wiki_engine.canonical_json instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = canonical_json
