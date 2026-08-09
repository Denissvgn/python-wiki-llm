"""Canonical bytes for a pristine wiki scaffold.

Bootstrap may replace the pristine scaffold content during first adoption. Any
other content under the target wiki directory belongs to an existing or partial
wiki and must be handled by sync or migration instead.
"""

from __future__ import annotations


INITIAL_WIKI_INDEX_MARKDOWN = (
    "# LLM Wiki Index\n\n"
    "Catalog of project modules and entities.\n\n"
    "## Entities\n\n"
    "## Modules\n\n"
    "## Workflows\n\n"
    "## Guides\n\n"
    "## Infrastructure\n"
)

INITIAL_WIKI_LOG_MARKDOWN = (
    "# Architectural Log\n\nAppend-only chronological log.\n\n"
)


__all__ = [
    "INITIAL_WIKI_INDEX_MARKDOWN",
    "INITIAL_WIKI_LOG_MARKDOWN",
]
