"""Compatibility alias for :mod:`llm_wiki_engine.secure_file`."""

import sys

from llm_wiki_engine import secure_file

sys.modules[__name__] = secure_file
