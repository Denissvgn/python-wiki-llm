"""One-shot compact delivery through the owned, locked task read lifecycle."""

from __future__ import annotations

from . import analysis_compatibility as ac
from ..config import DEFAULT_WIKI_DIR
from .context_session import ContextSession
from .task_compact import CompactTaskContext


@ac.bound_comparison
def build_compact_task_context(
    request, *, view_options=None, src_dir=".", wiki_dir=DEFAULT_WIKI_DIR,
    profile=None, policy=None, counter=None, allow_external_src=False,
    source_selection=None, helper_cache_dir=None, cancelled=None,
) -> CompactTaskContext:
    """Return a complete current view and its exact separately budgeted receipt."""
    with ContextSession(src_dir=src_dir, wiki_dir=wiki_dir, profile=profile,
            policy=policy, counter=counter, allow_external_src=allow_external_src,
            source_selection=source_selection, helper_cache_dir=helper_cache_dir,
            max_entries=0, max_bytes=0) as session:
        reply = session.read_compact(request, view_options=view_options, reuse=False,
                                     cancelled=cancelled)
        assert reply.view is not None
        return reply.view
