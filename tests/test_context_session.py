"""Session invalidation, detached ownership, deltas and resource boundaries."""

from dataclasses import replace
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_session
from llm_wiki_cli.services.context_session import build_delta
from tests import test_task_context as task_fixtures
from tests.test_task_context import request

project = task_fixtures.project


def _full(reply: api.SessionReply) -> api.TaskContext:
    assert reply.state == "full" and reply.context is not None
    return reply.context


def test_warm_unchanged_is_validated_and_cache_off_matches_cold(project, monkeypatch):
    session = api.open_context_session()
    cold = session.read(request())
    assert cold.state == "full" and not cold.metadata()["reuse"]["capture"]
    calls = 0
    original = context_session.packets._assert_source_unchanged

    def observe(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(context_session.packets, "_assert_source_unchanged", observe)
    warm = session.read(request(), if_result_id=cold.result_id)
    assert warm.state == "unchanged" and warm.context is None
    assert warm.metadata()["reuse"]["rendering"] and calls >= 2
    fresh = session.read(request(), reuse=False)
    assert _full(fresh).rendered == _full(cold).rendered
    assert fresh.metadata()["work"]["captures"] == 1


@pytest.mark.parametrize("mutation", ["source", "same-metadata", "delete", "ignore", "wiki", "untracked"])
def test_supported_mutations_never_return_false_unchanged(project, mutation):
    wiki = project / "docs/llm_wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# Guide\nOriginal reason.\n")
    req = request()
    if mutation == "untracked":
        req = request("limit", options={"read_scope": "full-inventory"})
    session = api.open_context_session(policy=api.WorkflowPolicy(read_scope="full-inventory"))
    first = session.read(req)
    source = project / "app.py"
    if mutation in {"source", "same-metadata"}:
        info = source.stat()
        source.write_text(source.read_text().replace("= 3", "= 4"))
        if mutation == "same-metadata":
            os.utime(source, ns=(info.st_atime_ns, info.st_mtime_ns))
    elif mutation == "delete":
        source.unlink()
    elif mutation == "ignore":
        (project / ".gitignore").write_text("app.py\n")
    elif mutation == "wiki":
        (wiki / "index.md").write_text("# Guide\nChanged reason.\n")
    else:
        (project / "other.py").write_text("def limit(value=12):\n    return value\n")
    current = session.read(req, if_result_id=first.result_id)
    assert current.state == "full" and current.result_id != first.result_id
    assert _full(current).rendered == api.build_task_context(req,
        policy=api.WorkflowPolicy(read_scope="full-inventory")).rendered


def test_returned_maps_cannot_mutate_cache_and_corrupt_cache_falls_back(project):
    session = api.open_context_session()
    first = session.read(request())
    payload = _full(first).to_payload()
    payload["facts"][0]["observation"]["contract"]["params"][0]["default"] = "999"
    metadata = first.metadata()
    metadata["work"]["retained_bytes"] = 0
    assert _full(session.read(request())).rendered == _full(first).rendered
    key, entry = next(iter(session._entries.items()))
    broken = api.TaskContext(True, '{"schema_version":"wrong"}\n', {})
    session._entries[key] = replace(entry, read=replace(entry.read, result=broken))
    recovered = session.read(request())
    assert _full(recovered).rendered == _full(first).rendered
    assert recovered.metadata()["reuse"]["capture"] is False


def test_delta_reconstruction_covers_deleted_facts_and_wrong_base(project):
    req = request()
    base = api.build_task_context(req)
    (project / "app.py").unlink()
    current = api.build_task_context(req)
    delta = build_delta(base, current)
    assert delta["updates"]["facts"] == []
    rebuilt = api.apply_task_delta(base.rendered, delta, req)
    assert rebuilt.rendered == current.rendered
    with pytest.raises(api.InvalidRequestError, match="base"):
        api.apply_task_delta(current.rendered, delta, req)
    corrupt = {**delta, "result_id": "sha256:" + "a" * 64}
    with pytest.raises(api.InvalidRequestError, match="identity"):
        api.apply_task_delta(base.rendered, corrupt, req)
    corrupt = {**delta, "removals": ["facts", "facts"]}
    with pytest.raises(api.InvalidRequestError):
        api.apply_task_delta(base.rendered, corrupt, req)


def test_session_delta_or_bounded_full_fallback_equals_cold(project):
    session = api.open_context_session()
    first = session.read(request())
    source = project / "app.py"
    source.write_text(source.read_text().replace("= 3", "= 4"))
    second = session.read(request(), if_result_id=first.result_id, delta=True)
    if second.state == "delta":
        assert second.delta is not None
        result = api.apply_task_delta(_full(first).rendered, second.delta, request())
    else:
        assert second.state == "full"
        result = _full(second)
    assert result.rendered == api.build_task_context(request()).rendered
    missing_base = session.read(request(), if_result_id="sha256:" + "0" * 64, delta=True)
    assert missing_base.state == "full"


def test_expiry_eviction_disablement_and_close_are_bounded(project, monkeypatch):
    tick = 100.0
    monkeypatch.setattr(context_session.time, "monotonic", lambda: tick)
    session = api.open_context_session(max_entries=1, ttl_seconds=1)
    first = session.read(request())
    assert first.metadata()["work"]["entries"] == 1
    session.read(request("app.py:caller"))
    assert len(session._entries) == 1
    assert not session.read(request()).metadata()["reuse"]["rendering"]
    tick += 2
    assert not session.read(request()).metadata()["reuse"]["capture"]
    session.close()
    assert not session._entries and session._bytes == 0
    with pytest.raises(api.InvalidRequestError, match="closed"):
        session.read(request())
    for max_entries, max_bytes in ((0, 16_777_216), (8, 1)):
        disabled = api.open_context_session(max_entries=max_entries, max_bytes=max_bytes)
        assert _full(disabled.read(request())).rendered == _full(first).rendered
        assert disabled._bytes == 0


