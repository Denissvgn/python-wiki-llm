"""Deprecated alias for :mod:`llm_wiki_engine.secure_file`."""

import sys
import warnings

from llm_wiki_engine import secure_file

warnings.warn(
    "llm_wiki_cli.services.secure_file is deprecated; import llm_wiki_engine.secure_file instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = secure_file
