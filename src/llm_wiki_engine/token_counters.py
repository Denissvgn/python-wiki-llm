"""Token counters for budgeted output.

A budget is accounted with a :class:`TokenCounter`. The engine supplies
:class:`EstimatedCounter`; an exact counter (for example one backed by a
local tokenizer) is supplied by the host application and passed in.
"""

from __future__ import annotations

from typing import Protocol


class TokenCounter(Protocol):
    identity: str
    exact: bool

    def count(self, text: str) -> int: ...


class EstimatedCounter:
    identity = "utf8-ceil-div4/v1"
    exact = False

    def count(self, text: str) -> int:
        return (len(text.encode("utf-8")) + 3) // 4


__all__ = ["EstimatedCounter", "TokenCounter"]