def test_hints_are_optional_unsaved_buffers_defer_and_cancellation_drops_cache(project):
    session = api.open_context_session()
    session.read(request())
    for _ in range(3):
        session.hint()
    assert not session.read(request()).metadata()["reuse"]["capture"]
    session.hint(unsaved_buffers=True)
    with pytest.raises(api.InvalidRequestError, match="unsaved"):
        session.read(request())
    session.hint(unsaved_buffers=False)
    assert _full(session.read(request())).ok
    with pytest.raises(api.InvalidRequestError, match="cancelled"):
        session.read(request(), cancelled=lambda: True)
    assert session._bytes == 0


def test_task_budget_and_counter_changes_do_not_reuse_rendering(project):
    session = api.open_context_session()
    first = session.read(request())
    for req in (request(text="different task"), request(options={"budget_tokens": 16000}),
                request("app.py:Other.limit")):
        actual = session.read(req)
        assert not actual.metadata()["reuse"]["rendering"]
        assert _full(actual).rendered == api.build_task_context(req).rendered
    assert first.result_id != actual.result_id


def test_workspaces_and_symlink_replacement_cannot_share_authority(project, monkeypatch):
    session = api.open_context_session()
    session.read(request())
    other = project / "other"
    other.mkdir()
    (other / "app.py").write_text("def limit(value=9):\n    return value\n")
    monkeypatch.chdir(other)
    with pytest.raises(api.InvalidRequestError, match="working directory"):
        session.read(request())
    other_result = api.open_context_session().read(request())
    assert _full(other_result).to_payload()["facts"][0]["observation"]["contract"]["params"][0]["default"] == "9"


def test_source_root_link_replacement_is_rejected_on_the_native_platform(project):
    source = project / "src"
    source.mkdir()
    (source / "app.py").write_text("def limit(value=3):\n    return value\n")
    session = api.open_context_session(src_dir="src")
    session.read(request())
    source.rename(project / "original-src")
    replacement = project / "replacement"
    replacement.mkdir()
    (replacement / "app.py").write_text("def limit(value=9):\n    return value\n")
    if os.name == "nt":
        created = subprocess.run(["cmd", "/c", "mklink", "/J", str(source), str(replacement)],
                                 capture_output=True, timeout=10)
        assert created.returncode == 0, created.stderr
    else:
        source.symlink_to(replacement, target_is_directory=True)
    try:
        with pytest.raises(api.InvalidRequestError, match="symlinks|reparse"):
            session.read(request())
    finally:
        source.rmdir() if os.name == "nt" else source.unlink()


def test_concurrent_reads_are_serialized_and_keep_detached_results(project):
    session = api.open_context_session(max_entries=2, max_bytes=1_048_576)
    with ThreadPoolExecutor(max_workers=4) as workers:
        replies = list(workers.map(lambda _: session.read(request()), range(8)))
    assert len({_full(reply).rendered for reply in replies}) == 1
    assert all(reply.metadata()["work"]["retained_bytes"] <= 1_048_576 for reply in replies)
    assert len(session._entries) <= 2


def test_capture_reuse_replans_new_intent_without_reextracting(project, monkeypatch):
    session = api.open_context_session()
    session.read(request())
    changed = request(text="inspect again with a different intent", options={"budget_tokens": 16000})
    expected = api.build_task_context(changed)
    monkeypatch.setattr(context_session.packets, "capture_context_read", lambda *a, **k: pytest.fail("duplicate extraction"))
    result = session.read(changed)
    assert result.metadata()["reuse"] == {"capture": True, "selection": False, "rendering": False}
    assert _full(result).rendered == expected.rendered


def test_cancellation_during_a_cold_read_releases_prior_entries(project):
    session = api.open_context_session()
    session.read(request())
    calls = 0

    def cancelled():
        nonlocal calls
        calls += 1
        return calls >= 3

    with pytest.raises(api.WorkspaceStateError, match="cancelled"):
        session.read(request(text="changed intent"), cancelled=cancelled)
    assert not session._entries and session._bytes == 0


@pytest.mark.parametrize("retain_owner", [False, True])
def test_foreign_capture_is_rejected_even_when_request_and_environment_keys_collide(project, retain_owner):
    for name, default in (("a", 3), ("b", 9)):
        source = project / name
        source.mkdir()
        (source / "app.py").write_text(f"def limit(value={default}):\n    return value\n")
    with api.open_context_session(src_dir="a", wiki_dir="wiki-a") as first, api.open_context_session(src_dir="b", wiki_dir="wiki-b") as second:
        first.read(request())
        foreign = second.read(request())
        key = next(iter(first._entries))
        foreign_entry = next(iter(second._entries.values()))
        assert key == next(iter(second._entries))
        first._entries[key] = replace(foreign_entry, owner=first._owner) if retain_owner else foreign_entry
        result = first.read(request(), if_result_id=foreign.result_id, delta=True)
        assert result.state == "full"
        assert result.metadata()["reuse"]["capture"] is False
        assert _full(result).to_payload()["facts"][0]["observation"]["contract"]["params"][0]["default"] == "3"
