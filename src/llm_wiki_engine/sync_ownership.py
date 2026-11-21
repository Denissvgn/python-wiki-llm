"""Errors raised when a sync cannot keep verified page ownership."""

from __future__ import annotations


class SyncOwnershipError(ValueError):
    """A page cannot be safely assigned to one recorded source entity."""


class PageTransitionError(SyncOwnershipError):
    """The intended page writes cannot preserve verified ownership."""


__all__ = ["PageTransitionError", "SyncOwnershipError"]
