"""Deprecated alias for :mod:`llm_wiki_engine.markdown_sections`."""

import sys
import warnings

from llm_wiki_engine import markdown_sections

warnings.warn(
    "llm_wiki_cli.services.markdown_sections is deprecated; import llm_wiki_engine.markdown_sections instead",
    DeprecationWarning,
    stacklevel=2,
)
sys.modules[__name__] = markdown_sections
