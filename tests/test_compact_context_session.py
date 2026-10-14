"""Compact publication and exact canonical custody under real session ownership."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_session, task_compact_delivery
from tests.developer_value.fixtures import POLICY_SOURCE
from tests.test_task_compact_receiving import tiny_request, view_options


@pytest.fixture(autouse=True, params=["v1", "v2"])
def view_version(request, monkeypatch):
    if request.param == "v2":
        monkeypatch.setattr(__import__(__name__, fromlist=["view_options"]), "view_options",
                            lambda budget=32000: {
                                "schema_version": "llm-wiki-task-view-request/v2",
                                "budget_tokens": budget,
                            })


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_bytes(POLICY_SOURCE.encode())
    return tmp_path


def session(**kwargs):
    return api.open_context_session(src_dir="src", wiki_dir="wiki", **kwargs)


def full(reply):
    assert reply.state == "full" and reply.view is not None and reply.canonical is not None
    assert reply.view.canonical_text == reply.canonical.rendered
    return reply.view


def receipt_identity(reply):
    assert reply.canonical is not None and reply.result_id is not None
    return reply.canonical.to_payload()["request_id"], reply.result_id


def test_exact_conditional_base_and_options_preserve_canonical_defaults(project):
    owner = session()
    req = tiny_request()
    first = owner.read_compact(req, view_options=view_options())
    full(first)
    warm = owner.read_compact(req, view_options=view_options(),
        if_result_id=first.result_id, if_view_id=first.view_id)
    assert warm.state == "unchanged" and warm.view is None
    assert warm.canonical == first.canonical
    assert warm.metadata()["reuse"]["rendering"]
    assert warm.metadata()["emitted_context_tokens"] == 0
    for opts, view in ((view_options(31999), first.view_id),
                       (view_options(), None), (view_options(), "sha256:" + "0" * 64)):
        current = owner.read_compact(req, view_options=opts,
            if_result_id=first.result_id, if_view_id=view)
        assert full(current).ok
    canonical = owner.read(req, if_result_id=first.result_id)
    assert canonical.state == "unchanged" and canonical.context is None


def test_missing_compact_base_never_borrows_canonical_only_entry(project):
    owner = session()
    req = tiny_request()
    canonical = owner.read(req)
    assert canonical.context is not None
    view = api.render_compact_task_context(canonical.context.rendered, req, view_options=view_options())
    current = owner.read_compact(req, view_options=view_options(),
        if_result_id=canonical.result_id, if_view_id=view.view_id)
    assert full(current).ok
    owner._receipts.clear()
    lost = owner.read_compact(req, view_options=view_options(),
        if_result_id=current.result_id, if_view_id=current.view_id)
    assert full(lost).ok


def test_exact_historical_receipt_and_current_failure_cannot_fallback(project):
    owner = session()
    req = tiny_request()
    first = owner.read_compact(req, view_options=view_options())
    identity = receipt_identity(first)
    saved = owner.canonical_receipt(*identity)
    assert saved.validation_scope == "historical-captured"
    assert saved.canonical == first.canonical
    assert owner.canonical_receipt(*identity, current=True).validation_scope == "current-revalidated"
    Path("src/policy.py").write_text(POLICY_SOURCE.replace("values[:limit]", "values[::-1]"))
    historical = owner.canonical_receipt(*identity)
    assert historical.canonical.rendered == saved.canonical.rendered
    with pytest.raises(api.WorkspaceStateError):
        owner.canonical_receipt(*identity, current=True)
    assert not owner._receipts and not owner._entries
    with pytest.raises(api.InvalidRequestError, match="not retained"):
        owner.canonical_receipt(*identity)


@pytest.mark.parametrize("bound", ["entries", "bytes", "expired", "lru", "close"])
def test_receipt_and_reuse_custody_share_limits(project, monkeypatch, bound):
    tick = 100.0
    monkeypatch.setattr(context_session.time, "monotonic", lambda: tick)
    owner = session(max_entries=0 if bound == "entries" else 1,
                    max_bytes=1 if bound == "bytes" else 16_777_216, ttl_seconds=1)
    first = owner.read_compact(tiny_request(), view_options=view_options())
    full(first)
    identity = receipt_identity(first)
    if bound == "expired":
        tick += 2
    elif bound == "lru":
        other = tiny_request()
        other["text"] = "independent task"
        owner.read_compact(other, view_options=view_options())
        assert len(owner._custody) == 1
    elif bound == "close":
        owner.close()
    with pytest.raises(api.InvalidRequestError):
        owner.canonical_receipt(*identity)
    assert owner._bytes == 0 and not owner._entries and not owner._receipts


def test_lru_touch_keeps_exact_receipt_and_combined_memory_accounting(project):
    owner = session(max_entries=2)
    first = owner.read_compact(tiny_request(), view_options=view_options())
    second_req = {**tiny_request(), "text": "second"}
    second = owner.read_compact(second_req, view_options=view_options())
    owner.canonical_receipt(*receipt_identity(first))
    third = owner.read_compact({**tiny_request(), "text": "third"}, view_options=view_options())
    assert len(owner._custody) == 2 and owner._bytes <= owner._max_bytes
    assert owner._bytes == context_session._memory_size((owner._entries, owner._receipts, owner._custody))
    assert owner.canonical_receipt(*receipt_identity(first)).canonical == first.canonical
    assert owner.canonical_receipt(*receipt_identity(third)).canonical == third.canonical
    with pytest.raises(api.InvalidRequestError):
        owner.canonical_receipt(*receipt_identity(second))


@pytest.mark.parametrize("unavailable", ["git", "producer", "helper"])
def test_receipt_only_never_authorizes_reuse_conditional_delta_or_current(project, monkeypatch, unavailable):
    if unavailable == "helper":
        original = context_session.build_task_read
        def build(*args, **kwargs):
            read = original(*args, **kwargs)
            assert read.scoped_state is not None
            read.scoped_state = replace(read.scoped_state, cacheable=False)
            return read
        monkeypatch.setattr(context_session, "build_task_read", build)
    else:
        monkeypatch.setattr(context_session, "_git_identity" if unavailable == "git" else "_producer_identity",
                            lambda *a, **kw: None)
    owner = session()
    first = owner.read_compact(tiny_request(), view_options=view_options())
    assert not owner._entries and len(owner._receipts) == 1
    assert owner.canonical_receipt(*receipt_identity(first)).canonical == first.canonical
    again = owner.read_compact(tiny_request(), view_options=view_options(),
        if_result_id=first.result_id, if_view_id=first.view_id, delta=True)
    assert full(again).ok and again.delta is None
    assert not again.metadata()["reuse"]["capture"]
    with pytest.raises(api.InvalidRequestError, match="historical only"):
        owner.canonical_receipt(*receipt_identity(again), current=True)


def test_no_repository_identity_keeps_existing_reuse_policy(project):
    assert context_session._git_identity(Path("src")) == {"state": "no-git"}
    owner = session()
    first = owner.read_compact(tiny_request(), view_options=view_options())
    again = owner.read_compact(tiny_request(), view_options=view_options(),
        if_result_id=first.result_id, if_view_id=first.view_id)
    assert again.state == "unchanged" and again.metadata()["reuse"]["capture"]


def test_compact_budget_failure_retains_valid_canonical_and_never_returns_unchanged(project):
    owner = session()
    first = owner.read_compact(tiny_request(), view_options=view_options(1000))
    view = full(first)
    assert not view.ok and view.error == "cannot-fit-compact" and not view.rendered
    assert view.diagnostic_rendered and first.view_id is None
    assert owner.canonical_receipt(*receipt_identity(first)).canonical == first.canonical
    again = owner.read_compact(tiny_request(), view_options=view_options(1000), if_result_id=first.result_id)
    assert not full(again).ok
    one_shot = task_compact_delivery.build_compact_task_context(tiny_request(),
        view_options=view_options(1000), src_dir="src", wiki_dir="wiki")
    assert one_shot.canonical_text == view.canonical_text and not one_shot.ok


def test_failed_canonical_is_not_salvaged_or_held(project):
    owner = session()
    req = deepcopy(tiny_request())
    req["options"]["budget_tokens"] = 1
    assert not api.build_task_context(req, src_dir="src", wiki_dir="wiki").ok
    with pytest.raises(api.InvalidRequestError, match="unsuccessful canonical"):
        owner.read_compact(req, view_options=view_options(1))
    assert not owner._receipts and not owner._entries


@pytest.mark.parametrize("one_shot", [False, True])
@pytest.mark.parametrize("budget", [1000, 32000])
def test_view_render_race_is_guarded_even_for_failure_diagnostics(project, monkeypatch, one_shot, budget):
    original = context_session.render_compact_task_context
    def mutate(*args, **kwargs):
        view = original(*args, **kwargs)
        Path("src/policy.py").write_text(POLICY_SOURCE.replace("values[:limit]", "values[::-1]"))
        return view
    monkeypatch.setattr(context_session, "render_compact_task_context", mutate)
    owner = session()
    with pytest.raises((api.WorkspaceStateError, context_session.packets.ContextPacketSourceMutationError)):
        if one_shot:
            task_compact_delivery.build_compact_task_context(tiny_request(),
                view_options=view_options(budget), src_dir="src", wiki_dir="wiki")
        else:
            owner.read_compact(tiny_request(), view_options=view_options(budget))
    assert not owner._entries and not owner._receipts


@pytest.mark.parametrize("mutation", ["source", "root", "producer", "unsaved", "cancel", "close"])
def test_callbacks_before_publication_cannot_leave_false_live_view(project, monkeypatch, mutation):
    owner = session()
    original = context_session.render_compact_task_context
    cancel = False
    def mutate(*args, **kwargs):
        nonlocal cancel
        view = original(*args, **kwargs)
        if mutation == "source":
            Path("src/policy.py").write_text(POLICY_SOURCE + "\n# changed\n")
        elif mutation == "root":
            Path("src").rename("original-src")
            Path("src").mkdir()
            Path("src/policy.py").write_bytes(POLICY_SOURCE.encode())
        elif mutation == "producer":
            monkeypatch.setattr(context_session, "_producer_identity", lambda *a, **kw: "changed")
        elif mutation == "unsaved":
            owner.hint(unsaved_buffers=True)
        elif mutation == "close":
            owner.close()
        else:
            cancel = True
        return view
    monkeypatch.setattr(context_session, "render_compact_task_context", mutate)
    with pytest.raises((api.WorkspaceStateError, api.InvalidRequestError)):
        owner.read_compact(tiny_request(), view_options=view_options(), cancelled=lambda: cancel)
    assert not owner._entries and not owner._receipts


def test_exact_counter_callback_after_view_work_is_inside_final_guard(project):
    class MutatingCounter:
        identity = "test-delivery-callback"
        exact = True
        armed = False
        def count(self, text):
            if self.armed and '"view_id"' in text:
                self.armed = False
                Path("src/policy.py").write_text(POLICY_SOURCE.replace("values[:limit]", "values[::-1]"))
            return len(text)
    counter = MutatingCounter()
    owner = session(counter=counter)
    # Arm only after the canonical read; mutation occurs in actual view count.
    original = context_session.render_compact_task_context
    def arm(*args, **kwargs):
        counter.armed = True
        return original(*args, **kwargs)
    from unittest.mock import patch
    with patch.object(context_session, "render_compact_task_context", arm):
        with pytest.raises(api.WorkspaceStateError):
            owner.read_compact(tiny_request(), view_options=view_options())
    assert not owner._receipts and not owner._entries


def test_concurrent_compact_reads_have_exact_owned_receipts(project):
    owner = session()
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: owner.read_compact(tiny_request(), view_options=view_options()), range(2)))
    assert full(replies[0]).rendered == full(replies[1]).rendered
    assert owner.canonical_receipt(*receipt_identity(replies[0])).canonical == replies[1].canonical
    metadata = replies[0].metadata()
    metadata["work"]["retained_bytes"] = 0
    assert owner._bytes > 0
    view = full(replies[0])
    assert isinstance(view.accounting, dict)
    with pytest.raises(TypeError, match="immutable"):
        view.accounting["used_tokens"] = 0


@pytest.mark.parametrize("one_shot", [False, True])
def test_cancellation_triggered_by_final_portable_validation_clears_custody(project, one_shot):
    import inspect
    from llm_wiki_cli.services.token_counting import EstimatedCounter
    flag = False
    class CancellingCounter(EstimatedCounter):
        def count(self, text):
            nonlocal flag
            if any(frame.function == "_check_publication" for frame in inspect.stack()):
                flag = True
            return super().count(text)
    owner = session(counter=CancellingCounter())
    with pytest.raises(api.InvalidRequestError, match="cancelled"):
        if one_shot:
            api.build_compact_task_context(tiny_request(), view_options=view_options(),
                src_dir="src", wiki_dir="wiki", counter=CancellingCounter(), cancelled=lambda: flag)
        else:
            owner.read_compact(tiny_request(), view_options=view_options(), cancelled=lambda: flag)
    assert flag and not owner._entries and not owner._receipts


def test_non_cancelling_callback_mutation_is_checked_after_last_counter(project):
    import inspect
    def cancelled():
        if any(frame.function == "_publication_cancelled" for frame in inspect.stack()):
            Path("src/policy.py").write_text(POLICY_SOURCE + "\n# cancellation callback edit\n")
        return False
    owner = session()
    with pytest.raises(api.WorkspaceStateError):
        owner.read_compact(tiny_request(), view_options=view_options(), cancelled=cancelled)
    assert not owner._receipts and not owner._entries


def test_current_receipt_counter_cancellation_never_falls_back_historical(project):
    import inspect
    from llm_wiki_cli.services.token_counting import EstimatedCounter
    flag = False
    armed = False
    class Counter(EstimatedCounter):
        def count(self, text):
            nonlocal flag
            if armed and any(frame.function == "_check_publication" for frame in inspect.stack()):
                flag = True
            return super().count(text)
    owner = session(counter=Counter())
    first = owner.read_compact(tiny_request(), view_options=view_options())
    armed = True
    with pytest.raises(api.InvalidRequestError, match="cancelled"):
        owner.canonical_receipt(*receipt_identity(first), current=True, cancelled=lambda: flag)
    assert flag and not owner._receipts and not owner._entries


def test_view_request_is_strict_and_receipt_ids_are_session_owned(project):
    owner = session()
    invalid_options: Any = {"budget_tokens": True}
    with pytest.raises(api.InvalidRequestError, match="budget"):
        owner.read_compact(tiny_request(), view_options=invalid_options)
    first = owner.read_compact(tiny_request(), view_options=view_options())
    other = session()
    with pytest.raises(api.InvalidRequestError, match="not retained"):
        other.canonical_receipt(*receipt_identity(first))
    invalid_current: Any = 1
    with pytest.raises(api.InvalidRequestError):
        owner.canonical_receipt(*receipt_identity(first), current=invalid_current)


def test_legacy_canonical_default_survives_but_compact_v1_request_refuses_before_capture(project, monkeypatch):
    owner = session()
    request = {"schema_version": "llm-wiki-task-request/v1"}
    canonical = owner.read(request)
    assert canonical.context is not None
    monkeypatch.setattr(context_session, "build_task_read", lambda *a, **kw: pytest.fail("unsupported compact capture"))
    with pytest.raises(api.InvalidRequestError, match="task v2"):
        owner.read_compact(request, view_options=view_options())


def test_corrupted_valid_receipt_never_returns_different_bytes_under_old_id(project):
    owner = session()
    req = tiny_request()
    first = owner.read_compact(req, view_options=view_options())
    identity = receipt_identity(first)
    saved = owner._receipts[identity]
    Path("src/policy.py").write_text(POLICY_SOURCE.replace("limit: int = 3", "limit: int = 4"))
    current = api.build_task_context(req, src_dir="src", wiki_dir="wiki")
    assert current.ok and current.result_id != first.result_id
    api.validate_task_context(current.rendered, req)
    owner._receipts[identity] = replace(saved,
        entry=replace(saved.entry, read=replace(saved.entry.read, result=current)))
    with pytest.raises(api.InvalidRequestError, match="identity does not match"):
        owner.canonical_receipt(*identity)
    assert not owner._receipts and not owner._entries
